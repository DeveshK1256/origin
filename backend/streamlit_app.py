from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Ensure backend-local imports work in hosted environments.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import (
    init_db,
    list_resume_analysis_history,
    save_fake_job_check,
    save_job_analysis,
    save_resume_ai_generation,
    save_resume_analysis,
)
from services.fake_job_detector import FakeJobDetector
from services.file_extractors import (
    allowed_resume_extension,
    extract_text_from_uploaded_file,
)
from services.job_matching import analyze_job_description, calculate_job_match
from services.job_recommender import recommend_jobs_for_resume
from services.resume_ai import generate_resume_ai_assets
from services.resume_parser import parse_resume_text


@dataclass
class UploadedFileAdapter:
    """Adapter to reuse Flask-style extractors with Streamlit upload objects."""

    uploaded_file: any

    @property
    def filename(self) -> str:
        return self.uploaded_file.name

    def read(self) -> bytes:
        return self.uploaded_file.getvalue()


def _initialize_state() -> None:
    defaults = {
        "resume_data": None,
        "resume_score": None,
        "recommended_jobs": None,
        "job_match": None,
        "scam_risk": None,
        "match_data": None,
        "job_analysis": None,
        "fake_job_data": None,
        "resume_ai_result": None,
        "resume_ai_parsed_resume": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def _load_detector() -> FakeJobDetector:
    return FakeJobDetector()


@st.cache_resource(show_spinner=False)
def _init_database() -> bool:
    try:
        init_db()
        return True
    except Exception:
        return False


def _build_resume_report(resume: dict, resume_score: int | None, recommended_jobs: list[dict[str, Any]] | None = None) -> str:
    domain = resume.get("domain_analysis", {})
    contact = resume.get("contact", {})
    experience_breakdown = resume.get("experience_breakdown", {})
    strongest_domain = domain.get("strongest_domain")
    strongest_assessment = None
    for item in domain.get("domain_assessments", []):
        if item.get("domain") == strongest_domain:
            strongest_assessment = item
            break

    lines = [
        "AI Recruitment Intelligence - Resume Analysis Report",
        f"Generated At: {datetime.utcnow().isoformat()}Z",
        "",
        "=== Resume Overview ===",
        f"Resume Score: {resume_score or 0}%",
        f"Experience: {resume.get('experience_years', 0)} years",
        f"Experience Confidence: {experience_breakdown.get('confidence', 'Unknown')}",
        f"Experience From Date Ranges: {experience_breakdown.get('from_date_ranges_years', 0)} years",
        f"Experience From Explicit Claims: {experience_breakdown.get('from_explicit_claim_years', 0)} years",
        f"Skills Detected: {len(resume.get('skills', []))}",
        f"Education Entries: {len(resume.get('education', []))}",
        f"Candidate Name: {resume.get('name', 'Not detected')}",
        f"Emails: {', '.join(contact.get('emails', [])) or 'N/A'}",
        f"Phones: {', '.join(contact.get('phones', [])) or 'N/A'}",
        f"Strongest Domain: {domain.get('strongest_domain', 'N/A')}",
        f"Strongest Domain Probability: {domain.get('strongest_domain_probability', 0)}%",
        "",
        "=== Profile Summary ===",
        resume.get("profile_summary", "Not detected"),
        "",
        "=== Experience Evidence ===",
    ]

    evidence = experience_breakdown.get("evidence", [])
    if evidence:
        lines.extend(f"- {item}" for item in evidence)
    else:
        lines.append("- Not enough explicit experience evidence found")

    lines.extend([
        "",
        "=== Recent Roles ===",
    ])

    recent_roles = resume.get("recent_roles", [])
    if recent_roles:
        lines.extend(f"- {item}" for item in recent_roles)
    else:
        lines.append("- Not detected")

    lines.extend([
        "",
        "=== Companies ===",
    ])

    companies = resume.get("companies", [])
    if companies:
        lines.extend(f"- {item}" for item in companies)
    else:
        lines.append("- Not detected")

    lines.extend([
        "",
        "=== Certifications ===",
    ])

    certifications = resume.get("certifications", [])
    if certifications:
        lines.extend(f"- {item}" for item in certifications)
    else:
        lines.append("- Not detected")

    lines.extend([
        "",
        "=== Projects ===",
    ])

    projects = resume.get("projects", [])
    if projects:
        lines.extend(f"- {item}" for item in projects)
    else:
        lines.append("- Not detected")

    lines.extend([
        "",
        "=== Achievements ===",
    ])

    achievements = resume.get("achievements", [])
    if achievements:
        lines.extend(f"- {item}" for item in achievements)
    else:
        lines.append("- Not detected")

    lines.extend([
        "",
        "=== Strength Signals ===",
    ])

    signals = (strongest_assessment or {}).get("strength_signals", [])
    if signals:
        lines.extend(f"- {item}" for item in signals)
    else:
        lines.append("- Not available")

    lines.extend(["", "=== Missing Skills For Strongest Domain ==="])
    missing = domain.get("missing_skills_for_strongest_domain", [])
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- No major gaps detected")

    lines.extend(["", "=== Domain Probabilities ==="])
    assessments = domain.get("domain_assessments", [])
    if assessments:
        lines.extend(
            f"- {item.get('domain')}: {item.get('probability')}% ({item.get('readiness')})"
            for item in assessments
        )
    else:
        lines.append("- Not available")

    lines.extend(["", "=== Skills ==="])
    skills = resume.get("skills", [])
    if skills:
        lines.extend(f"- {item}" for item in skills)
    else:
        lines.append("- None")

    lines.extend(["", "=== Education ==="])
    education = resume.get("education", [])
    if education:
        lines.extend(f"- {item}" for item in education)
    else:
        lines.append("- Not detected")

    lines.extend(["", "=== Keywords ==="])
    keywords = resume.get("keywords", [])
    if keywords:
        lines.extend(f"- {item}" for item in keywords)
    else:
        lines.append("- None")

    lines.extend(["", "=== Recommended Jobs ==="])
    jobs = recommended_jobs or []
    if jobs:
        for job in jobs:
            lines.append(
                f"- {job.get('title')} @ {job.get('company')} | "
                f"{job.get('fit_score')}% ({job.get('fit_label')})"
            )
            missing = job.get("missing_required_skills", [])
            lines.append(
                "  Missing skills: " + (", ".join(missing) if missing else "None")
            )
            lines.append(f"  Job link: {job.get('job_link') or 'N/A'}")
            lines.append(f"  Fallback link: {job.get('job_link_fallback') or 'N/A'}")
    else:
        lines.append("- Not available")

    return "\n".join(lines)


def _render_dashboard() -> None:
    st.header("Dashboard")
    st.caption(
        "ATS-style summary of candidate readiness, role fit, and scam risk."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Resume Score", f"{st.session_state.resume_score}%" if st.session_state.resume_score is not None else "--")
    c2.metric("Job Match", f"{st.session_state.job_match}%" if st.session_state.job_match is not None else "--")
    c3.metric("Scam Risk", f"{st.session_state.scam_risk}%" if st.session_state.scam_risk is not None else "--")

    st.subheader("Latest Signals")
    if st.session_state.resume_data:
        resume = st.session_state.resume_data
        st.write(
            f"Skills detected: **{len(resume.get('skills', []))}**, "
            f"experience: **{resume.get('experience_years', 0)} years**"
        )
        top_skills = ", ".join(resume.get("skills", [])[:8]) or "N/A"
        st.write(f"Top skills: {top_skills}")
    else:
        st.info("No resume parsed yet.")

    if st.session_state.match_data:
        st.write(
            f"Latest match score: **{st.session_state.match_data.get('match_score', 0)}%**"
        )
        overlap = ", ".join(st.session_state.match_data.get("overlapping_skills", [])[:8]) or "None"
        st.write(f"Overlap skills: {overlap}")
    else:
        st.info("No job match result yet.")

    if st.session_state.fake_job_data:
        data = st.session_state.fake_job_data
        st.write(
            f"Scam risk level: **{data.get('risk_level', 'N/A')}** "
            f"({round(data.get('scam_probability', 0), 2)}%)"
        )
    else:
        st.info("No fake-job analysis yet.")


def _parse_uploaded_resume(uploaded_resume) -> dict:
    if uploaded_resume is None:
        raise ValueError("Upload a resume file first.")

    adapter = UploadedFileAdapter(uploaded_resume)
    if not allowed_resume_extension(adapter.filename):
        raise ValueError("Unsupported file type. Allowed: PDF, DOCX, TXT.")

    extracted_text = extract_text_from_uploaded_file(adapter)
    if not extracted_text.strip():
        raise ValueError("Could not extract readable text from the uploaded file.")

    return parse_resume_text(extracted_text)


def _render_resume_scanner() -> None:
    st.header("Resume Scanner")
    st.caption("Upload PDF, DOCX, or TXT resume to extract structured candidate intelligence.")

    uploaded_resume = st.file_uploader(
        "Resume File",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=False,
    )

    if st.button("Parse Resume", type="primary"):
        try:
            with st.spinner("Parsing resume..."):
                parsed = _parse_uploaded_resume(uploaded_resume)
            st.session_state.resume_data = parsed
            st.session_state.resume_score = parsed.get("resume_score")
            st.session_state.recommended_jobs = recommend_jobs_for_resume(parsed, limit=6)
            save_resume_analysis(
                source="streamlit",
                resume_filename=uploaded_resume.name if uploaded_resume else None,
                parsed_resume=parsed,
                recommended_jobs=st.session_state.recommended_jobs,
            )
            st.success("Resume parsed successfully.")
        except Exception as exc:
            st.error(str(exc))

    st.subheader("Resume Scan History")
    history = list_resume_analysis_history(limit=20)
    if history:
        history_rows = []
        option_map: dict[str, dict[str, Any]] = {}
        for record in history:
            created_at = str(record.get("created_at") or "Unknown time")
            candidate_name = record.get("candidate_name") or "Unknown candidate"
            resume_score = record.get("resume_score")
            score_text = f"{resume_score}%" if resume_score is not None else "N/A"
            source = record.get("source") or "unknown"
            resume_filename = record.get("resume_filename") or "N/A"
            record_id = str(record.get("id") or "")
            short_id = record_id[:8] if record_id else "no-id"

            history_rows.append(
                {
                    "Time (UTC)": created_at,
                    "Candidate": candidate_name,
                    "Score": score_text,
                    "Source": source,
                    "File": resume_filename,
                }
            )

            label = f"{created_at} | {candidate_name} | {score_text} | {short_id}"
            option_map[label] = record

        st.dataframe(history_rows, use_container_width=True, hide_index=True)
        selected_label = st.selectbox(
            "Load a previous resume scan",
            options=list(option_map.keys()),
            key="resume_history_select",
        )
        if st.button("Load Selected History", key="resume_history_load_btn"):
            selected_record = option_map.get(selected_label) or {}
            payload = selected_record.get("payload") or {}
            previous_resume = payload.get("resume")
            previous_jobs = payload.get("recommended_jobs") or []

            if isinstance(previous_resume, dict):
                st.session_state.resume_data = previous_resume
                st.session_state.resume_score = previous_resume.get("resume_score")
                st.session_state.recommended_jobs = (
                    previous_jobs if isinstance(previous_jobs, list) else []
                )
                st.success("History loaded into Resume Scanner.")
            else:
                st.error("Selected history record does not contain valid resume data.")
    else:
        st.info("No resume scan history yet. Parse a resume to start building history.")

    if st.session_state.resume_data:
        resume = st.session_state.resume_data
        st.subheader(f"Resume Score: {resume.get('resume_score', 0)}%")
        st.write(f"Name: **{resume.get('name', 'Not detected')}**")
        if resume.get("profile_summary"):
            st.write(f"Summary: {resume.get('profile_summary')}")

        st.subheader("Resume Overview")
        overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
        overview_col1.metric("Experience", f"{resume.get('experience_years', 0)} years")
        overview_col2.metric("Skills", len(resume.get("skills", [])))
        overview_col3.metric("Education", len(resume.get("education", [])))
        overview_col4.metric("Keywords", len(resume.get("keywords", [])))

        experience_breakdown = resume.get("experience_breakdown", {})
        st.write("**Experience Estimation Details**")
        st.write(
            f"Confidence: **{experience_breakdown.get('confidence', 'Unknown')}** | "
            f"Date-range estimate: **{experience_breakdown.get('from_date_ranges_years', 0)} years** | "
            f"Explicit-claim estimate: **{experience_breakdown.get('from_explicit_claim_years', 0)} years**"
        )
        st.caption("Experience is estimated from date ranges and explicit claims detected in the resume.")
        evidence = experience_breakdown.get("evidence", [])
        if evidence:
            st.write("Evidence:")
            for item in evidence[:6]:
                st.write(f"- {item}")

        domain = resume.get("domain_analysis", {})
        if domain:
            st.subheader("Domain Employability Analysis")
            st.write(
                f"Strongest domain tendency: **{domain.get('strongest_domain', 'N/A')}**"
            )
            st.write(
                "Job probability in strongest domain: "
                f"**{domain.get('strongest_domain_probability', 0)}%**"
            )

            missing = domain.get("missing_skills_for_strongest_domain", [])
            st.write("**Missing Skills for Strongest Domain**")
            if missing:
                st.write(", ".join(missing))
            else:
                st.write("No major skill gaps detected.")

            st.write("**Domain-wise Probability**")
            domain_rows = []
            for item in domain.get("domain_assessments", []):
                domain_rows.append(
                    {
                        "Domain": item.get("domain"),
                        "Probability (%)": item.get("probability"),
                        "Readiness": item.get("readiness"),
                    }
                )
            if domain_rows:
                st.dataframe(domain_rows, use_container_width=True, hide_index=True)

        report_text = _build_resume_report(
            resume,
            resume.get("resume_score"),
            st.session_state.get("recommended_jobs") or [],
        )
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        st.download_button(
            label="Download Analyzed Report (.txt)",
            data=report_text,
            file_name=f"resume-analysis-report-{timestamp}.txt",
            mime="text/plain",
            use_container_width=False,
        )

        st.write("**Skills**")
        skills = resume.get("skills", [])
        if skills:
            st.write(", ".join(skills))
        else:
            st.write("No skill matches found.")

        st.write("**Education**")
        education = resume.get("education", [])
        if education:
            for item in education:
                st.write(f"- {item}")
        else:
            st.write("- Not detected")

        st.write("**Contact & Links**")
        contact = resume.get("contact", {})
        st.write(f"- Emails: {', '.join(contact.get('emails', [])) or 'Not found'}")
        st.write(f"- Phones: {', '.join(contact.get('phones', [])) or 'Not found'}")
        st.write(f"- LinkedIn: {contact.get('linkedin') or 'Not found'}")
        st.write(f"- GitHub: {contact.get('github') or 'Not found'}")

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Recent Roles**")
            roles = resume.get("recent_roles", [])
            if roles:
                for role in roles:
                    st.write(f"- {role}")
            else:
                st.write("- Not detected")

            st.write("**Projects**")
            projects = resume.get("projects", [])
            if projects:
                for project in projects:
                    st.write(f"- {project}")
            else:
                st.write("- Not detected")

        with c2:
            st.write("**Companies**")
            companies = resume.get("companies", [])
            if companies:
                for company in companies:
                    st.write(f"- {company}")
            else:
                st.write("- Not detected")

            st.write("**Certifications**")
            certifications = resume.get("certifications", [])
            if certifications:
                for cert in certifications:
                    st.write(f"- {cert}")
            else:
                st.write("- Not detected")

        st.write("**Achievements**")
        achievements = resume.get("achievements", [])
        if achievements:
            for achievement in achievements:
                st.write(f"- {achievement}")
        else:
            st.write("- Not detected")

        st.write("**Languages**")
        languages = resume.get("languages", [])
        st.write(", ".join(languages) if languages else "Not detected")

        recommended_jobs = st.session_state.get("recommended_jobs") or []
        if recommended_jobs:
            st.subheader("Jobs Matching This Resume")
            st.caption("Roles recommended based on your skills, experience, and strongest domain.")
            for job in recommended_jobs:
                with st.container(border=True):
                    st.write(
                        f"**{job.get('title')}** | {job.get('company')} | "
                        f"{job.get('location')} | {job.get('employment_type')}"
                    )
                    st.write(
                        f"Fit: **{job.get('fit_score')}% ({job.get('fit_label')})** | "
                        f"Domain: **{job.get('domain')}** | Experience: **{job.get('min_experience_years')}+ years**"
                    )
                    st.write(f"Salary: {job.get('salary_range')}")
                    if job.get("job_link"):
                        st.markdown(f"[Open Job Link]({job.get('job_link')})")
                    if job.get("job_link_fallback"):
                        st.markdown(f"[Fallback Search]({job.get('job_link_fallback')})")
                    st.write(
                        f"Coverage: **{job.get('required_coverage', 0)}% required** | "
                        f"**{job.get('preferred_coverage', 0)}% preferred**"
                    )
                    matched_required = job.get("matched_required_skills", [])
                    st.write(
                        "Matched required skills: "
                        + (", ".join(matched_required) if matched_required else "None")
                    )
                    reasons = job.get("reasons", [])
                    if reasons:
                        st.write("Why this matches:")
                        for reason in reasons:
                            st.write(f"- {reason}")

                    missing = job.get("missing_required_skills", [])
                    st.write(
                        "Missing required skills: "
                        + (", ".join(missing) if missing else "No major required skill gaps")
                    )


def _render_job_analyzer() -> None:
    st.header("Job Description Analyzer")
    st.caption("Analyze JD requirements and compute a candidate-job match percentage.")

    job_description = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste full job description...",
    )
    uploaded_resume = st.file_uploader(
        "Optional Resume Upload for Matching",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=False,
        key="job_match_resume_upload",
    )

    if st.button("Analyze Job & Match", type="primary"):
        if not job_description.strip():
            st.error("Please provide a job description.")
            return

        try:
            with st.spinner("Analyzing job description..."):
                job_analysis = analyze_job_description(job_description)
            st.session_state.job_analysis = job_analysis

            resume_payload = None
            if uploaded_resume is not None:
                with st.spinner("Parsing uploaded resume for match..."):
                    resume_payload = _parse_uploaded_resume(uploaded_resume)
            elif st.session_state.resume_data:
                resume_payload = st.session_state.resume_data

            if resume_payload is not None:
                with st.spinner("Calculating match score..."):
                    match = calculate_job_match(resume_payload, job_analysis)
                st.session_state.match_data = match
                st.session_state.job_match = match.get("match_score")
                st.success("Job analysis and match score computed.")
            else:
                st.warning("Job analyzed. Upload or parse a resume to get match score.")

            save_job_analysis(
                source="streamlit",
                job_description=job_description.strip(),
                analysis=job_analysis,
                match_result=st.session_state.match_data if resume_payload is not None else None,
            )
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.job_analysis:
        jd = st.session_state.job_analysis
        st.subheader("Job Insights")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Role", jd.get("role_title", "N/A"))
        c2.metric("Role Family", jd.get("role_family", "General"))
        c3.metric("Seniority", jd.get("seniority", "mid").title())
        c4.metric("JD Quality", f"{jd.get('quality_score', 0)}%")

        salary = jd.get("salary_range") or {}
        min_salary = salary.get("min")
        max_salary = salary.get("max")
        if min_salary or max_salary:
            salary_text = f"${min_salary:,.0f} - ${max_salary:,.0f}" if min_salary and max_salary else "Partially specified"
        else:
            salary_text = "Not specified"

        st.write(
            f"Compensation: **{salary_text}** | Hiring type: **{jd.get('hiring_type', 'N/A')}** | "
            f"Remote possible: **{'Yes' if jd.get('remote_possible') else 'No'}** | "
            f"Experience: **{jd.get('required_experience_years', 0)}+ years**"
        )

        notes = jd.get("quality_notes", [])
        if notes:
            st.warning("JD improvement notes:\n\n" + "\n".join(f"- {note}" for note in notes))

        left, right = st.columns(2)
        with left:
            st.write("**Required Skills**")
            st.write(", ".join(jd.get("required_skills", jd.get("job_skills", []))) or "Not specified")
        with right:
            st.write("**Preferred Skills**")
            st.write(", ".join(jd.get("preferred_skills", [])) or "Not explicitly listed")

    if st.session_state.match_data:
        match = st.session_state.match_data
        st.subheader(f"Match Score: {match.get('match_score', 0)}%")
        st.caption(f"Fit verdict: {match.get('fit_label', 'Match result')}")

        s1, s2, s3 = st.columns(3)
        s1.metric("Required Skill", f"{match.get('required_skill_score', match.get('skill_score', 0))}%")
        s2.metric("Preferred Skill", f"{match.get('preferred_skill_score', match.get('skill_score', 0))}%")
        s3.metric("Domain Alignment", f"{match.get('domain_alignment_score', 0)}%")
        s4, s5 = st.columns(2)
        s4.metric("Keyword Score", f"{match.get('keyword_score', 0)}%")
        s5.metric("Experience Score", f"{match.get('experience_score', 0)}%")

        st.write("**Critical Skill Gaps**")
        critical = match.get("critical_gaps", [])
        st.write(", ".join(critical) if critical else "No critical gaps.")

        st.write("**Required Skill Matches**")
        overlap_required = match.get("required_overlapping_skills", match.get("overlapping_skills", []))
        st.write(", ".join(overlap_required) if overlap_required else "None")

        st.write("**Next Steps**")
        next_steps = match.get("next_steps", [])
        if next_steps:
            for step in next_steps:
                st.write(f"- {step}")
        else:
            st.write("- Tailor resume to this role before applying.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Strengths**")
            strengths = match.get("strengths", [])
            if strengths:
                for item in strengths:
                    st.write(f"- {item}")
            else:
                st.write("- Limited strong signals so far.")
        with col_b:
            st.write("**Recommendations**")
            recs = match.get("recommendations", [])
            if recs:
                for rec in recs:
                    st.write(f"- {rec}")
            else:
                st.write("- No immediate recommendation.")


def _render_fake_job_detection() -> None:
    st.header("Fake Job Detection")
    st.caption("Evaluate job posts for scam probability and red flags using ML.")

    job_url = st.text_input("Job URL", placeholder="https://example.com/jobs/role")
    job_text = st.text_area(
        "Fallback Job Text (optional)",
        height=180,
        placeholder="Use this if the URL is blocked or unavailable.",
    )

    if st.button("Detect Scam Probability", type="primary"):
        try:
            with st.spinner("Running fake job detection model..."):
                detector = _load_detector()
                result = detector.analyze(
                    job_url=job_url.strip(),
                    fallback_text=job_text.strip(),
                )
            st.session_state.fake_job_data = result
            st.session_state.scam_risk = result.get("scam_probability")
            save_fake_job_check(
                source="streamlit",
                job_url=job_url.strip() or None,
                result=result,
            )
            st.success("Fake job analysis completed.")
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.fake_job_data:
        result = st.session_state.fake_job_data
        st.subheader(
            f"Scam Probability: {round(result.get('scam_probability', 0), 2)}% "
            f"({result.get('risk_level', 'N/A')} Risk)"
        )
        st.write(result.get("explanation", ""))
        st.progress(min(100, max(0, int(round(result.get("scam_probability", 0))))), text="Overall scam risk")

        m1, m2, m3 = st.columns(3)
        m1.metric("ML Score", f"{result.get('ml_probability', result.get('scam_probability', 0))}%")
        m2.metric("Rule Score", f"{result.get('rule_risk_score', 0)}%")
        m3.metric("Confidence", f"{int((result.get('confidence', 0.5)) * 100)}%")

        warning = result.get("fetch_warning")
        if warning:
            st.warning(warning)

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Red Flags**")
            flags = result.get("red_flags", [])
            if flags:
                for flag in flags:
                    st.write(f"- {flag}")
            else:
                st.write("- No major red flags found.")

        with col2:
            st.write("**Trust Signals**")
            safe_signals = result.get("safe_signals", [])
            if safe_signals:
                for signal in safe_signals:
                    st.write(f"- {signal}")
            else:
                st.write("- No strong trust signals detected.")

        drivers = result.get("risk_drivers", [])
        if drivers:
            st.write("**Top Risk Drivers**")
            st.dataframe(drivers, use_container_width=True, hide_index=True)

        st.write("**Feature Snapshot**")
        st.code(
            json.dumps(result.get("feature_snapshot", {}), indent=2),
            language="json",
        )


def _render_resume_ai() -> None:
    st.header("Resume AI")
    st.caption(
        "Create a resume from scratch or from an existing resume, then tailor it to a target job description."
    )

    source_label = st.radio(
        "Resume Source",
        options=["Create New Resume", "Use Existing Resume"],
        horizontal=True,
    )
    source_mode = "scratch" if source_label == "Create New Resume" else "existing"

    scratch_profile: dict[str, Any] = {}
    if source_mode == "scratch":
        st.subheader("Step 1: Create Resume From Scratch")
        col1, col2 = st.columns(2)
        with col1:
            scratch_profile["name"] = st.text_input("Full Name", key="resume_ai_name")
            scratch_profile["email"] = st.text_input("Email", key="resume_ai_email")
            scratch_profile["phone"] = st.text_input("Phone", key="resume_ai_phone")
            scratch_profile["location"] = st.text_input("Location", key="resume_ai_location")
            scratch_profile["linkedin"] = st.text_input("LinkedIn URL", key="resume_ai_linkedin")
            scratch_profile["github"] = st.text_input("GitHub URL", key="resume_ai_github")
            scratch_profile["experience_years"] = st.text_input(
                "Experience (years)", key="resume_ai_experience_years"
            )

        with col2:
            scratch_profile["skills"] = st.text_area(
                "Skills (comma separated)",
                key="resume_ai_skills",
                height=100,
            )
            scratch_profile["education"] = st.text_area(
                "Education (one line per entry)",
                key="resume_ai_education",
                height=100,
            )
            scratch_profile["projects"] = st.text_area(
                "Projects (one line per entry)",
                key="resume_ai_projects",
                height=100,
            )
            scratch_profile["certifications"] = st.text_area(
                "Certifications (one line per entry)",
                key="resume_ai_certs",
                height=100,
            )
            scratch_profile["achievements"] = st.text_area(
                "Achievements (one line per entry)",
                key="resume_ai_achievements",
                height=100,
            )

        scratch_profile["summary"] = st.text_area(
            "Professional Summary",
            key="resume_ai_summary",
            height=120,
        )
        scratch_profile["experience_highlights"] = st.text_area(
            "Experience Highlights (one line per bullet)",
            key="resume_ai_experience_highlights",
            height=140,
        )
    else:
        st.subheader("Step 1: Use Existing Resume")
        uploaded_resume = st.file_uploader(
            "Upload Existing Resume (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
            key="resume_ai_existing_resume_upload",
        )
        if st.button("Parse Existing Resume", key="resume_ai_parse_existing_btn"):
            try:
                parsed = _parse_uploaded_resume(uploaded_resume)
                st.session_state.resume_ai_parsed_resume = parsed
                st.success("Existing resume parsed successfully.")
            except Exception as exc:
                st.error(str(exc))

        if st.session_state.resume_ai_parsed_resume:
            parsed = st.session_state.resume_ai_parsed_resume
            st.info(
                f"Parsed: {parsed.get('name', 'Not detected')} | "
                f"Skills: {len(parsed.get('skills', []))} | "
                f"Experience: {parsed.get('experience_years', 0)} years"
            )

    st.subheader("Step 2: Target Job Description")
    job_description = st.text_area(
        "Paste target job description",
        key="resume_ai_job_description",
        height=220,
    )

    if st.button("Generate Resume AI Output", type="primary", key="resume_ai_generate_btn"):
        try:
            if not job_description.strip():
                raise ValueError("Please provide a target job description.")

            parsed_resume = None
            if source_mode == "existing":
                parsed_resume = st.session_state.resume_ai_parsed_resume
                if parsed_resume is None:
                    raise ValueError("Please parse an existing resume first.")

            with st.spinner("Generating tailored resume assets..."):
                result = generate_resume_ai_assets(
                    source_mode=source_mode,
                    job_description=job_description.strip(),
                    scratch_profile=scratch_profile if source_mode == "scratch" else None,
                    resume_parsed=parsed_resume if source_mode == "existing" else None,
                )

            st.session_state.resume_ai_result = result
            save_resume_ai_generation(
                source="streamlit",
                source_mode=source_mode,
                result=result,
            )
            st.success("Resume AI assets generated successfully.")
        except Exception as exc:
            st.error(str(exc))

    result = st.session_state.resume_ai_result
    if result:
        st.subheader("Generated Output")
        target = result.get("job_target", {})
        st.write(f"Target Role: **{target.get('role_title', 'N/A')}**")
        st.write(f"Role Family: **{target.get('role_family', 'N/A')}**")
        st.write(
            "Matched required skills: "
            + (", ".join(target.get("matched_required_skills", [])) or "None detected")
        )
        st.write(
            "Missing required skills: "
            + (", ".join(target.get("missing_required_skills", [])) or "No major gaps")
        )

        st.download_button(
            label="Download LaTeX (.tex)",
            data=result.get("latex_code", ""),
            file_name=result.get("latex_filename", "tailored-resume.tex"),
            mime="text/plain",
            key="resume_ai_download_tex",
        )

        docx_bytes = base64.b64decode(result.get("resume_docx_base64", ""))
        st.download_button(
            label="Download Resume (.docx)",
            data=docx_bytes,
            file_name=result.get("resume_filename", "tailored-resume.docx"),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="resume_ai_download_docx",
        )

        st.download_button(
            label="Download Resume Text (.txt)",
            data=result.get("resume_text", ""),
            file_name="resume-preview.txt",
            mime="text/plain",
            key="resume_ai_download_text",
        )

        st.link_button("Open in Overleaf", result.get("overleaf_url", "https://www.overleaf.com/docs"))
        st.caption(result.get("overleaf_hint", "Paste LaTeX code in a new Overleaf project."))

        st.write("Generated LaTeX Code")
        st.code(result.get("latex_code", ""), language="latex")


def main() -> None:
    st.set_page_config(
        page_title="AI Recruitment Intelligence Platform",
        page_icon=":mag:",
        layout="wide",
    )
    _initialize_state()
    db_ready = _init_database()

    st.title("AI Recruitment Intelligence Platform")
    st.caption(
        "Streamlit edition: parse resumes, analyze job fit, and detect fake job risk in one workspace."
    )
    st.sidebar.caption(f"Database: {'connected' if db_ready else 'unavailable'}")

    page = st.sidebar.radio(
        "Navigation",
        options=[
            "Resume Scanner",
            "Resume AI",
            "Job Description Analyzer",
            "Fake Job Detection",
        ],
    )

    if page == "Resume Scanner":
        _render_resume_scanner()
    elif page == "Resume AI":
        _render_resume_ai()
    elif page == "Job Description Analyzer":
        _render_job_analyzer()
    else:
        _render_fake_job_detection()


if __name__ == "__main__":
    main()
