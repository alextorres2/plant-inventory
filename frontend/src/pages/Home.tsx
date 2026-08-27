import PlantCard from '../components/PlantCard';
import type { Plant } from '../types/Plant';
import { Link } from 'react-router-dom';

function Home({ plants }: { plants: Plant[] }) {
  return (
    <main>
      <h1>My Plants</h1>
      <div className="plant-list">
        {plants.map((plant) => (
          <Link
            key={plant.id}
            to={`/plants/${plant.id}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <PlantCard plant={plant} />
          </Link>
        ))}
      </div>
    </main>
  );
}

export default Home;