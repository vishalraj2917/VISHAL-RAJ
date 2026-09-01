import React from 'react';
import { Thermometer, Droplets, Wind, Gauge } from 'lucide-react';

const WEATHER_CONFIGS = [
  { key: 'temperature', label: 'Temperature', unit: '°C', icon: Thermometer, color: '#f97316' },
  { key: 'humidity', label: 'Humidity', unit: '%', icon: Droplets, color: '#06b6d4' },
  { key: 'wind_speed', label: 'Wind Speed', unit: 'km/h', icon: Wind, color: '#10b981' },
  { key: 'pressure', label: 'Atm. Pressure', unit: 'hPa', icon: Gauge, color: '#8b5cf6' },
];

export const WeatherGrid = ({ weather }) => {
  if (!weather) return null;

  return (
    <div>
      <div className="metrics-section-title">
        <Thermometer size={18} style={{ color: 'var(--accent-amber)' }} />
        <span>Current Meteorological Conditions</span>
      </div>

      <div className="weather-grid">
        {WEATHER_CONFIGS.map((w) => {
          const val = weather[w.key];
          const Icon = w.icon;
          return (
            <div key={w.key} className="metric-card">
              <div className="metric-header">
                <span className="metric-name">{w.label}</span>
                <Icon size={18} style={{ color: w.color }} />
              </div>
              <div className="metric-value-row">
                <span className="metric-value">
                  {val !== undefined && val !== null ? val : 'N/A'}
                </span>
                <span className="metric-unit">{w.unit}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
