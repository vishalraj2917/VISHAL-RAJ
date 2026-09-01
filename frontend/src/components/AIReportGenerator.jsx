import React, { useState } from 'react';
import { FileText, Sparkles, CheckCircle2, RefreshCw, AlertCircle } from 'lucide-react';
import { generateAIReport } from '../services/api';

export const AIReportGenerator = ({ environmentalContext }) => {
  const [report, setReport] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleGenerate = async () => {
    if (!environmentalContext) {
      setErrorMsg('Please select a location with live environmental data to generate an AI report.');
      return;
    }

    setIsGenerating(true);
    setErrorMsg(null);

    try {
      const contextPayload = {
        latitude: environmentalContext.location?.latitude,
        longitude: environmentalContext.location?.longitude,
        predicted_aqi: environmentalContext.prediction?.aqi,
        aqi_category: environmentalContext.prediction?.category,
        dominant_pollutant: environmentalContext.prediction?.dominant_pollutant,
        pm25: environmentalContext.air_quality?.pm25,
        pm10: environmentalContext.air_quality?.pm10,
        co: environmentalContext.air_quality?.co,
        no2: environmentalContext.air_quality?.no2,
        so2: environmentalContext.air_quality?.so2,
        o3: environmentalContext.air_quality?.o3,
        temperature: environmentalContext.weather?.temperature,
        humidity: environmentalContext.weather?.humidity,
        wind_speed: environmentalContext.weather?.wind_speed,
        pressure: environmentalContext.weather?.pressure,
        observed_at: environmentalContext.observed_at,
      };

      const res = await generateAIReport(contextPayload);
      if (res && res.report) {
        setReport({
          ...res.report,
          generated_at: res.generated_at,
          disclaimer: res.disclaimer,
        });
      } else {
        throw new Error('Failed to parse AI report payload.');
      }
    } catch (err) {
      const errorText = err.response?.data?.detail || 'AI Report Generation is temporarily unavailable.';
      setErrorMsg(errorText);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="glass-card ai-feature-card">
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan))' }}>
            <FileText size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">AI Air Quality Executive Report</h2>
            <p className="ai-feature-subtitle">Comprehensive analytical synthesis of atmospheric & weather telemetry</p>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={isGenerating || !environmentalContext}
          style={{ padding: '0.65rem 1.25rem' }}
        >
          <Sparkles size={16} className={isGenerating ? 'spin-icon' : ''} />
          <span>{isGenerating ? 'Generating Report...' : report ? 'Regenerate Report' : 'Generate Report'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="chat-error-banner" style={{ margin: '1rem 0' }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {isGenerating && (
        <div className="ai-loading-box">
          <RefreshCw size={24} className="spin-icon" style={{ color: 'var(--accent-cyan)' }} />
          <span>Synthesizing environmental observations and computing meteorological impact...</span>
        </div>
      )}

      {!isGenerating && !report && !errorMsg && (
        <div className="ai-empty-placeholder">
          <FileText size={32} style={{ color: 'var(--text-muted)' }} />
          <p>Click <strong>"Generate Report"</strong> to produce an executive AI summary covering current particulate dispersal, meteorological impacts, and public safety guidance.</p>
        </div>
      )}

      {!isGenerating && report && (
        <div className="report-content-body">
          {/* Executive Summary */}
          <div className="report-section">
            <h3 className="report-section-title">1. Executive Overview</h3>
            <p className="report-text">{report.summary}</p>
          </div>

          {/* Air Quality & Pollutant Breakdown */}
          <div className="report-section">
            <h3 className="report-section-title">2. Pollutant Dynamics & Telemetry Analysis</h3>
            <p className="report-text">{report.air_quality_analysis}</p>
          </div>

          {/* Meteorological Dispersal */}
          <div className="report-section">
            <h3 className="report-section-title">3. Meteorological Impact on Dispersion</h3>
            <p className="report-text">{report.weather_impact}</p>
          </div>

          {/* Actionable Recommendations */}
          <div className="report-section">
            <h3 className="report-section-title">4. Strategic Health & Safety Action Items</h3>
            <ul className="report-recommendation-list">
              {report.safety_recommendations?.map((item, idx) => (
                <li key={idx} className="report-recommendation-item">
                  <CheckCircle2 size={16} style={{ color: 'var(--accent-emerald)', flexShrink: 0, marginTop: '2px' }} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="report-meta-footer">
            <span>Generated: {new Date(report.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            <span>{report.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  );
};
