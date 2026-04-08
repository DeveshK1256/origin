from __future__ import annotations

import datetime as dt
import re
from collections import Counter
from typing import Any

from services.nlp_utils import extract_keywords, extract_skills, get_nlp, normalize_whitespace

EDUCATION_KEYWORDS = [
    "bachelor",
    "master",
    "phd",
    "b.tech",
    "m.tech",
    "mba",
    "b.sc",
    "m.sc",
    "associate",
    "diploma",
    "university",
    "college",
    "school",
]

SECTION_HEADERS = {
    "summary": ["summary", "profile", "professional summary", "career summary", "about"],
    "experience": ["experience", "work history", "employment history", "professional experience"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects", "key projects"],
    "certifications": ["certifications", "certificates", "licenses"],
    "achievements": ["achievements", "accomplishments"],
    "languages": ["languages", "language proficiency"],
}

ROLE_KEYWORDS = {
    "engineer",
    "developer",
    "analyst",
    "scientist",
    "manager",
    "architect",
    "consultant",
    "intern",
    "lead",
    "specialist",
    "administrator",
}

DOMAIN_PROFILES = {
    "Backend Engineering": {
        "skills": [
            "Python",
            "Java",
            "Go",
            "Node.js",
            "Flask",
            "Django",
            "FastAPI",
            "SQL",
            "PostgreSQL",
            "REST API",
            "Docker",
            "Microservices",
        ],
        "keywords": ["api", "service", "backend", "database", "microservice"],
    },
    "Frontend Engineering": {
        "skills": [
            "JavaScript",
            "TypeScript",
            "React",
            "Next.js",
            "HTML",
            "CSS",
            "Tailwind",
            "Git",
            "Node.js",
        ],
        "keywords": ["frontend", "ui", "ux", "component", "web"],
    },
    "Data Science and ML": {
        "skills": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Pandas",
            "NumPy",
            "Scikit-learn",
            "TensorFlow",
            "PyTorch",
            "SQL",
            "Data Analysis",
        ],
        "keywords": ["model", "prediction", "analytics", "training", "classification"],
    },
    "DevOps and Cloud": {
        "skills": [
            "Docker",
            "Kubernetes",
            "Terraform",
            "AWS",
            "Azure",
            "GCP",
            "Linux",
            "CI/CD",
            "Jenkins",
            "GitHub Actions",
            "Microservices",
        ],
        "keywords": ["deployment", "infrastructure", "pipeline", "cloud", "automation"],
    },
    "Data Analytics and BI": {
        "skills": [
            "SQL",
            "Python",
            "Data Analysis",
            "Pandas",
            "NumPy",
            "Power BI",
            "Tableau",
            "Excel",
        ],
        "keywords": ["dashboard", "reporting", "insights", "business", "kpi"],
    },
}

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)

DATE_RANGE_MONTH_PATTERN = re.compile(
    rf"\b(?P<start_month>{MONTH_PATTERN})\s+(?P<start_year>19\d{{2}}|20\d{{2}})\s*"
    rf"(?:-|to|-|-|/)\s*"
    rf"(?:(?P<end_month>{MONTH_PATTERN})\s+(?P<end_year>19\d{{2}}|20\d{{2}})|(?P<end_word>present|current|now))\b",
    re.IGNORECASE,
)

DATE_RANGE_YEAR_PATTERN = re.compile(
    r"\b(?P<start_year>19\d{2}|20\d{2})\s*(?:-|to|-|-|/)\s*(?P<end_year>19\d{2}|20\d{2}|present|current|now)\b",
    re.IGNORECASE,
)

EXPLICIT_EXPERIENCE_PATTERNS = [
    re.compile(r"(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:work\s+)?experience", re.IGNORECASE),
    re.compile(r"experience\s*(?:of|:)?\s*(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+in\b", re.IGNORECASE),
]

LANGUAGE_WORDS = {
    "english",
    "hindi",
    "spanish",
    "french",
    "german",
    "italian",
    "portuguese",
    "mandarin",
    "arabic",
    "japanese",
    "korean",
}


def _normalized_header(line: str) -> str:
    return re.sub(r"[^a-z ]", "", line.lower()).strip()


def _split_into_sections(text: str) -> dict[str, list[str]]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    sections: dict[str, list[str]] = {key: [] for key in SECTION_HEADERS}
    sections["other"] = []

    current = "other"
    for line in lines:
        normalized = _normalized_header(line.rstrip(":"))
        matched_section = None
        for section, variants in SECTION_HEADERS.items():
            if normalized in variants:
                matched_section = section
                break
        if matched_section:
            current = matched_section
            continue

        sections.setdefault(current, []).append(line)

    return sections


def _extract_summary(text: str, sections: dict[str, list[str]]) -> str:
    if sections.get("summary"):
        return " ".join(sections["summary"][:3])[:420]

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    candidate_lines: list[str] = []
    for line in lines:
        normalized = _normalized_header(line.rstrip(":"))
        if any(normalized in variants for variants in SECTION_HEADERS.values()):
            break
        if not re.search(r"@|\+?\d", line):
            candidate_lines.append(line)
        if len(candidate_lines) >= 3:
            break

    return " ".join(candidate_lines)[:420]


def _extract_name(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        if re.search(r"@|\d", line):
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(word[0].isalpha() for word in words if word):
            return line[:80]

    nlp = get_nlp()
    doc = nlp(text[:800])
    if doc.ents:
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 5:
                return ent.text[:80]

    return "Not detected"


def _extract_contact_info(text: str) -> dict[str, Any]:
    email_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_matches = re.findall(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}", text)
    link_matches = re.findall(r"https?://[^\s]+", text)

    linkedin = next((link for link in link_matches if "linkedin.com" in link.lower()), "")
    github = next((link for link in link_matches if "github.com" in link.lower()), "")

    return {
        "emails": sorted(set(email_matches))[:3],
        "phones": sorted(set(phone_matches))[:2],
        "linkedin": linkedin,
        "github": github,
        "links": sorted(set(link_matches))[:5],
    }


def _extract_education_lines(text: str, max_items: int = 6) -> list[str]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    matches: list[str] = []

    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in EDUCATION_KEYWORDS):
            matches.append(line)

    if not matches:
        sentence_pattern = re.compile(
            r"\b(?:Bachelor|Master|PhD|B\.Tech|M\.Tech|MBA|B\.Sc|M\.Sc|Diploma)\b[^.\n]{0,100}",
            re.IGNORECASE,
        )
        matches = [match.strip() for match in sentence_pattern.findall(text)]

    deduped: list[str] = []
    seen = set()
    for entry in matches:
        compact = re.sub(r"\s+", " ", entry)
        key = compact.lower()
        if key not in seen:
            deduped.append(compact)
            seen.add(key)
        if len(deduped) >= max_items:
            break

    return deduped


def _extract_projects(sections: dict[str, list[str]], text: str) -> list[str]:
    project_lines = sections.get("projects", [])[:6]
    if project_lines:
        return project_lines

    fallback = []
    for line in [line.strip() for line in text.split("\n") if line.strip()]:
        lowered = line.lower()
        if "project" in lowered and len(line) <= 140:
            fallback.append(line)
        if len(fallback) >= 6:
            break

    return fallback


def _extract_certifications(sections: dict[str, list[str]], text: str) -> list[str]:
    cert_lines = sections.get("certifications", [])[:6]
    if cert_lines:
        return cert_lines

    patterns = (
        "certified",
        "certification",
        "certificate",
        "pmp",
        "scrum",
        "aws certified",
        "azure certified",
        "google cloud certified",
    )
    found = []
    for line in [line.strip() for line in text.split("\n") if line.strip()]:
        lowered = line.lower()
        if any(token in lowered for token in patterns):
            found.append(line)
        if len(found) >= 6:
            break

    return found


def _extract_languages(sections: dict[str, list[str]], text: str) -> list[str]:
    candidates: list[str] = []

    for line in sections.get("languages", []):
        parts = re.split(r"[:,|/]", line)
        candidates.extend(part.strip() for part in parts if part.strip())

    if not candidates:
        for line in text.split("\n"):
            lowered = line.lower()
            if "language" in lowered:
                parts = re.split(r"[:,|/]", line)
                candidates.extend(part.strip() for part in parts if part.strip())

    normalized = []
    seen = set()
    for item in candidates:
        for token in re.split(r",|;", item):
            word = token.strip().lower()
            if word in LANGUAGE_WORDS and word not in seen:
                normalized.append(word.title())
                seen.add(word)

    return normalized[:6]


def _extract_achievements(sections: dict[str, list[str]], text: str) -> list[str]:
    achievement_lines = sections.get("achievements", [])[:6]
    if achievement_lines:
        return achievement_lines

    metric_pattern = re.compile(
        r"(?:\d+%|\$\d|\d+x|increased|reduced|improved|saved|boosted|grew|delivered)",
        re.IGNORECASE,
    )
    found = []
    for line in [line.strip() for line in text.split("\n") if line.strip()]:
        if metric_pattern.search(line):
            found.append(line)
        if len(found) >= 6:
            break

    return found


def _extract_roles_and_companies(sections: dict[str, list[str]], text: str) -> tuple[list[str], list[str]]:
    source_lines = sections.get("experience", []) or [line.strip() for line in text.split("\n") if line.strip()]

    role_lines: list[str] = []
    companies: list[str] = []

    company_pattern = re.compile(
        r"\b[A-Z][A-Za-z&.,'\- ]{2,}(?:Inc|LLC|Ltd|Corp|Corporation|Technologies|Technology|Solutions|Systems|Labs|Pvt\.?\s*Ltd\.?)\b"
    )

    for line in source_lines:
        lowered = line.lower()
        words = re.findall(r"[A-Za-z]+", lowered)
        if any(word in ROLE_KEYWORDS for word in words) and len(line) <= 120:
            role_lines.append(line)

        segments = [segment.strip() for segment in re.split(r"[|,;/]", line) if segment.strip()]
        for segment in segments:
            match = company_pattern.search(segment)
            if match:
                cleaned = re.sub(r"\s+", " ", match.group(0)).strip(" ,.")
                lowered_cleaned = cleaned.lower()
                cleaned_words = set(re.findall(r"[a-z]+", lowered_cleaned))
                if ROLE_KEYWORDS.intersection(cleaned_words):
                    if " at " in lowered_cleaned:
                        cleaned = cleaned.split(" at ", 1)[1].strip(" ,.")
                    elif "," in cleaned:
                        cleaned = cleaned.split(",")[-1].strip(" ,.")
                if cleaned:
                    companies.append(cleaned)

        at_match = re.search(r"\bat\s+([A-Z][A-Za-z&.,' -]{2,80})", line)
        if at_match:
            candidate = re.sub(r"\s+", " ", at_match.group(1)).strip(" ,.")
            if candidate and len(candidate.split()) <= 10:
                companies.append(candidate)

        if len(role_lines) >= 6 and len(companies) >= 6:
            break

    dedup_roles = list(dict.fromkeys(role_lines))[:6]
    dedup_companies = list(dict.fromkeys(companies))[:8]
    return dedup_roles, dedup_companies


def _extract_experience_section_text(sections: dict[str, list[str]], text: str) -> str:
    experience_lines = sections.get("experience", [])
    if experience_lines:
        return "\n".join(experience_lines)

    # Fallback: remove obvious education lines to reduce noise when no experience section exists.
    filtered = []
    for line in [line.strip() for line in text.split("\n") if line.strip()]:
        lowered = line.lower()
        if any(keyword in lowered for keyword in EDUCATION_KEYWORDS):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def _parse_month(month_word: str | None, default_month: int) -> int:
    if not month_word:
        return default_month
    return MONTH_MAP.get(month_word.lower(), default_month)


def _extract_experience_intervals(experience_text: str) -> tuple[list[tuple[int, int]], list[str]]:
    intervals: list[tuple[int, int]] = []
    evidence: list[str] = []
    now = dt.datetime.utcnow()
    max_month_index = (now.year * 12) + now.month

    lines = [line.strip() for line in experience_text.split("\n") if line.strip()]
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in EDUCATION_KEYWORDS):
            continue

        for match in DATE_RANGE_MONTH_PATTERN.finditer(line):
            start_year = int(match.group("start_year"))
            start_month = _parse_month(match.group("start_month"), 1)

            end_word = match.group("end_word")
            if end_word:
                end_year = now.year
                end_month = now.month
            else:
                end_year = int(match.group("end_year"))
                end_month = _parse_month(match.group("end_month"), 12)

            start_idx = (start_year * 12) + start_month
            end_idx = (end_year * 12) + end_month

            if 1950 <= start_year <= now.year + 1 and start_idx <= end_idx <= max_month_index:
                if (end_idx - start_idx) <= (40 * 12):
                    intervals.append((start_idx, end_idx))
                    evidence.append(line)

        for match in DATE_RANGE_YEAR_PATTERN.finditer(line):
            start_year = int(match.group("start_year"))
            end_token = match.group("end_year").lower()
            if end_token in {"present", "current", "now"}:
                end_year = now.year
                end_month = now.month
            else:
                end_year = int(end_token)
                end_month = 12

            start_idx = (start_year * 12) + 1
            end_idx = (end_year * 12) + end_month

            if 1950 <= start_year <= end_year <= now.year + 1 and start_idx <= end_idx <= max_month_index:
                if (end_idx - start_idx) <= (40 * 12):
                    intervals.append((start_idx, end_idx))
                    evidence.append(line)

    # Deduplicate intervals
    unique = sorted(set(intervals), key=lambda item: item[0])
    dedup_evidence = list(dict.fromkeys(evidence))[:8]
    return unique, dedup_evidence


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda item: item[0])
    merged = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= (last_end + 1):
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def _extract_explicit_experience_values(experience_text: str) -> list[float]:
    values: list[float] = []
    for pattern in EXPLICIT_EXPERIENCE_PATTERNS:
        for match in pattern.findall(experience_text):
            try:
                value = float(match)
            except ValueError:
                continue
            if 0 < value <= 40:
                values.append(value)
    return values


def _estimate_experience_years(sections: dict[str, list[str]], text: str) -> tuple[int, dict[str, Any]]:
    experience_text = _extract_experience_section_text(sections, text)

    intervals, interval_evidence = _extract_experience_intervals(experience_text)
    merged = _merge_intervals(intervals)
    total_months = sum((end - start) for start, end in merged)
    date_years = round(total_months / 12.0, 1) if total_months > 0 else 0.0

    explicit_values = _extract_explicit_experience_values(experience_text)
    explicit_years = max(explicit_values) if explicit_values else 0.0

    if date_years > 0 and explicit_years > 0:
        if abs(date_years - explicit_years) <= 1.5:
            estimated = max(date_years, explicit_years)
            confidence = "High"
        elif abs(date_years - explicit_years) <= 4.0:
            estimated = round((date_years * 0.6) + (explicit_years * 0.4), 1)
            confidence = "Medium"
        elif explicit_years > (date_years + 4.0):
            estimated = round(date_years + min(3.0, (explicit_years - date_years) / 3.0), 1)
            confidence = "Medium"
        elif date_years > (explicit_years + 4.0):
            estimated = round(explicit_years + min(4.0, (date_years - explicit_years) / 2.0), 1)
            confidence = "Medium"
        else:
            estimated = max(date_years, explicit_years)
            confidence = "Medium"
    elif date_years > 0:
        estimated = date_years
        confidence = "Medium"
    elif explicit_years > 0:
        estimated = explicit_years
        confidence = "Low"
    else:
        estimated = 0.0
        confidence = "Low"

    estimated = max(0.0, min(40.0, estimated))
    estimated_int = int(round(estimated))

    explicit_evidence = []
    for line in [line.strip() for line in experience_text.split("\n") if line.strip()]:
        if re.search(r"\b(?:years?|yrs?)\b", line, re.IGNORECASE):
            explicit_evidence.append(line)
        if len(explicit_evidence) >= 5:
            break

    evidence_lines = list(dict.fromkeys(interval_evidence + explicit_evidence))[:8]

    breakdown = {
        "estimated_years": estimated_int,
        "from_date_ranges_years": date_years,
        "from_explicit_claim_years": round(explicit_years, 1),
        "confidence": confidence,
        "evidence": evidence_lines,
        "interval_count": len(merged),
    }
    return estimated_int, breakdown


def _detect_sections(text: str) -> dict[str, bool]:
    lowered = text.lower()
    section_presence = {}
    for section, variants in SECTION_HEADERS.items():
        section_presence[section] = any(variant in lowered for variant in variants)
    return section_presence


def _resume_score(skills_count: int, experience_years: int, education_count: int, keyword_count: int) -> int:
    score = 0
    score += min(skills_count * 2.5, 35)
    score += min(experience_years * 2.0, 30)
    score += min(education_count * 12, 20)
    score += min(keyword_count * 1.2, 15)
    return int(round(min(score, 100)))


def _readiness_label(probability: int) -> str:
    if probability >= 75:
        return "High"
    if probability >= 50:
        return "Medium"
    return "Developing"


def _analyze_domain_fit(skills: list[str], keywords: list[str], experience_years: int) -> dict[str, Any]:
    skill_set = {skill.lower() for skill in skills}
    keyword_set = {kw.lower() for kw in keywords}

    assessments = []
    for domain_name, profile in DOMAIN_PROFILES.items():
        domain_skills = profile["skills"]
        matched_skills = sorted(
            [skill for skill in domain_skills if skill.lower() in skill_set],
            key=str.lower,
        )
        missing_skills = sorted(
            [skill for skill in domain_skills if skill.lower() not in skill_set],
            key=str.lower,
        )

        keyword_hits = sum(1 for keyword in profile["keywords"] if keyword in keyword_set)

        skill_alignment = len(matched_skills) / max(1, len(domain_skills))
        experience_alignment = min(1.0, experience_years / 6.0)
        keyword_alignment = min(1.0, keyword_hits / max(1, len(profile["keywords"])))

        probability = int(
            round(
                min(
                    95.0,
                    18.0 + (skill_alignment * 78.0) + (experience_alignment * 15.0) + (keyword_alignment * 7.0),
                )
            )
        )
        probability = max(10, probability)

        strength_signals = []
        if matched_skills:
            strength_signals.append(f"Matched {len(matched_skills)} core skills.")
        if experience_years >= 3:
            strength_signals.append(f"{experience_years} years of experience supports employability.")
        if keyword_hits >= 2:
            strength_signals.append("Resume language aligns with domain-specific terminology.")

        assessments.append(
            {
                "domain": domain_name,
                "probability": probability,
                "readiness": _readiness_label(probability),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills[:8],
                "strength_signals": strength_signals,
            }
        )

    assessments.sort(key=lambda item: item["probability"], reverse=True)
    strongest = assessments[0] if assessments else None

    return {
        "strongest_domain": strongest["domain"] if strongest else None,
        "strongest_domain_probability": strongest["probability"] if strongest else 0,
        "strongest_domain_strength_signals": strongest["strength_signals"] if strongest else [],
        "missing_skills_for_strongest_domain": strongest["missing_skills"] if strongest else [],
        "domain_probabilities": {item["domain"]: item["probability"] for item in assessments},
        "domain_assessments": assessments,
    }


def parse_resume_text(resume_text: str) -> dict[str, Any]:
    cleaned = normalize_whitespace(resume_text)

    if not cleaned:
        raise ValueError("Resume text is empty after normalization.")

    sections_map = _split_into_sections(cleaned)

    skills = extract_skills(cleaned)
    keywords = extract_keywords(cleaned, top_n=20)
    experience_years, experience_breakdown = _estimate_experience_years(sections_map, cleaned)
    education = _extract_education_lines(cleaned)
    sections_detected = _detect_sections(cleaned)

    summary = _extract_summary(cleaned, sections_map)
    candidate_name = _extract_name(cleaned)
    contact = _extract_contact_info(cleaned)
    projects = _extract_projects(sections_map, cleaned)
    certifications = _extract_certifications(sections_map, cleaned)
    achievements = _extract_achievements(sections_map, cleaned)
    languages = _extract_languages(sections_map, cleaned)
    recent_roles, companies = _extract_roles_and_companies(sections_map, cleaned)

    token_counter = Counter(word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9.+#/-]{1,}", cleaned))
    top_terms = [token for token, _ in token_counter.most_common(12)]

    score = _resume_score(
        skills_count=len(skills),
        experience_years=experience_years,
        education_count=len(education),
        keyword_count=len(keywords),
    )

    domain_analysis = _analyze_domain_fit(
        skills=skills,
        keywords=keywords,
        experience_years=experience_years,
    )

    return {
        "name": candidate_name,
        "contact": contact,
        "profile_summary": summary,
        "skills": skills,
        "experience_years": experience_years,
        "experience_breakdown": experience_breakdown,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "languages": languages,
        "recent_roles": recent_roles,
        "companies": companies,
        "keywords": keywords,
        "sections_detected": sections_detected,
        "top_terms": top_terms,
        "resume_score": score,
        "domain_analysis": domain_analysis,
        "text_length": len(cleaned),
        "preview": cleaned[:500],
    }
