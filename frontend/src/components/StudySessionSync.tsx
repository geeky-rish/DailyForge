import React, { useState } from 'react';

interface StudySessionSyncProps {
  defaultSolvedCount: number;
  onRecordAndSync: (data: {
    questions_solved: number;
    duration_minutes?: number;
    notes?: string;
  }) => Promise<{ commit_sha?: string; diff_preview?: string; error?: string }>;
}

export const StudySessionSync: React.FC<StudySessionSyncProps> = ({
  defaultSolvedCount,
  onRecordAndSync,
}) => {
  const [questionsSolved, setQuestionsSolved] = useState<number>(defaultSolvedCount || 2);
  const [durationMinutes, setDurationMinutes] = useState<number>(60);
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [syncResult, setSyncResult] = useState<{
    success: boolean;
    commit_sha?: string;
    message?: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSyncResult(null);

    try {
      const res = await onRecordAndSync({
        questions_solved: Number(questionsSolved),
        duration_minutes: Number(durationMinutes),
        notes: notes.trim() || undefined,
      });

      if (res.error) {
        setSyncResult({ success: false, message: res.error });
      } else {
        setSyncResult({
          success: true,
          commit_sha: res.commit_sha,
          message: res.commit_sha
            ? `Successfully committed to GitHub README (commit ${res.commit_sha.slice(0, 7)})`
            : 'Study session recorded and streak updated!',
        });
        setNotes('');
      }
    } catch (err: any) {
      setSyncResult({ success: false, message: err?.message || 'Failed to record session' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="sync-section">
      <div className="section-title" style={{ marginBottom: '12px' }}>
        <span>Record Study Session &amp; Sync GitHub Profile</span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Updates geeky-rish/geeky-rish README
        </span>
      </div>

      <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
        Record your daily preparation session to increment your consistency streak and automatically sync your live challenge statistics to your GitHub Profile README.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="sync-form">
          <div className="form-group">
            <label htmlFor="questions-solved">Questions Solved Today</label>
            <input
              id="questions-solved"
              type="number"
              min="0"
              max="50"
              className="form-control"
              value={questionsSolved}
              onChange={(e) => setQuestionsSolved(Number(e.target.value))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="duration-mins">Session Duration (Minutes)</label>
            <input
              id="duration-mins"
              type="number"
              min="5"
              max="720"
              className="form-control"
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(Number(e.target.value))}
            />
          </div>

          <div className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label htmlFor="session-notes">Session Notes / Insights (Optional)</label>
            <input
              id="session-notes"
              type="text"
              placeholder="e.g. Mastered Kadane's algorithm and two-pointer subinterval merges."
              className="form-control"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Recording & Syncing...' : '🚀 Save Session & Update GitHub Profile'}
          </button>
        </div>
      </form>

      {syncResult && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '0.88rem',
            background: syncResult.success ? 'var(--success-bg)' : 'var(--danger-bg)',
            border: `1px solid ${syncResult.success ? 'var(--success-border)' : 'rgba(239, 68, 68, 0.3)'}`,
            color: syncResult.success ? 'var(--success-light)' : 'var(--danger-light)',
          }}
        >
          {syncResult.success ? '✅ ' : '⚠️ '}
          {syncResult.message}
        </div>
      )}
    </div>
  );
};
