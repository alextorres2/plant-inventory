from pydantic import BaseModel, ConfigDict
from datetime import date

class PlantCreate(BaseModel):
    name: str
    species: str
    location: str
    date_acquired: date

class Plant(PlantCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int