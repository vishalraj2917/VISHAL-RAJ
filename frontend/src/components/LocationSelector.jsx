import React from 'react';
import { MapPin, Search, Navigation } from 'lucide-react';

const PRESET_LOCATIONS = [
  { name: 'Bengaluru', lat: 12.9716, lon: 77.5946 },
  { name: 'Delhi', lat: 28.7041, lon: 77.1025 },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
  { name: 'Coimbatore', lat: 11.0168, lon: 76.9558 },
  { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867 },
  { name: 'Kolkata', lat: 22.5726, lon: 88.3639 },
];

export const LocationSelector = ({
  latitude,
  longitude,
  onLatitudeChange,
  onLongitudeChange,
  onFetchLive,
  isLoading,
  onUseCurrentLocation,
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onFetchLive();
  };

  const handleSelectPreset = (preset) => {
    onLatitudeChange(preset.lat);
    onLongitudeChange(preset.lon);
  };

  return (
    <div className="glass-card location-panel">
      <form onSubmit={handleSubmit} className="location-form">
        <div className="input-group">
          <label className="input-label" htmlFor="lat-input">
            Latitude (-90.0 to 90.0)
          </label>
          <input
            id="lat-input"
            type="number"
            step="any"
            className="input-field"
            value={latitude}
            onChange={(e) => onLatitudeChange(e.target.value)}
            placeholder="e.g. 12.9716"
            required
          />
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="lon-input">
            Longitude (-180.0 to 180.0)
          </label>
          <input
            id="lon-input"
            type="number"
            step="any"
            className="input-field"
            value={longitude}
            onChange={(e) => onLongitudeChange(e.target.value)}
            placeholder="e.g. 77.5946"
            required
          />
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={isLoading}
        >
          <Search size={18} />
          <span>{isLoading ? 'Analyzing...' : 'Get Live AQI'}</span>
        </button>

        {onUseCurrentLocation && (
          <button
            type="button"
            className="btn-secondary"
            onClick={onUseCurrentLocation}
            title="Use current GPS location"
          >
            <Navigation size={18} />
            <span>My Location</span>
          </button>
        )}
      </form>

      <div className="city-presets">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <MapPin size={14} /> Quick Select:
        </span>
        {PRESET_LOCATIONS.map((city) => (
          <button
            key={city.name}
            type="button"
            className="preset-chip"
            onClick={() => handleSelectPreset(city)}
          >
            {city.name}
          </button>
        ))}
      </div>
    </div>
  );
};
