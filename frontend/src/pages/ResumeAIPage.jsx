import { useMemo, useState } from "react";
import { generateResumeAI, parseResume } from "../api/client";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";

const scratchDefaults = {
  name: "",
  email: "",
  phone: "",
  location: "",
  linkedin: "",
  github: "",
  summary: "",
  experience_years: "",
  skills: "",
  experience_highlights: "",
  education: "",
  projects: "",
  certifications: "",
  achievements: ""
};

function modeButtonClass(active) {
  if (active) return "rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white";
  return "rounded-lg bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-teal-50";
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

function downloadBase64File(filename, base64Content, mimeType) {
  const binary = window.atob(base64Content || "");
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  downloadFile(filename, bytes, mimeType);
}

export default function ResumeAIPage() {
  const [sourceMode, setSourceMode] = useState("scratch");
  const [scratchProfile, setScratchProfile] = useState(scratchDefaults);
  const [resumeFile, setResumeFile] = useState(null);
  const [parsedResume, setParsedResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parseLoading, setParseLoading] = useState(false);
  const [error, setError] = useState("");

  const parsedResumeSummary = useMemo(() => {
    if (!parsedResume) return null;
    return {
      name: parsedResume.name || "Not detected",
      skills: (parsedResume.skills || []).length,
      experienceYears: parsedResume.experience_years || 0
    };
  }, [parsedResume]);

  const parseExistingResume = async () => {
    setError("");
    if (!resumeFile) {
      setError("Upload a resume file first.");
      return null;
    }

    setParseLoading(true);
    try {
      const response = await parseResume(resumeFile);
      setParsedResume(response.resume);
      return response.resume;
    } catch (apiError) {
      setError(apiError.message || "Failed to parse existing resume.");
      return null;
    } finally {
      setParseLoading(false);
    }
  };

  const handleGenerate = async (event) => {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!jobDescription.trim()) {
      setError("Add a target job description before generating resume assets.");
      return;
    }

    setLoading(true);
    try {
      let resumeParsedPayload = null;
      if (sourceMode === "existing") {
        resumeParsedPayload = parsedResume;
        if (!resumeParsedPayload) {
          resumeParsedPayload = await parseExistingResume();
        }
        if (!resumeParsedPayload) {
          setLoading(false);
          return;
        }
      }

      const response = await generateResumeAI({
        sourceMode,
        jobDescription,
        scratchProfile: sourceMode === "scratch" ? scratchProfile : undefined,
        resumeParsed: sourceMode === "existing" ? resumeParsedPayload : undefined
      });
      setResult(response);
    } catch (apiError) {
      setError(apiError.message || "Failed to generate Resume AI output.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-ink">Resume AI</h2>
        <p className="text-sm text-slate-600">
          Build a targeted resume from scratch or from an existing resume, then generate LaTeX + downloadable resume.
        </p>
      </div>

      <form onSubmit={handleGenerate} className="space-y-4">
        <div className="rounded-2xl border border-edge bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Step 1 - Choose Resume Source</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setSourceMode("scratch")}
              className={modeButtonClass(sourceMode === "scratch")}
            >
              Create New Resume
            </button>
            <button
              type="button"
              onClick={() => setSourceMode("existing")}
              className={modeButtonClass(sourceMode === "existing")}
            >
              Use Existing Resume
            </button>
          </div>

          {sourceMode === "scratch" && (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <label className="text-sm font-semibold text-slate-700">
                Full Name
                <input
                  value={scratchProfile.name}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, name: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="Jane Doe"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Email
                <input
                  value={scratchProfile.email}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, email: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="jane@email.com"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Phone
                <input
                  value={scratchProfile.phone}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, phone: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="+1 555 123 4567"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Location
                <input
                  value={scratchProfile.location}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, location: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="San Francisco, CA"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                LinkedIn URL
                <input
                  value={scratchProfile.linkedin}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, linkedin: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="https://linkedin.com/in/username"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                GitHub URL
                <input
                  value={scratchProfile.github}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, github: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="https://github.com/username"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700 md:col-span-2">
                Professional Summary
                <textarea
                  value={scratchProfile.summary}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, summary: event.target.value }))}
                  className="mt-1 block h-24 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="Short professional summary..."
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Experience (years)
                <input
                  value={scratchProfile.experience_years}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, experience_years: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="5"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700 md:col-span-2">
                Skills (comma separated)
                <input
                  value={scratchProfile.skills}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, skills: event.target.value }))}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                  placeholder="Python, SQL, AWS, Docker"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700 md:col-span-2">
                Experience Highlights (one bullet per line)
                <textarea
                  value={scratchProfile.experience_highlights}
                  onChange={(event) =>
                    setScratchProfile((prev) => ({ ...prev, experience_highlights: event.target.value }))
                  }
                  className="mt-1 block h-28 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700 md:col-span-2">
                Education (one line per entry)
                <textarea
                  value={scratchProfile.education}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, education: event.target.value }))}
                  className="mt-1 block h-24 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700 md:col-span-2">
                Projects (one line per entry)
                <textarea
                  value={scratchProfile.projects}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, projects: event.target.value }))}
                  className="mt-1 block h-24 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Certifications (one line per entry)
                <textarea
                  value={scratchProfile.certifications}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, certifications: event.target.value }))}
                  className="mt-1 block h-24 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Achievements (one line per entry)
                <textarea
                  value={scratchProfile.achievements}
                  onChange={(event) => setScratchProfile((prev) => ({ ...prev, achievements: event.target.value }))}
                  className="mt-1 block h-24 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
            </div>
          )}

          {sourceMode === "existing" && (
            <div className="mt-4 space-y-3">
              <label className="block text-sm font-semibold text-slate-700">
                Upload Existing Resume (PDF, DOCX, TXT)
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(event) => {
                    setResumeFile(event.target.files?.[0] ?? null);
                    setParsedResume(null);
                  }}
                  className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
                />
              </label>
              <button
                type="button"
                onClick={parseExistingResume}
                disabled={parseLoading}
                className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal-800 disabled:opacity-60"
              >
                Parse Existing Resume
              </button>
              {parseLoading && <LoadingSpinner label="Parsing existing resume..." />}
              {parsedResumeSummary && (
                <div className="rounded-xl border border-edge bg-panel p-3 text-sm text-slate-700">
                  <p>
                    Parsed candidate: <span className="font-semibold text-slate-900">{parsedResumeSummary.name}</span>
                  </p>
                  <p>Skills detected: {parsedResumeSummary.skills}</p>
                  <p>Experience: {parsedResumeSummary.experienceYears} years</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-edge bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Step 2 - Target Job Description</p>
          <label className="mt-3 block text-sm font-semibold text-slate-700">
            Paste Target Job Description
            <textarea
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              className="mt-1 block h-48 w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
              placeholder="Paste full target job description here..."
            />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="mt-3 rounded-xl bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-700 disabled:opacity-60"
          >
            Generate Resume AI Output
          </button>
          {loading && <div className="mt-3"><LoadingSpinner label="Generating tailored LaTeX and resume file..." /></div>}
          <div className="mt-3">
            <ErrorAlert message={error} />
          </div>
        </div>
      </form>

      {result && (
        <div className="space-y-4 rounded-2xl border border-edge bg-white p-5">
          <h3 className="font-display text-xl font-bold text-ink">Generated Resume Assets</h3>
          <div className="rounded-xl border border-edge bg-panel p-4 text-sm text-slate-700">
            <p>
              Target Role: <span className="font-semibold text-slate-900">{result.job_target?.role_title || "N/A"}</span>
            </p>
            <p>Role Family: {result.job_target?.role_family || "N/A"}</p>
            <p>
              Matched Required Skills: {(result.job_target?.matched_required_skills || []).join(", ") || "None detected"}
            </p>
            <p>
              Missing Required Skills: {(result.job_target?.missing_required_skills || []).join(", ") || "No major gaps"}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => downloadFile(result.latex_filename || "resume.tex", result.latex_code || "", "text/plain;charset=utf-8")}
              className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal-800"
            >
              Download LaTeX (.tex)
            </button>
            <button
              type="button"
              onClick={() =>
                downloadBase64File(
                  result.resume_filename || "resume.docx",
                  result.resume_docx_base64 || "",
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
              }
              className="rounded-lg bg-orange-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-orange-700"
            >
              Download Resume (.docx)
            </button>
            <button
              type="button"
              onClick={() =>
                downloadFile(
                  "resume-preview.txt",
                  result.resume_text || "",
                  "text/plain;charset=utf-8"
                )
              }
              className="rounded-lg bg-slate-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
            >
              Download Resume Text
            </button>
            <a
              href={result.overleaf_url || "https://www.overleaf.com/docs"}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-800"
            >
              Open in Overleaf
            </a>
          </div>
          <p className="text-xs text-slate-500">{result.overleaf_hint}</p>

          <div className="rounded-xl border border-edge bg-panel p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Generated LaTeX Code</p>
            <pre className="mt-2 max-h-[420px] overflow-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-3 text-xs text-slate-100">
              {result.latex_code}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
