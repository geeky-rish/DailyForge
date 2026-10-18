// Backend API client — supports both HTTP-only cookies and Bearer tokens for cross-origin hosting
import type {
  DashboardData,
  HealthResponse,
  ProblemStatus,
  ReadyResponse,
  StudySession,
  User,
} from '../types';

// Read API base URL from Vite environment variables (supports VITE_API_BASE_URL and VITE_API_URL)
export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://dailyforge-backend-kwti.onrender.com' : 'http://localhost:8000')
).replace(/\/$/, '');

const TOKEN_STORAGE_KEY = 'dailyforge_auth_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY) || sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
      sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore storage errors in restricted iframe environments
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${path}`;

  let res: Response;
  try {
    res = await fetch(url, {
      credentials: 'include', // Send HTTP-only session cookie
      ...options,
      headers,
    });
  } catch (netErr: any) {
    throw new ApiError(0, `Network error: Backend unreachable at ${API_BASE}. (${netErr?.message || 'offline'})`);
  }

  if (res.status === 401) {
    setStoredToken(null);
    throw new ApiError(401, 'Not authenticated');
  }
  if (res.status === 403) throw new ApiError(403, 'Not authorized');
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }
  if (res.status === 204) return {} as T;
  return res.json() as Promise<T>;
}

// ─── Health & Cold-Start Wake-up ──────────────────────────────────────────────

export const checkHealth = () => request<HealthResponse>('/health');
export const checkReady = () => request<ReadyResponse>('/ready');

/**
 * Wake up a sleeping Render backend service with retry backoff.
 */
export async function wakeBackend(
  onProgress?: (attempt: number, elapsedSeconds: number) => void
): Promise<{ success: boolean; attempts: number; elapsedSeconds: number; error?: string }> {
  const startTime = Date.now();
  let attempt = 0;
  const maxAttempts = 30; // 30 attempts * 3s ~ 90 seconds max wait for Render free tier

  while (attempt < maxAttempts) {
    attempt++;
    const elapsedSeconds = Math.round((Date.now() - startTime) / 1000);
    if (onProgress) onProgress(attempt, elapsedSeconds);

    try {
      const h = await checkHealth();
      if (h.status === 'ok') {
        // Also verify ready
        try {
          await checkReady();
        } catch {
          // Ready may take a moment for database connection
        }
        return { success: true, attempts: attempt, elapsedSeconds };
      }
    } catch {
      // Still waking up
    }

    // Wait 3 seconds before next retry
    await new Promise((r) => setTimeout(r, 3000));
  }

  return {
    success: false,
    attempts: attempt,
    elapsedSeconds: Math.round((Date.now() - startTime) / 1000),
    error: `Backend did not respond after ${attempt} attempts.`,
  };
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const startGithubAuth = () =>
  request<{ auth_url: string; state: string }>('/auth/github/start', { method: 'POST' });

export const logout = async () => {
  setStoredToken(null);
  try {
    return await request<{ status: string }>('/auth/logout', { method: 'POST' });
  } catch {
    return { status: 'logged_out' };
  }
};

// ─── User ────────────────────────────────────────────────────────────────────

export const getMe = () => request<User>('/api/me');

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const getDashboard = () => request<DashboardData>('/api/dashboard');

// ─── Problem Mutations ───────────────────────────────────────────────────────

export const markAttempted = (problemId: number) =>
  request<{ status: ProblemStatus; attempts: number }>(`/api/problems/${problemId}/attempted`, {
    method: 'POST',
  });

export const markSolved = (problemId: number, isExtra = false) =>
  request<{ status: ProblemStatus; solved_at: string }>(`/api/problems/${problemId}/solved`, {
    method: 'POST',
    body: JSON.stringify({ problem_db_id: problemId, is_extra: isExtra }),
  });

export const markDeferred = (problemId: number) =>
  request<{ status: ProblemStatus }>(`/api/problems/${problemId}/deferred`, { method: 'POST' });

export const markNeedsRevision = (problemId: number) =>
  request<{ status: ProblemStatus }>(`/api/problems/${problemId}/needs-revision`, { method: 'POST' });

// ─── Study Sessions ──────────────────────────────────────────────────────────

export const createStudySession = (data: {
  questions_solved: number;
  duration_minutes?: number;
  notes?: string;
}) => request<StudySession>('/api/study-sessions', { method: 'POST', body: JSON.stringify(data) });

export const getStudySessions = (limit = 14) =>
  request<StudySession[]>(`/api/study-sessions?limit=${limit}`);

// ─── GitHub README Sync ──────────────────────────────────────────────────────

export const updateGithubReadme = (sessionId?: number, dryRun = false) =>
  request<{ status: string; commit_sha?: string; diff_preview?: string; dry_run: boolean }>(
    '/api/github/profile-readme',
    { method: 'POST', body: JSON.stringify({ session_id: sessionId || undefined, dry_run: dryRun }) }
  );
