import { useParams, useNavigate } from 'react-router-dom';
import { useRef, useState } from 'react';
import type { Plant } from '../types/Plant';
import PlantForm from '../components/PlantForm';
import PlantPhotos from '../components/PlantPhotos';
import type { PlantFormData } from '../types/PlantFormData';

type PlantDetailProps = {
    plants: Plant[];
    onUpdatePlant: (id: number, updatedPlant: PlantFormData) => Promise<void>;
    onDeletePlant: (plantId: number) => Promise<void>;
    onPlantPhotosChanged: () => Promise<void>;
};

function PlantDetail({ plants, onUpdatePlant, onDeletePlant, onPlantPhotosChanged }: PlantDetailProps) {
    const { id } = useParams();
    const plant = plants.find((p) => p.id === Number(id));
    const [isEditing, setIsEditing] = useState(false);
    const navigate = useNavigate();
    const [error, setError] = useState("");
    const [isUpdating, setIsUpdating] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const deletionInProgress = useRef(false);

    async function handleDelete() {
        if (deletionInProgress.current || isUpdating) return;

        deletionInProgress.current = true;
        setIsDeleting(true);
        setError('');
        try {
            await onDeletePlant(plant!.id);
            navigate('/');
        } catch (caught: unknown) {
            const message = caught instanceof Error
                ? caught.message
                : typeof caught === 'string'
                    ? caught
                    : '';
            setError(message.trim() || 'Unable to delete the plant. Please try again.');
        } finally {
            deletionInProgress.current = false;
            setIsDeleting(false);
        }
    }

    if (!plant) {
        return (
            <main className="page-content">
                <h1>Plant not found</h1>
            </main>
        );
    }

    return (
        <main className="page-content">
            {error && (
                <div className="form-error" role="alert">
                    {error}
                </div>
            )}
            {isEditing ? (
                <PlantForm
                    initialPlant={plant}
                    submitLabel="Update Plant"
                    disabled={isDeleting}
                    onPendingChange={setIsUpdating}
                    onSubmit={async (formData) => {
                        await onUpdatePlant(Number(id), formData);
                        setIsEditing(false);
                    }}
                />
            ) : 
            (
                <section className="detail-card">
                    <h1>{plant.name}</h1>
                    <p><em>{plant.scientificName}</em></p>
                    <p>Location: {plant.location}</p>
                    <p>Acquired Date: {plant.acquiredDate}</p>
                </section>
            )
            }
            <div className="detail-actions">
                <button
                    onClick={() => {
                        setError('');
                        setIsEditing(!isEditing);
                    }}
                    disabled={isUpdating || isDeleting}
                >
                    {isEditing ? 'Cancel' : 'Edit'}
                </button>
                <button className="danger-button" onClick={handleDelete} disabled={isUpdating || isDeleting}>
                    {isDeleting ? 'Deleting...' : 'Delete'}
                </button>
            </div>
            <PlantPhotos plantId={plant.id} canEdit={isEditing} onPhotosChanged={onPlantPhotosChanged} />
        </main>
    );
}

export default PlantDetail;