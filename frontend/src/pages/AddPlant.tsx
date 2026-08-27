import { useNavigate } from 'react-router-dom';
import type { Plant } from '../types/Plant';
import PlantForm from '../components/PlantForm';

type AddPlantProps = {
    onAddPlant: (plant: Plant) => void;
};

function AddPlant({ onAddPlant }: AddPlantProps) {
    const navigate = useNavigate();

    return (
        <main>
            <h1>Add a New Plant</h1>
            <PlantForm
                submitLabel="Add Plant"
                onSubmit={(updatedPlant) => {
                    onAddPlant(updatedPlant)
                    navigate('/');
                }
            }
            />
        </main>
    );
}

export default AddPlant;