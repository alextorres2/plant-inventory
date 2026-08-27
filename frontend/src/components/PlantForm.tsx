import { useState } from 'react';
import type { Plant } from '../types/Plant';

type PlantFormProps = {
  initialPlant?: Plant;
  submitLabel: string;
  onSubmit: (plant: Plant) => void;
};

function PlantForm({ initialPlant, submitLabel, onSubmit }: PlantFormProps) {
    const [name, setName] = useState(initialPlant?.name || '');
    const [scientificName, setScientificName] = useState(initialPlant?.scientificName || '');
    const [location, setLocation] = useState(initialPlant?.location || '');
    const [acquiredDate, setAcquiredDate] = useState(initialPlant?.acquiredDate || '');
    const [error, setError] = useState("");

    function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!name.trim() || !scientificName.trim() || !location.trim() || !acquiredDate.trim()) {
            setError("All fields are required.");
            return;
        }
        setError("");
        onSubmit({
            id: initialPlant?.id || Date.now(),
            name,
            scientificName,
            location,
            acquiredDate,
        });
        setName('');
        setScientificName('');
        setLocation('');
        setAcquiredDate('');
    }

    return (
        <main>
            {error && <p className="form-error">{error}</p>}
            <form onSubmit={handleSubmit}>
                <label>
                    Name:
                    <input
                        type="text"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        required
                    />
                </label>
                <br />
                <label>
                    Scientific Name:
                    <input
                        type="text"
                        value={scientificName}
                        onChange={(event) => setScientificName(event.target.value)}
                        required
                    />
                </label>
                <br />
                <label>
                    Location:
                    <input
                        type="text"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        required
                    />
                </label>
                <br />
                <label>
                    Acquired Date:
                    <input
                        type="date"
                        value={acquiredDate}
                        onChange={(event) => setAcquiredDate(event.target.value)}
                        required
                    />
                </label>
                <br />
                <button type="submit">{submitLabel}</button>
            </form>
        </main>
    )
}

export default PlantForm;