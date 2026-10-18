import React from 'react';
import type { BackendStatus } from '../types';

interface BackendBannerProps {
  status: BackendStatus;
  wakeSeconds: number;
  errorMessage?: string;
  onActivate: () => void;
}

export const BackendBanner: React.FC<BackendBannerProps> = ({
  status,
  wakeSeconds,
  errorMessage,
  onActivate,
}) => {
  if (status === 'ready') return null;

  return (
    <div className="wake-banner">
      <div className="wake-info">
        {status === 'waking' ? (
          <div className="wake-spinner" />
        ) : (
          <span style={{ fontSize: '1.4rem' }}>⚡</span>
        )}
        <div>
          <strong style={{ display: 'block', fontSize: '0.95rem' }}>
            {status === 'waking'
              ? `Waking up Render backend (${wakeSeconds}s)...`
              : 'Backend service may be sleeping'}
          </strong>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            {status === 'waking'
              ? 'Render free instances spin down after inactivity. Waking takes ~30-50s on first load.'
              : errorMessage || 'Render free instances sleep after inactivity. Click Activate to spin up the container.'}
          </span>
        </div>
      </div>

      {status !== 'waking' && (
        <button className="btn btn-primary btn-sm" onClick={onActivate}>
          Activate Backend Now
        </button>
      )}
    </div>
  );
};
