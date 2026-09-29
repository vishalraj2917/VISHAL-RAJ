import React, { useState, useEffect, useRef } from 'react';
import { Search, Navigation, MapPin, CheckCircle2, Loader2, ExternalLink } from 'lucide-react';
import { searchPlaces, PRESET_FALLBACKS } from '../utils/geocoding';

export const LocationSelector = ({
  selectedLocationName,
  onSelectLocation,
  isLoading,
  onUseCurrentLocation,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search for suggestions as user types
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchPlaces(searchQuery);
        setSuggestions(results);
        setShowDropdown(results.length > 0);
      } catch (err) {
        console.warn('Autocomplete fetch warning:', err);
      } finally {
        setIsSearching(false);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setShowDropdown(false);

    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await searchPlaces(searchQuery);
      if (results && results.length > 0) {
        const best = results[0];
        onSelectLocation(best.lat, best.lon, best.name);
      } else {
        alert('Location not found. Please try entering a different city or address.');
      }
    } catch (err) {
      alert('Search failed. Please check your internet connection.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectSuggestion = (place) => {
    setSearchQuery(place.shortName || place.name);
    setShowDropdown(false);
    onSelectLocation(place.lat, place.lon, place.name);
  };

  const handleSelectPreset = (preset) => {
    setSearchQuery(preset.name);
    setShowDropdown(false);
    onSelectLocation(preset.lat, preset.lon, `${preset.name}, ${preset.country}`);
  };

  const googleMapsSearchUrl = selectedLocationName
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedLocationName)}`
    : 'https://maps.google.com';

  return (
    <div className="glass-card location-panel">
      <div className="location-search-wrapper" ref={dropdownRef}>
        <form onSubmit={handleFormSubmit} className="location-form">
          <div className="input-group">
            <label className="input-label" htmlFor="place-search-input">
              Search Location / Address
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="place-search-input"
                type="text"
                className="input-field"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                placeholder="Search any city, address, or landmark (e.g. MG Road Bengaluru, Times Square NY)..."
                autoComplete="off"
              />
              {isSearching && (
                <div style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: '#0284c7' }}>
                  <Loader2 size={18} className="spin-icon" />
                </div>
              )}
            </div>

            {/* Suggestions Dropdown */}
            {showDropdown && suggestions.length > 0 && (
              <div className="suggestions-dropdown">
                {suggestions.map((place, idx) => (
                  <div
                    key={idx}
                    className="suggestion-item"
                    onClick={() => handleSelectSuggestion(place)}
                  >
                    <MapPin size={16} style={{ color: '#2563eb', flexShrink: 0 }} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {place.name}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || isSearching}
          >
            <Search size={18} />
            <span>{isLoading ? 'Searching...' : 'Search Air Quality'}</span>
          </button>

          {onUseCurrentLocation && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onUseCurrentLocation}
              title="Use current GPS location"
            >
              <Navigation size={18} style={{ color: '#2563eb' }} />
              <span>My Location</span>
            </button>
          )}
        </form>
      </div>

      {/* Currently Selected Location Badge & Google Maps Link */}
      {selectedLocationName && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
          <div className="active-location-badge" style={{ marginTop: 0 }}>
            <CheckCircle2 size={16} style={{ color: '#059669' }} />
            <span>Showing Live Air Quality for: <strong>{selectedLocationName}</strong></span>
          </div>

          <a
            href={googleMapsSearchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem', textDecoration: 'none' }}
          >
            <ExternalLink size={14} style={{ color: '#2563eb' }} />
            <span>Google Maps</span>
          </a>
        </div>
      )}

      {/* Quick Select Preset City Chips */}
      <div className="city-presets">
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
          <MapPin size={14} style={{ color: '#2563eb' }} /> Quick Select:
        </span>
        {PRESET_FALLBACKS.slice(0, 7).map((city) => (
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
