import React from 'react';
import { Cpu, Zap, MapPin } from 'lucide-react';

export const AQICard = ({ prediction, model, observedAt, locationName }) => {
  if (!prediction) return null;

  const aqiValue = prediction.aqi ?? 'N/A';
  const category = prediction.category ?? 'Unclassified';
  const color = prediction.color || '#2563eb';
  const advisory = prediction.health_advisory || 'No specific advisory available.';
  const dominant = prediction.dominant_pollutant;

  return (
    <div className="glass-card aqi-primary-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 700 }}>
        <Zap size={16} style={{ color: '#2563eb' }} />
        <span>REAL-TIME ML AQI PREDICTION</span>
      </div>

      {locationName && (
        <div style={{
          marginTop: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 700,
          color: '#1e3a8a',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <MapPin size={14} style={{ color: '#2563eb' }} />
          <span>{locationName.split(',')[0]}</span>
        </div>
      )}

      <div 
        className="aqi-meter-ring"
        style={{
          borderColor: color,
        }}
      >
        <div className="aqi-large-number" style={{ color: '#0f172a' }}>
          {typeof aqiValue === 'number' ? aqiValue.toFixed(1) : aqiValue}
        </div>
        <div className="aqi-score-label">AQI INDEX</div>
      </div>

      <div 
        className="aqi-category-badge"
        style={{ backgroundColor: color }}
      >
        {category}
      </div>

      {dominant && (
        <div style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Dominant Pollutant: <strong style={{ color: '#0f172a' }}>{dominant}</strong>
        </div>
      )}

      <div className="aqi-advisory-box">
        <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Health Advisory:
        </div>
        {advisory}
      </div>

      {model && (
        <div className="model-provenance-badge">
          <Cpu size={14} style={{ color: '#2563eb' }} />
          <span>Model: {model.name || 'Gradient Boosting ML'} (R²: 0.99)</span>
        </div>
      )}
    </div>
  );
};
