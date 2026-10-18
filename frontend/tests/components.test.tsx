import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../src/components/Header';
import { QuoteCard } from '../src/components/QuoteCard';
import { StatsGrid } from '../src/components/StatsGrid';
import { DailyQuestions } from '../src/components/DailyQuestions';
import { LoginView } from '../src/components/LoginView';
import type { DailyAssignment, ProgressStats, Quote, StreakInfo } from '../src/types';

describe('Frontend Component Suite', () => {
  it('renders Header with brand title and streak info', () => {
    render(
      <Header
        user={{
          github_id: 1,
          username: 'geeky-rish',
        }}
        challengeDay={5}
        streak={3}
        backendStatus="ready"
        wakeSeconds={0}
        onActivateBackend={vi.fn()}
        onLogin={vi.fn()}
        onLogout={vi.fn()}
      />
    );

    expect(screen.getByText('DailyForge')).toBeInTheDocument();
    expect(screen.getByText('Day 5 of 100')).toBeInTheDocument();
    expect(screen.getByText('🔥 3 Days')).toBeInTheDocument();
    expect(screen.getByText('🟢 Backend Ready')).toBeInTheDocument();
  });

  it('renders QuoteCard properly', () => {
    const mockQuote: Quote = {
      day: 5,
      text: 'Consistency is what transforms average into excellence.',
      author: 'DailyForge Coach',
    };

    render(<QuoteCard quote={mockQuote} />);
    expect(screen.getByText(/Consistency is what transforms average/i)).toBeInTheDocument();
    expect(screen.getByText(/DailyForge Coach/i)).toBeInTheDocument();
  });

  it('renders StatsGrid with accurate calculations', () => {
    const mockStats: ProgressStats = {
      total: 180,
      solved: 25,
      attempted_not_solved: 5,
      deferred: 2,
      needs_revision: 3,
      remaining: 155,
      extra_questions_solved: 0,
      completion_pct: 13.88,
      is_complete: false,
    };

    const mockStreak: StreakInfo = {
      current_streak: 7,
      longest_streak: 12,
      recent_sessions: [],
    };

    render(<StatsGrid stats={mockStats} streak={mockStreak} />);
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('155')).toBeInTheDocument();
    expect(screen.getByText('🔥 7')).toBeInTheDocument();
    expect(screen.getByText('🏆 12')).toBeInTheDocument();
    expect(screen.getByText('13.9% Completed')).toBeInTheDocument();
  });

  it('renders DailyQuestions with assigned problem list and actions', () => {
    const mockAssignment: DailyAssignment = {
      id: 1,
      date: '2024-01-05',
      is_complete: false,
      total_assigned: 2,
      solved_count: 1,
      problems: [
        {
          id: 101,
          problem_id: 'SDE001',
          sheet_order: 1,
          title: 'Set Matrix Zeros',
          topic: 'Arrays',
          subtopic: 'Matrix',
          difficulty: 'Medium',
          url: 'https://leetcode.com/problems/set-matrix-zeroes/',
          status: 'solved',
          attempts: 2,
          is_extra: false,
        },
        {
          id: 102,
          problem_id: 'SDE002',
          sheet_order: 2,
          title: "Pascal's Triangle",
          topic: 'Arrays',
          subtopic: 'Matrix',
          difficulty: 'Easy',
          url: 'https://leetcode.com/problems/pascals-triangle/',
          status: 'unsolved',
          attempts: 0,
          is_extra: false,
        },
      ],
    };

    render(
      <DailyQuestions
        assignment={mockAssignment}
        onMarkAttempted={vi.fn()}
        onMarkSolved={vi.fn()}
        onMarkDeferred={vi.fn()}
        onMarkNeedsRevision={vi.fn()}
      />
    );
    expect(screen.getByText('Set Matrix Zeros')).toBeInTheDocument();
    expect(screen.getByText("Pascal's Triangle")).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Easy')).toBeInTheDocument();
  });

  it('renders LoginView when user is unauthenticated', () => {
    render(
      <LoginView
        backendStatus="idle"
        wakeSeconds={0}
        onLogin={vi.fn()}
        onWakeBackend={vi.fn()}
      />
    );

    expect(screen.getByText('DailyForge')).toBeInTheDocument();
    expect(screen.getByText(/Sign in with GitHub/i)).toBeInTheDocument();
    expect(screen.getByText(/Wake Backend/i)).toBeInTheDocument();
  });
});
