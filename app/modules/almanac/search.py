import re

from pydantic import BaseModel
from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.almanac.models import AlmanacEntry


class AlmanacSearchHit(BaseModel):
    slug: str
    title: str
    topic: str
    content: str
    source_note: str


async def search_almanac(
    session: AsyncSession,
    question: str,
    *,
    limit: int = 3,
) -> list[AlmanacSearchHit]:
    if not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")

    words = re.findall(r"[^\W_]+", question.casefold())
    terms = list(dict.fromkeys(words))[:40]
    if not terms:
        return []

    query = func.websearch_to_tsquery("english", " OR ".join(terms))

    # PostgreSQL requires a "char" weight. Only these fixed labels are SQL literals.
    headings = func.setweight(
        func.to_tsvector("english", AlmanacEntry.title + " " + AlmanacEntry.topic),
        literal_column("""'A'::"char" """.strip()),
    )
    body = func.setweight(
        func.to_tsvector("english", AlmanacEntry.content),
        literal_column("""'B'::"char" """.strip()),
    )

    document = headings.op("||")(body)
    rank = func.ts_rank(document, query)

    statement = (
        select(AlmanacEntry)
        .where(
            AlmanacEntry.is_active.is_(True),
            document.bool_op("@@")(query),
        )
        .order_by(rank.desc(), AlmanacEntry.slug)
        .limit(limit)
    )

    entries = await session.scalars(statement)
    return [
        AlmanacSearchHit(
            slug=entry.slug,
            title=entry.title,
            topic=entry.topic,
            content=entry.content,
            source_note=entry.source_note,
        )
        for entry in entries
    ]