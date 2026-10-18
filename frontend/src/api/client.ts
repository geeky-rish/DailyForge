// Backend API client — never puts secrets in localStorage or frontend code

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include', // send HTTP-only cookies
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (res.status === 401) throw new ApiError(401, 'Not authenticated');
  if (res.status === 403) throw new ApiError(403, 'Not authorized');
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }
  if (res.status === 204) return {} as T;
  return res.json() as Promise<T>;
}

// ─── Health ─────────────────────────────────────────────────────────────────

export const health = () => request<{ status: string }>('/health');
export const ready = () => request<{ status: string; database: string }>('/ready');

// ─── Auth ────────────────────────────────────────────────────────────────────

export const startGithubAuth = () =>
  request<{ auth_url: string; state: string }>('/auth/github/start', { method: 'POST' });

export const logout = () => request<{ status: string }>('/auth/logout', { method: 'POST' });

// ─── User ────────────────────────────────────────────────────────────────────

export const getMe = () =>
  request<{ github_id: number; username: string; name?: string; avatar_url?: string }>('/api/me');

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const getDashboard = () => request<import('./types').DashboardData>('/api/dashboard');

// ─── Problem mutations ───────────────────────────────────────────────────────

export const markAttempted = (problemId: number) =>
  request<{ status: string; attempts: number }>(`/api/problems/${problemId}/attempted`, { method: 'POST' });

export const markSolved = (problemId: number, isExtra = false) =>
  request<{ status: string; solved_at: string }>(`/api/problems/${problemId}/solved`, {
    method: 'POST',
    body: JSON.stringify({ problem_db_id: problemId, is_extra: isExtra }),
  });

export const markDeferred = (problemId: number) =>
  request<{ status: string }>(`/api/problems/${problemId}/deferred`, { method: 'POST' });

export const markNeedsRevision = (problemId: number) =>
  request<{ status: string }>(`/api/problems/${problemId}/needs-revision`, { method: 'POST' });

// ─── Study sessions ──────────────────────────────────────────────────────────

export const createStudySession = (data: {
  questions_solved: number;
  duration_minutes?: number;
  notes?: string;
}) => request<import('./types').StudySession>('/api/study-sessions', { method: 'POST', body: JSON.stringify(data) });

export const getStudySessions = (limit = 14) =>
  request<import('./types').StudySession[]>(`/api/study-sessions?limit=${limit}`);

// ─── GitHub README ───────────────────────────────────────────────────────────

export const updateGithubReadme = (sessionId: number, dryRun = false) =>
  request<{ status: string; commit_sha?: string; diff_preview?: string; dry_run: boolean }>(
    '/api/github/profile-readme',
    { method: 'POST', body: JSON.stringify({ session_id: sessionId, dry_run: dryRun }) }
  );

export { ApiError };
