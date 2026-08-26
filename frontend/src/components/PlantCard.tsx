import "./PlantCard.css";
import type {Plant} from '../types/Plant'

type PlantCardProps = {
    plant: Plant;
}

function PlantCard({ plant }: PlantCardProps) {
    return (
        <div className="plant-card">
                <p><strong>{plant.name}</strong></p>
                <p><em>{plant.scientificName}</em></p>
            <p>Location: {plant.location}</p>
            <p>Acquired Date: {plant.acquiredDate}</p>
        </div>
    );
}

export default PlantCard;