import React from 'react';
import { Loader2, AlertCircle, Compass } from 'lucide-react';

export const LoadingState = () => (
  <div className="glass-card state-container">
    <div className="state-icon loading">
      <Loader2 size={36} />
    </div>
    <div className="state-title">Fetching Real-time Environmental Data</div>
    <div className="state-description">
      Acquiring live meteorological parameters & pollutant telemetry, engineering 21 ML features, and running neural gradient boosting inference...
    </div>
  </div>
);

export const ErrorState = ({ message, onRetry }) => (
  <div className="glass-card state-container">
    <div className="state-icon error">
      <AlertCircle size={36} />
    </div>
    <div className="state-title">Environmental Data Unavailable</div>
    <div className="state-description">
      {message || 'Unable to retrieve live environmental observations for the specified coordinates. Please verify coordinates and try again.'}
    </div>
    {onRetry && (
      <button className="btn-primary" onClick={onRetry} style={{ marginTop: '0.75rem' }}>
        Retry Request
      </button>
    )}
  </div>
);

export const EmptyState = () => (
  <div className="glass-card state-container">
    <div className="state-icon empty">
      <Compass size={36} />
    </div>
    <div className="state-title">Select a Location to Begin</div>
    <div className="state-description">
      Enter target geographic coordinates (Latitude / Longitude) or click any of the preset cities above to generate a real-time AI Air Quality Index prediction.
    </div>
  </div>
);
