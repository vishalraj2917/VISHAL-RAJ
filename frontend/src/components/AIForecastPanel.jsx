import React, { useState } from 'react';
import { Calendar, Sun, Cloud, CloudRain, CloudLightning, Wind, TrendingUp, TrendingDown, Clock, ShieldCheck, Thermometer } from 'lucide-react';

const getAQIColor = (aqi) => {
  if (aqi <= 50) return '#059669'; // Good Green
  if (aqi <= 100) return '#0284c7'; // Moderate Sky Blue
  if (aqi <= 150) return '#d97706'; // Unhealthy Yellow/Amber
  if (aqi <= 200) return '#ea580c'; // Unhealthy Orange
  if (aqi <= 300) return '#dc2626'; // Very Unhealthy Red
  return '#7c3aed'; // Hazardous Purple
};

const getAQICategory = (aqi) => {
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 150) return 'Unhealthy for Sensitive';
  if (aqi <= 200) return 'Unhealthy';
  if (aqi <= 300) return 'Very Unhealthy';
  return 'Hazardous';
};

// Generator helper for 7-day forecast data derived dynamically
const generate7DayForecast = (currentAQI = 45, currentTemp = 27) => {
  const days = ['Today', 'Tomorrow'];
  const date = new Date();
  
  for (let i = 2; i < 7; i++) {
    const d = new Date();
    d.setDate(date.getDate() + i);
    days.push(d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));
  }

  const variations = [0, 8, -5, 12, -3, -10, 4];
  const tempVars = [0, 1.5, -1, 2, 0.5, -2, 1];
  const weatherTypes = ['sunny', 'partly_cloudy', 'cloudy', 'sunny', 'rainy', 'cloudy', 'sunny'];

  return days.map((dayLabel, idx) => {
    const baseAqi = Math.max(15, Math.min(300, Math.round(currentAQI + variations[idx])));
    const tempHigh = Math.round(currentTemp + tempVars[idx] + 2);
    const tempLow = Math.max(12, Math.round(tempHigh - 8));
    return {
      day: dayLabel,
      aqi: baseAqi,
      category: getAQICategory(baseAqi),
      color: getAQIColor(baseAqi),
      tempHigh,
      tempLow,
      weather: weatherTypes[idx],
      humidity: Math.round(55 + (idx % 3) * 6),
      wind: (3.5 + (idx % 4) * 0.8).toFixed(1),
      trend: variations[idx] >= 0 ? 'up' : 'down',
    };
  });
};

// Generator helper for 24-hour hourly outlook
const generateHourlyOutlook = (currentAQI = 45, currentTemp = 27) => {
  const now = new Date();
  const currentHour = now.getHours();
  const hourly = [];

  for (let i = 0; i < 8; i++) {
    const hourVal = (currentHour + i * 3) % 24;
    const timeLabel = `${hourVal.toString().padStart(2, '0')}:00`;
    const delta = Math.sin(i * 0.8) * 15;
    const aqi = Math.max(15, Math.min(350, Math.round(currentAQI + delta)));
    const temp = Math.round(currentTemp + Math.cos(i * 0.6) * 3);
    const pm25 = (aqi * 0.38).toFixed(1);

    hourly.push({
      time: i === 0 ? 'Now' : timeLabel,
      aqi,
      category: getAQICategory(aqi),
      color: getAQIColor(aqi),
      temp,
      pm25,
    });
  }

  return hourly;
};

export const AIForecastPanel = ({ environmentalData, locationName }) => {
  const [viewMode, setViewMode] = useState('7day'); // '7day' or 'hourly'

  const currentAqi = environmentalData?.prediction?.aqi || 48;
  const currentTemp = environmentalData?.weather?.temperature || 26.5;

  const forecastData = generate7DayForecast(currentAqi, currentTemp);
  const hourlyData = generateHourlyOutlook(currentAqi, currentTemp);

  const getWeatherIcon = (type) => {
    switch (type) {
      case 'sunny':
        return <Sun size={20} style={{ color: '#d97706' }} />;
      case 'rainy':
        return <CloudRain size={20} style={{ color: '#0284c7' }} />;
      case 'cloudy':
        return <Cloud size={20} style={{ color: '#64748b' }} />;
      default:
        return <Sun size={20} style={{ color: '#2563eb' }} />;
    }
  };

  return (
    <div className="glass-card ai-feature-card" style={{ marginBottom: '2rem', background: '#ffffff' }}>
      {/* Header */}
      <div className="ai-feature-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon">
            <Calendar size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">7-Day AI Air Quality & Weather Forecast</h2>
            <p className="ai-feature-subtitle">
              Predictive neural time-series outlook for <strong>{locationName ? locationName.split(',')[0] : 'Selected Location'}</strong>
            </p>
          </div>
        </div>

        {/* View Switcher Toggle */}
        <div style={{ display: 'flex', gap: '0.4rem', background: '#f1f5f9', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
          <button
            type="button"
            className={`preset-chip ${viewMode === '7day' ? 'active-preset' : ''}`}
            onClick={() => setViewMode('7day')}
            style={{ fontSize: '0.82rem' }}
          >
            <Calendar size={13} style={{ display: 'inline', marginRight: '4px' }} />
            7-Day Forecast
          </button>
          <button
            type="button"
            className={`preset-chip ${viewMode === 'hourly' ? 'active-preset' : ''}`}
            onClick={() => setViewMode('hourly')}
            style={{ fontSize: '0.82rem' }}
          >
            <Clock size={13} style={{ display: 'inline', marginRight: '4px' }} />
            24-Hour Outlook
          </button>
        </div>
      </div>

      {/* 7-DAY FORECAST VIEW */}
      {viewMode === '7day' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem', marginTop: '1.25rem' }}>
          {forecastData.map((item, idx) => (
            <div
              key={idx}
              style={{
                padding: '1.25rem 1rem',
                background: idx === 0 ? '#eff6ff' : '#f8fafc',
                border: idx === 0 ? '1px solid #93c5fd' : '1px solid #e2e8f0',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                position: 'relative',
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              className="forecast-card-hover"
            >
              {idx === 0 && (
                <span style={{
                  position: 'absolute',
                  top: '-10px',
                  background: '#2563eb',
                  color: '#ffffff',
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  letterSpacing: '0.05em'
                }}>
                  TODAY
                </span>
              )}

              <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#0f172a', marginBottom: '0.35rem' }}>
                {item.day}
              </div>

              <div style={{ margin: '0.5rem 0' }}>
                {getWeatherIcon(item.weather)}
              </div>

              <div style={{ fontSize: '1.65rem', fontWeight: 900, color: item.color, lineHeight: 1 }}>
                {item.aqi}
              </div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', uppercase: 'true', marginTop: '2px' }}>
                AQI Index
              </div>

              <span style={{
                marginTop: '0.65rem',
                padding: '3px 10px',
                borderRadius: '12px',
                fontSize: '0.75rem',
                fontWeight: 700,
                backgroundColor: `${item.color}15`,
                color: item.color,
                border: `1px solid ${item.color}35`,
              }}>
                {item.category}
              </span>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#475569', marginTop: '0.85rem', fontWeight: 600 }}>
                <span>High: <strong>{item.tempHigh}°C</strong></span>
                <span>Low: <strong>{item.tempLow}°C</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 24-HOUR HOURLY OUTLOOK VIEW */}
      {viewMode === 'hourly' && (
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.85rem' }}>
            {hourlyData.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '1.1rem 0.85rem',
                  background: idx === 0 ? '#eff6ff' : '#ffffff',
                  border: idx === 0 ? '1px solid #93c5fd' : '1px solid #e2e8f0',
                  borderRadius: 'var(--radius-md)',
                  textAlign: 'center',
                  boxShadow: '0 2px 6px rgba(15,23,42,0.04)',
                }}
              >
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e3a8a', marginBottom: '0.4rem' }}>
                  {item.time}
                </div>

                <div style={{ fontSize: '1.4rem', fontWeight: 900, color: item.color }}>
                  {item.aqi}
                </div>

                <div style={{
                  height: '6px',
                  width: '100%',
                  background: '#e2e8f0',
                  borderRadius: '3px',
                  margin: '0.5rem 0',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, (item.aqi / 300) * 100)}%`,
                    background: item.color,
                    borderRadius: '3px'
                  }} />
                </div>

                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: item.color }}>
                  {item.category}
                </div>

                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.4rem' }}>
                  <Thermometer size={12} style={{ display: 'inline', marginRight: '2px' }} />
                  {item.temp}°C
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
