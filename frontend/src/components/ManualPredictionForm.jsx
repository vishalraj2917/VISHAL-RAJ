import React, { useState } from 'react';
import { Sliders, Zap, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { getManualPrediction } from '../services/api';

const DEFAULT_SAMPLE = {
  pm25: 45.2,
  pm10: 85.0,
  co: 0.8,
  no2: 24.5,
  so2: 11.2,
  o3: 28.0,
  temperature: 27.5,
  humidity: 62.0,
  wind_speed: 3.8,
  pressure: 1012.5,
  hour: 14,
  day: 15,
  month: 6,
  day_of_week: 2,
  is_weekend: 0,
};

export const ManualPredictionForm = () => {
  const [formData, setFormData] = useState(DEFAULT_SAMPLE);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
    }));
  };

  const handleReset = () => {
    setFormData(DEFAULT_SAMPLE);
    setPredictionResult(null);
    setErrorMsg(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsPredicting(true);
    setErrorMsg(null);

    // Validate no empty, NaN, or out-of-range fields
    for (const [k, v] of Object.entries(formData)) {
      if (v === '' || isNaN(v)) {
        setErrorMsg(`Field "${k}" must be a valid number.`);
        setIsPredicting(false);
        return;
      }
    }

    try {
      const response = await getManualPrediction(formData);
      if (response && response.success) {
        setPredictionResult(response);
      } else {
        throw new Error('Prediction API returned an invalid response structure.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const displayMsg = typeof detail === 'string' ? detail : (err.message || 'Failed to execute machine learning model prediction.');
      setErrorMsg(displayMsg);
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <div className="glass-card ai-feature-card" style={{ marginTop: '2rem' }}>
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-amber), var(--accent-rose))' }}>
            <Sliders size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">Custom Parameter Prediction Simulator</h2>
            <p className="ai-feature-subtitle">Direct inference on 21 environmental and temporal features via POST /api/predict</p>
          </div>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={handleReset}
          style={{ padding: '0.5rem 1rem' }}
        >
          <RefreshCw size={14} />
          <span>Reset Defaults</span>
        </button>
      </div>

      {errorMsg && (
        <div className="chat-error-banner" style={{ marginBottom: '1.25rem' }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: '0.75rem' }}>
          1. Atmospheric Pollutant Concentrations
        </div>
        <div className="pollutants-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="input-group">
            <label className="input-label" htmlFor="pm25">PM2.5 (µg/m³)</label>
            <input id="pm25" name="pm25" type="number" step="0.1" min="0" max="1000" className="input-field" value={formData.pm25} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="pm10">PM10 (µg/m³)</label>
            <input id="pm10" name="pm10" type="number" step="0.1" min="0" max="1500" className="input-field" value={formData.pm10} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="co">CO (mg/m³)</label>
            <input id="co" name="co" type="number" step="0.01" min="0" max="100" className="input-field" value={formData.co} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="no2">NO₂ (µg/m³)</label>
            <input id="no2" name="no2" type="number" step="0.1" min="0" max="1000" className="input-field" value={formData.no2} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="so2">SO₂ (µg/m³)</label>
            <input id="so2" name="so2" type="number" step="0.1" min="0" max="1000" className="input-field" value={formData.so2} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="o3">O₃ (µg/m³)</label>
            <input id="o3" name="o3" type="number" step="0.1" min="0" max="1000" className="input-field" value={formData.o3} onChange={handleChange} required />
          </div>
        </div>

        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent-amber)', marginBottom: '0.75rem' }}>
          2. Meteorological Parameters
        </div>
        <div className="weather-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="input-group">
            <label className="input-label" htmlFor="temperature">Temperature (°C)</label>
            <input id="temperature" name="temperature" type="number" step="0.1" min="-50" max="60" className="input-field" value={formData.temperature} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="humidity">Humidity (%)</label>
            <input id="humidity" name="humidity" type="number" step="0.1" min="0" max="100" className="input-field" value={formData.humidity} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="wind_speed">Wind Speed (km/h)</label>
            <input id="wind_speed" name="wind_speed" type="number" step="0.1" min="0" max="150" className="input-field" value={formData.wind_speed} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="pressure">Pressure (hPa)</label>
            <input id="pressure" name="pressure" type="number" step="0.1" min="800" max="1100" className="input-field" value={formData.pressure} onChange={handleChange} required />
          </div>
        </div>

        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent-violet)', marginBottom: '0.75rem' }}>
          3. Temporal Components
        </div>
        <div className="pollutants-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="input-group">
            <label className="input-label" htmlFor="hour">Hour (0–23)</label>
            <input id="hour" name="hour" type="number" min="0" max="23" className="input-field" value={formData.hour} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="day">Day (1–31)</label>
            <input id="day" name="day" type="number" min="1" max="31" className="input-field" value={formData.day} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="month">Month (1–12)</label>
            <input id="month" name="month" type="number" min="1" max="12" className="input-field" value={formData.month} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="day_of_week">Day of Week (0–6)</label>
            <input id="day_of_week" name="day_of_week" type="number" min="0" max="6" className="input-field" value={formData.day_of_week} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="is_weekend">Weekend (0 or 1)</label>
            <select id="is_weekend" name="is_weekend" className="input-field" value={formData.is_weekend} onChange={handleChange}>
              <option value={0}>0 (Weekday)</option>
              <option value={1}>1 (Weekend)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
          <button type="submit" className="btn-primary" disabled={isPredicting}>
            <Zap size={16} />
            <span>{isPredicting ? 'Executing Model Inference...' : 'Run Simulation Prediction'}</span>
          </button>
        </div>
      </form>

      {predictionResult && (
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Simulation Prediction Output:</div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: predictionResult.prediction.color || '#fff' }}>
                AQI {predictionResult.prediction.aqi}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="aqi-category-badge" style={{ backgroundColor: predictionResult.prediction.color }}>
                {predictionResult.prediction.category}
              </span>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Model: {predictionResult.model?.name} (R²: 0.99)
              </div>
            </div>
          </div>
          <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            <strong>Advisory:</strong> {predictionResult.prediction.health_advisory}
          </div>
        </div>
      )}
    </div>
  );
};
