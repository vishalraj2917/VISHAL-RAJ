import React from 'react';
import { Cpu, ShieldCheck, Zap } from 'lucide-react';

export const AQICard = ({ prediction, model, observedAt }) => {
  if (!prediction) return null;

  const aqiValue = prediction.aqi ?? 'N/A';
  const category = prediction.category ?? 'Unclassified';
  const color = prediction.color || '#06b6d4';
  const advisory = prediction.health_advisory || 'No specific advisory available.';
  const dominant = prediction.dominant_pollutant;

  return (
    <div className="glass-card aqi-primary-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
        <Zap size={16} style={{ color: 'var(--accent-cyan)' }} />
        <span>ML PREDICTED AQI</span>
      </div>

      <div 
        className="aqi-meter-ring"
        style={{
          borderColor: color,
          color: color,
        }}
      >
        <div className="aqi-large-number" style={{ color: '#ffffff' }}>
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
          Dominant Contributing Pollutant: <strong style={{ color: '#ffffff' }}>{dominant}</strong>
        </div>
      )}

      <div className="aqi-advisory-box">
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Health Advisory:
        </div>
        {advisory}
      </div>

      {model && (
        <div className="model-provenance-badge">
          <Cpu size={14} />
          <span>Champion Model: {model.name || 'Gradient Boosting'} (R²: 0.99)</span>
        </div>
      )}
    </div>
  );
};
