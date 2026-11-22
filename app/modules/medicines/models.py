from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    generic_name: Mapped[str] = mapped_column(String(160))
    strength: Mapped[str] = mapped_column(String(80))
    dosage_form: Mapped[str] = mapped_column(String(80))