import React from 'react';
import type { StudySession } from '../types';

interface RecentSessionsProps {
  sessions: StudySession[];
}

export const RecentSessions: React.FC<RecentSessionsProps> = ({ sessions }) => {
  if (!sessions || sessions.length === 0) {
    return null;
  }

  return (
    <div>
      <div className="section-title">
        <span>Recent Study History</span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Last {sessions.length} recorded sessions
        </span>
      </div>

      <div className="sessions-table-wrapper">
        <table className="sessions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Challenge Day</th>
              <th>Solved</th>
              <th>Duration</th>
              <th>Notes</th>
              <th>GitHub Synced</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{s.date}</td>
                <td style={{ fontWeight: 600, color: 'var(--primary-light)' }}>
                  Day {s.challenge_day > 100 ? 1 : s.challenge_day}
                </td>
                <td style={{ color: 'var(--success-light)', fontWeight: 600 }}>
                  {s.questions_solved}
                </td>
                <td>{s.duration_minutes ? `${s.duration_minutes}m` : '—'}</td>
                <td style={{ color: 'var(--text-muted)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {s.notes || '—'}
                </td>
                <td>
                  {s.github_updated ? (
                    <span style={{ color: 'var(--success-light)', fontSize: '0.82rem' }}>
                      ✅ Synced {s.github_commit_sha ? `(${s.github_commit_sha.slice(0, 7)})` : ''}
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-subtle)', fontSize: '0.82rem' }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
