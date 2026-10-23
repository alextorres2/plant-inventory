from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import Plant as PlantSchema, PlantCreate

router = APIRouter(
    prefix="/plants",
    tags=["plants"]
)

@router.get("/", response_model=list[PlantSchema])
def get_plants(db: Session = Depends(get_db)):
    return db.query(models.Plant).all()

@router.get("/{plant_id}", response_model=PlantSchema)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant

@router.post("/", response_model=PlantSchema)
def create_plant(plant: PlantCreate, db: Session = Depends(get_db)):
    new_plant = models.Plant(**plant.model_dump())
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    return new_plant

@router.put("/{plant_id}", response_model=PlantSchema)
def update_plant(plant_id: int, updated_plant: PlantCreate, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    for field, value in updated_plant.model_dump().items():
        setattr(plant, field, value)

    db.commit()
    db.refresh(plant)
    return plant

@router.delete("/{plant_id}")
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.get(models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    db.delete(plant)
    db.commit()
    return {"message": "Plant deleted successfully"}