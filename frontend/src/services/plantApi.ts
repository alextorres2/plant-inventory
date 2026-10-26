import type { Plant } from '../types/Plant';
import type { PlantApi } from '../types/PlantApi';
import type { PlantPhotoApi } from '../types/PlantApi';
import type { PlantFormData } from '../types/PlantFormData';
import type { PlantPhoto } from '../types/PlantPhoto';

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function apiPlantToPlant(plant: PlantApi): Plant {
  return {
    id: plant.id,
    name: plant.name,
    scientificName: plant.species,
    location: plant.location,
    acquiredDate: plant.date_acquired,
    latestPhotoUrl: plant.latest_photo_url ? `${API_URL}${plant.latest_photo_url}` : null,
  };
}

function apiPhotoToPhoto(photo: PlantPhotoApi): PlantPhoto {
  return {
    id: photo.id,
    dateTaken: photo.date_taken,
    caption: photo.caption,
    imageUrl: `${API_URL}${photo.image_url}`,
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

async function throwPhotoRequestError(response: Response, fallback: string): Promise<void> {
  if (response.ok) return;
  let message = fallback;
  try {
    const body: { detail?: unknown } = await response.json();
    if (typeof body.detail === 'string' && body.detail.trim()) message = body.detail;
  } catch {
    // Keep the readable fallback when the server did not return JSON.
  }
  throw new Error(message);
}

export async function getPlantPhotos(plantId: number): Promise<PlantPhoto[]> {
  const response = await fetch(`${API_URL}/plants/${plantId}/photos`);
  await throwPhotoRequestError(response, 'Unable to load plant photos.');
  const data: PlantPhotoApi[] = await response.json();
  return data.map(apiPhotoToPhoto);
}

export async function uploadPlantPhoto(
  plantId: number,
  file: File,
  dateTaken: string,
  caption: string,
): Promise<PlantPhoto> {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('date_taken', dateTaken);
  formData.append('caption', caption);

  const response = await fetch(`${API_URL}/plants/${plantId}/photos`, {
    method: 'POST',
    body: formData,
  });
  await throwPhotoRequestError(response, 'Unable to upload this photo.');
  const data: PlantPhotoApi = await response.json();
  return apiPhotoToPhoto(data);
}

export async function deletePlantPhoto(plantId: number, photoId: number): Promise<void> {
  const response = await fetch(`${API_URL}/plants/${plantId}/photos/${photoId}`, {
    method: 'DELETE',
  });
  await throwPhotoRequestError(response, 'Unable to delete this photo.');
}