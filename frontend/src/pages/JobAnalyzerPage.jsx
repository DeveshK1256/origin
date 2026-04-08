import { useState } from "react";
import { analyzeJobDescription, matchJob } from "../api/client";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";

function formatSalaryRange(rangeObj) {
  if (!rangeObj || (!rangeObj.min && !rangeObj.max)) return "Not specified";
  const min = rangeObj.min ? `$${Number(rangeObj.min).toLocaleString()}` : "--";
  const max = rangeObj.max ? `$${Number(rangeObj.max).toLocaleString()}` : "--";
  return `${min} - ${max}`;
}

function ScoreBar({ label, value, tone = "teal" }) {
  const safeValue = Math.max(0, Math.min(100, Number(value || 0)));
  const barColor = tone === "orange" ? "bg-orange-500" : tone === "slate" ? "bg-slate-700" : "bg-teal-600";
  return (
    <div className="rounded-xl border border-edge bg-panel p-3">
      <div className="mb-1 flex items-center justify-between text-sm">
        <p className="font-semibold text-slate-700">{label}</p>
        <p className="font-display text-lg font-bold text-ink">{safeValue.toFixed(0)}%</p>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full ${barColor}`} style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}

export default function JobAnalyzerPage({ resumeData, onMatched }) {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [matchPayload, setMatchPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canMatch = Boolean(resumeFile || resumeData);

  const handleAnalyzeAndMatch = async (event) => {
    event.preventDefault();
    setError("");

    if (!jobDescription.trim()) {
      setError("Please paste a job description.");
      return;
    }

    setLoading(true);
    try {
      const jdAnalysis = await analyzeJobDescription(jobDescription.trim());
      setAnalysis(jdAnalysis);

      if (canMatch) {
        const payload = await matchJob({
          jobDescription: jobDescription.trim(),
          resumeFile,
          resumeParsed: resumeFile ? null : resumeData
        });
        setMatchPayload(payload);
        onMatched?.(payload);
      } else {
        setMatchPayload(null);
      }
    } catch (apiError) {
      setError(apiError.message || "Failed to analyze job description.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-ink">Job Description Analyzer</h2>
        <p className="text-sm text-slate-600">
          Analyze role requirements and compute candidate-job match score.
        </p>
      </div>

      <form onSubmit={handleAnalyzeAndMatch} className="space-y-4 rounded-2xl border border-edge bg-white p-5">
        <label className="block text-sm font-semibold text-slate-700">
          Job Description
          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            rows={9}
            placeholder="Paste full job description here..."
            className="mt-2 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
          />
        </label>

        <label className="block text-sm font-semibold text-slate-700">
          Optional Resume Upload (for matching)
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
            className="mt-2 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
          />
        </label>

        {!resumeFile && resumeData && (
          <p className="text-sm text-teal-700">
            Using latest parsed resume from Resume Scanner for match scoring.
          </p>
        )}

        {!resumeFile && !resumeData && (
          <p className="text-sm text-amber-700">
            Add a resume file or parse one in Resume Scanner to generate match score.
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Analyze Job
        </button>

        {loading && <LoadingSpinner label="Analyzing JD and calculating match..." />}
        <ErrorAlert message={error} />
      </form>

      {analysis && (
        <div className="space-y-4 rounded-2xl border border-edge bg-white p-5">
          <h3 className="font-display text-xl font-bold text-ink">Job Insights</h3>

          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</p>
              <p className="font-semibold text-slate-800">{analysis.role_title || "Not specified"}</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role Family</p>
              <p className="font-semibold text-slate-800">{analysis.role_family || "General"}</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Seniority</p>
              <p className="font-semibold capitalize text-slate-800">{analysis.seniority || "mid"}</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">JD Quality</p>
              <p className="font-semibold text-slate-800">{analysis.quality_score ?? 0}%</p>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Compensation</p>
              <p className="font-semibold text-slate-800">{formatSalaryRange(analysis.salary_range)}</p>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Work Setup</p>
              <p className="font-semibold text-slate-800">
                {analysis.hiring_type} • {analysis.remote_possible ? "Remote option" : "On-site / Hybrid"}
              </p>
              <p className="text-slate-700">Experience: {analysis.required_experience_years || 0}+ years</p>
            </div>
          </div>

          {analysis.quality_notes?.length > 0 && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-amber-800">JD Improvement Notes</p>
              <ul className="mt-2 space-y-1 text-sm text-amber-900">
                {analysis.quality_notes.map((note) => (
                  <li key={note}>- {note}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Required Skills</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(analysis.required_skills || analysis.job_skills || []).map((skill) => (
                  <span key={`req-${skill}`} className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-900">
                    {skill}
                  </span>
                ))}
                {(analysis.required_skills || analysis.job_skills || []).length === 0 && (
                  <span className="text-sm text-slate-600">No explicit required skills found.</span>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Preferred Skills</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(analysis.preferred_skills || []).map((skill) => (
                  <span key={`pref-${skill}`} className="rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold text-teal-900">
                    {skill}
                  </span>
                ))}
                {(analysis.preferred_skills || []).length === 0 && (
                  <span className="text-sm text-slate-600">No preferred skills explicitly listed.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {matchPayload?.match && (
        <div className="space-y-4 rounded-2xl border border-edge bg-white p-5">
          <h3 className="font-display text-xl font-bold text-ink">Match Result</h3>
          <p className="text-sm text-slate-700">
            Match Score:{" "}
            <span className="font-display text-2xl font-extrabold text-orange-700">
              {matchPayload.match.match_score}%
            </span>
          </p>
          <p className="text-sm text-slate-700">
            Fit Verdict:{" "}
            <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-900">
              {matchPayload.match.fit_label || "Match result"}
            </span>
          </p>

          <div className="grid gap-3 md:grid-cols-2">
            <ScoreBar label="Required Skill Score" value={matchPayload.match.required_skill_score ?? matchPayload.match.skill_score} tone="orange" />
            <ScoreBar label="Preferred Skill Score" value={matchPayload.match.preferred_skill_score ?? matchPayload.match.skill_score} tone="teal" />
            <ScoreBar label="Keyword Score" value={matchPayload.match.keyword_score} tone="slate" />
            <ScoreBar label="Experience Score" value={matchPayload.match.experience_score} tone="teal" />
            <ScoreBar label="Domain Alignment" value={matchPayload.match.domain_alignment_score ?? 0} tone="orange" />
            <ScoreBar label="Overall Match" value={matchPayload.match.match_score} tone="slate" />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Required Skill Matches
              </p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(matchPayload.match.required_overlapping_skills || matchPayload.match.overlapping_skills || []).map((skill) => (
                  <li key={skill}>- {skill}</li>
                ))}
                {(matchPayload.match.required_overlapping_skills || matchPayload.match.overlapping_skills || []).length === 0 && <li>- None detected</li>}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Critical Skill Gaps
              </p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(matchPayload.match.critical_gaps || matchPayload.match.missing_skills || []).map((skill) => (
                  <li key={skill}>- {skill}</li>
                ))}
                {(matchPayload.match.critical_gaps || matchPayload.match.missing_skills || []).length === 0 && <li>- None</li>}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Suggested Next Steps
              </p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(matchPayload.match.next_steps || []).map((step) => (
                  <li key={step}>- {step}</li>
                ))}
                {(matchPayload.match.next_steps || []).length === 0 && <li>- Tailor resume to this role before applying.</li>}
              </ul>
            </div>
          </div>

          {(matchPayload.match.strengths?.length > 0 || matchPayload.match.recommendations?.length > 0) && (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-teal-200 bg-teal-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-teal-800">Strengths</p>
                <ul className="mt-2 space-y-1 text-sm text-teal-900">
                  {(matchPayload.match.strengths || []).map((item) => (
                    <li key={item}>- {item}</li>
                  ))}
                  {(matchPayload.match.strengths || []).length === 0 && <li>- No strong signals identified yet.</li>}
                </ul>
              </div>
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-amber-800">Recommendations</p>
                <ul className="mt-2 space-y-1 text-sm text-amber-900">
                  {(matchPayload.match.recommendations || []).map((item) => (
                    <li key={item}>- {item}</li>
                  ))}
                  {(matchPayload.match.recommendations || []).length === 0 && <li>- No immediate actions required.</li>}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
