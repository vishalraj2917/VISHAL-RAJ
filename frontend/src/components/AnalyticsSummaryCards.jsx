import React from 'react';
import { Activity, TrendingUp, TrendingDown, Minus, Clock, BarChart3 } from 'lucide-react';

export const AnalyticsSummaryCards = ({ summary }) => {
  if (!summary) return null;

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving':
        return (
          <span style={{ color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem' }}>
            <TrendingDown size={16} /> Improving (Lower AQI)
          </span>
        );
      case 'deteriorating':
        return (
          <span style={{ color: 'var(--accent-rose)', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem' }}>
            <TrendingUp size={16} /> Deteriorating (Higher AQI)
          </span>
        );
      default:
        return (
          <span style={{ color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem' }}>
            <Minus size={16} /> Stable Baseline
          </span>
        );
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
      {/* Current AQI Card */}
      <div className="metric-card glass-card">
        <div className="metric-header">
          <span className="metric-name">Active AQI</span>
          <Activity size={18} style={{ color: summary.current_color || 'var(--accent-cyan)' }} />
        </div>
        <div className="metric-value-row">
          <span className="metric-value" style={{ color: summary.current_color || 'var(--text-primary)' }}>
            {summary.current_aqi !== null ? summary.current_aqi : '—'}
          </span>
          <span className="metric-unit">{summary.current_category || 'N/A'}</span>
        </div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Status Category: <strong>{summary.current_category || 'Pending'}</strong>
        </div>
      </div>

      {/* Average AQI Card */}
      <div className="metric-card glass-card">
        <div className="metric-header">
          <span className="metric-name">Average AQI</span>
          <BarChart3 size={18} style={{ color: 'var(--accent-blue)' }} />
        </div>
        <div className="metric-value-row">
          <span className="metric-value">{summary.average_aqi || '0.0'}</span>
          <span className="metric-unit">Overall</span>
        </div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Samples recorded: <strong>{summary.total_predictions}</strong>
        </div>
      </div>

      {/* Max / Min Dynamic Range */}
      <div className="metric-card glass-card">
        <div className="metric-header">
          <span className="metric-name">Range (Min / Max)</span>
          <Activity size={18} style={{ color: 'var(--accent-amber)' }} />
        </div>
        <div className="metric-value-row">
          <span className="metric-value">{summary.min_aqi}</span>
          <span className="metric-unit">to {summary.max_aqi}</span>
        </div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Extreme recorded variations
        </div>
      </div>

      {/* Trend Direction */}
      <div className="metric-card glass-card">
        <div className="metric-header">
          <span className="metric-name">Trajectory Trend</span>
          <Clock size={18} style={{ color: 'var(--accent-violet)' }} />
        </div>
        <div style={{ marginTop: '0.25rem' }}>
          {getTrendIcon(summary.trend_direction)}
        </div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {summary.most_recent_timestamp
            ? `Updated: ${new Date(summary.most_recent_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
            : 'No prior records'}
        </div>
      </div>
    </div>
  );
};
