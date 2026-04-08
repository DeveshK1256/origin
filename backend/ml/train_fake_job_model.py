from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from ml.feature_engineering import FEATURE_NAMES, extract_features
except ModuleNotFoundError:
    # Allows running this file directly: python ml/train_fake_job_model.py
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from ml.feature_engineering import FEATURE_NAMES, extract_features

LEGIT_TITLES = [
    "Software Engineer",
    "Data Analyst",
    "Backend Developer",
    "Product Manager",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Frontend Developer",
    "QA Engineer",
]

SCAM_TITLES = [
    "Work From Home Earning Specialist",
    "Instant Income Executive",
    "Easy Money Online Agent",
    "Fast Cash Hiring Coordinator",
    "Immediate Offer Processor",
]

COMPANIES = [
    "Apex Systems Inc",
    "Northwind Technologies LLC",
    "Nimbus Analytics Ltd",
    "Brightline Software Corp",
    "Delta Grid Solutions",
    "Vertex Labs",
]

LOCATIONS = ["New York", "Austin", "Remote", "Bengaluru", "San Francisco", "Chicago"]

SCAM_URLS = [
    "http://quick-income-job-247.xyz/open-role",
    "http://urgent-hiring-fastcash.top/apply-now",
    "https://bit.ly/start-income-role",
    "http://earn-money-click.work/join",
]

LEGIT_URLS = [
    "https://careers.apexsystems.com/jobs/software-engineer",
    "https://jobs.northwindtech.com/openings/backend-developer",
    "https://www.linkedin.com/jobs/view/1234567890",
    "https://greenhouse.io/nimbus/jobs/987654",
]

SCAM_PHRASES = [
    "No interview required and no experience needed.",
    "Guaranteed income with daily payout.",
    "Apply now, limited slots available today only!",
    "Registration fee refundable after onboarding.",
    "Contact immediately on WhatsApp for quick selection.",
]

LEGIT_RESPONSIBILITIES = [
    "Design, build, and maintain scalable APIs and services.",
    "Collaborate with cross-functional teams to ship product improvements.",
    "Write clean, testable code and participate in code reviews.",
    "Monitor application reliability and performance in production.",
    "Document technical decisions and implementation plans.",
]

LEGIT_REQUIREMENTS = [
    "3+ years of professional software development experience.",
    "Strong Python and SQL skills with exposure to cloud environments.",
    "Excellent communication and stakeholder collaboration skills.",
    "Experience with REST APIs, Git workflows, and CI/CD tooling.",
    "Bachelor degree in Computer Science or equivalent experience.",
]


def _generate_legit_posting(rng: random.Random) -> tuple[str, str, int]:
    title = rng.choice(LEGIT_TITLES)
    company = rng.choice(COMPANIES)
    location = rng.choice(LOCATIONS)
    salary_low = rng.randint(65000, 125000)
    salary_high = salary_low + rng.randint(10000, 50000)
    responsibilities = " ".join(rng.sample(LEGIT_RESPONSIBILITIES, 3))
    requirements = " ".join(rng.sample(LEGIT_REQUIREMENTS, 3))

    text = (
        f"{company} is hiring a {title} in {location}. "
        f"Compensation range: ${salary_low:,} - ${salary_high:,} per year. "
        f"About us: We are a product engineering company focused on enterprise software. "
        f"Responsibilities: {responsibilities} "
        f"Requirements: {requirements} "
        f"Please apply through our official portal."
    )
    return text, rng.choice(LEGIT_URLS), 0


def _generate_scam_posting(rng: random.Random) -> tuple[str, str, int]:
    title = rng.choice(SCAM_TITLES)
    salary = rng.randint(300000, 950000)
    phrase_block = " ".join(rng.sample(SCAM_PHRASES, 3))
    contact_email = rng.choice(["topjobalert@gmail.com", "hiringdesk@yahoo.com", "urgentwork@outlook.com"])

    text = (
        f"{title}! Earn up to ${salary:,} instantly!! "
        f"{phrase_block} "
        f"Send your details to {contact_email}. "
        f"No background checks, no interview, immediate joining."
    )
    return text, rng.choice(SCAM_URLS), 1


def _build_dataset(sample_size: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = random.Random(seed)
    rows: list[list[float]] = []
    labels: list[int] = []

    for _ in range(sample_size):
        if rng.random() < 0.52:
            text, url, label = _generate_scam_posting(rng)
        else:
            text, url, label = _generate_legit_posting(rng)

        features = extract_features(text, url)
        rows.append([features[name] for name in FEATURE_NAMES])
        labels.append(label)

    return np.array(rows, dtype=float), np.array(labels, dtype=int)


def train_model_artifact(
    output_path: str | Path | None = None,
    sample_size: int = 2200,
    seed: int = 42,
) -> tuple[Path, dict]:
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "fake_job_model.joblib"
    else:
        output_path = Path(output_path)

    X, y = _build_dataset(sample_size=sample_size, seed=seed)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=seed,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=280,
        max_depth=9,
        random_state=seed,
        class_weight="balanced_subsample",
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "f1": round(float(f1_score(y_test, pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "sample_size": int(sample_size),
    }

    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "metrics": metrics,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)

    return output_path, metrics


if __name__ == "__main__":
    destination, eval_metrics = train_model_artifact()
    print(f"Saved model artifact: {destination}")
    print(f"Metrics: {eval_metrics}")
