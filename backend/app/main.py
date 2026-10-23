import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import Plant, PlantCreate
from app.routers import plants

from app.database import Base, engine
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    origin.strip()
    for origin in os.getenv(
        "PLANT_INVENTORY_CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plants.router)

@app.get("/")
def root():
    return {"message": "Plant Inventory API!"}


