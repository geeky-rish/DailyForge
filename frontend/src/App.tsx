import React, { useEffect, useState, useCallback } from 'react';
import type { BackendStatus, DashboardData, StudySession, User } from './types';
import {
  checkHealth,
  createStudySession,
  getDashboard,
  getMe,
  getStudySessions,
  logout,
  markAttempted,
  markDeferred,
  markNeedsRevision,
  markSolved,
  setStoredToken,
  startGithubAuth,
  updateGithubReadme,
  wakeBackend,
} from './api/client';
import { Header } from './components/Header';
import { BackendBanner } from './components/BackendBanner';
import { QuoteCard } from './components/QuoteCard';
import { StatsGrid } from './components/StatsGrid';
import { DailyQuestions } from './components/DailyQuestions';
import { StudySessionSync } from './components/StudySessionSync';
import { RecentSessions } from './components/RecentSessions';
import './styles/main.css';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('idle');
  const [wakeSeconds, setWakeSeconds] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  // Load user data and dashboard
  const refreshData = useCallback(async () => {
    try {
      const currentUser = await getMe();
      setUser(currentUser);
      const data = await getDashboard();
      setDashboard(data);
      const recent = await getStudySessions(10);
      setSessions(recent);
    } catch (err: any) {
      if (err?.status === 401) {
        setUser(null);
      } else {
        console.error('Failed to load dashboard:', err);
      }
    }
  }, []);

  // Check health and activate backend if needed
  const activateBackend = useCallback(async () => {
    setBackendStatus('waking');
    setErrorMessage('');
    const res = await wakeBackend((_attempt, seconds) => {
      setWakeSeconds(seconds);
    });

    if (res.success) {
      setBackendStatus('ready');
      await refreshData();
    } else {
      setBackendStatus('error');
      setErrorMessage(res.error || 'Failed to wake backend. Please check hosting status.');
    }
  }, [refreshData]);

  // Initial load
  useEffect(() => {
    const init = async () => {
      // 1. Check URL parameters for OAuth redirect
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');
      const err = urlParams.get('auth_error');

      if (token) {
        setStoredToken(token);
        // Clean URL to avoid leaking token in browser history
        urlParams.delete('token');
        urlParams.delete('auth');
        const cleanQuery = urlParams.toString() ? `?${urlParams.toString()}` : '';
        window.history.replaceState({}, document.title, window.location.pathname + cleanQuery + window.location.hash);
      }

      if (err) {
        setAuthError(err === 'unauthorized' ? 'Access restricted to authorized account (geeky-rish).' : `Authentication error: ${err}`);
      }

      // 2. Probe backend health
      try {
        const h = await checkHealth();
        if (h.status === 'ok') {
          setBackendStatus('ready');
          await refreshData();
        } else {
          setBackendStatus('idle');
        }
      } catch {
        setBackendStatus('idle');
      } finally {
        setIsInitializing(false);
      }
    };

    init();
  }, [refreshData]);

  const handleLogin = async () => {
    try {
      if (backendStatus !== 'ready') {
        await activateBackend();
      }
      const { auth_url } = await startGithubAuth();
      window.location.href = auth_url;
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to start GitHub login');
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
    setDashboard(null);
  };

  const handleMarkAttempted = async (problemId: number) => {
    await markAttempted(problemId);
    await refreshData();
  };

  const handleMarkSolved = async (problemId: number, isExtra = false) => {
    await markSolved(problemId, isExtra);
    await refreshData();
  };

  const handleMarkDeferred = async (problemId: number) => {
    await markDeferred(problemId);
    await refreshData();
  };

  const handleMarkNeedsRevision = async (problemId: number) => {
    await markNeedsRevision(problemId);
    await refreshData();
  };

  const handleRecordAndSync = async (data: {
    questions_solved: number;
    duration_minutes?: number;
    notes?: string;
  }) => {
    const sessionRes = await createStudySession(data);
    let commitSha: string | undefined;
    let diffPreview: string | undefined;
    let error: string | undefined;

    const sessionId = sessionRes.session_id || sessionRes.id;
    if (sessionId) {
      try {
        const readmeRes = await updateGithubReadme(sessionId, false);
        commitSha = readmeRes.commit_sha;
        diffPreview = readmeRes.diff_preview;
      } catch (readmeErr: any) {
        console.warn('GitHub README sync failed:', readmeErr);
        error = `Session saved, but GitHub sync failed: ${readmeErr?.message || 'Check GITHUB_WRITE_TOKEN'}`;
      }
    }

    await refreshData();
    return { commit_sha: commitSha, diff_preview: diffPreview, error };
  };

  return (
    <div className="app-container">
      <Header
        user={user}
        challengeDay={dashboard?.challenge_day || 1}
        streak={dashboard?.streak?.current_streak || 0}
        backendStatus={backendStatus}
        wakeSeconds={wakeSeconds}
        onActivateBackend={activateBackend}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />

      {authError && (
        <div className="wake-banner" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: 'rgba(239, 68, 68, 0.4)', color: 'var(--danger-light)' }}>
          <span>⚠️ {authError}</span>
          <button className="btn btn-outline btn-sm" onClick={() => setAuthError(null)}>Dismiss</button>
        </div>
      )}

      <BackendBanner
        status={backendStatus}
        wakeSeconds={wakeSeconds}
        errorMessage={errorMessage}
        onActivate={activateBackend}
      />

      <QuoteCard quote={dashboard?.quote || null} />

      <StatsGrid
        stats={dashboard?.stats || null}
        streak={dashboard?.streak || null}
      />

      <DailyQuestions
        assignment={dashboard?.assignment || null}
        onMarkAttempted={handleMarkAttempted}
        onMarkSolved={handleMarkSolved}
        onMarkDeferred={handleMarkDeferred}
        onMarkNeedsRevision={handleMarkNeedsRevision}
      />

      {user && (
        <StudySessionSync
          defaultSolvedCount={dashboard?.assignment?.solved_count || 2}
          onRecordAndSync={handleRecordAndSync}
        />
      )}

      <RecentSessions sessions={sessions} />

      {!user && !isInitializing && (
        <div className="question-card" style={{ textAlign: 'center', padding: '40px 20px', marginTop: '32px' }}>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', marginBottom: '8px' }}>
            Ready to Forge Your Consistency?
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '20px', maxWidth: '500px', margin: '0 auto 20px auto' }}>
            Sign in with your authorized GitHub account (geeky-rish) to track your daily progress, streaks, and sync to your GitHub Profile README.
          </p>
          <button className="btn btn-primary" onClick={handleLogin}>
            Sign in with GitHub
          </button>
        </div>
      )}
    </div>
  );
};
