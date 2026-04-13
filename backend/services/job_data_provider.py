from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup

from services.nlp_utils import extract_skills

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def _request_trust_env() -> bool:
    # Default to not inheriting system proxy variables to avoid broken proxy configs.
    return os.getenv("JOB_REQUEST_TRUST_ENV", "0").strip().lower() in {"1", "true", "yes", "on"}


def _http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
) -> requests.Response:
    session = requests.Session()
    session.trust_env = _request_trust_env()
    merged_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    if headers:
        merged_headers.update(headers)
    return session.get(url, params=params, timeout=timeout, headers=merged_headers)


def _skill_split(skills: list[str]) -> tuple[list[str], list[str]]:
    required = skills[:8]
    preferred = skills[8:14]
    return required, preferred


def _extract_years(description: str) -> int:
    matches = re.findall(r"(\d{1,2})\+?\s*(?:years?|yrs?)", description.lower())
    values = [int(value) for value in matches]
    return max(values) if values else 0


def _infer_domain(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("devops", "kubernetes", "terraform", "cloud", "sre")):
        return "DevOps and Cloud"
    if any(token in lowered for token in ("analyst", "tableau", "power bi", "report", "dashboard")):
        return "Data Analytics and BI"
    if any(token in lowered for token in ("ml", "machine learning", "data scientist", "nlp")):
        return "Data Science and ML"
    if any(token in lowered for token in ("frontend", "react", "javascript", "ui", "ux")):
        return "Frontend Engineering"
    if any(token in lowered for token in ("backend", "api", "python", "django", "flask")):
        return "Backend Engineering"
    return "General"


def _salary_range(item: dict[str, Any]) -> str:
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    if salary_min and salary_max:
        return f"${int(salary_min):,} - ${int(salary_max):,}"
    if salary_min:
        return f"From ${int(salary_min):,}"
    if salary_max:
        return f"Up to ${int(salary_max):,}"
    return "Not specified"


def _normalize_adzuna_job(item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "Software Engineer").strip()
    description = str(item.get("description") or "").strip()
    skills = extract_skills(f"{title}\n{description}", limit=16)
    required_skills, preferred_skills = _skill_split(skills)

    company_obj = item.get("company") or {}
    location_obj = item.get("location") or {}

    return {
        "job_id": str(item.get("id") or item.get("redirect_url") or title),
        "title": title,
        "company": str(company_obj.get("display_name") or "Unknown Company"),
        "job_link": str(item.get("redirect_url") or "").strip(),
        "domain": _infer_domain(f"{title} {description}"),
        "employment_type": str(item.get("contract_time") or item.get("contract_type") or "Full-time").title(),
        "location": str(location_obj.get("display_name") or "United States"),
        "salary_range": _salary_range(item),
        "min_experience_years": _extract_years(description),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "description": description,
        "source": "adzuna",
    }


def fetch_jobs_from_adzuna(query: str, limit: int = 20) -> list[dict[str, Any]]:
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    country = os.getenv("ADZUNA_COUNTRY", "us").strip().lower() or "us"
    location = os.getenv("ADZUNA_LOCATION", "United States").strip() or "United States"

    if not app_id or not app_key:
        return []

    endpoint = f"{ADZUNA_BASE_URL}/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": max(5, min(50, limit)),
        "content-type": "application/json",
    }

    try:
        response = _http_get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        jobs = [_normalize_adzuna_job(item) for item in results if isinstance(item, dict)]
        return jobs[:limit]
    except Exception:
        return []


def fetch_jobs_by_scraping(query: str, limit: int = 20) -> list[dict[str, Any]]:
    # Best-effort HTML fallback when API quotas/keys are unavailable.
    params = urlencode({"q": query, "l": "United States"})
    url = f"https://www.indeed.com/jobs?{params}"

    try:
        response = _http_get(url, timeout=12)
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: list[dict[str, Any]] = []
    seen_links: set[str] = set()

    anchors = soup.select("a[href*='/viewjob'], a.jcs-JobTitle, a[data-jk]")
    for anchor in anchors:
        href = str(anchor.get("href") or "").strip()
        if not href and anchor.get("data-jk"):
            href = f"/viewjob?jk={anchor.get('data-jk')}"
        title = " ".join(anchor.get_text(" ", strip=True).split())
        if not href or not title:
            continue

        full_link = href if href.startswith("http") else urljoin("https://www.indeed.com", href)
        if full_link in seen_links:
            continue
        seen_links.add(full_link)

        skills = extract_skills(title, limit=10)
        required_skills, preferred_skills = _skill_split(skills)

        jobs.append(
            {
                "job_id": full_link,
                "title": title,
                "company": "Company listed on Indeed",
                "job_link": full_link,
                "domain": _infer_domain(title),
                "employment_type": "Full-time",
                "location": "United States",
                "salary_range": "Not specified",
                "min_experience_years": 0,
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
                "description": "",
                "source": "scraped",
            }
        )

        if len(jobs) >= limit:
            break

    return jobs


def fetch_job_posts(query: str, limit: int = 20) -> list[dict[str, Any]]:
    api_jobs = fetch_jobs_from_adzuna(query, limit=limit)
    if api_jobs:
        return api_jobs

    scraped_jobs = fetch_jobs_by_scraping(query, limit=limit)
    return scraped_jobs[:limit]
