from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


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



class MedicineUpdate(BaseModel):
    
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=160)
    generic_name: str | None = Field(default=None, min_length=1, max_length=160)
    strength: str | None = Field(default=None, min_length=1, max_length=80)
    dosage_form: str | None = Field(default=None, min_length=1, max_length=80)

    @model_validator(mode="after")
    def validate_changes(self) -> "MedicineUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        return self