export type Plant = {
    id: number;
    name: string;
    scientificName: string;
    location: string;
    acquiredDate: string;
    latestPhotoUrl?: string | null;
}