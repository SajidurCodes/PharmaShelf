from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class AlmanacEntry(Base):
    __tablename__ = "almanac_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(80), index=True)

    content: Mapped[str] = mapped_column(Text)
    source_note: Mapped[str] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AlmanacChunk(Base):
    __tablename__ = "almanac_chunks"
    __table_args__ = (
        UniqueConstraint("entry_id", "chunk_index", name="uq_almanac_chunk_position"),
        CheckConstraint("chunk_index >= 0", name="ck_almanac_chunk_index"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("almanac_entries.id", ondelete="CASCADE"),
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(384), nullable=False)
