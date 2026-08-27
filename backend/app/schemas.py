from pydantic import BaseModel

class Plant(BaseModel):
    id: int
    name: str
    species: str
    location: str
    date_acquired: str

class PlantCreate(BaseModel):
    name: str
    species: str
    location: str
    date_acquired: str