from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MedicineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    generic_name: str
    strength: str
    dosage_form: str