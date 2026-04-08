import { useState } from "react";
import { parseResume } from "../api/client";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";

function getStrongestAssessment(resume) {
  const domainAnalysis = resume?.domain_analysis || {};
  const strongest = domainAnalysis.strongest_domain;
  if (!strongest) return null;
  return (domainAnalysis.domain_assessments || []).find((item) => item.domain === strongest) || null;
}

function buildResumeReport(resume, resumeScore, recommendedJobs = []) {
  const domainAnalysis = resume.domain_analysis || {};
  const strongestAssessment = getStrongestAssessment(resume);
  const strongestSignals = strongestAssessment?.strength_signals || [];
  const missingForStrongest = domainAnalysis.missing_skills_for_strongest_domain || [];
  const experienceBreakdown = resume.experience_breakdown || {};

  const lines = [
    "AI Recruitment Intelligence - Resume Analysis Report",
    `Generated At: ${new Date().toISOString()}`,
    "",
    "=== Resume Overview ===",
    `Resume Score: ${resumeScore}%`,
    `Experience: ${resume.experience_years || 0} years`,
    `Experience Confidence: ${experienceBreakdown.confidence || "Unknown"}`,
    `Experience From Date Ranges: ${experienceBreakdown.from_date_ranges_years ?? 0} years`,
    `Experience From Explicit Claims: ${experienceBreakdown.from_explicit_claim_years ?? 0} years`,
    `Skills Detected: ${(resume.skills || []).length}`,
    `Education Entries: ${(resume.education || []).length}`,
    `Candidate Name: ${resume.name || "Not detected"}`,
    `Emails: ${(resume.contact?.emails || []).join(", ") || "N/A"}`,
    `Phones: ${(resume.contact?.phones || []).join(", ") || "N/A"}`,
    `Strongest Domain: ${domainAnalysis.strongest_domain || "N/A"}`,
    `Strongest Domain Probability: ${domainAnalysis.strongest_domain_probability ?? 0}%`,
    "",
    "=== Profile Summary ===",
    resume.profile_summary || "Not detected",
    "",
    "=== Experience Evidence ===",
    ...((experienceBreakdown.evidence || []).length
      ? (experienceBreakdown.evidence || []).map((item) => `- ${item}`)
      : ["- Not enough explicit experience evidence found"]),
    "",
    "=== Recent Roles ===",
    ...(resume.recent_roles?.length ? resume.recent_roles.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Companies ===",
    ...(resume.companies?.length ? resume.companies.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Certifications ===",
    ...(resume.certifications?.length ? resume.certifications.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Projects ===",
    ...(resume.projects?.length ? resume.projects.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Achievements ===",
    ...(resume.achievements?.length ? resume.achievements.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Strength Signals ===",
    ...(strongestSignals.length ? strongestSignals.map((item) => `- ${item}`) : ["- Not available"]),
    "",
    "=== Missing Skills For Strongest Domain ===",
    ...(missingForStrongest.length ? missingForStrongest.map((item) => `- ${item}`) : ["- No major gaps detected"]),
    "",
    "=== Domain Probabilities ===",
    ...((domainAnalysis.domain_assessments || []).map(
      (item) => `- ${item.domain}: ${item.probability}% (${item.readiness})`
    ) || ["- Not available"]),
    "",
    "=== Skills ===",
    ...(resume.skills?.length ? resume.skills.map((item) => `- ${item}`) : ["- None"]),
    "",
    "=== Education ===",
    ...(resume.education?.length ? resume.education.map((item) => `- ${item}`) : ["- Not detected"]),
    "",
    "=== Keywords ===",
    ...(resume.keywords?.length ? resume.keywords.map((item) => `- ${item}`) : ["- None"]),
    "",
    "=== Recommended Jobs ===",
    ...(recommendedJobs.length
      ? recommendedJobs.flatMap((job) => [
          `- ${job.title} @ ${job.company} | ${job.fit_score}% (${job.fit_label})`,
          `  Missing skills: ${(job.missing_required_skills || []).join(", ") || "None"}`,
          `  Job link: ${job.job_link || "N/A"}`,
          `  Fallback link: ${job.job_link_fallback || "N/A"}`,
        ])
      : ["- Not available"]),
  ];

  return lines.join("\n");
}

function jobToneClass(score) {
  if (score >= 78) return "bg-teal-100 text-teal-900";
  if (score >= 60) return "bg-orange-100 text-orange-900";
  return "bg-slate-200 text-slate-800";
}

function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

export default function ResumeScannerPage({ onParsed }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!resumeFile) {
      setError("Please upload a resume file (PDF, DOCX, or TXT).");
      return;
    }

    setLoading(true);
    try {
      const response = await parseResume(resumeFile);
      setResult(response);
      onParsed?.(response);
    } catch (apiError) {
      setError(apiError.message || "Failed to parse resume.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-ink">Resume Scanner</h2>
        <p className="text-sm text-slate-600">
          Upload candidate resume files to extract skills, experience, education, and keyword signals.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-edge bg-white p-5">
        <label className="block text-sm font-semibold text-slate-700">
          Resume File
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
            className="mt-2 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Parse Resume
        </button>

        {loading && <LoadingSpinner label="Parsing resume and extracting entities..." />}
        <ErrorAlert message={error} />
      </form>

      {result?.resume && (
        <div className="space-y-4 rounded-2xl border border-edge bg-white p-5">
          <h3 className="font-display text-xl font-bold text-ink">Parsed Resume Output</h3>
          <p className="text-sm text-slate-600">
            Resume Score: <span className="font-semibold text-teal-700">{result.resume_score}%</span>
          </p>

          <div className="rounded-xl border border-edge bg-panel p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Resume Overview</p>
            <p className="mt-2 text-sm text-slate-700">
              Candidate profile shows strongest tendency toward{" "}
              <span className="font-semibold text-teal-800">
                {result.resume.domain_analysis?.strongest_domain || "N/A"}
              </span>{" "}
              with estimated employability probability of{" "}
              <span className="font-semibold text-teal-800">
                {result.resume.domain_analysis?.strongest_domain_probability ?? 0}%
              </span>.
            </p>
            <p className="mt-2 text-sm text-slate-700">
              Name: <span className="font-semibold text-teal-900">{result.resume.name || "Not detected"}</span>
            </p>
            {(result.resume.profile_summary || "").trim() && (
              <p className="mt-2 text-sm text-slate-700">
                Summary: <span className="text-slate-800">{result.resume.profile_summary}</span>
              </p>
            )}
            <div className="mt-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-lg border border-edge bg-white px-3 py-2 text-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">Experience</p>
                <p className="font-semibold text-slate-800">{result.resume.experience_years || 0} years</p>
              </div>
              <div className="rounded-lg border border-edge bg-white px-3 py-2 text-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">Skills</p>
                <p className="font-semibold text-slate-800">{(result.resume.skills || []).length}</p>
              </div>
              <div className="rounded-lg border border-edge bg-white px-3 py-2 text-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">Education</p>
                <p className="font-semibold text-slate-800">{(result.resume.education || []).length}</p>
              </div>
              <div className="rounded-lg border border-edge bg-white px-3 py-2 text-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">Keywords</p>
                <p className="font-semibold text-slate-800">{(result.resume.keywords || []).length}</p>
              </div>
            </div>
            <div className="mt-3 rounded-lg border border-edge bg-white p-3 text-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Experience Estimation Details</p>
              <p className="mt-1 text-slate-700">
                Confidence:{" "}
                <span className="font-semibold text-slate-900">
                  {result.resume.experience_breakdown?.confidence || "Unknown"}
                </span>
              </p>
              <p className="text-slate-700">
                From date ranges:{" "}
                <span className="font-semibold">{result.resume.experience_breakdown?.from_date_ranges_years ?? 0} years</span>
              </p>
              <p className="text-slate-700">
                From explicit claims:{" "}
                <span className="font-semibold">{result.resume.experience_breakdown?.from_explicit_claim_years ?? 0} years</span>
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Experience is estimated from date ranges and explicit claims found in the resume.
              </p>
            </div>
          </div>

          {result.resume.domain_analysis && (
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Domain Employability Analysis
              </p>
              <p className="mt-2 text-sm text-slate-700">
                Strongest domain tendency:{" "}
                <span className="font-semibold text-teal-800">
                  {result.resume.domain_analysis.strongest_domain || "N/A"}
                </span>
              </p>
              <p className="text-sm text-slate-700">
                Job probability in strongest domain:{" "}
                <span className="font-semibold text-teal-800">
                  {result.resume.domain_analysis.strongest_domain_probability ?? 0}%
                </span>
              </p>
              <p className="mt-2 text-sm font-semibold text-slate-700">Missing skills for strongest domain:</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {(result.resume.domain_analysis.missing_skills_for_strongest_domain || []).map((skill) => (
                  <span key={skill} className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-900">
                    {skill}
                  </span>
                ))}
                {(result.resume.domain_analysis.missing_skills_for_strongest_domain || []).length === 0 && (
                  <span className="text-sm text-slate-600">No major skill gaps detected.</span>
                )}
              </div>

              <p className="mt-3 text-sm font-semibold text-slate-700">Domain-wise probability:</p>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                {(result.resume.domain_analysis.domain_assessments || []).map((assessment) => (
                  <div key={assessment.domain} className="rounded-lg border border-edge bg-white px-3 py-2 text-sm">
                    <p className="font-semibold text-slate-800">{assessment.domain}</p>
                    <p className="text-slate-700">
                      Probability: <span className="font-semibold">{assessment.probability}%</span>
                    </p>
                    <p className="text-xs text-slate-500">Readiness: {assessment.readiness}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl border border-edge bg-panel p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
              Downloadable Analysis Report
            </p>
            <p className="mt-2 text-sm text-slate-700">
              Download resume overview and analyzed intelligence report for ATS sharing.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
                  const reportText = buildResumeReport(result.resume, result.resume_score, result.recommended_jobs || []);
                  downloadFile(`resume-analysis-report-${stamp}.txt`, reportText, "text/plain;charset=utf-8");
                }}
                className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal-800"
              >
                Download Analysis Report (.txt)
              </button>
            </div>
          </div>

          {(result.recommended_jobs || []).length > 0 && (
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                Jobs Matching This Resume
              </p>
              <p className="mt-2 text-sm text-slate-700">
                Recommended job roles based on your skills, experience, and strongest domain tendency.
              </p>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {result.recommended_jobs.map((job) => (
                  <article key={job.job_id} className="rounded-xl border border-edge bg-white p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-slate-900">{job.title}</p>
                        <p className="text-xs text-slate-600">
                          {job.company} • {job.location} • {job.employment_type}
                        </p>
                      </div>
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${jobToneClass(job.fit_score)}`}>
                        {job.fit_score}% {job.fit_label}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-600">
                      Domain: {job.domain} • Experience: {job.min_experience_years}+ years • Salary: {job.salary_range}
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      Coverage: {job.required_coverage ?? 0}% required • {job.preferred_coverage ?? 0}% preferred
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      Matched required skills: {(job.matched_required_skills || []).join(", ") || "None"}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {job.job_link && (
                        <a
                          href={job.job_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex rounded-lg bg-teal-700 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-teal-800"
                        >
                          Open Job Link
                        </a>
                      )}
                      {job.job_link_fallback && (
                        <a
                          href={job.job_link_fallback}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex rounded-lg bg-slate-700 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-800"
                        >
                          Fallback Search
                        </a>
                      )}
                    </div>
                    <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Why this fits</p>
                    <ul className="mt-1 space-y-1 text-sm text-slate-700">
                      {(job.reasons || []).map((reason) => (
                        <li key={reason}>- {reason}</li>
                      ))}
                    </ul>
                    <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Missing required skills</p>
                    <p className="mt-1 text-sm text-slate-700">
                      {(job.missing_required_skills || []).join(", ") || "No major required skill gaps"}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Skills</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {result.resume.skills.map((skill) => (
                  <span key={skill} className="rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold text-teal-800">
                    {skill}
                  </span>
                ))}
                {result.resume.skills.length === 0 && (
                  <span className="text-sm text-slate-600">No explicit skills matched.</span>
                )}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Education</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {result.resume.education.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {result.resume.education.length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Contact & Links</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                <li>- Emails: {(result.resume.contact?.emails || []).join(", ") || "Not found"}</li>
                <li>- Phones: {(result.resume.contact?.phones || []).join(", ") || "Not found"}</li>
                <li>- LinkedIn: {result.resume.contact?.linkedin || "Not found"}</li>
                <li>- GitHub: {result.resume.contact?.github || "Not found"}</li>
              </ul>
            </div>

            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Experience Evidence</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.experience_breakdown?.evidence || []).slice(0, 6).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.experience_breakdown?.evidence || []).length === 0 && (
                  <li>- Not enough explicit experience evidence found.</li>
                )}
              </ul>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Recent Roles</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.recent_roles || []).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.recent_roles || []).length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Companies</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.companies || []).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.companies || []).length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Languages</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.languages || []).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.languages || []).length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Projects</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.projects || []).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.projects || []).length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
            <div className="rounded-xl border border-edge bg-panel p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Certifications</p>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {(result.resume.certifications || []).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
                {(result.resume.certifications || []).length === 0 && <li>- Not detected</li>}
              </ul>
            </div>
          </div>

          <div className="rounded-xl border border-edge bg-panel p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Achievements</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-700">
              {(result.resume.achievements || []).map((item) => (
                <li key={item}>- {item}</li>
              ))}
              {(result.resume.achievements || []).length === 0 && <li>- Not detected</li>}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
