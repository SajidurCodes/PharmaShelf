from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    generic_name: str
    strength: str
    dosage_form: str



class MedicineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    generic_name: str = Field(min_length=1, max_length=160)
    strength: str = Field(min_length=1, max_length=80)
    dosage_form: str = Field(min_length=1, max_length=80)