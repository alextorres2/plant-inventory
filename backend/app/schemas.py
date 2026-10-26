from datetime import date

from pydantic import BaseModel, ConfigDict

class PlantCreate(BaseModel):
    name: str
    species: str
    location: str
    date_acquired: date

class Plant(PlantCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latest_photo_url: str | None = None


class PlantPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_taken: date
    caption: str | None
    image_url: str