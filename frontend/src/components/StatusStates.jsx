import React from 'react';
import { Loader2, AlertCircle, Compass } from 'lucide-react';

export const LoadingState = () => (
  <div className="glass-card state-container">
    <div className="state-icon loading">
      <Loader2 size={36} />
    </div>
    <div className="state-title">Fetching Live Air Quality Data</div>
    <div className="state-description">
      Acquiring real-time meteorological parameters & pollutant telemetry, engineering ML features, and running neural prediction inference...
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
      {message || 'Unable to retrieve live environmental observations for the selected location. Please search for a valid city or address and try again.'}
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
    <div className="state-title">Search a Location to View Air Quality</div>
    <div className="state-description">
      Search any city, address, or landmark above or click any of the preset cities to generate a real-time AI Air Quality Index prediction.
    </div>
  </div>
);
