from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app import models
from app.schemas import Plant as PlantSchema, PlantCreate

router = APIRouter(
    prefix="/plants",
    tags=["plants"]
)

plants: list[Plant] = [
    Plant(
        id=1,
        name="Monstera 1",
        species="Monstera deliciosa",
        location="Living Room",
        date_acquired="2023-01-15",
    ),
    Plant(
        id=2,
        name="Fiddle Leaf Fig",
        species="Ficus lyrata",
        location="Bedroom",
        date_acquired="2022-11-20",
    ),
]

@router.get("/", response_model=list[PlantSchema])
def get_plants(db: Session = Depends(get_db)):
    return db.query(models.Plant).all()

@router.get("/{plant_id}")
def get_plant(plant_id: int):
    for plant in plants:
        if plant.id == plant_id:
            return plant
    raise HTTPException(status_code=404, detail="Plant not found")

@router.post("/", response_model=Plant)
def create_plant(plant: PlantCreate):
    new_id = max(
        (plant.id for plant in plants),
        default=0
    ) + 1
    new_plant = Plant(
        id=new_id,
        name=plant.name,
        species=plant.species,
        location=plant.location,
        date_acquired=plant.date_acquired,
    )
    plants.append(new_plant)
    return new_plant

@router.put("/{plant_id}", response_model=Plant)
def update_plant(plant_id: int, updated_plant: PlantCreate):
    for index, plant in enumerate(plants):
        if plant.id == plant_id:
            plants[index] = Plant(
                id=plant_id,
                name=updated_plant.name,
                species=updated_plant.species,
                location=updated_plant.location,
                date_acquired=updated_plant.date_acquired,
            )
            return plants[index]
    raise HTTPException(status_code=404, detail="Plant not found")

@router.delete("/{plant_id}")
def delete_plant(plant_id: int):
    for index, plant in enumerate(plants):
        if plant.id == plant_id:
            plants.pop(index)
            return {"message": "Plant deleted successfully"}
    raise HTTPException(status_code=404, detail="Plant not found")