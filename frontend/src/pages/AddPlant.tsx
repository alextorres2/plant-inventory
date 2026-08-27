import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import type { PlantFormData } from '../types/PlantFormData';
import PlantForm from '../components/PlantForm';

type AddPlantProps = {
    onAddPlant: (plant: PlantFormData) => Promise<void>;
};

function AddPlant({ onAddPlant }: AddPlantProps) {
    const navigate = useNavigate();
    const [error, setError] = useState("");

    return (
        <main>
            <h1>Add a New Plant</h1>
            <PlantForm
                submitLabel="Add Plant"
                onSubmit={async (plantData) => {
                    try {
                        await onAddPlant(plantData);
                        navigate('/');
                    } catch (error) {
                        setError("Failed to add plant");
                    }
                }}
            />
        </main>
    );
}

export default AddPlant;