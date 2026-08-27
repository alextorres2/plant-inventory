export type PlantApi = {
    id: number;
    name: string;
    species: string;
    location: string;
    date_acquired: string;
};

export type PlantFormData = {
  name: string;
  scientificName: string;
  location: string;
  acquiredDate: string;
};