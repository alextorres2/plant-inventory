import './App.css'
import PlantCard from './components/PlantCard';
import type { Plant } from './types/Plant';

function App() {
  const plants: Plant[] = [
    {
      id: 1,
      name: 'Monstera 1',
      scientificName: 'Monstera deliciosa',
      location: 'Living Room',
      acquiredDate: '2023-01-15',
    },
    {
      id: 2,
      name: 'Fiddle Leaf Fig',
      scientificName: 'Ficus lyrata',
      location: 'Bedroom',
      acquiredDate: '2022-11-20',
    },
    {
      id: 3,
      name: 'Snake Plant',
      scientificName: 'Sansevieria trifasciata',
      location: 'Office',
      acquiredDate: '2023-03-05',
    },
    {
      id: 4,
      name: 'ZZ Plant',
      scientificName: 'Zamioculcas zamiifolia',
      location: 'Living Room',
      acquiredDate: '2023-01-20',
    }
  ];

  return (
    <main>
      <h1>My Plants</h1>
      <div className="plant-list">
        {plants.map((plant) => (
          <PlantCard key={plant.id} plant={plant} />
        ))}
      </div>
    </main>
  );
}

export default App;