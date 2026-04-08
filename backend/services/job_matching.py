from __future__ import annotations

import re
from typing import Any

from services.nlp_utils import (
    extract_keywords,
    extract_required_experience,
    extract_skills,
    normalize_whitespace,
)

ROLE_FAMILY_KEYWORDS = {
    "Backend Engineering": {"backend", "api", "flask", "django", "fastapi", "node", "microservice", "golang"},
    "Frontend Engineering": {"frontend", "react", "angular", "vue", "next.js", "ui", "ux", "typescript"},
    "Data Science and ML": {"machine learning", "ml", "nlp", "model", "tensorflow", "pytorch", "data scientist"},
    "DevOps and Cloud": {"devops", "kubernetes", "terraform", "aws", "azure", "gcp", "ci/cd", "infrastructure"},
    "Data Analytics and BI": {"analyst", "power bi", "tableau", "reporting", "dashboard", "sql", "kpi"},
    "Product and Project": {"product manager", "project manager", "roadmap", "stakeholder", "delivery"},
}


def _extract_salary_range(text: str) -> tuple[int | None, int | None]:
    salary_tokens = re.findall(r"\$?\s*(\d{2,3}(?:,\d{3})+|\d{2,3}k)\b", text.lower())
    values: list[int] = []
    for token in salary_tokens:
        cleaned = token.replace(",", "").strip()
        if cleaned.endswith("k"):
            try:
                values.append(int(float(cleaned[:-1]) * 1000))
            except ValueError:
                continue
        else:
            try:
                values.append(int(cleaned))
            except ValueError:
                continue

    if not values:
        return None, None
    return min(values), max(values)


def _infer_seniority(text: str) -> str:
    lowered = text.lower()
    if any(key in lowered for key in ("principal", "staff", "architect")):
        return "principal"
    if any(key in lowered for key in ("senior", "lead", "sr.")):
        return "senior"
    if any(key in lowered for key in ("intern", "trainee")):
        return "intern"
    if any(key in lowered for key in ("junior", "entry level", "fresher")):
        return "junior"
    return "mid"


def _extract_role_title(text: str) -> str:
    patterns = [
        re.compile(r"(?:job title|role)\s*[:\-]\s*([^\n]{3,80})", re.IGNORECASE),
        re.compile(r"we are hiring (?:for )?(?:a |an )?([^\n.,]{3,80})", re.IGNORECASE),
        re.compile(r"(?:hiring|looking for)\s+(?:a |an )?([^\n.,]{3,80})", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip().title()

    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first_line and len(first_line) <= 80:
        return first_line.title()
    return "Not specified"


def _infer_role_family(job_description: str, job_skills: list[str]) -> str:
    lowered = job_description.lower()
    skill_lowered = {skill.lower() for skill in job_skills}
    best_family = "General"
    best_score = 0

    for family, keywords in ROLE_FAMILY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in lowered:
                score += 2
            if keyword in skill_lowered:
                score += 3
        if score > best_score:
            best_family = family
            best_score = score

    return best_family


def _split_required_and_preferred_skills(text: str, extracted_skills: list[str]) -> tuple[list[str], list[str]]:
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    required_lines = [
        line
        for line in lines
        if any(token in line for token in ("must", "required", "qualification", "requirements", "mandatory"))
    ]
    preferred_lines = [
        line for line in lines if any(token in line for token in ("preferred", "nice to have", "plus", "good to have"))
    ]

    required = []
    preferred = []
    for skill in extracted_skills:
        lowered_skill = skill.lower()
        if any(lowered_skill in line for line in preferred_lines):
            preferred.append(skill)
        elif any(lowered_skill in line for line in required_lines):
            required.append(skill)

    remaining = [skill for skill in extracted_skills if skill not in required and skill not in preferred]
    required.extend(remaining)

    # Keep deterministic order and remove duplicates
    required = list(dict.fromkeys(required))
    preferred = [skill for skill in dict.fromkeys(preferred) if skill not in required]
    return required, preferred


def _jd_quality_score(
    description: str,
    required_skills: list[str],
    has_salary: bool,
    has_experience: bool,
    has_company_signal: bool,
) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    word_count = len(description.split())

    if word_count >= 180:
        score += 25
    elif word_count >= 110:
        score += 16
        notes.append("Add more detail on ownership, team scope, and outcomes.")
    else:
        score += 8
        notes.append("Job description is brief; add richer context and responsibilities.")

    if len(required_skills) >= 6:
        score += 25
    elif len(required_skills) >= 3:
        score += 16
    else:
        score += 8
        notes.append("Skills section appears thin; define concrete technical requirements.")

    if has_experience:
        score += 20
    else:
        notes.append("Specify expected years of experience.")

    if has_salary:
        score += 20
    else:
        notes.append("Compensation range is missing.")

    if has_company_signal:
        score += 10
    else:
        notes.append("Add company details to build trust with candidates.")

    return min(100, score), notes


def analyze_job_description(job_description: str) -> dict[str, Any]:
    cleaned = normalize_whitespace(job_description)
    if not cleaned:
        raise ValueError("Job description is empty.")

    required_experience = extract_required_experience(cleaned)
    job_skills = extract_skills(cleaned, limit=50)
    required_skills, preferred_skills = _split_required_and_preferred_skills(cleaned, job_skills)
    job_keywords = extract_keywords(cleaned, top_n=25)

    lowered = cleaned.lower()
    hiring_type = "full-time"
    if "contract" in lowered:
        hiring_type = "contract"
    elif "intern" in lowered:
        hiring_type = "internship"
    elif "part-time" in lowered:
        hiring_type = "part-time"

    role_title = _extract_role_title(cleaned)
    role_family = _infer_role_family(cleaned, job_skills)
    seniority = _infer_seniority(cleaned)
    salary_min, salary_max = _extract_salary_range(cleaned)
    has_company_signal = bool(
        re.search(r"\b(inc|llc|ltd|corp|company|organization|about us|headquartered|founded)\b", lowered)
    )
    quality_score, quality_notes = _jd_quality_score(
        description=cleaned,
        required_skills=required_skills,
        has_salary=salary_min is not None,
        has_experience=required_experience > 0,
        has_company_signal=has_company_signal,
    )

    return {
        "role_title": role_title,
        "role_family": role_family,
        "seniority": seniority,
        "required_experience_years": required_experience,
        "job_skills": job_skills,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "job_keywords": job_keywords,
        "hiring_type": hiring_type,
        "remote_possible": "remote" in lowered or "work from home" in lowered,
        "salary_range": {
            "min": salary_min,
            "max": salary_max,
        },
        "quality_score": quality_score,
        "quality_notes": quality_notes,
        "description_length": len(cleaned),
    }


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    intersection = left.intersection(right)
    union = left.union(right)
    return len(intersection) / len(union)


def _experience_score(candidate_years: int, required_years: int) -> float:
    if required_years <= 0:
        return 85.0
    ratio = candidate_years / required_years if required_years else 0
    if ratio >= 1.5:
        return 100.0
    return max(0.0, min(100.0, ratio * 100))


def _label_from_score(score: int) -> str:
    if score >= 80:
        return "Excellent Fit"
    if score >= 65:
        return "Strong Fit"
    if score >= 50:
        return "Moderate Fit"
    return "Low Fit"


def calculate_job_match(resume_data: dict, job_data: dict) -> dict[str, Any]:
    resume_skills = {skill.lower() for skill in resume_data.get("skills", [])}
    job_skills = {skill.lower() for skill in job_data.get("job_skills", [])}
    required_skills = {skill.lower() for skill in job_data.get("required_skills", [])}
    preferred_skills = {skill.lower() for skill in job_data.get("preferred_skills", [])}

    if not required_skills and job_skills:
        required_skills = set(job_skills)

    resume_keywords = {word.lower() for word in resume_data.get("keywords", [])}
    job_keywords = {word.lower() for word in job_data.get("job_keywords", [])}

    overlapping_skills = sorted(skill for skill in resume_skills.intersection(job_skills))
    missing_skills = sorted(skill for skill in job_skills.difference(resume_skills))
    required_overlap = sorted(skill for skill in resume_skills.intersection(required_skills))
    required_missing = sorted(skill for skill in required_skills.difference(resume_skills))
    preferred_overlap = sorted(skill for skill in resume_skills.intersection(preferred_skills))
    preferred_missing = sorted(skill for skill in preferred_skills.difference(resume_skills))

    if required_skills:
        required_skill_score = (len(required_overlap) / len(required_skills)) * 100
    else:
        required_skill_score = 75.0

    if preferred_skills:
        preferred_skill_score = (len(preferred_overlap) / len(preferred_skills)) * 100
    else:
        preferred_skill_score = required_skill_score

    keyword_score = _jaccard_similarity(resume_keywords, job_keywords) * 100

    candidate_experience = int(resume_data.get("experience_years", 0))
    required_experience = int(job_data.get("required_experience_years", 0))
    experience_score = _experience_score(candidate_experience, required_experience)

    resume_domain = (
        (resume_data.get("domain_analysis") or {}).get("strongest_domain", "").lower()
    )
    role_family = (job_data.get("role_family") or "").lower()
    domain_alignment_score = 85.0 if resume_domain and resume_domain == role_family else 62.0
    if not role_family or role_family == "general":
        domain_alignment_score = 70.0

    weighted_score = (
        (required_skill_score * 0.45)
        + (preferred_skill_score * 0.15)
        + (keyword_score * 0.15)
        + (experience_score * 0.15)
        + (domain_alignment_score * 0.10)
    )
    match_score = int(round(max(0.0, min(100.0, weighted_score))))

    strengths = []
    if required_skill_score >= 75:
        strengths.append("Strong overlap with required skills.")
    if preferred_skill_score >= 50:
        strengths.append("Good coverage of preferred stack and tooling.")
    if experience_score >= 90:
        strengths.append("Experience aligns well with the expected seniority.")
    if keyword_score >= 35:
        strengths.append("Resume language is aligned with job description terminology.")
    if domain_alignment_score >= 80:
        strengths.append("Candidate domain tendency aligns well with this role family.")

    recommendations = []
    if required_missing:
        recommendations.append("Prioritize missing required skills with project evidence.")
    if preferred_missing:
        recommendations.append("Improve profile with preferred tools to boost competitiveness.")
    if keyword_score < 30:
        recommendations.append("Tailor resume wording to match the target job description.")
    if required_experience and candidate_experience < required_experience:
        recommendations.append("Highlight leadership, ownership, and measurable outcomes.")
    if not recommendations:
        recommendations.append("Profile is well aligned. Focus on quantified impact in experience bullets.")

    critical_gaps = required_missing[:5]
    next_steps = []
    if critical_gaps:
        next_steps.append("Address at least 2 critical skill gaps before applying.")
    if match_score < 65:
        next_steps.append("Rewrite summary and projects to mirror core job requirements.")
    if match_score >= 65:
        next_steps.append("Proceed to apply with role-focused resume customization.")

    return {
        "match_score": match_score,
        "fit_label": _label_from_score(match_score),
        "skill_score": round(required_skill_score, 2),
        "required_skill_score": round(required_skill_score, 2),
        "preferred_skill_score": round(preferred_skill_score, 2),
        "keyword_score": round(keyword_score, 2),
        "experience_score": round(experience_score, 2),
        "domain_alignment_score": round(domain_alignment_score, 2),
        "required_overlapping_skills": required_overlap,
        "required_missing_skills": required_missing,
        "preferred_overlapping_skills": preferred_overlap,
        "preferred_missing_skills": preferred_missing,
        "critical_gaps": critical_gaps,
        "overlapping_skills": overlapping_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "recommendations": recommendations,
        "next_steps": next_steps,
    }
