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
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            boxShadow: '0 8px 16px rgba(0,0,0,0.5)',
          }}
        >
          <p style={{ color: '#fff', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.4rem' }}>
            {payload[0]?.payload?.fullTime}
          </p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, fontSize: '0.82rem', margin: '2px 0' }}>
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h3 className="metrics-section-title" style={{ margin: 0 }}>
          <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>Historical Analytics & Atmospheric Trends</span>
        </h3>

        <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.25)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <button
            type="button"
            className={`preset-chip ${timeRange === 24 ? 'active-filter' : ''}`}
            onClick={() => setTimeRange(24)}
            style={timeRange === 24 ? { background: 'rgba(6, 182, 212, 0.25)', borderColor: 'var(--accent-cyan)', color: '#fff' } : {}}
          >
            Last 24 Hours
          </button>
          <button
            type="button"
            className={`preset-chip ${timeRange === 168 ? 'active-filter' : ''}`}
            onClick={() => setTimeRange(168)}
            style={timeRange === 168 ? { background: 'rgba(6, 182, 212, 0.25)', borderColor: 'var(--accent-cyan)', color: '#fff' } : {}}
          >
            Last 7 Days
          </button>
          <button
            type="button"
            className={`preset-chip ${timeRange === 720 ? 'active-filter' : ''}`}
            onClick={() => setTimeRange(720)}
            style={timeRange === 720 ? { background: 'rgba(6, 182, 212, 0.25)', borderColor: 'var(--accent-cyan)', color: '#fff' } : {}}
          >
            Last 30 Days
          </button>
        </div>
      </div>

      {chartPoints.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No historical predictions recorded in this timeframe yet. Run predictions above to populate time-series trends.
        </div>
      ) : (
        <div className="charts-grid">
          {/* Chart 1: AQI Chronological History */}
          <div className="glass-card chart-card">
            <h4 className="chart-title">
              <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>AQI Progression Over Time</span>
            </h4>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartPoints}>
                  <defs>
                    <linearGradient id="aqiAreaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="time" stroke="#9ca3af" fontSize={11} tickLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={11} tickLine={false} domain={[0, 'auto']} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="aqi" stroke="#06b6d4" strokeWidth={2.5} fillOpacity={1} fill="url(#aqiAreaGrad)" name="AQI" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Multi-Pollutant Relative Trend */}
          <div className="glass-card chart-card">
            <h4 className="chart-title">
              <Wind size={18} style={{ color: 'var(--accent-amber)' }} />
              <span>Pollutant Fluctuation Dynamics</span>
            </h4>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="time" stroke="#9ca3af" fontSize={11} tickLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={11} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                  <Line type="monotone" dataKey="pm25" stroke="#f43f5e" strokeWidth={2} dot={false} name="PM2.5" />
                  <Line type="monotone" dataKey="pm10" stroke="#f59e0b" strokeWidth={2} dot={false} name="PM10" />
                  <Line type="monotone" dataKey="no2" stroke="#3b82f6" strokeWidth={1.8} dot={false} name="NO₂" />
                  <Line type="monotone" dataKey="o3" stroke="#10b981" strokeWidth={1.8} dot={false} name="O₃" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
