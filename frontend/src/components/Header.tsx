import React from 'react';
import type { BackendStatus, User } from '../types';

interface HeaderProps {
  user: User | null;
  challengeDay: number;
  streak: number;
  backendStatus: BackendStatus;
  wakeSeconds: number;
  onActivateBackend: () => void;
  onLogin: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  challengeDay,
  streak,
  backendStatus,
  wakeSeconds,
  onActivateBackend,
  onLogin,
  onLogout,
}) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <span className="brand-logo" role="img" aria-label="sword">⚔️</span>
        <div>
          <h1 className="brand-title">DailyForge</h1>
          <p className="brand-subtitle">Striver SDE 180 &bull; Consistency Tracker</p>
        </div>
      </div>

      <div className="header-actions">
        {user && (
          <>
            <span className="badge badge-day">
              Day {challengeDay || 1} of 100
            </span>
            <span className="badge badge-streak">
              🔥 {streak} {streak === 1 ? 'Day' : 'Days'}
            </span>
          </>
        )}

        {backendStatus === 'ready' && (
          <span className="badge badge-backend ready" title="Render backend service is live and connected to database">
            🟢 Backend Ready
          </span>
        )}

        {backendStatus === 'waking' && (
          <span className="badge badge-backend waking" title="Waking up Render free tier container">
            ⏳ Waking ({wakeSeconds}s)...
          </span>
        )}

        {(backendStatus === 'idle' || backendStatus === 'error' || backendStatus === 'timeout') && (
          <button
            className="btn btn-outline btn-sm"
            onClick={onActivateBackend}
            title="Click to ping and wake up Render backend"
          >
            ⚡ Activate Backend
          </button>
        )}

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.username}
                style={{ width: '28px', height: '28px', borderRadius: '50%', border: '1px solid var(--border-card)' }}
              />
            )}
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{user.username}</span>
            <button className="btn btn-outline btn-sm" onClick={onLogout}>
              Logout
            </button>
          </div>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={onLogin}>
            Sign in with GitHub
          </button>
        )}
      </div>
    </header>
  );
};
