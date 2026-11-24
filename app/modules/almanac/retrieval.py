import asyncio

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.almanac.models import AlmanacChunk, AlmanacEntry
from scripts.ingest_almanac import embed


class AlmanacPassage(BaseModel):
    slug: str
    title: str
    content: str
    source_note: str
    similarity: float




async def retrieve_passages(session: AsyncSession,question: str,*,limit: int = 3,min_similarity: float = 0.65,) -> list[AlmanacPassage]:
    
    
    question = question.strip()

    if not question:
        return []
    if not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    if not -1 <= min_similarity <= 1:
        raise ValueError("min_similarity must be between -1 and 1")


    
    vectors = await asyncio.to_thread(embed, [question])
    distance = AlmanacChunk.embedding.cosine_distance(vectors[0])


    statement = (
        select(
            AlmanacEntry.slug,
            AlmanacEntry.title,
            AlmanacChunk.content,
            AlmanacEntry.source_note,
            distance.label("distance"),
        )
        .select_from(AlmanacChunk)
        .join(AlmanacEntry, AlmanacEntry.id == AlmanacChunk.entry_id)
        .where(
            AlmanacEntry.is_active.is_(True),
            distance <= 1.0 - min_similarity,
        )
        .order_by(distance, AlmanacEntry.slug, AlmanacChunk.chunk_index)
        .limit(limit)
    )



    rows = (await session.execute(statement)).mappings()
    return [
        AlmanacPassage(
            slug=row["slug"],
            title=row["title"],
            content=row["content"],
            source_note=row["source_note"],
            similarity=1.0 - float(row["distance"]),
        )
        for row in rows
    ]