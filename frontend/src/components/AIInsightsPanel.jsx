import React from 'react';
import { Sparkles, Activity, Wind, ShieldCheck, RefreshCw, CheckCircle2, AlertTriangle, AlertCircle, Compass, Home } from 'lucide-react';

export const AIInsightsPanel = ({ insights, onRefresh, isRefreshing }) => {
  if (!insights) return null;

  return (
    <div className="glass-card ai-feature-card" style={{ marginBottom: '2rem' }}>
      {/* Header */}
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-violet), var(--accent-cyan))' }}>
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">AI Air Quality Insights & Recommendations</h2>
            <p className="ai-feature-subtitle">Deterministic diagnostic interpretation driven by the champion ML model</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={onRefresh}
            disabled={isRefreshing}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin-icon' : ''} />
            <span>{isRefreshing ? 'Updating...' : 'Refresh Insights'}</span>
          </button>
        </div>
      </div>

      {/* Top Overview Cards Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.25)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Predicted AQI</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: insights.color || 'var(--accent-cyan)', marginTop: '2px' }}>
            {insights.aqi}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Status: <strong>{insights.category}</strong></div>
        </div>

        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.25)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Evaluated Risk</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>
            {insights.risk_level}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Confidence: <strong>{Math.round((insights.confidence || 0.95) * 100)}%</strong></div>
        </div>

        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.25)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Trajectory Trend</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '6px' }}>
            {insights.trend}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Historical comparative</div>
        </div>

        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.25)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Primary Pollutants</div>
          <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
            {insights.primary_pollutants?.map((p, i) => (
              <span key={i} style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid rgba(6, 182, 212, 0.3)', color: 'var(--accent-cyan)', fontSize: '0.8rem', fontWeight: 600 }}>
                {p}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Main Insights Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Left Column: Summary & Activity Advice */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="report-section">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Sparkles size={16} style={{ color: 'var(--accent-cyan)' }} />
              <h3 className="report-section-title" style={{ margin: 0 }}>Executive AI Diagnosis</h3>
            </div>
            <p className="report-text">{insights.summary}</p>
          </div>

          <div className="report-section">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Compass size={16} style={{ color: 'var(--accent-amber)' }} />
              <h3 className="report-section-title" style={{ margin: 0 }}>Outdoor Activity & Exercise</h3>
            </div>
            <p className="report-text">{insights.outdoor_activity}</p>
          </div>
        </div>

        {/* Right Column: Ventilation & Protective Measures */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="report-section">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Home size={16} style={{ color: 'var(--accent-emerald)' }} />
              <h3 className="report-section-title" style={{ margin: 0 }}>Ventilation & Air Purifier Guidance</h3>
            </div>
            <p className="report-text">{insights.ventilation}</p>
          </div>

          <div className="report-section">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <ShieldCheck size={16} style={{ color: 'var(--accent-rose)' }} />
              <h3 className="report-section-title" style={{ margin: 0 }}>Protective Gear / Mask Advice</h3>
            </div>
            <p className="report-text">{insights.mask_recommendation}</p>
          </div>
        </div>
      </div>

      {/* Smart Recommendations List */}
      <div className="report-section">
        <h3 className="report-section-title" style={{ marginBottom: '0.75rem' }}>Actionable Health & Lifestyle Action Items</h3>
        <ul className="report-recommendation-list">
          {insights.recommendations?.map((item, idx) => (
            <li key={idx} className="report-recommendation-item">
              <CheckCircle2 size={16} style={{ color: 'var(--accent-emerald)', flexShrink: 0, marginTop: '2px' }} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Meta Footer */}
      <div className="report-meta-footer" style={{ marginTop: '1.25rem' }}>
        <span>Engine: <strong>{insights.generated_by}</strong> | Updated: {new Date(insights.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        <span>General Awareness Notice: Environmental AI insights do not replace medical advice from a qualified healthcare professional.</span>
      </div>
    </div>
  );
};
