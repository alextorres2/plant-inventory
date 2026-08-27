import { useParams } from 'react-router-dom';
import type { Plant } from '../types/Plant';
import PlantForm from '../components/PlantForm';
import { useState } from 'react';

type PlantDetailProps = {
    plants: Plant[];
    onUpdatePlant: (updatedPlant: Plant) => void;
};

function PlantDetail({ plants, onUpdatePlant }: PlantDetailProps) {
    const { id } = useParams();
    const plant = plants.find((p) => p.id === Number(id));
    const [isEditing, setIsEditing] = useState(false);

    if (!plant) {
        return (
            <main>
                <h1>Plant not found</h1>
            </main>
        );
    }

    return (
        <main>
            {isEditing ? (
                <PlantForm
                    initialPlant={plant}
                    submitLabel="Update Plant"
                    onSubmit={(updatedPlant) => {
                        onUpdatePlant(updatedPlant);
                        setIsEditing(false);
                    }}
                />
            ) : 
            (
                <div>
                    <h1>{plant.name}</h1>
                    <p><em>{plant.scientificName}</em></p>
                    <p>Location: {plant.location}</p>
                    <p>Acquired Date: {plant.acquiredDate}</p>
                </div>
            )
            }
            <button onClick={() => setIsEditing(!isEditing)}>
                {isEditing ? 'Cancel' : 'Edit'}
            </button>
        </main>
    );
}

export default PlantDetail;