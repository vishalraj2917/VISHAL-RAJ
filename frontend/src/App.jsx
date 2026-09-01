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
import { PredictionHistoryTable } from './components/PredictionHistoryTable';
import { ManualPredictionForm } from './components/ManualPredictionForm';
import { AIChatbot } from './components/AIChatbot';
import { AIReportGenerator } from './components/AIReportGenerator';
import { AIHealthAdvisor } from './components/AIHealthAdvisor';
import { LoginModal } from './components/LoginModal';
import { RegisterModal } from './components/RegisterModal';
import { ProfileModal } from './components/ProfileModal';
import { LoadingState, ErrorState, EmptyState } from './components/StatusStates';
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

  // Coordinates state
  const [latitude, setLatitude] = useState('12.9716');
  const [longitude, setLongitude] = useState('77.5946');

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

  // Fetch live prediction logic
  const handleFetchLive = useCallback(async (latVal = latitude, lonVal = longitude) => {
    const latNum = parseFloat(latVal);
    const lonNum = parseFloat(lonVal);

    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setErrorMessage('Please enter a valid latitude between -90.0 and 90.0 degrees.');
      return;
    }
    if (isNaN(lonNum) || lonNum < -180 || lonNum > 180) {
      setErrorMessage('Please enter a valid longitude between -180.0 and 180.0 degrees.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getLivePrediction(latNum, lonNum);
      if (response && response.success) {
        setData(response);
        // Refresh analytics and AI insights after new live inference
        fetchAnalyticsAndInsights(timeRange);
      } else {
        throw new Error('API returned an unsuccessful payload structure.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const displayMsg = typeof detail === 'string' ? detail : (err.message || 'Failed to connect to environmental prediction service.');
      setErrorMessage(displayMsg);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [latitude, longitude, fetchAnalyticsAndInsights, timeRange]);

  // Initial load
  useEffect(() => {
    handleFetchLive('12.9716', '77.5946');
  }, []);

  // Refresh handler
  const handleRefresh = () => {
    setIsRefreshing(true);
    handleFetchLive(latitude, longitude);
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
      (pos) => {
        const lat = pos.coords.latitude.toFixed(4);
        const lon = pos.coords.longitude.toFixed(4);
        setLatitude(lat);
        setLongitude(lon);
        handleFetchLive(lat, lon);
      },
      (err) => {
        setIsLoading(false);
        setErrorMessage('Unable to retrieve device GPS coordinates. Please input coordinates manually.');
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
        latitude={latitude}
        longitude={longitude}
        onLatitudeChange={setLatitude}
        onLongitudeChange={setLongitude}
        onFetchLive={() => handleFetchLive(latitude, longitude)}
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

      {isLoading && <LoadingState />}

      {!isLoading && errorMessage && (
        <ErrorState
          message={errorMessage}
          onRetry={() => handleFetchLive(latitude, longitude)}
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

          {/* Manual Parameter Simulation Form */}
          <ManualPredictionForm />

          {/* Dashboard Meta Footer */}
          <footer className="dashboard-footer" style={{ marginTop: '2rem' }}>
            <div>
              Observation Timestamp: <strong>{data.observed_at || 'Live Stream'}</strong> | Target: <strong>{data.location?.latitude}°N, {data.location?.longitude}°E</strong>
            </div>
            <div>
              System Version: 1.0.0 | Connected API: <code>/api/insights</code> & <code>/api/predict/live</code>
            </div>
          </footer>
        </>
      )}

      {/* Auth Modals */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onSwitchToRegister={() => {
          setIsLoginOpen(false);
          setIsRegisterOpen(true);
        }}
      />

      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSwitchToLogin={() => {
          setIsRegisterOpen(false);
          setIsLoginOpen(true);
        }}
      />

      <ProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}

export default App;
