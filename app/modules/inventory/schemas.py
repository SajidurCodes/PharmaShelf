from pydantic import BaseModel


class AvailabilityRead(BaseModel):
    available: bool