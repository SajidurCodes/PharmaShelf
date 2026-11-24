from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


EntrySlug = Annotated[
    str,
    Field(
        min_length=1,
        max_length=160,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
    ),
]
EntryTitle = Annotated[str, Field(min_length=1, max_length=200)]
EntryTopic = Annotated[str, Field(min_length=1, max_length=80)]
EntryText = Annotated[str, Field(min_length=1)]




class AlmanacEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: EntrySlug
    title: EntryTitle
    topic: EntryTopic
    content: EntryText
    source_note: EntryText
    is_active: bool = True


class AlmanacEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: EntryTitle | None = None
    topic: EntryTopic | None = None
    content: EntryText | None = None
    source_note: EntryText | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "AlmanacEntryUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")

        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


class AlmanacEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    topic: str
    content: str
    source_note: str
    is_active: bool
    created_at: datetime
    updated_at: datetime