import React, { useState } from 'react';
import type { DailyAssignment, Problem } from '../types';

interface DailyQuestionsProps {
  assignment: DailyAssignment | null;
  onMarkAttempted: (problemId: number) => Promise<void>;
  onMarkSolved: (problemId: number, isExtra?: boolean) => Promise<void>;
  onMarkDeferred: (problemId: number) => Promise<void>;
  onMarkNeedsRevision: (problemId: number) => Promise<void>;
}

export const DailyQuestions: React.FC<DailyQuestionsProps> = ({
  assignment,
  onMarkAttempted,
  onMarkSolved,
  onMarkDeferred,
  onMarkNeedsRevision,
}) => {
  const [loadingId, setLoadingId] = useState<number | null>(null);

  if (!assignment || !assignment.problems || assignment.problems.length === 0) {
    return (
      <div className="question-card" style={{ textAlign: 'center', padding: '36px 20px' }}>
        <p style={{ color: 'var(--text-muted)' }}>
          No questions assigned for today yet. Make sure you are signed in and the backend is active.
        </p>
      </div>
    );
  }

  const handleAction = async (problemId: number, action: () => Promise<void>) => {
    try {
      setLoadingId(problemId);
      await action();
    } finally {
      setLoadingId(null);
    }
  };

  const getDifficultyClass = (difficulty?: string) => {
    const diff = (difficulty || '').toLowerCase();
    if (diff === 'easy') return 'tag-easy';
    if (diff === 'medium') return 'tag-medium';
    if (diff === 'hard') return 'tag-hard';
    return '';
  };

  return (
    <div>
      <div className="section-title">
        <span>Today&apos;s Striver SDE 180 Assignments</span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500 }}>
          {assignment.solved_count} / {assignment.total_assigned} Solved Today
        </span>
      </div>

      <div className="questions-list">
        {assignment.problems.map((problem: Problem, idx: number) => {
          const isSolved = problem.status === 'solved';
          const isAttempted = problem.status === 'attempted';
          const isRevision = problem.status === 'needs_revision';
          const isDeferred = problem.status === 'deferred';
          const isLoading = loadingId === problem.id;

          return (
            <div
              key={problem.id}
              className={`question-card ${isSolved ? 'solved' : ''}`}
            >
              <div className="question-top">
                <a
                  href={problem.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="question-title"
                  title="Open problem in new tab"
                >
                  <span style={{ color: 'var(--primary-light)', fontFamily: 'var(--font-mono)' }}>
                    Q{idx + 1}.
                  </span>
                  {problem.title}
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>↗</span>
                </a>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {problem.difficulty && (
                    <span className={`tag ${getDifficultyClass(problem.difficulty)}`}>
                      {problem.difficulty}
                    </span>
                  )}
                  {problem.status && problem.status !== 'unsolved' && (
                    <span
                      className="tag"
                      style={{
                        background: isSolved
                          ? 'var(--success-bg)'
                          : isAttempted
                          ? 'var(--warning-bg)'
                          : 'rgba(255, 255, 255, 0.08)',
                        color: isSolved
                          ? 'var(--success-light)'
                          : isAttempted
                          ? 'var(--warning-light)'
                          : 'var(--text-muted)',
                      }}
                    >
                      {problem.status.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>

              <div className="question-meta">
                <span className="tag">📂 {problem.topic}</span>
                {problem.subtopic && <span className="tag">🏷️ {problem.subtopic}</span>}
                {problem.attempts > 0 && (
                  <span className="tag">🔄 {problem.attempts} {problem.attempts === 1 ? 'attempt' : 'attempts'}</span>
                )}
                {isSolved && problem.solved_at && (
                  <span className="tag" style={{ color: 'var(--success-light)' }}>
                    ✅ Solved {new Date(problem.solved_at).toLocaleDateString()}
                  </span>
                )}
              </div>

              <div className="question-actions">
                <button
                  className={`btn btn-sm btn-action ${isSolved ? 'active-solved' : 'btn-outline'}`}
                  disabled={isLoading}
                  onClick={() => handleAction(problem.id, () => onMarkSolved(problem.id, false))}
                >
                  {isSolved ? '✅ Solved' : 'Mark Solved'}
                </button>

                <button
                  className={`btn btn-sm btn-action ${isAttempted ? 'active-attempted' : 'btn-outline'}`}
                  disabled={isLoading || isSolved}
                  onClick={() => handleAction(problem.id, () => onMarkAttempted(problem.id))}
                >
                  Attempted
                </button>

                <button
                  className={`btn btn-sm btn-action ${isRevision ? 'active-revision' : 'btn-outline'}`}
                  disabled={isLoading}
                  onClick={() => handleAction(problem.id, () => onMarkNeedsRevision(problem.id))}
                >
                  🔖 Need Revision
                </button>

                <button
                  className={`btn btn-sm btn-action ${isDeferred ? 'btn-outline' : 'btn-outline'}`}
                  disabled={isLoading || isSolved}
                  onClick={() => handleAction(problem.id, () => onMarkDeferred(problem.id))}
                >
                  ⏳ Defer
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
