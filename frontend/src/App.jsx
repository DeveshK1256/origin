import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
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

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(platformState));
  }, [platformState]);

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

  return (
    <AppLayout metrics={summaryMetrics}>
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
