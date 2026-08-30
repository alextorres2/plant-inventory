import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import type { Plant } from '../types/Plant';
import PlantForm from '../components/PlantForm';
import type { PlantFormData } from '../types/PlantFormData';

type PlantDetailProps = {
    plants: Plant[];
    onUpdatePlant: (id: number, updatedPlant: PlantFormData) => Promise<void>;
    onDeletePlant: (plantId: number) => Promise<void>;
};

function PlantDetail({ plants, onUpdatePlant, onDeletePlant }: PlantDetailProps) {
    const { id } = useParams();
    const plant = plants.find((p) => p.id === Number(id));
    const [isEditing, setIsEditing] = useState(false);
    const navigate = useNavigate();
    const [error, setError] = useState("");

    if (!plant) {
        return (
            <main>
                <h1>Plant not found</h1>
            </main>
        );
    }

    return (
        <main>
            {error && (
                <div role="alert" style={{ color: 'red' }}>
                    {error}
                </div>
            )}
            {isEditing ? (
                <PlantForm
                    initialPlant={plant}
                    submitLabel="Update Plant"
                    onSubmit={async (formData) => {
                        try {
                            await onUpdatePlant(Number(id), formData);
                            setIsEditing(false);
                        } catch (error) {
                            setError("Failed to update plant");
                        }
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
            <button onClick={async () => {
                try {
                    await onDeletePlant(plant.id);
                    navigate('/');
                } catch (error) {
                    setError("Failed to delete plant");
                }
            }}>
                Delete
            </button>
        </main>
    );
}

export default PlantDetail;