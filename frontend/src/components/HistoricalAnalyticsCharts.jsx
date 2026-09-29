import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import { Activity, Wind } from 'lucide-react';

export const HistoricalAnalyticsCharts = ({ trendsData, timeRange, setTimeRange }) => {
  const chartPoints = (trendsData || []).map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    fullTime: new Date(item.timestamp).toLocaleString(),
    aqi: item.aqi,
    pm25: item.pm25,
    pm10: item.pm10,
    no2: item.no2,
    o3: item.o3,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div
          style={{
            background: '#ffffff',
            border: '1px solid #dbeafe',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            boxShadow: '0 8px 24px rgba(15, 23, 42, 0.12)',
          }}
        >
          <p style={{ color: '#0f172a', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            {payload[0]?.payload?.fullTime}
          </p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, fontSize: '0.82rem', margin: '3px 0', fontWeight: 600 }}>
              <strong>{entry.name}:</strong> {entry.value !== null ? entry.value : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* Time Range Filter Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <h3 className="metrics-section-title" style={{ margin: 0 }}>
          <Activity size={18} style={{ color: '#2563eb' }} />
          <span>Historical Analytics & Atmospheric Trends</span>
        </h3>

        <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
          <button
            type="button"
            className={`preset-chip ${timeRange === 24 ? 'active-preset' : ''}`}
            onClick={() => setTimeRange(24)}
          >
            Last 24 Hours
          </button>
          <button
            type="button"
            className={`preset-chip ${timeRange === 168 ? 'active-preset' : ''}`}
            onClick={() => setTimeRange(168)}
          >
            Last 7 Days
          </button>
          <button
            type="button"
            className={`preset-chip ${timeRange === 720 ? 'active-preset' : ''}`}
            onClick={() => setTimeRange(720)}
          >
            Last 30 Days
          </button>
        </div>
      </div>

      {chartPoints.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No historical predictions recorded in this timeframe yet. Perform searches above to populate time-series trends.
        </div>
      ) : (
        <div className="charts-grid">
          {/* Chart 1: AQI Chronological History */}
          <div className="glass-card chart-card">
            <h4 className="chart-title">
              <Activity size={18} style={{ color: '#2563eb' }} />
              <span>AQI Progression Over Time</span>
            </h4>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartPoints}>
                  <defs>
                    <linearGradient id="aqiAreaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={[0, 'auto']} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="aqi" stroke="#2563eb" strokeWidth={2.5} fillOpacity={1} fill="url(#aqiAreaGrad)" name="AQI" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Multi-Pollutant Relative Trend */}
          <div className="glass-card chart-card">
            <h4 className="chart-title">
              <Wind size={18} style={{ color: '#0284c7' }} />
              <span>Pollutant Fluctuation Dynamics</span>
            </h4>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                  <Line type="monotone" dataKey="pm25" stroke="#dc2626" strokeWidth={2} dot={false} name="PM2.5" />
                  <Line type="monotone" dataKey="pm10" stroke="#d97706" strokeWidth={2} dot={false} name="PM10" />
                  <Line type="monotone" dataKey="no2" stroke="#2563eb" strokeWidth={1.8} dot={false} name="NO₂" />
                  <Line type="monotone" dataKey="o3" stroke="#059669" strokeWidth={1.8} dot={false} name="O₃" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
