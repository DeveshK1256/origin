import { useState } from "react";
import { detectFakeJob } from "../api/client";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";

function riskStyles(level) {
  if (level === "High") {
    return {
      badge: "bg-red-100 text-red-900",
      bar: "bg-red-500",
      card: "border-red-300 bg-red-50"
    };
  }
  if (level === "Medium") {
    return {
      badge: "bg-amber-100 text-amber-900",
      bar: "bg-amber-500",
      card: "border-amber-300 bg-amber-50"
    };
  }
  return {
    badge: "bg-teal-100 text-teal-900",
    bar: "bg-teal-600",
    card: "border-teal-300 bg-teal-50"
  };
}

export default function FakeJobDetectionPage({ onScored }) {
  const [jobUrl, setJobUrl] = useState("");
  const [fallbackText, setFallbackText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async (event) => {
    event.preventDefault();
    setError("");

    if (!jobUrl.trim() && !fallbackText.trim()) {
      setError("Please provide a job URL or fallback job text.");
      return;
    }

    setLoading(true);
    try {
      const payload = await detectFakeJob({
        jobUrl: jobUrl.trim(),
        jobText: fallbackText.trim()
      });
      setResult(payload);
      onScored?.(payload);
    } catch (apiError) {
      setError(apiError.message || "Could not evaluate fake-job risk.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-ink">Fake Job Detection</h2>
        <p className="text-sm text-slate-600">
          Analyze job posting URLs with an ML model to estimate scam probability and explain risks.
        </p>
      </div>

      <form onSubmit={handleAnalyze} className="space-y-4 rounded-2xl border border-edge bg-white p-5">
        <label className="block text-sm font-semibold text-slate-700">
          Job URL
          <input
            type="url"
            value={jobUrl}
            onChange={(event) => setJobUrl(event.target.value)}
            placeholder="https://example.com/job/software-engineer"
            className="mt-2 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
          />
        </label>

        <label className="block text-sm font-semibold text-slate-700">
          Optional Fallback Job Text
          <textarea
            rows={4}
            value={fallbackText}
            onChange={(event) => setFallbackText(event.target.value)}
            placeholder="Optional text if URL blocks scraping."
            className="mt-2 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Detect Scam Probability
        </button>

        {loading && <LoadingSpinner label="Running fake-job risk model..." />}
        <ErrorAlert message={error} />
      </form>

      {result && (
        <div className="space-y-4 rounded-2xl border border-edge bg-white p-5">
          <h3 className="font-display text-xl font-bold text-ink">Risk Assessment</h3>
          {(() => {
            const tone = riskStyles(result.risk_level);
            const riskValue = Math.max(0, Math.min(100, Number(result.scam_probability || 0)));
            return (
              <div className={`rounded-xl border p-4 ${tone.card}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm text-slate-700">
                    Scam Probability:{" "}
                    <span className="font-display text-3xl font-extrabold text-slate-900">
                      {Math.round(riskValue)}%
                    </span>
                  </p>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${tone.badge}`}>
                    {result.risk_level} Risk
                  </span>
                </div>
                <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-white/80">
                  <div className={`h-full ${tone.bar}`} style={{ width: `${riskValue}%` }} />
                </div>
                <p className="mt-3 text-sm text-slate-700">{result.explanation || "Risk explanation not available."}</p>
              </div>
            );
          })()}

          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">ML Score</p>
              <p className="font-display text-xl font-bold text-slate-900">{Math.round(result.ml_probability ?? result.scam_probability)}%</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Rule Score</p>
              <p className="font-display text-xl font-bold text-slate-900">{Math.round(result.rule_risk_score ?? 0)}%</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Confidence</p>
              <p className="font-display text-xl font-bold text-slate-900">{Math.round((result.confidence ?? 0.5) * 100)}%</p>
            </div>
          </div>

          {result.fetch_warning && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              {result.fetch_warning}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Red Flags</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {result.red_flags.map((flag) => (
                  <li key={flag}>- {flag}</li>
                ))}
                {result.red_flags.length === 0 && <li>- No major red flags detected.</li>}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Trust Signals</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.safe_signals || []).map((signal) => (
                  <li key={signal}>- {signal}</li>
                ))}
                {(result.safe_signals || []).length === 0 && <li>- No strong trust indicators found.</li>}
              </ul>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Top Risk Drivers</p>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {(result.risk_drivers || []).slice(0, 6).map((driver) => (
                <div key={`${driver.feature}-${driver.factor}`} className="rounded-lg border border-edge bg-panel p-3 text-sm">
                  <p className="font-semibold text-slate-800">{driver.factor}</p>
                  <p className="text-slate-700">Impact: {driver.impact}</p>
                  <p className="text-xs text-slate-500">Feature: {driver.feature} = {driver.value}</p>
                </div>
              ))}
              {(result.risk_drivers || []).length === 0 && (
                <p className="text-sm text-slate-600">No high-impact risk drivers found.</p>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-edge bg-panel p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Feature Snapshot</p>
            <pre className="mt-2 overflow-auto rounded-lg bg-slate-900 p-3 font-mono text-xs text-slate-100">
{JSON.stringify(result.feature_snapshot, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
