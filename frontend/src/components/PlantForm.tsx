import { useRef, useState } from 'react';
import type { Plant } from '../types/Plant';
import type { PlantFormData } from '../types/PlantFormData';

type PlantFormProps = {
  initialPlant?: Plant;
  submitLabel: string;
  onSubmit: (plant: PlantFormData) => Promise<void>;
  onPendingChange?: (pending: boolean) => void;
  disabled?: boolean;
};

function PlantForm({ initialPlant, submitLabel, onSubmit, onPendingChange, disabled = false }: PlantFormProps) {
    const [name, setName] = useState(initialPlant?.name || '');
    const [scientificName, setScientificName] = useState(initialPlant?.scientificName || '');
    const [location, setLocation] = useState(initialPlant?.location || '');
    const [acquiredDate, setAcquiredDate] = useState(initialPlant?.acquiredDate || '');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const submissionInProgress = useRef(false);

    async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        if (submissionInProgress.current || disabled) return;
        setError('');

        if (!name.trim() || !scientificName.trim() || !location.trim() || !acquiredDate.trim()) {
            setError('All fields are required.');
            return;
        }

        submissionInProgress.current = true;
        setIsSubmitting(true);
        onPendingChange?.(true);
        try {
            await onSubmit({
                name,
                scientificName,
                location,
                acquiredDate,
            });
            if (!initialPlant) {
                setName('');
                setScientificName('');
                setLocation('');
                setAcquiredDate('');
            }
        } catch (err: unknown) {
            const message = err instanceof Error
                ? err.message
                : typeof err === 'string'
                    ? err
                    : '';
            setError(message.trim() || 'Unable to save the plant. Please try again.');
        } finally {
            submissionInProgress.current = false;
            setIsSubmitting(false);
            onPendingChange?.(false);
        }
    }

    return (
        <div className="plant-form">
            {error && (
                <div className="form-error" role="alert">
                    {error}
                </div>
            )}
            <form onSubmit={handleSubmit}>
                <div className="form-fields">
                    <label className="form-field">
                    Name
                    <input
                        type="text"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        disabled={isSubmitting || disabled}
                        required
                    />
                    </label>
                    <label className="form-field">
                    Scientific name
                    <input
                        type="text"
                        value={scientificName}
                        onChange={(event) => setScientificName(event.target.value)}
                        disabled={isSubmitting || disabled}
                        required
                    />
                    </label>
                    <label className="form-field">
                    Location
                    <input
                        type="text"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        disabled={isSubmitting || disabled}
                        required
                    />
                    </label>
                    <label className="form-field">
                    Acquired date
                    <input
                        type="date"
                        value={acquiredDate}
                        onChange={(event) => setAcquiredDate(event.target.value)}
                        disabled={isSubmitting || disabled}
                        required
                    />
                    </label>
                </div>
                <button className="form-submit" type="submit" disabled={isSubmitting || disabled}>
                    {isSubmitting ? 'Saving...' : submitLabel}
                </button>
            </form>
        </div>
    )
}

export default PlantForm;