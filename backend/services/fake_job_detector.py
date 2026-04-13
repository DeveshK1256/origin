from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import requests
from bs4 import BeautifulSoup

from ml.feature_engineering import FEATURE_NAMES, extract_features
from ml.train_fake_job_model import train_model_artifact


class FakeJobDetector:
    def __init__(self, model_path: str | Path | None = None):
        if model_path is None:
            model_path = Path(__file__).resolve().parents[1] / "ml" / "fake_job_model.joblib"
        self.model_path = Path(model_path)
        self.model = None
        self.feature_names = FEATURE_NAMES
        self.model_metrics: dict[str, Any] = {}
        self.hf_model_id = os.getenv("HF_FAKE_JOB_MODEL_ID", "").strip()
        self.hf_api_token = os.getenv("HF_API_TOKEN", "").strip()
        self.hf_timeout_seconds = int(os.getenv("HF_TIMEOUT_SECONDS", "12"))
        self._load_or_train()

    def _load_or_train(self) -> None:
        if not self.model_path.exists():
            train_model_artifact(output_path=self.model_path)

        artifact = joblib.load(self.model_path)
        self.model = artifact["model"]
        self.feature_names = artifact.get("feature_names", FEATURE_NAMES)
        self.model_metrics = artifact.get("metrics", {})

    @staticmethod
    def _fetch_job_post(job_url: str) -> tuple[str, str]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        }
        response = requests.get(job_url, headers=headers, timeout=12)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = ""
        if soup.title and soup.title.text:
            title = " ".join(soup.title.text.split())

        collected: list[str] = []
        for selector in ("h1", "h2", "p", "li"):
            for node in soup.select(selector):
                text = " ".join(node.get_text(" ", strip=True).split())
                if len(text) > 20:
                    collected.append(text)

        body_text = " ".join(collected).strip()
        if len(body_text) < 120:
            body_text = " ".join(soup.get_text(" ", strip=True).split())

        return title, body_text[:35000]

    @staticmethod
    def _build_red_flags(features: dict[str, float]) -> list[str]:
        flags: list[str] = []
        if features["salary_anomaly"] >= 1:
            flags.append("Salary pattern looks unrealistic or highly inconsistent.")
        if features["missing_company_info"] >= 1:
            flags.append("Company identity or employer information appears incomplete.")
        if features["suspicious_keyword_count"] >= 2:
            flags.append("Job post contains suspicious high-risk keywords.")
        if features["free_email_contact"] >= 1:
            flags.append("Contact uses free email domains instead of corporate email.")
        if features["external_contact_request"] >= 1:
            flags.append("Asks candidates to contact via external messaging channels.")
        if features["url_suspicious"] >= 1:
            flags.append("Job URL structure looks suspicious or untrusted.")
        if features["no_experience_claim"] >= 1:
            flags.append("Role claims no experience needed for potentially high compensation.")
        if features["short_description"] >= 1:
            flags.append("Job description is very short and lacks role detail.")
        return flags

    @staticmethod
    def _build_safe_signals(features: dict[str, float]) -> list[str]:
        signals: list[str] = []
        if features["salary_anomaly"] < 1 and features["salary_missing"] < 1:
            signals.append("Compensation information looks structured and plausible.")
        if features["missing_company_info"] < 1:
            signals.append("Company information appears present in the posting.")
        if features["suspicious_keyword_count"] < 1:
            signals.append("No high-risk scam keywords detected.")
        if features["external_contact_request"] < 1:
            signals.append("No external messaging app contact request detected.")
        if features["url_suspicious"] < 1:
            signals.append("URL pattern appears standard and trusted.")
        return signals

    @staticmethod
    def _build_risk_drivers(features: dict[str, float]) -> list[dict[str, Any]]:
        drivers: list[dict[str, Any]] = []
        weights = {
            "salary_anomaly": 18.0,
            "salary_missing": 5.0,
            "missing_company_info": 10.0,
            "suspicious_keyword_count": 7.0,
            "urgent_terms": 2.5,
            "free_email_contact": 14.0,
            "external_contact_request": 16.0,
            "short_description": 6.0,
            "no_experience_claim": 10.0,
            "url_suspicious": 12.0,
            "hype_punctuation_ratio": 8.0,
        }
        labels = {
            "salary_anomaly": "Unrealistic salary signal",
            "salary_missing": "No salary transparency",
            "missing_company_info": "Missing company details",
            "suspicious_keyword_count": "Suspicious wording density",
            "urgent_terms": "Urgency pressure terms",
            "free_email_contact": "Free-email recruiter contact",
            "external_contact_request": "External messaging contact request",
            "short_description": "Low-detail posting",
            "no_experience_claim": "No-experience promise",
            "url_suspicious": "Suspicious job URL",
            "hype_punctuation_ratio": "Hype/exclamation pattern",
        }

        for feature_name, weight in weights.items():
            value = float(features.get(feature_name, 0.0))
            if value <= 0:
                continue
            impact = min(30.0, value * weight)
            drivers.append(
                {
                    "factor": labels.get(feature_name, feature_name),
                    "feature": feature_name,
                    "value": round(value, 3),
                    "impact": round(impact, 2),
                }
            )

        drivers.sort(key=lambda item: item["impact"], reverse=True)
        return drivers

    def _rule_based_risk_score(self, features: dict[str, float]) -> float:
        drivers = self._build_risk_drivers(features)
        raw_score = sum(driver["impact"] for driver in drivers)

        # Trust boosters reduce risk when strong positive signs exist.
        if features["missing_company_info"] < 1:
            raw_score -= 6
        if features["suspicious_keyword_count"] < 1:
            raw_score -= 6
        if features["external_contact_request"] < 1:
            raw_score -= 4
        if features["salary_anomaly"] < 1 and features["salary_missing"] < 1:
            raw_score -= 4

        return max(0.0, min(100.0, raw_score))

    @staticmethod
    def _count_major_flags(features: dict[str, float]) -> int:
        count = 0
        major_features = (
            "salary_anomaly",
            "missing_company_info",
            "free_email_contact",
            "external_contact_request",
            "no_experience_claim",
            "url_suspicious",
        )
        for feature in major_features:
            if features.get(feature, 0) >= 1:
                count += 1
        if features.get("suspicious_keyword_count", 0) >= 2:
            count += 1
        if features.get("urgent_terms", 0) >= 3:
            count += 1
        return count

    @staticmethod
    def _confidence(drivers_count: int, fetch_warning: str | None) -> float:
        base = 0.55 + (drivers_count * 0.06)
        if fetch_warning:
            base -= 0.08
        return round(max(0.35, min(0.95, base)), 2)

    @staticmethod
    def _risk_level(probability: float) -> str:
        if probability >= 72:
            return "High"
        if probability >= 42:
            return "Medium"
        return "Low"

    @staticmethod
    def _normalize_hf_items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            if payload and isinstance(payload[0], list):
                nested = payload[0]
                return [item for item in nested if isinstance(item, dict)]
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    @staticmethod
    def _hf_risk_from_labels(items: list[dict[str, Any]]) -> float | None:
        if not items:
            return None

        scored: list[tuple[str, float]] = []
        for item in items:
            label = str(item.get("label") or "").strip().lower()
            try:
                score = float(item.get("score") or 0.0)
            except (TypeError, ValueError):
                score = 0.0
            scored.append((label, max(0.0, min(1.0, score))))

        if not scored:
            return None

        risky_tokens = ("fake", "scam", "fraud", "label_1", "negative")
        safe_tokens = ("real", "legit", "genuine", "label_0", "positive")

        risk_score = 0.0
        for label, score in scored:
            if any(token in label for token in risky_tokens):
                risk_score = max(risk_score, score)
            elif any(token in label for token in safe_tokens):
                risk_score = max(risk_score, 1.0 - score)

        if risk_score > 0:
            return round(risk_score * 100, 2)

        # Fallback if labels are unknown: use top score as risk signal.
        best_score = max(score for _, score in scored)
        return round(best_score * 100, 2)

    def _hugging_face_probability(self, text: str) -> tuple[float | None, str | None]:
        if not self.hf_model_id or not self.hf_api_token:
            return None, "Hugging Face model/token not configured."

        endpoint = f"https://api-inference.huggingface.co/models/{self.hf_model_id}"
        headers = {
            "Authorization": f"Bearer {self.hf_api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": text[:3500],
            "options": {"wait_for_model": True},
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=self.hf_timeout_seconds)
            if response.status_code >= 400:
                return None, f"Hugging Face API returned {response.status_code}."

            data = response.json()
            items = self._normalize_hf_items(data)
            probability = self._hf_risk_from_labels(items)
            if probability is None:
                return None, "Hugging Face output was not in expected format."
            return probability, None
        except Exception as exc:
            return None, f"Hugging Face request failed: {exc}"

    def analyze(self, job_url: str = "", fallback_text: str = "") -> dict[str, Any]:
        if not job_url and not fallback_text:
            raise ValueError("Please provide a job URL or job text for analysis.")

        fetched_title = ""
        fetch_warning = None
        source_text = fallback_text.strip()

        if job_url:
            try:
                fetched_title, source_text = self._fetch_job_post(job_url)
            except Exception as exc:
                if not source_text:
                    raise ValueError(
                        f"Could not fetch job URL content. Provide 'job_text' fallback. ({exc})"
                    ) from exc
                fetch_warning = f"URL fetch failed; used fallback text. ({exc})"

        if not source_text.strip():
            raise ValueError("No analyzable job content found.")

        features = extract_features(source_text, job_url=job_url)
        vector = np.array([[features[name] for name in self.feature_names]], dtype=float)
        local_ml_probability = float(self.model.predict_proba(vector)[0][1] * 100)
        hf_probability, hf_warning = self._hugging_face_probability(source_text)
        if hf_probability is not None:
            ml_probability = (local_ml_probability * 0.6) + (hf_probability * 0.4)
            ml_source = "huggingface+local"
        else:
            ml_probability = local_ml_probability
            ml_source = "local"
        rule_risk_score = self._rule_based_risk_score(features)

        scam_probability = (ml_probability * 0.55) + (rule_risk_score * 0.45)
        major_flags = self._count_major_flags(features)

        # Escalate obvious scam patterns to avoid under-reporting clear fraudulent posts.
        if major_flags >= 4 and scam_probability < 78:
            scam_probability = 78 + min(18, (major_flags - 4) * 5)
        if major_flags == 0 and scam_probability > 35:
            scam_probability = min(scam_probability, 35.0)

        scam_probability = round(max(0.0, min(100.0, scam_probability)), 2)

        red_flags = self._build_red_flags(features)
        safe_signals = self._build_safe_signals(features)
        risk_drivers = self._build_risk_drivers(features)
        confidence = self._confidence(len(risk_drivers), fetch_warning)
        explanation = (
            f"Risk is driven by {len(red_flags)} red-flag signals and {major_flags} major risk indicators."
            if red_flags
            else "No major red flags were detected. Keep normal verification checks."
        )

        return {
            "title": fetched_title,
            "job_url": job_url,
            "scam_probability": scam_probability,
            "ml_probability": round(ml_probability, 2),
            "local_ml_probability": round(local_ml_probability, 2),
            "hf_probability": round(hf_probability, 2) if hf_probability is not None else None,
            "ml_source": ml_source,
            "hf_model_id": self.hf_model_id or None,
            "rule_risk_score": round(rule_risk_score, 2),
            "risk_level": self._risk_level(scam_probability),
            "red_flags": red_flags,
            "safe_signals": safe_signals,
            "risk_drivers": risk_drivers,
            "major_flag_count": major_flags,
            "confidence": confidence,
            "explanation": explanation,
            "feature_snapshot": features,
            "model_metrics": self.model_metrics,
            "preview": source_text[:450],
            "fetch_warning": fetch_warning,
            "hf_warning": hf_warning,
        }
