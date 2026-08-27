import './App.css'
import Home from './pages/Home';
import About from './pages/About';
import PlantDetail from './pages/PlantDetail';
import AddPlant from './pages/AddPlant';

import type { Plant } from './types/Plant';
import { initialPlants } from './data/plants';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { useState } from 'react';

function App() {
  const [plants, setPlants] = useState<Plant[]>(initialPlants);

  function addPlant(plant: Plant) {
    setPlants([...plants, plant]);
  }

  function updatePlant(updatedPlant: Plant) {
    setPlants(
      plants.map((plant) => (
        plant.id === updatedPlant.id ? updatedPlant : plant
      ))
    );
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
          <Route path="plants/:id" element={<PlantDetail plants={plants} onUpdatePlant={updatePlant} />} />
          <Route path="plants/new" element={<AddPlant onAddPlant={addPlant} />} />
        </Routes>
      </BrowserRouter>
    </main>
  );
}

export default App;