import React, { useState } from 'react';
import { ShieldCheck, Activity, AlertCircle, Heart, User, CheckCircle2, Info, Wind } from 'lucide-react';

const ACTIVITIES = [
  { id: 'jogging', name: 'Outdoor Jogging / Running', intensity: 'High' },
  { id: 'cycling', name: 'Cycling / Biking', intensity: 'High' },
  { id: 'walking', name: 'Walking & Daily Commute', intensity: 'Moderate' },
  { id: 'play', name: 'Children Outdoor Play', intensity: 'Moderate' },
  { id: 'sports', name: 'Outdoor Sports / Field Work', intensity: 'High' },
  { id: 'stroll', name: 'Light Stroll / Relaxing', intensity: 'Low' },
];

const TARGET_GROUPS = [
  { id: 'general', name: 'General Healthy Adults' },
  { id: 'children', name: 'Children & Toddlers' },
  { id: 'seniors', name: 'Seniors (Age 65+)' },
  { id: 'respiratory', name: 'Asthma / Heart & Respiratory Condition' },
];

export const OutdoorHealthCalculator = ({ environmentalData, locationName }) => {
  const [selectedActivity, setSelectedActivity] = useState('jogging');
  const [selectedGroup, setSelectedGroup] = useState('general');

  const currentAQI = environmentalData?.prediction?.aqi || 55;
  const pm25 = environmentalData?.air_quality?.pm25 || 18.5;

  // Calculate safety & mask recommendations
  const getRecommendation = () => {
    const act = ACTIVITIES.find((a) => a.id === selectedActivity);
    const grp = TARGET_GROUPS.find((g) => g.id === selectedGroup);

    let riskMultiplier = 1.0;
    if (act?.intensity === 'High') riskMultiplier *= 1.35;
    if (grp?.id === 'children' || grp?.id === 'seniors') riskMultiplier *= 1.3;
    if (grp?.id === 'respiratory') riskMultiplier *= 1.6;

    const effectiveAQI = Math.round(currentAQI * riskMultiplier);

    let maskType = 'No Mask Needed';
    let maskColor = '#059669';
    let safetyScore = 95;
    let safeDuration = 'Unrestricted Outdoor Exposure';
    let advice = 'Air quality is favorable. Outdoor exercise is safe and encouraged.';

    if (effectiveAQI > 200) {
      maskType = 'N95 / FFP2 Respirator Required';
      maskColor = '#dc2626';
      safetyScore = 25;
      safeDuration = 'Avoid outdoor exertion (Max 15 mins essential only)';
      advice = 'Hazardous air conditions. Remain indoors with air purification if possible.';
    } else if (effectiveAQI > 120) {
      maskType = 'N95 / KN95 Mask Strongly Advised';
      maskColor = '#ea580c';
      safetyScore = 50;
      safeDuration = 'Limit exertion to 30 minutes max';
      advice = 'Unhealthy air for sensitive individuals. Wear an N95 mask during prolonged exposure.';
    } else if (effectiveAQI > 75) {
      maskType = 'Cloth or Surgical Mask Recommended';
      maskColor = '#d97706';
      safetyScore = 75;
      safeDuration = '1 to 2 hours of light exertion';
      advice = 'Moderate air pollution. Sensitive groups should take frequent indoor breaks.';
    }

    return {
      effectiveAQI,
      maskType,
      maskColor,
      safetyScore,
      safeDuration,
      advice,
      activityName: act?.name,
      groupName: grp?.name,
    };
  };

  const result = getRecommendation();

  return (
    <div className="glass-card ai-feature-card" style={{ marginBottom: '2rem', background: '#ffffff' }}>
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon">
            <Heart size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">Outdoor Health & Mask Recommendation Calculator</h2>
            <p className="ai-feature-subtitle">
              Personalized activity safety score for <strong>{locationName ? locationName.split(',')[0] : 'Current Location'}</strong> (AQI: {currentAQI})
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.75rem', marginTop: '1rem' }}>
        {/* Input Selectors */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="input-group">
            <label className="input-label" htmlFor="activity-select">
              Select Outdoor Activity
            </label>
            <select
              id="activity-select"
              className="input-field"
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
            >
              {ACTIVITIES.map((act) => (
                <option key={act.id} value={act.id}>
                  {act.name} ({act.intensity} Intensity)
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="group-select">
              Select Individual Health Profile
            </label>
            <select
              id="group-select"
              className="input-field"
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
            >
              {TARGET_GROUPS.map((grp) => (
                <option key={grp.id} value={grp.id}>
                  {grp.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ padding: '1rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', color: '#475569' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: '#1e3a8a', marginBottom: '4px' }}>
              <Info size={15} style={{ color: '#2563eb' }} />
              <span>Real-Time Environmental Metrics</span>
            </div>
            Current AQI: <strong>{currentAQI}</strong> | Fine PM2.5: <strong>{pm25} µg/m³</strong>
          </div>
        </div>

        {/* Calculation Result Display */}
        <div style={{
          padding: '1.5rem',
          background: '#eff6ff',
          border: '1px solid #93c5fd',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#1e40af', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Personalized Outdoor Risk Index
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '0.75rem 0' }}>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 900, color: result.maskColor, lineHeight: 1 }}>
                  {result.safetyScore}%
                </div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>Safety Index</div>
              </div>

              <span style={{
                padding: '0.4rem 1rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.85rem',
                fontWeight: 800,
                backgroundColor: result.maskColor,
                color: '#ffffff',
                boxShadow: '0 4px 10px rgba(0,0,0,0.15)'
              }}>
                {result.maskType}
              </span>
            </div>

            <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '0.85rem', color: '#0f172a', fontWeight: 700 }}>
                Safe Outdoor Duration:
              </div>
              <div style={{ fontSize: '0.9rem', color: '#1d4ed8', fontWeight: 600, marginTop: '2px' }}>
                {result.safeDuration}
              </div>
            </div>

            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: '#334155', lineHeight: 1.5 }}>
              <strong>Health Tip:</strong> {result.advice}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
