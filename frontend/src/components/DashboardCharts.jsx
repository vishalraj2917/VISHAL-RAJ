import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from 'recharts';
import { BarChart3, PieChart } from 'lucide-react';

export const PollutantBarChart = ({ airQuality }) => {
  if (!airQuality) return null;

  const data = [
    { name: 'PM2.5', value: airQuality.pm25, unit: 'µg/m³', color: '#f43f5e' },
    { name: 'PM10', value: airQuality.pm10, unit: 'µg/m³', color: '#fb923c' },
    { name: 'NO2', value: airQuality.no2, unit: 'µg/m³', color: '#facc15' },
    { name: 'SO2', value: airQuality.so2, unit: 'µg/m³', color: '#a855f7' },
    { name: 'O3', value: airQuality.o3, unit: 'µg/m³', color: '#06b6d4' },
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div style={{
          backgroundColor: '#1f2937',
          padding: '0.6rem 0.9rem',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#fff',
          fontSize: '0.85rem'
        }}>
          <div style={{ fontWeight: 600, color: item.color }}>{item.name}</div>
          <div>Concentration: <strong>{item.value} {item.unit}</strong></div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card chart-card">
      <div className="chart-title">
        <BarChart3 size={18} style={{ color: 'var(--accent-cyan)' }} />
        <span>Particulate & Atmospheric Pollutants (µg/m³)</span>
      </div>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} />
            <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const EnvironmentalGaugeChart = ({ weather, prediction }) => {
  if (!weather || !prediction) return null;

  const aqiScore = prediction.aqi || 0;
  const aqiColor = prediction.color || '#10b981';

  const gaugeData = [
    {
      name: 'AQI',
      value: Math.min(aqiScore, 500),
      fill: aqiColor,
    },
  ];

  return (
    <div className="glass-card chart-card">
      <div className="chart-title">
        <PieChart size={18} style={{ color: 'var(--accent-emerald)' }} />
        <span>AQI Severity Scale (0 – 500)</span>
      </div>
      <div style={{ width: '100%', height: 260, position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            barSize={18}
            data={gaugeData}
            startAngle={180}
            endAngle={0}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 500]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: 'rgba(255, 255, 255, 0.06)' }}
              dataKey="value"
              cornerRadius={10}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div style={{
          position: 'absolute',
          bottom: '22%',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: aqiColor, lineHeight: 1 }}>
            {typeof aqiScore === 'number' ? aqiScore.toFixed(1) : aqiScore}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {prediction.category || 'Standard'}
          </div>
        </div>
      </div>
    </div>
  );
};
