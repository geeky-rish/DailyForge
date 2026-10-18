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
    <div style={{ maxWidth: '800px', margin: '40px auto 0 auto' }}>
      <div className="question-card" style={{ textAlign: 'center', padding: '48px 32px' }}>
        <div style={{ fontSize: '3.5rem', marginBottom: '16px', lineHeight: 1 }}>⚔️</div>
        
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '2.2rem', fontWeight: 800, marginBottom: '12px', background: 'linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Forge Your Consistency
        </h2>
        
        <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', lineHeight: 1.6, maxWidth: '600px', margin: '0 auto 28px auto' }}>
          Your dedicated productivity suite for conquering the <strong>Striver SDE 180 DSA Challenge</strong>. Track two questions daily, build unstoppable streaks, and automatically showcase your progress on your GitHub Profile.
        </p>

        {errorMessage && (
          <div style={{ marginBottom: '20px', padding: '12px 16px', borderRadius: '8px', background: 'var(--danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--danger-light)', fontSize: '0.88rem' }}>
            ⚠️ {errorMessage}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px', marginBottom: '36px' }}>
          <button
            className="btn btn-primary"
            style={{ fontSize: '1.1rem', padding: '14px 32px', minWidth: '260px', borderRadius: '12px' }}
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
              🟢 Backend is active and connected
            </span>
          ) : (
            <button
              className="btn btn-outline btn-sm"
              style={{ fontSize: '0.8rem' }}
              onClick={onWakeBackend}
              disabled={isWaking}
            >
              {isWaking ? `Waking Render container (${wakeSeconds}s)...` : '⚡ Wake Backend Preemptively'}
            </button>
          )}
        </div>

        <div style={{ borderTop: '1px solid var(--border-card)', paddingTop: '28px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px', textAlign: 'left' }}>
            <div style={{ padding: '12px', background: 'var(--bg-card-subtle)', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>📋</div>
              <strong style={{ fontSize: '0.88rem', color: '#FFFFFF', display: 'block' }}>2 Questions Daily</strong>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Curated Striver SDE 180 sheet progression</span>
            </div>

            <div style={{ padding: '12px', background: 'var(--bg-card-subtle)', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>🔥</div>
              <strong style={{ fontSize: '0.88rem', color: '#FFFFFF', display: 'block' }}>Streak Tracking</strong>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Freeze &amp; gap protected consistency engine</span>
            </div>

            <div style={{ padding: '12px', background: 'var(--bg-card-subtle)', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>📧</div>
              <strong style={{ fontSize: '0.88rem', color: '#FFFFFF', display: 'block' }}>7:00 AM Briefing</strong>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Automated morning email via Gmail SMTP</span>
            </div>

            <div style={{ padding: '12px', background: 'var(--bg-card-subtle)', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>🐙</div>
              <strong style={{ fontSize: '0.88rem', color: '#FFFFFF', display: 'block' }}>GitHub Profile Sync</strong>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Auto-updates geeky-rish/geeky-rish README</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
