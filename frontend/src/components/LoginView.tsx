import React from 'react';
import type { BackendStatus } from '../types';

interface LoginViewProps {
  backendStatus: BackendStatus;
  wakeSeconds: number;
  errorMessage?: string;
  onLogin: () => void;
  onWakeBackend: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({
  backendStatus,
  wakeSeconds,
  errorMessage,
  onLogin,
  onWakeBackend,
}) => {
  const isWaking = backendStatus === 'waking';

  return (
    <div style={{ maxWidth: '520px', margin: '60px auto 0 auto' }}>
      <div className="question-card" style={{ textAlign: 'center', padding: '48px 36px' }}>
        <div style={{ fontSize: '3.5rem', marginBottom: '16px', lineHeight: 1 }}>⚔️</div>
        
        <h2 style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '2rem',
          fontWeight: 800,
          marginBottom: '8px',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.5px'
        }}>
          DailyForge
        </h2>
        
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '28px' }}>
          Striver SDE 180 Consistency Suite.<br />
          Please sign in with your GitHub account to continue.
        </p>

        {errorMessage && (
          <div style={{
            marginBottom: '20px',
            padding: '12px 14px',
            borderRadius: '8px',
            background: 'var(--danger-bg)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--danger-light)',
            fontSize: '0.86rem'
          }}>
            ⚠️ {errorMessage}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
          <button
            className="btn btn-primary"
            style={{
              fontSize: '1.05rem',
              padding: '14px 28px',
              width: '100%',
              borderRadius: '12px',
              fontWeight: 700
            }}
            onClick={onLogin}
            disabled={isWaking}
          >
            {isWaking ? (
              <>
                <div className="wake-spinner" style={{ width: '18px', height: '18px' }} />
                <span>Waking Backend ({wakeSeconds}s)...</span>
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
                </svg>
                <span>Sign in with GitHub</span>
              </>
            )}
          </button>

          {backendStatus === 'ready' ? (
            <span style={{ fontSize: '0.82rem', color: 'var(--success-light)', fontWeight: 500 }}>
              🟢 Backend Ready
            </span>
          ) : (
            <button
              className="btn btn-outline btn-sm"
              style={{ fontSize: '0.8rem', width: '100%' }}
              onClick={onWakeBackend}
              disabled={isWaking}
            >
              {isWaking ? `Waking Render container (${wakeSeconds}s)...` : '⚡ Wake Backend'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
