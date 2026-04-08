import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ContactPage from "./pages/ContactPage";
import FeaturesPage from "./pages/FeaturesPage";
import FakeJobDetectionPage from "./pages/FakeJobDetectionPage";
import HomePage from "./pages/HomePage";
import HowItWorksPage from "./pages/HowItWorksPage";
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

function AppWorkspace({ summaryMetrics, platformState, updatePlatformState }) {
  return (
    <AppLayout metrics={summaryMetrics}>
      <Routes>
        <Route path="/" element={<Navigate to="/app/resume-scanner" replace />} />
        <Route
          path="/app/resume-scanner"
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
        <Route path="/app/resume-ai" element={<ResumeAIPage />} />
        <Route
          path="/app/job-analyzer"
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
          path="/app/fake-job-detection"
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
        <Route path="/app/dashboard" element={<Navigate to="/app/resume-scanner" replace />} />
        <Route path="*" element={<Navigate to="/app/resume-scanner" replace />} />
      </Routes>
    </AppLayout>
  );
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
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/features" element={<FeaturesPage />} />
      <Route path="/how-it-works" element={<HowItWorksPage />} />
      <Route path="/contact" element={<ContactPage />} />

      <Route
        path="/app/*"
        element={
          <AppWorkspace
            summaryMetrics={summaryMetrics}
            platformState={platformState}
            updatePlatformState={updatePlatformState}
          />
        }
      />

      <Route path="/resume-scanner" element={<Navigate to="/app/resume-scanner" replace />} />
      <Route path="/resume-ai" element={<Navigate to="/app/resume-ai" replace />} />
      <Route path="/job-analyzer" element={<Navigate to="/app/job-analyzer" replace />} />
      <Route path="/fake-job-detection" element={<Navigate to="/app/fake-job-detection" replace />} />
      <Route path="/dashboard" element={<Navigate to="/app/resume-scanner" replace />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
