import MetricCard from "../components/MetricCard";

function formatPercent(value) {
  if (value === null || value === undefined) return "--";
  return `${Math.round(value)}%`;
}

export default function DashboardPage({ state }) {
  const hasAnyData =
    state.resumeScore !== null || state.jobMatch !== null || state.scamRisk !== null;

  return (
    <section className="space-y-6">
      <div>
        <h2 className="font-display text-2xl font-bold text-ink">Dashboard</h2>
        <p className="text-sm text-slate-600">
          Central ATS-style snapshot of resume quality, role fit, and fraud risk.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Resume Score"
          value={formatPercent(state.resumeScore)}
          hint="Completeness and skill coverage from parsed resume."
          tone="teal"
        />
        <MetricCard
          label="Job Match"
          value={formatPercent(state.jobMatch)}
          hint="How well candidate profile aligns with job requirements."
          tone="orange"
        />
        <MetricCard
          label="Scam Risk"
          value={formatPercent(state.scamRisk)}
          hint="Predicted risk level for the analyzed job posting."
          tone="slate"
        />
      </div>

      <div className="rounded-2xl border border-edge bg-white p-5">
        <h3 className="font-display text-xl font-bold text-ink">Latest Intelligence Summary</h3>
        {!hasAnyData && (
          <p className="mt-2 text-sm text-slate-600">
            No analyses yet. Start with Resume Scanner, then run Job Analyzer and Fake Job Detection.
          </p>
        )}

        {hasAnyData && (
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Resume Insights
              </p>
              {state.resumeData ? (
                <>
                  <p className="mt-2 text-sm text-slate-700">
                    Skills detected: <span className="font-semibold">{state.resumeData.skills.length}</span>
                  </p>
                  <p className="text-sm text-slate-700">
                    Experience estimate:{" "}
                    <span className="font-semibold">{state.resumeData.experience_years} years</span>
                  </p>
                  <p className="mt-2 text-sm text-slate-700">
                    Top skills: {state.resumeData.skills.slice(0, 6).join(", ") || "N/A"}
                  </p>
                </>
              ) : (
                <p className="mt-2 text-sm text-slate-600">No resume parsed yet.</p>
              )}
            </div>

            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Matching & Risk
              </p>
              {state.matchData ? (
                <p className="mt-2 text-sm text-slate-700">
                  Overlap skills:{" "}
                  <span className="font-semibold">
                    {state.matchData.overlapping_skills.slice(0, 6).join(", ") || "Low overlap"}
                  </span>
                </p>
              ) : (
                <p className="mt-2 text-sm text-slate-600">No job matching run yet.</p>
              )}
              {state.fakeJobData ? (
                <p className="mt-2 text-sm text-slate-700">
                  Risk level: <span className="font-semibold">{state.fakeJobData.risk_level}</span>
                </p>
              ) : (
                <p className="mt-2 text-sm text-slate-600">No fake-job detection run yet.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
