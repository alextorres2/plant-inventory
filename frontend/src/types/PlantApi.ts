export type PlantApi = {
    id: number;
    name: string;
    species: string;
    location: string;
    date_acquired: string;
    latest_photo_url?: string | null;
};

export type PlantPhotoApi = {
    id: number;
    date_taken: string;
    caption: string | null;
    image_url: string;
};