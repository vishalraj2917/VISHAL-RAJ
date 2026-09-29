import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardHeader } from './components/DashboardHeader';
import { LocationSelector } from './components/LocationSelector';
import { AQICard } from './components/AQICard';
import { PollutantGrid } from './components/PollutantGrid';
import { WeatherGrid } from './components/WeatherGrid';
import { PollutantBarChart, EnvironmentalGaugeChart } from './components/DashboardCharts';
import { AnalyticsSummaryCards } from './components/AnalyticsSummaryCards';
import { HistoricalAnalyticsCharts } from './components/HistoricalAnalyticsCharts';
import { AIInsightsPanel } from './components/AIInsightsPanel';
import { AIForecastPanel } from './components/AIForecastPanel';
import { OutdoorHealthCalculator } from './components/OutdoorHealthCalculator';
import { PredictionHistoryTable } from './components/PredictionHistoryTable';
import { AIChatbot } from './components/AIChatbot';
import { AIReportGenerator } from './components/AIReportGenerator';
import { AIHealthAdvisor } from './components/AIHealthAdvisor';
import { AirQualityMap } from './components/AirQualityMap';
import { LoginModal } from './components/LoginModal';
import { RegisterModal } from './components/RegisterModal';
import { ProfileModal } from './components/ProfileModal';
import { LoadingState, ErrorState, EmptyState } from './components/StatusStates';
import { reverseGeocode, PRESET_FALLBACKS } from './utils/geocoding';

import {
  getLivePrediction,
  checkHealth,
  getAnalyticsSummary,
  getAnalyticsTrends,
  getPredictionHistory,
  getInsights,
} from './services/api';

function DashboardContent() {
  const { user } = useAuth();

  // Auth modal states
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Active Location state
  const [latitude, setLatitude] = useState('12.9716');
  const [longitude, setLongitude] = useState('77.5946');
  const [locationName, setLocationName] = useState('Bengaluru, Karnataka, India');

  // Application telemetry & model states
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [data, setData] = useState(null);
  const [backendStatus, setBackendStatus] = useState('ok');

  // Analytics & History states
  const [summaryData, setSummaryData] = useState(null);
  const [trendsData, setTrendsData] = useState([]);
  const [historyData, setHistoryData] = useState({ count: 0, total: 0, history: [] });
  const [timeRange, setTimeRange] = useState(168); // 7 days

  // AI Insights state
  const [insightsData, setInsightsData] = useState(null);

  // Fetch analytics, history, and AI insights
  const fetchAnalyticsAndInsights = useCallback(async (hours = timeRange) => {
    try {
      const [sumRes, trendsRes, histRes, insRes] = await Promise.allSettled([
        getAnalyticsSummary(hours),
        getAnalyticsTrends(hours),
        getPredictionHistory(10, 0),
        getInsights(),
      ]);

      if (sumRes.status === 'fulfilled') setSummaryData(sumRes.value);
      if (trendsRes.status === 'fulfilled') setTrendsData(trendsRes.value.trends || []);
      if (histRes.status === 'fulfilled') setHistoryData(histRes.value);
      if (insRes.status === 'fulfilled') setInsightsData(insRes.value);
    } catch (err) {
      console.warn('Analytics & Insights retrieval warning:', err);
    }
  }, [timeRange]);

  // Re-fetch user-scoped data when authentication state changes
  useEffect(() => {
    fetchAnalyticsAndInsights(timeRange);
  }, [user, fetchAnalyticsAndInsights, timeRange]);

  useEffect(() => {
    const initSystem = async () => {
      try {
        const res = await checkHealth();
        setBackendStatus(res.status || 'ok');
      } catch (err) {
        setBackendStatus('degraded');
      }
      fetchAnalyticsAndInsights();
    };
    initSystem();
  }, [fetchAnalyticsAndInsights]);

  // Periodic Auto-refresh (every 60s)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAnalyticsAndInsights(timeRange);
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchAnalyticsAndInsights, timeRange]);

  // Fetch live prediction logic for chosen location
  const handleFetchLive = useCallback(async (latVal = latitude, lonVal = longitude, nameVal = locationName) => {
    const latNum = parseFloat(latVal);
    const lonNum = parseFloat(lonVal);

    if (isNaN(latNum) || isNaN(lonNum)) {
      setErrorMessage('Invalid location coordinates. Please search for a valid city or address.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getLivePrediction(latNum, lonNum);
      if (response && response.success) {
        // Attach user-friendly location name to data payload
        const enrichedData = {
          ...response,
          locationName: nameVal || response.city || 'Searched Location',
        };
        setData(enrichedData);
        if (nameVal) setLocationName(nameVal);
        setLatitude(latVal.toString());
        setLongitude(lonVal.toString());

        fetchAnalyticsAndInsights(timeRange);
      } else {
        throw new Error('Environmental API returned an unsuccessful response structure.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const displayMsg = typeof detail === 'string' ? detail : (err.message || 'Failed to connect to environmental prediction service.');
      setErrorMessage(displayMsg);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [latitude, longitude, locationName, fetchAnalyticsAndInsights, timeRange]);

  // Initial load
  useEffect(() => {
    handleFetchLive('12.9716', '77.5946', 'Bengaluru, Karnataka, India');
  }, []);

  // Handle direct location selection from search or quick chips
  const handleSelectLocation = (lat, lon, name) => {
    setLatitude(lat.toString());
    setLongitude(lon.toString());
    setLocationName(name);
    handleFetchLive(lat.toString(), lon.toString(), name);
  };

  // Refresh handler
  const handleRefresh = () => {
    setIsRefreshing(true);
    handleFetchLive(latitude, longitude, locationName);
    fetchAnalyticsAndInsights(timeRange);
  };

  // Pagination handler for history
  const handleHistoryPagination = async (limit, offset) => {
    try {
      const res = await getPredictionHistory(limit, offset);
      if (res && res.success) {
        setHistoryData(res);
      }
    } catch (err) {
      console.warn('Pagination error:', err);
    }
  };

  // HTML5 Geolocation support
  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }

    setIsLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude.toFixed(4);
        const lon = pos.coords.longitude.toFixed(4);
        let placeName = `Current Device Location (${lat}, ${lon})`;
        try {
          placeName = await reverseGeocode(lat, lon);
        } catch (e) {
          console.warn('Reverse geocode error:', e);
        }
        handleSelectLocation(lat, lon, placeName);
      },
      (err) => {
        setIsLoading(false);
        setErrorMessage('Unable to retrieve device GPS location. Please search for a city or address manually.');
      }
    );
  };

  return (
    <div className="dashboard-container">
      <DashboardHeader
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        backendStatus={backendStatus}
        lastUpdated={data?.observed_at || data?.timestamp}
        onOpenLogin={() => setIsLoginOpen(true)}
        onOpenRegister={() => setIsRegisterOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
      />

      <LocationSelector
        selectedLocationName={locationName}
        onSelectLocation={handleSelectLocation}
        isLoading={isLoading}
        onUseCurrentLocation={handleUseCurrentLocation}
      />

      {/* Analytics Summary Cards Banner */}
      <AnalyticsSummaryCards summary={summaryData} />

      {/* AI-Powered Insights & Smart Recommendations Panel */}
      <AIInsightsPanel
        insights={insightsData}
        onRefresh={() => fetchAnalyticsAndInsights(timeRange)}
        isRefreshing={isRefreshing}
      />

      {/* Interactive Geospatial Air Quality Map */}
      <AirQualityMap
        latitude={latitude}
        longitude={longitude}
        locationName={locationName}
        prediction={data?.prediction}
        airQuality={data?.air_quality}
        cityPresets={PRESET_FALLBACKS}
        onLocationSelect={(newLat, newLon, newName) => {
          handleSelectLocation(newLat, newLon, newName);
        }}
      />

      {/* 7-Day AI Air Quality & Weather Forecast */}
      <AIForecastPanel environmentalData={data} locationName={locationName} />

      {/* Outdoor Health & Mask Recommendation Calculator */}
      <OutdoorHealthCalculator environmentalData={data} locationName={locationName} />

      {isLoading && <LoadingState />}

      {!isLoading && errorMessage && (
        <ErrorState
          message={errorMessage}
          onRetry={() => handleFetchLive(latitude, longitude, locationName)}
        />
      )}

      {!isLoading && !errorMessage && !data && <EmptyState />}

      {!isLoading && !errorMessage && data && (
        <>
          {/* Main Top Grid: AQI Card + Pollutant & Weather breakdown */}
          <div className="main-grid">
            <AQICard
              prediction={data.prediction}
              model={data.model}
              observedAt={data.observed_at}
              locationName={locationName}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <PollutantGrid airQuality={data.air_quality} />
              <WeatherGrid weather={data.weather} />
            </div>
          </div>

          {/* Visual Analytics Real-time Gauges */}
          <div className="charts-grid">
            <PollutantBarChart airQuality={data.air_quality} />
            <EnvironmentalGaugeChart weather={data.weather} prediction={data.prediction} />
          </div>

          {/* Historical Analytics Time Series & Fluctuation Trends */}
          <HistoricalAnalyticsCharts
            trendsData={trendsData}
            timeRange={timeRange}
            setTimeRange={(range) => {
              setTimeRange(range);
              fetchAnalyticsAndInsights(range);
            }}
          />

          {/* Prediction Ledger Table */}
          <PredictionHistoryTable
            historyData={historyData}
            onRefresh={handleHistoryPagination}
          />

          {/* AI Conversational & Specialized Modules */}
          <div className="ai-section-container">
            <AIChatbot environmentalContext={data} />
            <AIReportGenerator environmentalContext={data} />
            <AIHealthAdvisor environmentalContext={data} />
          </div>
        </>
      )}

      {/* Auth Modals */}
      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />
      <RegisterModal isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} />
      <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />

      <footer style={{
        marginTop: '4rem',
        padding: '1.5rem 0',
        borderTop: '1px solid var(--border-color)',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.85rem'
      }}>
        <div>
          AI Air Quality Prediction Engine &copy; {new Date().getFullYear()} &bull; Blue & White Environmental Intelligence Platform
        </div>
        {data && (
          <div style={{ fontSize: '0.78rem', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            Observation Timestamp: <strong>{data.observed_at || 'Live Stream'}</strong> | Location: <strong>{locationName || data.city || 'Bengaluru'}</strong>
          </div>
        )}
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
