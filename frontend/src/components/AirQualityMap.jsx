import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Navigation, ExternalLink, Layers } from 'lucide-react';

// Custom pulsing map marker with blue accent ring
const createCustomIcon = (color = '#2563eb') => {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        position: relative;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          position: absolute;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: ${color};
          opacity: 0.25;
          animation: marker-pulse 2s infinite ease-out;
        "></div>
        <div style="
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: ${color};
          border: 3px solid #ffffff;
          box-shadow: 0 4px 10px rgba(0,0,0,0.25);
          z-index: 2;
        "></div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

// Component to smoothly pan the map when coordinates change
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
}

// Helper to get color by AQI
const getAQIColor = (aqi) => {
  if (aqi <= 50) return '#059669'; // Good Green
  if (aqi <= 100) return '#0284c7'; // Moderate Sky Blue
  if (aqi <= 150) return '#d97706'; // Unhealthy Yellow/Amber
  if (aqi <= 200) return '#ea580c'; // Unhealthy Orange
  if (aqi <= 300) return '#dc2626'; // Very Unhealthy Red
  return '#7c3aed'; // Hazardous Purple
};

// Map Layer Configurations
const MAP_LAYERS = {
  google_streets: {
    name: 'Google Maps',
    url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps',
  },
  google_satellite: {
    name: 'Google Satellite',
    url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps Satellite',
  },
  carto_voyager: {
    name: 'Clean Blue Style',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; CARTO',
  },
};

export const AirQualityMap = ({
  latitude,
  longitude,
  locationName,
  prediction,
  airQuality,
  onLocationSelect,
  cityPresets = [],
}) => {
  const [activeLayer, setActiveLayer] = useState('google_streets');

  const lat = parseFloat(latitude) || 12.9716;
  const lon = parseFloat(longitude) || 77.5946;
  const aqiValue = prediction?.aqi || 45;
  const aqiColor = getAQIColor(aqiValue);
  const customIcon = createCustomIcon(aqiColor);

  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;

  return (
    <div className="glass-card map-card" style={{ marginBottom: '2rem', padding: '1.75rem', background: '#ffffff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon">
            <Navigation size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title" style={{ margin: 0, fontSize: '1.25rem' }}>
              Interactive Environmental Geospatial Map
            </h2>
            <p className="ai-feature-subtitle" style={{ margin: 0 }}>
              Live telemetry coverage for: <strong>{locationName || 'Target Location'}</strong>
            </p>
          </div>
        </div>

        {/* Action Controls & External Link to Google Maps */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <a
            href={googleMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
            style={{ padding: '0.45rem 0.95rem', fontSize: '0.82rem', textDecoration: 'none' }}
            title="Open exact location in Google Maps"
          >
            <ExternalLink size={14} />
            <span>Open in Google Maps</span>
          </a>
        </div>
      </div>

      {/* Map Mode Selector Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          <Layers size={14} style={{ color: '#2563eb' }} />
          <span>Map Provider:</span>
          {Object.entries(MAP_LAYERS).map(([key, cfg]) => (
            <button
              key={key}
              type="button"
              className={`preset-chip ${activeLayer === key ? 'active-preset' : ''}`}
              onClick={() => setActiveLayer(key)}
              style={{ padding: '3px 10px', fontSize: '0.78rem' }}
            >
              {cfg.name}
            </button>
          ))}
        </div>

        {/* City Quick Navigation on Map */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          {cityPresets.slice(0, 5).map((city) => (
            <button
              key={city.name}
              type="button"
              className="preset-chip"
              onClick={() => onLocationSelect && onLocationSelect(city.lat, city.lon, city.name)}
              style={{
                borderColor: (Math.abs(lat - parseFloat(city.lat)) < 0.05 && Math.abs(lon - parseFloat(city.lon)) < 0.05)
                  ? '#2563eb'
                  : 'var(--border-color)',
                background: (Math.abs(lat - parseFloat(city.lat)) < 0.05 && Math.abs(lon - parseFloat(city.lon)) < 0.05)
                  ? '#2563eb'
                  : '#eff6ff',
                color: (Math.abs(lat - parseFloat(city.lat)) < 0.05 && Math.abs(lon - parseFloat(city.lon)) < 0.05)
                  ? '#ffffff'
                  : '#1e40af',
                fontSize: '0.78rem',
                padding: '3px 10px',
              }}
            >
              <MapPin size={11} style={{ display: 'inline', marginRight: '3px' }} />
              {city.name}
            </button>
          ))}
        </div>
      </div>

      {/* Leaflet Map Container */}
      <div style={{
        height: '440px',
        width: '100%',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        position: 'relative',
        boxShadow: '0 4px 12px rgba(15, 23, 42, 0.06)',
      }}>
        <MapContainer
          center={[lat, lon]}
          zoom={12}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%' }}
        >
          <ChangeView center={[lat, lon]} zoom={12} />

          {/* Active Map Tile Layer (Google Maps or Voyager) */}
          <TileLayer
            attribution={MAP_LAYERS[activeLayer].attribution}
            url={MAP_LAYERS[activeLayer].url}
          />

          {/* Environmental Dispersion Zone Radius */}
          <Circle
            center={[lat, lon]}
            radius={6000}
            pathOptions={{
              color: aqiColor,
              fillColor: aqiColor,
              fillOpacity: 0.15,
              weight: 2,
              dashArray: '5, 5',
            }}
          />

          <Marker position={[lat, lon]} icon={customIcon}>
            <Popup className="clean-popup">
              <div style={{
                color: '#0f172a',
                fontFamily: 'Outfit, sans-serif',
                padding: '4px 2px',
                minWidth: '180px',
              }}>
                <div style={{ fontWeight: 800, fontSize: '0.95rem', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px', marginBottom: '6px' }}>
                  {locationName ? locationName.split(',')[0] : 'Monitoring Station'}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#475569' }}>
                  Predicted AQI: <strong style={{ color: aqiColor, fontSize: '1.05rem' }}>{aqiValue}</strong>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#475569' }}>
                  Category: <strong>{prediction?.category || 'Moderate'}</strong>
                </div>
                {airQuality?.pm2_5 !== undefined && (
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                    PM2.5: <strong>{airQuality.pm2_5} µg/m³</strong> | PM10: <strong>{airQuality.pm10} µg/m³</strong>
                  </div>
                )}
                <div style={{ marginTop: '8px', borderTop: '1px solid #e2e8f0', paddingTop: '6px' }}>
                  <a
                    href={googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: '#2563eb',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '3px',
                      textDecoration: 'none'
                    }}
                  >
                    View in Google Maps <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            </Popup>
          </Marker>
        </MapContainer>

        {/* Floating Map HUD overlay */}
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(12px)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.65rem 1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          boxShadow: '0 4px 16px rgba(15, 23, 42, 0.12)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: aqiColor, boxShadow: `0 0 8px ${aqiColor}` }}></span>
            <span style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 600 }}>
              AQI: <strong style={{ color: aqiColor }}>{aqiValue}</strong> ({prediction?.category || 'Analyzing'})
            </span>
          </div>
          <a
            href={googleMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.78rem',
              color: '#2563eb',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              textDecoration: 'none'
            }}
          >
            Google Maps <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
};
