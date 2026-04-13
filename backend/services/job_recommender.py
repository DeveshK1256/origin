from __future__ import annotations

from math import ceil
from typing import Any
from urllib.parse import urlencode

from services.job_data_provider import fetch_job_posts

LOCAL_JOB_CATALOG: list[dict[str, Any]] = [
    {
        "job_id": "L-1001",
        "title": "Backend Engineer (Python)",
        "company": "Local Reference Role",
        "job_link": "",
        "domain": "Backend Engineering",
        "employment_type": "Full-time",
        "location": "Remote",
        "salary_range": "$120,000 - $155,000",
        "min_experience_years": 3,
        "required_skills": ["Python", "Flask", "FastAPI", "SQL", "Docker", "REST API"],
        "preferred_skills": ["AWS", "CI/CD", "Microservices"],
        "source": "local",
    },
    {
        "job_id": "L-1002",
        "title": "Senior Platform Engineer",
        "company": "Local Reference Role",
        "job_link": "",
        "domain": "DevOps and Cloud",
        "employment_type": "Full-time",
        "location": "Hybrid",
        "salary_range": "$140,000 - $180,000",
        "min_experience_years": 5,
        "required_skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform"],
        "preferred_skills": ["Jenkins", "GitHub Actions", "Microservices"],
        "source": "local",
    },
    {
        "job_id": "L-1003",
        "title": "Data Analyst",
        "company": "Local Reference Role",
        "job_link": "",
        "domain": "Data Analytics and BI",
        "employment_type": "Full-time",
        "location": "On-site",
        "salary_range": "$85,000 - $110,000",
        "min_experience_years": 2,
        "required_skills": ["SQL", "Python", "Power BI", "Tableau", "Data Analysis"],
        "preferred_skills": ["Excel", "Pandas", "NumPy"],
        "source": "local",
    },
]

DOMAIN_QUERY_HINTS = {
    "backend engineering": "Backend Engineer",
    "frontend engineering": "Frontend Engineer",
    "devops and cloud": "DevOps Engineer",
    "data analytics and bi": "Data Analyst",
    "data science and ml": "Machine Learning Engineer",
    "general": "Software Engineer",
}


def _score_label(score: int) -> str:
    if score >= 78:
        return "Highly Recommended"
    if score >= 60:
        return "Good Match"
    if score >= 45:
        return "Potential Match"
    return "Low Match"


def _experience_fit(candidate_years: int, required_years: int) -> float:
    if required_years <= 0:
        return 1.0
    ratio = candidate_years / required_years
    return max(0.0, min(1.0, ratio))


def _build_job_link(job: dict[str, Any]) -> str:
    existing_link = str(job.get("job_link") or "").strip()
    if existing_link.startswith("http"):
        return existing_link

    title = str(job.get("title", "")).strip() or "Software Engineer"
    location_label = str(job.get("location", "")).strip().lower()
    required_skills = [str(skill).strip() for skill in job.get("required_skills", []) if skill]

    query_parts = [title, "jobs"]
    if location_label == "remote":
        query_parts.append("remote")
    elif location_label == "hybrid":
        query_parts.append("hybrid")

    query_parts.extend(required_skills[:2])
    query = " ".join(part for part in query_parts if part).strip()

    params: dict[str, str] = {"q": query, "l": "United States"}
    return f"https://www.indeed.com/jobs?{urlencode(params)}"


def _build_fallback_job_link(job: dict[str, Any]) -> str:
    title = str(job.get("title", "")).strip() or "Software Engineer"
    params = {"q": f"{title} jobs United States"}
    return f"https://www.google.com/search?{urlencode(params)}"


def _build_search_query(resume_data: dict[str, Any]) -> str:
    strongest_domain = str(
        ((resume_data.get("domain_analysis") or {}).get("strongest_domain") or "")
    ).strip()
    top_skills = [str(skill).strip() for skill in resume_data.get("skills", []) if skill][:4]

    query_parts = []
    if strongest_domain:
        query_parts.append(strongest_domain)
    if top_skills:
        query_parts.append(" ".join(top_skills))
    if not query_parts:
        query_parts.append("software engineer")

    return " ".join(query_parts).strip()


def _build_search_queries(resume_data: dict[str, Any]) -> list[str]:
    strongest_domain = str(
        ((resume_data.get("domain_analysis") or {}).get("strongest_domain") or "")
    ).strip()
    strongest_domain_key = strongest_domain.lower()
    domain_hint = DOMAIN_QUERY_HINTS.get(strongest_domain_key, "")

    top_skills = [str(skill).strip() for skill in resume_data.get("skills", []) if skill][:6]
    queries: list[str] = []

    primary_query = _build_search_query(resume_data)
    if primary_query:
        queries.append(primary_query)

    if strongest_domain and top_skills:
        queries.append(f"{strongest_domain} {' '.join(top_skills[:3])}")
    if domain_hint and top_skills:
        queries.append(f"{domain_hint} {' '.join(top_skills[:3])}")
        queries.append(f"{domain_hint} remote")
    if top_skills:
        queries.append(f"{' '.join(top_skills[:2])} jobs")
        queries.append(f"{top_skills[0]} jobs")
    if domain_hint:
        queries.append(domain_hint)
    queries.append("Software Engineer")

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = " ".join(query.split()).strip()
        if len(normalized) < 3:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)

    return deduped[:8]


def _job_catalog_for_resume(resume_data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    target_dynamic_count = max(20, limit * 4)
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for query in _build_search_queries(resume_data):
        dynamic_jobs = fetch_job_posts(query=query, limit=target_dynamic_count)
        for job in dynamic_jobs:
            unique_key = str(job.get("job_id") or job.get("job_link") or "").strip().lower()
            if not unique_key:
                unique_key = str(job.get("title") or "").strip().lower()
            if not unique_key or unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            collected.append(job)

        if len(collected) >= target_dynamic_count:
            break

    if collected:
        return collected

    return LOCAL_JOB_CATALOG


def recommend_jobs_for_resume(resume_data: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    resume_skills = {str(skill).lower() for skill in resume_data.get("skills", [])}
    candidate_years = int(resume_data.get("experience_years", 0))
    strongest_domain = (
        ((resume_data.get("domain_analysis") or {}).get("strongest_domain") or "").lower()
    )

    recommendations: list[dict[str, Any]] = []
    for job in _job_catalog_for_resume(resume_data, limit=limit):
        required = [str(skill).lower() for skill in job.get("required_skills", []) if skill]
        preferred = [str(skill).lower() for skill in job.get("preferred_skills", []) if skill]

        required_overlap = [skill for skill in required if skill in resume_skills]
        required_missing = [skill for skill in required if skill not in resume_skills]
        preferred_overlap = [skill for skill in preferred if skill in resume_skills]

        required_score = len(required_overlap) / max(1, len(required))
        preferred_score = len(preferred_overlap) / max(1, len(preferred)) if preferred else required_score
        experience_score = _experience_fit(candidate_years, int(job.get("min_experience_years", 0)))
        domain_score = 1.0 if strongest_domain and strongest_domain == str(job.get("domain", "")).lower() else 0.65

        fit = (
            (required_score * 0.55)
            + (preferred_score * 0.15)
            + (experience_score * 0.20)
            + (domain_score * 0.10)
        )
        fit_score = int(round(max(0.0, min(100.0, fit * 100))))
        minimum_required_matches = max(1, ceil(len(required) * 0.4))
        meets_requirements = (
            len(required_overlap) >= minimum_required_matches and experience_score >= 0.4 and fit_score >= 45
        )

        reasons: list[str] = []
        if required_overlap:
            reasons.append(f"Matched {len(required_overlap)} required skills.")
        if experience_score >= 1.0:
            reasons.append("Experience level meets or exceeds role expectation.")
        if domain_score >= 0.95:
            reasons.append("Role aligns with strongest resume domain tendency.")
        if not reasons:
            reasons.append("Some baseline overlap exists; profile may fit with customization.")

        recommendations.append(
            {
                "job_id": str(job.get("job_id") or job.get("job_link") or job.get("title")),
                "title": str(job.get("title") or "Role"),
                "company": str(job.get("company") or "Unknown Company"),
                "job_link": _build_job_link(job),
                "job_link_fallback": _build_fallback_job_link(job),
                "domain": str(job.get("domain") or "General"),
                "employment_type": str(job.get("employment_type") or "Full-time"),
                "location": str(job.get("location") or "United States"),
                "salary_range": str(job.get("salary_range") or "Not specified"),
                "min_experience_years": int(job.get("min_experience_years") or 0),
                "fit_score": fit_score,
                "fit_label": _score_label(fit_score),
                "matched_required_skills": [
                    skill
                    for skill in job.get("required_skills", [])
                    if str(skill).lower() in resume_skills
                ],
                "missing_required_skills": [
                    skill
                    for skill in job.get("required_skills", [])
                    if str(skill).lower() not in resume_skills
                ],
                "required_coverage": int(round(required_score * 100)),
                "preferred_coverage": int(round(preferred_score * 100)),
                "meets_requirements": meets_requirements,
                "reasons": reasons,
                "source": str(job.get("source") or "local"),
            }
        )

    recommendations.sort(key=lambda item: item["fit_score"], reverse=True)
    qualified = [item for item in recommendations if item["meets_requirements"]]
    if qualified:
        return qualified[:limit]

    fallback = [
        item
        for item in recommendations
        if item["fit_score"] >= 45 and len(item["matched_required_skills"]) >= 1
    ]
    if fallback:
        return fallback[:limit]

    return recommendations[: max(1, min(3, limit))]
