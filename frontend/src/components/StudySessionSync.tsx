import React, { useState } from 'react';
import type { Quote } from '../types';

interface StudySessionSyncProps {
  quote?: Quote | null;
  onCommitToGithub: () => Promise<{ commit_sha?: string; error?: string }>;
}

export const StudySessionSync: React.FC<StudySessionSyncProps> = ({
  quote,
  onCommitToGithub,
}) => {
  const [isCommitting, setIsCommitting] = useState<boolean>(false);
  const [result, setResult] = useState<{
    success: boolean;
    commit_sha?: string;
    message?: string;
  } | null>(null);

  const handleCommit = async () => {
    setIsCommitting(true);
    setResult(null);

    try {
      const res = await onCommitToGithub();
      if (res.error) {
        setResult({ success: false, message: res.error });
      } else {
        setResult({
          success: true,
          commit_sha: res.commit_sha,
          message: res.commit_sha
            ? `Successfully committed new quote to geeky-rish/geeky-rish (commit ${res.commit_sha.slice(0, 7)})`
            : 'Quote committed and consistency streak recorded!',
        });
      }
    } catch (err: any) {
      setResult({ success: false, message: err?.message || 'Failed to commit quote to GitHub' });
    } finally {
      setIsCommitting(false);
    }
  };

  return (
    <div className="sync-section">
      <div className="section-title" style={{ marginBottom: '10px' }}>
        <span>Sync Random Dev Quote to GitHub</span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Updates geeky-rish/geeky-rish README
        </span>
      </div>

      <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.5 }}>
        Sync a fresh dev quote directly to the <strong>Random Dev Quote</strong> section of your GitHub profile README with a single click.
      </p>

      {quote && (
        <div style={{
          padding: '14px 18px',
          background: 'var(--bg-card-subtle)',
          border: '1px solid var(--border-card)',
          borderRadius: '10px',
          marginBottom: '18px',
          fontStyle: 'italic',
          color: 'var(--text-secondary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <div>
            &ldquo;{quote.text}&rdquo; <span style={{ fontStyle: 'normal', color: 'var(--accent)', fontWeight: 600 }}>&mdash; {quote.author}</span>
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'normal' }}>
            Random Dev Quote
          </span>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        <button
          type="button"
          className="btn btn-primary"
          style={{ padding: '12px 24px', fontSize: '0.98rem', fontWeight: 600, borderRadius: '10px' }}
          onClick={handleCommit}
          disabled={isCommitting}
        >
          {isCommitting ? (
            <>
              <div className="wake-spinner" style={{ width: '16px', height: '16px' }} />
              <span>Committing to GitHub...</span>
            </>
          ) : (
            <>
              <span>🐙 Commit to GitHub</span>
            </>
          )}
        </button>
      </div>

      {result && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '0.88rem',
            background: result.success ? 'var(--success-bg)' : 'var(--danger-bg)',
            border: `1px solid ${result.success ? 'var(--success-border)' : 'rgba(239, 68, 68, 0.3)'}`,
            color: result.success ? 'var(--success-light)' : 'var(--danger-light)',
          }}
        >
          {result.success ? '✅ ' : '⚠️ '}
          {result.message}
        </div>
      )}
    </div>
  );
};
