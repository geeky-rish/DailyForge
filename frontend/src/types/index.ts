// DailyForge TypeScript type definitions

export type ProblemStatus = 'unsolved' | 'attempted' | 'solved' | 'deferred' | 'needs_revision';
export type BackendStatus = 'idle' | 'waking' | 'ready' | 'error' | 'timeout';

export interface Problem {
  id: number;
  problem_id: string;
  sheet_order: number;
  title: string;
  topic: string;
  subtopic?: string;
  difficulty?: string;
  url?: string;
  notes?: string;
  status: ProblemStatus;
  attempts: number;
  solved_at?: string;
  is_extra: boolean;
}

export interface DailyAssignment {
  id: number;
  date: string;
  is_complete: boolean;
  problems: Problem[];
  total_assigned: number;
  solved_count: number;
}

export interface ProgressStats {
  total: number;
  solved: number;
  attempted_not_solved: number;
  deferred: number;
  needs_revision: number;
  remaining: number;
  extra_questions_solved: number;
  completion_pct: number;
  is_complete: boolean;
}

export interface StudySession {
  id?: number;
  session_id?: number;
  date?: string;
  session_date?: string;
  challenge_day: number;
  questions_solved: number;
  duration_minutes?: number;
  notes?: string;
  github_updated?: boolean;
  github_commit_sha?: string;
}

export interface StreakInfo {
  current_streak: number;
  longest_streak: number;
  last_session_date?: string;
  recent_sessions: Array<{
    date: string;
    challenge_day: number;
    questions_solved: number;
    github_updated: boolean;
  }>;
}

export interface Quote {
  day: number;
  text: string;
  author: string;
}

export interface DashboardData {
  today: string;
  challenge_day: number;
  assignment: DailyAssignment;
  stats: ProgressStats;
  streak: StreakInfo;
  quote: Quote;
}

export interface User {
  github_id: number;
  username: string;
  name?: string;
  avatar_url?: string;
}

export interface HealthResponse {
  status: string;
  service?: string;
}

export interface ReadyResponse {
  status: string;
  database: string;
}
