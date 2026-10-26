import "./PlantCard.css";
import type {Plant} from '../types/Plant'

type PlantCardProps = {
    plant: Plant;
}

function PlantCard({ plant }: PlantCardProps) {
    return (
        <div className="plant-card">
            {plant.latestPhotoUrl ? (
                <img className="plant-card-thumbnail" src={plant.latestPhotoUrl} alt={`Latest photo of ${plant.name}`} />
            ) : (
                <div className="plant-card-placeholder" aria-label="No plant photo yet" role="img">
                    <span aria-hidden="true">🌱</span>
                    <span>No photo yet</span>
                </div>
            )}
                <p><strong>{plant.name}</strong></p>
                <p><em>{plant.scientificName}</em></p>
            <p>Location: {plant.location}</p>
            <p>Acquired Date: {plant.acquiredDate}</p>
        </div>
    );
}

export default PlantCard;