import './App.css'
import Home from './pages/Home';
import About from './pages/About';
import PlantDetail from './pages/PlantDetail';
import AddPlant from './pages/AddPlant';

import type { Plant } from './types/Plant';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getPlants, createPlant, updatePlant, deletePlant } from './services/plantApi';
import type { PlantFormData } from './types/PlantFormData';

function App() {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [isLoading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function loadPlants() {
      try {
        const data = await getPlants();
        setPlants(data);
      } catch (error) {
        console.error('Failed to fetch plants:', error);
        setError('Failed to fetch plants');
      } finally {
        setLoading(false);
      }
    }
    loadPlants();
  }, []);

  async function handleAddPlant(plant: PlantFormData) {
    const createdPlant = await createPlant(plant);
    setPlants((currentPlants) => [...currentPlants, createdPlant]);
  }

  async function handleUpdatePlant(id: number, plant: PlantFormData) {
    const updatedPlant = await updatePlant(id, plant);
    setPlants((currentPlants) =>
      currentPlants.map((currentPlant) =>
        currentPlant.id === updatedPlant.id
          ? updatedPlant
          : currentPlant
      )
    );
  }

  async function handleDeletePlant(plantId: number) {
    await deletePlant(plantId);
    setPlants((currentPlants) => 
      currentPlants.filter((plant) => plant.id !== plantId)
    );
  }

  if (isLoading) {
    return <p>Loading plants...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>{error}</p>;
  }

  return (
    <main>
      <BrowserRouter>
        <nav>
          <Link to="/">Home</Link> |{" "}
          <Link to="/plants/new">Add Plant</Link> |{" "}
          <Link to="/about">About</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home plants={plants} />} />
          <Route path="about" element={<About />} />
          <Route path="plants/:id" element={<PlantDetail plants={plants} onUpdatePlant={handleUpdatePlant} onDeletePlant={handleDeletePlant} />} />
          <Route path="plants/new" element={<AddPlant onAddPlant={handleAddPlant} />} />
        </Routes>
      </BrowserRouter>
    </main>
  );
}

export default App;