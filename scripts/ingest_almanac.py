import asyncio
import json
import math
import os
from urllib.request import Request, urlopen

from sqlalchemy import delete, select

import app.db.all_models
from app.db.session import SessionLocal
from app.modules.almanac.models import AlmanacChunk, AlmanacEntry


def make_passages(entry: AlmanacEntry) -> list[str]:
    words = entry.content.split()
    passages = []
    start = 0

    while start < len(words):
        end = min(start + 100, len(words))
        text = " ".join(words[start:end])
        passages.append(f"{entry.title}\n{entry.topic}\n{text}")
        if end == len(words):
            break
        start = end - 15

    return passages


def embed(passages: list[str]) -> list[list[float]]:
    base_url = os.getenv("EMBEDDING_BASE_URL", "http://embeddings")
    vectors = []

    for start in range(0, len(passages), 8):
        batch = passages[start:start + 8]
        request = Request(
            f"{base_url.rstrip('/')}/embed",
            data=json.dumps({"inputs": batch}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            result = json.load(response)

        if not isinstance(result, list) or len(result) != len(batch):
            raise ValueError("Embedding service returned an unexpected vector count")

        for vector in result:
            if (
                not isinstance(vector, list)
                or len(vector) != 384
                or not all(
                    type(value) in (float, int) and math.isfinite(value)
                    for value in vector
                )
            ):
                raise ValueError("Embedding service returned an invalid vector")

        vectors.extend(result)

    return vectors


async def main() -> None:
    async with SessionLocal() as session:
        entry_ids = list(await session.scalars(
            select(AlmanacEntry.id).order_by(AlmanacEntry.id)
        ))

    changed = 0
    skipped = 0

    for entry_id in entry_ids:
        async with SessionLocal.begin() as session:
            entry = await session.get(AlmanacEntry, entry_id, with_for_update=True)
            if entry is None:
                continue

            passages = make_passages(entry) if entry.is_active else []
            existing = list(await session.scalars(
                select(AlmanacChunk.content)
                .where(AlmanacChunk.entry_id == entry_id)
                .order_by(AlmanacChunk.chunk_index)
            ))

            if existing == passages:
                skipped += 1
                continue

            vectors = await asyncio.to_thread(embed, passages)
            await session.execute(
                delete(AlmanacChunk).where(AlmanacChunk.entry_id == entry_id)
            )
            session.add_all([
                AlmanacChunk(
                    entry_id=entry_id,
                    chunk_index=index,
                    content=passage,
                    embedding=vector,
                )
                for index, (passage, vector) in enumerate(
                    zip(passages, vectors, strict=True)
                )
            ])
        changed += 1

    print(f"Almanac ingest complete. Updated: {changed}. Unchanged: {skipped}.")


if __name__ == "__main__":
    asyncio.run(main())