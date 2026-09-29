/**
 * OpenStreetMap Nominatim Geocoding Utility
 */

const PRESET_FALLBACKS = [
  { name: 'Bengaluru', lat: 12.9716, lon: 77.5946, country: 'India' },
  { name: 'Delhi', lat: 28.7041, lon: 77.1025, country: 'India' },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777, country: 'India' },
  { name: 'Coimbatore', lat: 11.0168, lon: 76.9558, country: 'India' },
  { name: 'Chennai', lat: 13.0827, lon: 80.2707, country: 'India' },
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, country: 'India' },
  { name: 'Kolkata', lat: 22.5726, lon: 88.3639, country: 'India' },
  { name: 'London', lat: 51.5074, lon: -0.1278, country: 'UK' },
  { name: 'New York', lat: 40.7128, lon: -74.0060, country: 'USA' },
  { name: 'Tokyo', lat: 35.6762, lon: 139.6503, country: 'Japan' },
  { name: 'Dubai', lat: 25.2048, lon: 55.2708, country: 'UAE' },
  { name: 'Paris', lat: 48.8566, lon: 2.3522, country: 'France' },
  { name: 'Singapore', lat: 1.3521, lon: 103.8198, country: 'Singapore' },
];

/**
 * Search places/addresses using OpenStreetMap Nominatim API
 */
export const searchPlaces = async (query) => {
  if (!query || query.trim().length < 2) return [];

  const q = query.trim().toLowerCase();

  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5&addressdetails=1`;
    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'en',
      },
    });

    if (res.ok) {
      const results = await res.json();
      if (results && results.length > 0) {
        return results.map((item) => ({
          name: item.display_name,
          lat: parseFloat(item.lat),
          lon: parseFloat(item.lon),
          shortName: item.address?.city || item.address?.town || item.address?.village || item.display_name.split(',')[0],
        }));
      }
    }
  } catch (err) {
    console.warn('Geocoding API failed, utilizing fallback dataset:', err);
  }

  // Fallback filtering if network issue or no API result
  return PRESET_FALLBACKS.filter((p) => p.name.toLowerCase().includes(q)).map((p) => ({
    name: `${p.name}, ${p.country}`,
    lat: p.lat,
    lon: p.lon,
    shortName: p.name,
  }));
};

/**
 * Convert lat & lon into place name via reverse geocoding
 */
export const reverseGeocode = async (lat, lon) => {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&addressdetails=1`;
    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'en',
      },
    });

    if (res.ok) {
      const data = await res.json();
      if (data && data.display_name) {
        return data.display_name;
      }
    }
  } catch (err) {
    console.warn('Reverse geocoding error:', err);
  }

  return `Location (${parseFloat(lat).toFixed(4)}, ${parseFloat(lon).toFixed(4)})`;
};

export { PRESET_FALLBACKS };
