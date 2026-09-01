import React from 'react';
import { Activity, RefreshCw, User, LogIn, LogOut, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const DashboardHeader = ({
  onRefresh,
  isRefreshing,
  backendStatus,
  lastUpdated,
  onOpenLogin,
  onOpenRegister,
  onOpenProfile,
}) => {
  const { user, logout } = useAuth();

  return (
    <header className="dashboard-header">
      <div className="brand-badge">
        <div className="brand-icon">
          <Activity size={24} />
        </div>
        <div>
          <h1 className="brand-title">AI Air Quality Prediction</h1>
          <p className="brand-subtitle">Real-time Environmental Forecasting & ML Health Insights</p>
        </div>
      </div>

      <div className="header-status">
        <div className="status-pill">
          <span className="status-dot"></span>
          <span>{backendStatus === 'ok' ? 'System Online' : 'System Degraded'}</span>
        </div>

        <button
          className="btn-secondary"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh live environmental observations"
        >
          <RefreshCw size={16} className={isRefreshing ? 'spin-icon' : ''} />
          <span>{isRefreshing ? 'Updating...' : 'Refresh'}</span>
        </button>

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: '0.5rem' }}>
            <button
              className="btn-secondary"
              onClick={onOpenProfile}
              title="Account Settings"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <User size={15} style={{ color: 'var(--accent-cyan)' }} />
              <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.name || user.username}
              </span>
            </button>

            <button
              className="btn-secondary"
              onClick={logout}
              title="Log Out"
              style={{ padding: '0.5rem', color: 'var(--accent-rose)' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: '0.5rem' }}>
            <button
              className="btn-secondary"
              onClick={onOpenLogin}
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <LogIn size={15} />
              <span>Sign In</span>
            </button>

            <button
              className="btn-primary"
              onClick={onOpenRegister}
              style={{ padding: '0.5rem 0.9rem', fontSize: '0.85rem' }}
            >
              <span>Register</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
