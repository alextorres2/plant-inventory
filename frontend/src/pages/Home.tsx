import { useState } from 'react';
import PlantCard from '../components/PlantCard';
import type { Plant } from '../types/Plant';
import { Link } from 'react-router-dom';
import './Home.css';

function Home({ plants }: { plants: Plant[] }) {
  const [search, setSearch] = useState('');
  const [location, setLocation] = useState('');
  const locations = [...new Set(plants.map((plant) => plant.location))].sort((a, b) =>
    a.localeCompare(b),
  );
  const normalizedSearch = search.trim().toLocaleLowerCase();
  const matchingPlants = plants.filter((plant) => {
    const matchesSearch =
      !normalizedSearch ||
      plant.name.toLocaleLowerCase().includes(normalizedSearch) ||
      plant.scientificName.toLocaleLowerCase().includes(normalizedSearch);
    const matchesLocation = !location || plant.location === location;
    return matchesSearch && matchesLocation;
  });

  function clearFilters() {
    setSearch('');
    setLocation('');
  }

  return (
    <main>
      <h1>My Plants</h1>
      <section className="plant-filters" aria-label="Filter plants">
        <label>
          Search by name or scientific name
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search plants"
          />
        </label>
        <label>
          Location
          <select value={location} onChange={(event) => setLocation(event.target.value)}>
            <option value="">All locations</option>
            {locations.map((plantLocation) => (
              <option key={plantLocation} value={plantLocation}>
                {plantLocation}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={clearFilters} disabled={!search && !location}>
          Clear filters
        </button>
      </section>
      <p className="plant-result-count" aria-live="polite">
        {matchingPlants.length} {matchingPlants.length === 1 ? 'plant' : 'plants'} found
      </p>
      {plants.length === 0 ? (
        <p>No plants in your inventory yet.</p>
      ) : matchingPlants.length === 0 ? (
        <p>No plants match your filters. Try adjusting or clearing them.</p>
      ) : (
      <div className="plant-list">
        {matchingPlants.map((plant) => (
          <Link
            key={plant.id}
            to={`/plants/${plant.id}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <PlantCard plant={plant} />
          </Link>
        ))}
      </div>
      )}
    </main>
  );
}

export default Home;