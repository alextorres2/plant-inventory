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

  async function handlePlantPhotosChanged() {
    const refreshedPlants = await getPlants();
    setPlants(refreshedPlants);
  }

  if (isLoading) {
    return <main className="page-content status-message" role="status">Loading plants...</main>;
  }

  if (error) {
    return <main className="page-content status-message error-message" role="alert">{error}</main>;
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="site-nav" aria-label="Main navigation">
          <Link className="site-brand" to="/">Plant Inventory</Link>
          <div className="site-nav-links">
            <Link to="/">Home</Link>
            <Link to="/plants/new">Add Plant</Link>
            <Link to="/about">About</Link>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Home plants={plants} />} />
          <Route path="about" element={<About />} />
          <Route path="plants/:id" element={<PlantDetail plants={plants} onUpdatePlant={handleUpdatePlant} onDeletePlant={handleDeletePlant} onPlantPhotosChanged={handlePlantPhotosChanged} />} />
          <Route path="plants/new" element={<AddPlant onAddPlant={handleAddPlant} />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;