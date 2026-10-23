import type { Plant } from '../types/Plant';
import type { PlantApi } from '../types/PlantApi';
import type { PlantFormData } from '../types/PlantFormData';

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function apiPlantToPlant(plant: PlantApi): Plant {
  return {
    id: plant.id,
    name: plant.name,
    scientificName: plant.species,
    location: plant.location,
    acquiredDate: plant.date_acquired,
  };
}

function plantToApiPlant(plant: PlantFormData) {
  return {
    name: plant.name,
    species: plant.scientificName,
    location: plant.location,
    date_acquired: plant.acquiredDate,
  };
}

export async function getPlants(): Promise<Plant[]> {
  const response = await fetch(`${API_URL}/plants`);
  if (!response.ok) {
    throw new Error('Failed to fetch plants');
  }
  const data: PlantApi[] = await response.json();
  return data.map(apiPlantToPlant);
}

export async function getPlant(id: number): Promise<Plant> {
  const response = await fetch(`${API_URL}/plants/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch plant');
  }
  const data: PlantApi = await response.json();
  return apiPlantToPlant(data);
}

export async function createPlant(plant: PlantFormData): Promise<Plant> {
  const response = await fetch(`${API_URL}/plants`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(plantToApiPlant(plant)),
  });
  if (!response.ok) {
    throw new Error('Failed to add plant');
  }
  const data: PlantApi = await response.json();
  return apiPlantToPlant(data);
}

export async function updatePlant(id: number, plant: PlantFormData): Promise<Plant> {
  const response = await fetch(`${API_URL}/plants/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(plantToApiPlant(plant) as PlantApi),
  });
  if (!response.ok) {
    throw new Error('Failed to update plant');
  }
  const data: PlantApi = await response.json();
  return apiPlantToPlant(data);
}

export async function deletePlant(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/plants/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete plant');
  }
}