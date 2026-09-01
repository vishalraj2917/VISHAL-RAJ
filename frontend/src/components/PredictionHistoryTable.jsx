import React, { useState } from 'react';
import { History, ChevronLeft, ChevronRight, MapPin, Calendar, Clock } from 'lucide-react';

export const PredictionHistoryTable = ({ historyData, onRefresh, limit = 10 }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const items = historyData?.history || [];
  const total = historyData?.total || 0;
  const totalPages = Math.ceil(total / limit) || 1;

  const handlePrev = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
      onRefresh(limit, (currentPage - 2) * limit);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
      onRefresh(limit, currentPage * limit);
    }
  };

  return (
    <div className="glass-card ai-feature-card" style={{ marginBottom: '2rem' }}>
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))' }}>
            <History size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">Prediction & Observation History</h2>
            <p className="ai-feature-subtitle">Comprehensive ledger of past ML model inferences and sensory telemetry</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <span>Page {currentPage} of {totalPages} ({total} records)</span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              type="button"
              className="btn-icon-secondary"
              onClick={handlePrev}
              disabled={currentPage <= 1}
              style={{ width: '32px', height: '32px' }}
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className="btn-icon-secondary"
              onClick={handleNext}
              disabled={currentPage >= totalPages}
              style={{ width: '32px', height: '32px' }}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="ai-empty-placeholder">
          <History size={32} style={{ color: 'var(--text-muted)' }} />
          <p>No prediction history recorded yet. Use the prediction form or select a location to record observations.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
                <th style={{ padding: '0.75rem 1rem' }}>Location / City</th>
                <th style={{ padding: '0.75rem 1rem' }}>Predicted AQI</th>
                <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                <th style={{ padding: '0.75rem 1rem' }}>PM2.5</th>
                <th style={{ padding: '0.75rem 1rem' }}>PM10</th>
                <th style={{ padding: '0.75rem 1rem' }}>Temp (°C)</th>
                <th style={{ padding: '0.75rem 1rem' }}>Humidity</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.2s' }}>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(row.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} style={{ color: 'var(--accent-cyan)' }} />
                      <span>{row.city}</span>
                    </div>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: row.color }}>
                    {row.predicted_aqi}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: `${row.color}25`,
                        color: row.color,
                        border: `1px solid ${row.color}40`,
                      }}
                    >
                      {row.aqi_category}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>{row.pm25 !== null ? `${row.pm25} µg` : '—'}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{row.pm10 !== null ? `${row.pm10} µg` : '—'}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{row.temperature !== null ? `${row.temperature}°` : '—'}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{row.humidity !== null ? `${row.humidity}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
