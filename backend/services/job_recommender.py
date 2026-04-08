from __future__ import annotations

from math import ceil
from typing import Any
from urllib.parse import urlencode

JOB_CATALOG: list[dict[str, Any]] = [
    {
        "job_id": "J-1001",
        "title": "Backend Engineer (Python)",
        "company": "Northwind Technologies",
        "job_link": "https://careers.northwindtech.com/jobs/J-1001",
        "domain": "Backend Engineering",
        "employment_type": "Full-time",
        "location": "Remote",
        "salary_range": "$120,000 - $155,000",
        "min_experience_years": 3,
        "required_skills": ["Python", "Flask", "FastAPI", "SQL", "Docker", "REST API"],
        "preferred_skills": ["AWS", "CI/CD", "Microservices"],
    },
    {
        "job_id": "J-1002",
        "title": "Senior Platform Engineer",
        "company": "Delta Systems Inc",
        "job_link": "https://careers.deltasystemsinc.com/jobs/J-1002",
        "domain": "DevOps and Cloud",
        "employment_type": "Full-time",
        "location": "Hybrid",
        "salary_range": "$140,000 - $180,000",
        "min_experience_years": 5,
        "required_skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform"],
        "preferred_skills": ["Jenkins", "GitHub Actions", "Microservices"],
    },
    {
        "job_id": "J-1003",
        "title": "Data Analyst",
        "company": "Apex Business Labs",
        "job_link": "https://careers.apexbusinesslabs.com/jobs/J-1003",
        "domain": "Data Analytics and BI",
        "employment_type": "Full-time",
        "location": "On-site",
        "salary_range": "$85,000 - $110,000",
        "min_experience_years": 2,
        "required_skills": ["SQL", "Python", "Power BI", "Tableau", "Data Analysis"],
        "preferred_skills": ["Excel", "Pandas", "NumPy"],
    },
    {
        "job_id": "J-1004",
        "title": "Machine Learning Engineer",
        "company": "Nimbus AI",
        "job_link": "https://careers.nimbusai.com/jobs/J-1004",
        "domain": "Data Science and ML",
        "employment_type": "Full-time",
        "location": "Remote",
        "salary_range": "$130,000 - $170,000",
        "min_experience_years": 3,
        "required_skills": ["Python", "Machine Learning", "Scikit-learn", "NLP", "SQL"],
        "preferred_skills": ["TensorFlow", "PyTorch", "Deep Learning"],
    },
    {
        "job_id": "J-1005",
        "title": "Frontend Engineer (React)",
        "company": "Orbit Commerce",
        "job_link": "https://careers.orbitcommerce.com/jobs/J-1005",
        "domain": "Frontend Engineering",
        "employment_type": "Full-time",
        "location": "Hybrid",
        "salary_range": "$105,000 - $140,000",
        "min_experience_years": 2,
        "required_skills": ["React", "JavaScript", "TypeScript", "HTML", "CSS"],
        "preferred_skills": ["Next.js", "Tailwind", "Node.js"],
    },
    {
        "job_id": "J-1006",
        "title": "Cloud Support Engineer",
        "company": "Brightline Cloud",
        "job_link": "https://careers.brightlinecloud.com/jobs/J-1006",
        "domain": "DevOps and Cloud",
        "employment_type": "Full-time",
        "location": "Remote",
        "salary_range": "$95,000 - $125,000",
        "min_experience_years": 2,
        "required_skills": ["AWS", "Linux", "Docker", "SQL"],
        "preferred_skills": ["Terraform", "Kubernetes", "CI/CD"],
    },
    {
        "job_id": "J-1007",
        "title": "Backend API Developer",
        "company": "Vertex Labs",
        "job_link": "https://careers.vertexlabs.com/jobs/J-1007",
        "domain": "Backend Engineering",
        "employment_type": "Contract",
        "location": "Remote",
        "salary_range": "$55/hr - $80/hr",
        "min_experience_years": 2,
        "required_skills": ["Python", "REST API", "FastAPI", "SQL"],
        "preferred_skills": ["Docker", "PostgreSQL", "AWS"],
    },
    {
        "job_id": "J-1008",
        "title": "BI Reporting Analyst",
        "company": "Summit Insights",
        "job_link": "https://careers.summitinsights.com/jobs/J-1008",
        "domain": "Data Analytics and BI",
        "employment_type": "Full-time",
        "location": "Hybrid",
        "salary_range": "$80,000 - $102,000",
        "min_experience_years": 1,
        "required_skills": ["Power BI", "SQL", "Excel", "Data Analysis"],
        "preferred_skills": ["Python", "Tableau"],
    },
]


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


def recommend_jobs_for_resume(resume_data: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    resume_skills = {skill.lower() for skill in resume_data.get("skills", [])}
    candidate_years = int(resume_data.get("experience_years", 0))
    strongest_domain = ((resume_data.get("domain_analysis") or {}).get("strongest_domain") or "").lower()

    recommendations: list[dict[str, Any]] = []
    for job in JOB_CATALOG:
        required = [skill.lower() for skill in job.get("required_skills", [])]
        preferred = [skill.lower() for skill in job.get("preferred_skills", [])]

        required_overlap = [skill for skill in required if skill in resume_skills]
        required_missing = [skill for skill in required if skill not in resume_skills]
        preferred_overlap = [skill for skill in preferred if skill in resume_skills]

        required_score = len(required_overlap) / max(1, len(required))
        preferred_score = len(preferred_overlap) / max(1, len(preferred)) if preferred else required_score
        experience_score = _experience_fit(candidate_years, int(job.get("min_experience_years", 0)))
        domain_score = 1.0 if strongest_domain and strongest_domain == job.get("domain", "").lower() else 0.65

        fit = (
            (required_score * 0.55)
            + (preferred_score * 0.15)
            + (experience_score * 0.20)
            + (domain_score * 0.10)
        )
        fit_score = int(round(max(0.0, min(100.0, fit * 100))))
        minimum_required_matches = max(2, ceil(len(required) * 0.45))
        meets_requirements = (
            len(required_overlap) >= minimum_required_matches
            and experience_score >= 0.5
            and fit_score >= 50
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
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "job_link": _build_job_link(job),
                "job_link_fallback": _build_fallback_job_link(job),
                "domain": job["domain"],
                "employment_type": job["employment_type"],
                "location": job["location"],
                "salary_range": job["salary_range"],
                "min_experience_years": job["min_experience_years"],
                "fit_score": fit_score,
                "fit_label": _score_label(fit_score),
                "matched_required_skills": [skill for skill in job["required_skills"] if skill.lower() in resume_skills],
                "missing_required_skills": [skill for skill in job["required_skills"] if skill.lower() not in resume_skills],
                "required_coverage": int(round(required_score * 100)),
                "preferred_coverage": int(round(preferred_score * 100)),
                "meets_requirements": meets_requirements,
                "reasons": reasons,
            }
        )

    recommendations.sort(key=lambda item: item["fit_score"], reverse=True)
    qualified = [item for item in recommendations if item["meets_requirements"]]
    if qualified:
        return qualified[:limit]

    fallback = [
        item
        for item in recommendations
        if item["fit_score"] >= 45 and len(item["matched_required_skills"]) >= 2
    ]
    if fallback:
        return fallback[:limit]

    return recommendations[: min(3, limit)]
