from __future__ import annotations

import re
from urllib.parse import urlparse

SUSPICIOUS_KEYWORDS = [
    "quick money",
    "easy money",
    "guaranteed income",
    "no interview",
    "no experience needed",
    "limited slots",
    "pay upfront",
    "registration fee",
    "security deposit",
    "whatsapp",
    "telegram",
    "urgent hiring",
    "immediate joining",
    "earn from home",
    "daily payout",
    "crypto payment",
    "processing fee",
    "interview fee",
    "guaranteed job",
    "no documents required",
    "instant joining bonus",
    "limited-time offer",
]

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
}

URL_SHORTENERS = {"bit.ly", "tinyurl.com", "rb.gy", "t.co", "goo.gl", "ow.ly"}
SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".gq", ".work", ".loan"}

FEATURE_NAMES = [
    "salary_anomaly",
    "salary_missing",
    "missing_company_info",
    "suspicious_keyword_count",
    "suspicious_keyword_density",
    "urgent_terms",
    "free_email_contact",
    "external_contact_request",
    "short_description",
    "no_experience_claim",
    "url_suspicious",
    "hype_punctuation_ratio",
]


def _parse_money_value(raw: str) -> int:
    value = raw.strip().lower().replace("$", "").replace(",", "")
    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)
    return int(float(value))


def _extract_salary_values(text: str) -> list[int]:
    # Examples matched: $120,000, 80k, 45,000
    salary_tokens = re.findall(r"\$?\s*(\d{2,3}(?:,\d{3})+|\d{2,3}k)\b", text.lower())
    salaries: list[int] = []
    for token in salary_tokens:
        try:
            salaries.append(_parse_money_value(token))
        except ValueError:
            continue
    return salaries


def _is_url_suspicious(job_url: str) -> int:
    if not job_url:
        return 0

    parsed = urlparse(job_url)
    hostname = (parsed.netloc or "").lower()

    if not hostname:
        return 1
    if hostname in URL_SHORTENERS:
        return 1
    if not job_url.lower().startswith("https://"):
        return 1
    if any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return 1
    if hostname.count("-") >= 3:
        return 1
    if sum(char.isdigit() for char in hostname) >= 4:
        return 1

    return 0


def extract_features(job_text: str, job_url: str = "") -> dict[str, float]:
    lowered = job_text.lower()
    words = re.findall(r"\b\w+\b", lowered)
    word_count = max(1, len(words))

    salary_values = _extract_salary_values(job_text)
    salary_missing = 1 if not salary_values else 0
    salary_anomaly = 0
    if salary_values:
        max_salary = max(salary_values)
        min_salary = min(salary_values)
        if max_salary >= 350000 or min_salary <= 12000:
            salary_anomaly = 1
        if min_salary > 0 and (max_salary / min_salary) >= 8:
            salary_anomaly = 1

    has_company_signal = bool(
        re.search(
            r"\b(inc|llc|ltd|corp|company|organization|about us|headquartered|our team|founded)\b",
            lowered,
        )
    )
    missing_company_info = 0 if has_company_signal else 1

    suspicious_keyword_count = sum(
        1 for phrase in SUSPICIOUS_KEYWORDS if phrase in lowered
    )
    suspicious_keyword_density = suspicious_keyword_count / word_count

    urgent_terms = len(
        re.findall(r"\b(urgent|immediately|apply now|limited|today only|hurry)\b", lowered)
    )

    emails = re.findall(r"[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", lowered)
    free_email_contact = 1 if any(domain in FREE_EMAIL_DOMAINS for domain in emails) else 0

    external_contact_request = 1 if re.search(
        r"\b(whatsapp|telegram|signal|dm us|text us|contact directly)\b", lowered
    ) else 0

    short_description = 1 if word_count < 120 else 0
    no_experience_claim = 1 if re.search(
        r"\b(no experience|freshers welcome|anyone can apply)\b", lowered
    ) else 0

    url_suspicious = _is_url_suspicious(job_url)

    exclamation_count = job_text.count("!")
    hype_punctuation_ratio = min(1.0, exclamation_count / max(3, word_count // 10))

    return {
        "salary_anomaly": float(salary_anomaly),
        "salary_missing": float(salary_missing),
        "missing_company_info": float(missing_company_info),
        "suspicious_keyword_count": float(suspicious_keyword_count),
        "suspicious_keyword_density": float(suspicious_keyword_density),
        "urgent_terms": float(urgent_terms),
        "free_email_contact": float(free_email_contact),
        "external_contact_request": float(external_contact_request),
        "short_description": float(short_description),
        "no_experience_claim": float(no_experience_claim),
        "url_suspicious": float(url_suspicious),
        "hype_punctuation_ratio": float(hype_punctuation_ratio),
    }
