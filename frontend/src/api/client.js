const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = payload?.error || "Request failed";
    throw new Error(message);
  }
  return payload;
}

export async function parseResume(file) {
  const formData = new FormData();
  formData.append("resume", file);
  return request("/api/resume/parse", { method: "POST", body: formData });
}

export async function analyzeJobDescription(jobDescription) {
  return request("/api/job/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description: jobDescription })
  });
}

export async function matchJob({ jobDescription, resumeFile, resumeParsed, resumeText }) {
  if (resumeFile) {
    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);
    return request("/api/job/match", { method: "POST", body: formData });
  }

  return request("/api/job/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description: jobDescription,
      resume_parsed: resumeParsed,
      resume_text: resumeText
    })
  });
}

export async function detectFakeJob({ jobUrl, jobText }) {
  return request("/api/fake-job/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_url: jobUrl,
      job_text: jobText
    })
  });
}

export async function generateResumeAI({
  sourceMode,
  jobDescription,
  scratchProfile,
  resumeParsed,
  resumeText
}) {
  return request("/api/resume-ai/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_mode: sourceMode,
      job_description: jobDescription,
      scratch_profile: scratchProfile,
      resume_parsed: resumeParsed,
      resume_text: resumeText
    })
  });
}
