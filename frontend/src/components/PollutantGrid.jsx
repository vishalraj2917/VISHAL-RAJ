import React from 'react';
import { Wind, Activity } from 'lucide-react';

const POLLUTANT_CONFIGS = [
  { key: 'pm25', label: 'PM 2.5', unit: 'µg/m³', desc: 'Fine Particulate Matter (<2.5 µm)' },
  { key: 'pm10', label: 'PM 10', unit: 'µg/m³', desc: 'Coarse Particulate Matter (<10 µm)' },
  { key: 'co', label: 'CO', unit: 'mg/m³', desc: 'Carbon Monoxide' },
  { key: 'no2', label: 'NO₂', unit: 'µg/m³', desc: 'Nitrogen Dioxide' },
  { key: 'so2', label: 'SO₂', unit: 'µg/m³', desc: 'Sulfur Dioxide' },
  { key: 'o3', label: 'O₃', unit: 'µg/m³', desc: 'Surface Ozone' },
];

export const PollutantGrid = ({ airQuality }) => {
  if (!airQuality) return null;

  return (
    <div>
      <div className="metrics-section-title">
        <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
        <span>Live Pollutant Concentrations</span>
      </div>

      <div className="pollutants-grid">
        {POLLUTANT_CONFIGS.map((p) => {
          const val = airQuality[p.key];
          return (
            <div key={p.key} className="metric-card">
              <div className="metric-header">
                <span className="metric-name">{p.label}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.desc}</span>
              </div>
              <div className="metric-value-row">
                <span className="metric-value">
                  {val !== undefined && val !== null ? val : 'N/A'}
                </span>
                <span className="metric-unit">{p.unit}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
