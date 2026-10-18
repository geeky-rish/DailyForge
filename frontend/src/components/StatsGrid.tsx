import React from 'react';
import type { ProgressStats, StreakInfo } from '../types';

interface StatsGridProps {
  stats: ProgressStats | null;
  streak: StreakInfo | null;
}

export const StatsGrid: React.FC<StatsGridProps> = ({ stats, streak }) => {
  const solved = stats?.solved ?? 0;
  const remaining = stats?.remaining ?? 180;
  const completionPct = stats?.completion_pct ?? 0;
  const currentStreak = streak?.current_streak ?? 0;
  const longestStreak = streak?.longest_streak ?? 0;

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Problems Solved</div>
          <div className="stat-value" style={{ color: 'var(--success-light)' }}>
            {solved}
            <span style={{ fontSize: '1rem', color: 'var(--text-subtle)' }}> / 180</span>
          </div>
          <div className="stat-subtext">
            {stats?.extra_questions_solved ? `+${stats.extra_questions_solved} extra solved` : 'Striver SDE 180'}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Remaining</div>
          <div className="stat-value" style={{ color: 'var(--warning-light)' }}>
            {remaining}
          </div>
          <div className="stat-subtext">Problems left to complete</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Current Streak</div>
          <div className="stat-value" style={{ color: '#FB923C' }}>
            🔥 {currentStreak}
          </div>
          <div className="stat-subtext">Consecutive active days</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Longest Streak</div>
          <div className="stat-value" style={{ color: '#EAB308' }}>
            🏆 {longestStreak}
          </div>
          <div className="stat-subtext">Personal best consistency</div>
        </div>
      </div>

      <div className="progress-container">
        <div className="progress-header">
          <span style={{ fontWeight: 600 }}>Challenge Progress</span>
          <span style={{ color: 'var(--primary-light)', fontWeight: 700 }}>
            {completionPct.toFixed(1)}% Completed
          </span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${Math.min(100, Math.max(0, completionPct))}%` }}
          />
        </div>
      </div>
    </div>
  );
};
