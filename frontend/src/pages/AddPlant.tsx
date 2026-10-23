import { useNavigate } from 'react-router-dom';
import type { PlantFormData } from '../types/PlantFormData';
import PlantForm from '../components/PlantForm';

type AddPlantProps = {
    onAddPlant: (plant: PlantFormData) => Promise<void>;
};

function AddPlant({ onAddPlant }: AddPlantProps) {
    const navigate = useNavigate();

    return (
        <main className="page-content">
            <h1>Add a New Plant</h1>
            <PlantForm
                submitLabel="Add Plant"
                onSubmit={async (plantData) => {
                    await onAddPlant(plantData);
                    navigate('/');
                }}
            />
        </main>
    );
}

export default AddPlant;