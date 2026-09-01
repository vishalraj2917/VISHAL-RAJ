import React, { useState } from 'react';
import { HeartPulse, Sparkles, ShieldCheck, AlertTriangle, XCircle, RefreshCw, AlertCircle } from 'lucide-react';
import { getAIHealthAdvice } from '../services/api';

const ACTIVITIES = [
  'Outdoor Exercise (Running / Jogging)',
  'Walking & Commuting',
  'Cycling & High-Intensity Cardio',
  'Outdoor Work & Construction',
  'Children Playground Activities',
  'General Outdoor Leisure',
];

const TARGET_GROUPS = [
  'General Public',
  'Sensitive Groups (Asthma / Respiratory)',
  'Elderly & Seniors',
  'Children & Infants',
  'High-Performance Athletes',
];

export const AIHealthAdvisor = ({ environmentalContext }) => {
  const [selectedActivity, setSelectedActivity] = useState(ACTIVITIES[0]);
  const [selectedTargetGroup, setSelectedTargetGroup] = useState(TARGET_GROUPS[0]);
  const [adviceData, setAdviceData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleGetAdvice = async () => {
    if (!environmentalContext) {
      setErrorMsg('Please select a location with live environmental observations first.');
      return;
    }

    setIsLoading(true);
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

      const res = await getAIHealthAdvice(selectedActivity, selectedTargetGroup, contextPayload);
      if (res && res.advice) {
        setAdviceData(res);
      } else {
        throw new Error('Failed to retrieve personalized health advice.');
      }
    } catch (err) {
      const errorText = err.response?.data?.detail || 'Health Advisory service is temporarily unavailable.';
      setErrorMsg(errorText);
    } finally {
      setIsLoading(false);
    }
  };

  const getSafetyBadge = (rating) => {
    switch (rating) {
      case 'Safe':
        return (
          <span className="safety-rating-badge safe">
            <ShieldCheck size={16} /> Safe for Activity
          </span>
        );
      case 'Caution':
        return (
          <span className="safety-rating-badge caution">
            <AlertTriangle size={16} /> Caution Advised
          </span>
        );
      case 'Unfavorable':
        return (
          <span className="safety-rating-badge unfavorable">
            <XCircle size={16} /> Unfavorable Conditions
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="glass-card ai-feature-card">
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-rose), var(--accent-amber))' }}>
            <HeartPulse size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">Personalized Health & Safety Advisor</h2>
            <p className="ai-feature-subtitle">Contextual preventive recommendations tailored to your planned activity</p>
          </div>
        </div>
      </div>

      <div className="health-controls-grid">
        <div className="input-group">
          <label className="input-label" htmlFor="activity-select">
            Planned Activity:
          </label>
          <select
            id="activity-select"
            className="input-field"
            value={selectedActivity}
            onChange={(e) => setSelectedActivity(e.target.value)}
          >
            {ACTIVITIES.map((act) => (
              <option key={act} value={act} style={{ background: '#111827', color: '#fff' }}>
                {act}
              </option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="group-select">
            Target Audience Group:
          </label>
          <select
            id="group-select"
            className="input-field"
            value={selectedTargetGroup}
            onChange={(e) => setSelectedTargetGroup(e.target.value)}
          >
            {TARGET_GROUPS.map((grp) => (
              <option key={grp} value={grp} style={{ background: '#111827', color: '#fff' }}>
                {grp}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={handleGetAdvice}
          disabled={isLoading || !environmentalContext}
          style={{ height: '46px', alignSelf: 'flex-end' }}
        >
          <Sparkles size={16} className={isLoading ? 'spin-icon' : ''} />
          <span>{isLoading ? 'Consulting Advisor...' : 'Get Personalized Advice'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="chat-error-banner" style={{ margin: '1rem 0' }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {isLoading && (
        <div className="ai-loading-box">
          <RefreshCw size={24} className="spin-icon" style={{ color: 'var(--accent-rose)' }} />
          <span>Analyzing target group vulnerabilities against current particulate levels...</span>
        </div>
      )}

      {!isLoading && !adviceData && !errorMsg && (
        <div className="ai-empty-placeholder">
          <HeartPulse size={32} style={{ color: 'var(--text-muted)' }} />
          <p>Select your planned outdoor activity and target group above, then click <strong>"Get Personalized Advice"</strong> to evaluate atmospheric exposure risks.</p>
        </div>
      )}

      {!isLoading && adviceData && (
        <div className="health-advice-body">
          <div className="health-rating-row">
            <div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Evaluated Activity: </span>
              <strong>{adviceData.activity}</strong> ({adviceData.target_group})
            </div>
            {getSafetyBadge(adviceData.safety_rating)}
          </div>

          <div className="health-advice-text">
            {adviceData.advice}
          </div>

          {adviceData.recommended_precautions?.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.6rem' }}>
                Recommended Actionable Precautions:
              </div>
              <ul className="health-precaution-list">
                {adviceData.recommended_precautions.map((prec, idx) => (
                  <li key={idx} className="health-precaution-item">
                    <ShieldCheck size={16} style={{ color: 'var(--accent-cyan)', flexShrink: 0, marginTop: '2px' }} />
                    <span>{prec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="ai-medical-disclaimer" style={{ marginTop: '1.5rem' }}>
            ⚠️ {adviceData.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
