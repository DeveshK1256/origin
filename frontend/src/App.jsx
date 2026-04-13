import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { configureApiAuth } from "./api/client";
import { supabase, isSupabaseEnabled } from "./auth/supabaseClient";
import AuthGate from "./components/AuthGate";
import AppLayout from "./components/AppLayout";
import FakeJobDetectionPage from "./pages/FakeJobDetectionPage";
import JobAnalyzerPage from "./pages/JobAnalyzerPage";
import ResumeAIPage from "./pages/ResumeAIPage";
import ResumeScannerPage from "./pages/ResumeScannerPage";

const STORAGE_KEY = "ai_recruitment_platform_state";

const baseState = {
  resumeScore: null,
  jobMatch: null,
  scamRisk: null,
  resumeData: null,
  matchData: null,
  fakeJobData: null,
  lastUpdated: null
};

function loadStoredState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return baseState;
    return { ...baseState, ...JSON.parse(raw) };
  } catch {
    return baseState;
  }
}

export default function App() {
  const [platformState, setPlatformState] = useState(loadStoredState);
  const [session, setSession] = useState(null);
  const [authBootstrapped, setAuthBootstrapped] = useState(!isSupabaseEnabled);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(platformState));
  }, [platformState]);

  useEffect(() => {
    if (!isSupabaseEnabled || !supabase) {
      configureApiAuth(() => null);
      return undefined;
    }

    supabase.auth.getSession().then(({ data, error }) => {
      if (!error) {
        setSession(data.session || null);
      }
      setAuthBootstrapped(true);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession || null);
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    configureApiAuth(() => session?.access_token || null);
  }, [session]);

  const updatePlatformState = (partialUpdate) => {
    setPlatformState((prev) => ({
      ...prev,
      ...partialUpdate,
      lastUpdated: new Date().toISOString()
    }));
  };

  const summaryMetrics = useMemo(
    () => ({
      resumeScore: platformState.resumeScore,
      jobMatch: platformState.jobMatch,
      scamRisk: platformState.scamRisk
    }),
    [platformState.resumeScore, platformState.jobMatch, platformState.scamRisk]
  );

  const handleSignIn = async (email, password) => {
    if (!supabase) return;
    setAuthError("");
    setAuthLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setAuthError(error.message || "Sign-in failed.");
    }
    setAuthLoading(false);
  };

  const handleSignUp = async (email, password) => {
    if (!supabase) return;
    setAuthError("");
    setAuthLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) {
      setAuthError(error.message || "Sign-up failed.");
    } else {
      setAuthError("Signup successful. Check your email if confirmation is required.");
    }
    setAuthLoading(false);
  };

  const handleSignOut = async () => {
    if (!supabase) return;
    setAuthError("");
    await supabase.auth.signOut();
  };

  if (!authBootstrapped) {
    return (
      <div className="min-h-screen bg-mist p-8 text-center text-slate-700">
        Loading authentication...
      </div>
    );
  }

  if (isSupabaseEnabled && !session) {
    return (
      <AuthGate
        onSignIn={handleSignIn}
        onSignUp={handleSignUp}
        loading={authLoading}
        authError={authError}
      />
    );
  }

  return (
    <AppLayout
      metrics={summaryMetrics}
      authEnabled={isSupabaseEnabled}
      userEmail={session?.user?.email || ""}
      onSignOut={handleSignOut}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/resume-scanner" replace />} />
        <Route
          path="/resume-scanner"
          element={
            <ResumeScannerPage
              onParsed={(payload) =>
                updatePlatformState({
                  resumeData: payload.resume,
                  resumeScore: payload.resume_score
                })
              }
            />
          }
        />
        <Route
          path="/resume-ai"
          element={<ResumeAIPage />}
        />
        <Route
          path="/job-analyzer"
          element={
            <JobAnalyzerPage
              resumeData={platformState.resumeData}
              onMatched={(payload) =>
                updatePlatformState({
                  jobMatch: payload.match.match_score,
                  matchData: payload.match
                })
              }
            />
          }
        />
        <Route
          path="/fake-job-detection"
          element={
            <FakeJobDetectionPage
              onScored={(payload) =>
                updatePlatformState({
                  scamRisk: payload.scam_probability,
                  fakeJobData: payload
                })
              }
            />
          }
        />
        <Route path="/dashboard" element={<Navigate to="/resume-scanner" replace />} />
        <Route path="*" element={<Navigate to="/resume-scanner" replace />} />
      </Routes>
    </AppLayout>
  );
}
