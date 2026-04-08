from __future__ import annotations

import re
from collections import Counter

import spacy

SKILL_LIBRARY = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "Go",
    "Rust",
    "SQL",
    "NoSQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Flask",
    "Django",
    "FastAPI",
    "React",
    "Next.js",
    "Node.js",
    "Express",
    "Tailwind",
    "HTML",
    "CSS",
    "Git",
    "Docker",
    "Kubernetes",
    "Terraform",
    "AWS",
    "Azure",
    "GCP",
    "Linux",
    "REST API",
    "GraphQL",
    "Microservices",
    "CI/CD",
    "Jenkins",
    "GitHub Actions",
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "spaCy",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Data Analysis",
    "Pandas",
    "NumPy",
    "Power BI",
    "Tableau",
    "Excel",
    "Agile",
    "Scrum",
]

_SKILL_PATTERNS = [
    (skill, re.compile(rf"(?<!\w){re.escape(skill.lower())}(?!\w)"))
    for skill in SKILL_LIBRARY
]

_NLP = None


def get_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP

    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        # Fallback for environments where the model is not pre-downloaded.
        _NLP = spacy.blank("en")
        if "sentencizer" not in _NLP.pipe_names:
            _NLP.add_pipe("sentencizer")
    return _NLP


def normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).replace("\r", "\n").strip()


def extract_skills(text: str, limit: int = 40) -> list[str]:
    normalized = text.lower()
    matched = [skill for skill, pattern in _SKILL_PATTERNS if pattern.search(normalized)]
    return sorted(set(matched), key=str.lower)[:limit]


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    nlp = get_nlp()
    doc = nlp(text[:250000])
    counts: Counter[str] = Counter()

    if doc.has_annotation("DEP"):
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()
            if len(phrase) >= 3 and not phrase.isdigit():
                counts[phrase] += 2

    if doc.ents:
        for entity in doc.ents:
            phrase = entity.text.strip().lower()
            if len(phrase) >= 3 and not phrase.isdigit():
                counts[phrase] += 2

    for token in doc:
        if token.is_stop or token.is_punct or token.like_num:
            continue
        lemma = token.lemma_.strip().lower() if token.lemma_ else token.text.strip().lower()
        if len(lemma) >= 3:
            counts[lemma] += 1

    keywords = [word for word, _ in counts.most_common(top_n)]
    return keywords


def extract_required_experience(text: str) -> int:
    patterns = [
        re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience", re.IGNORECASE),
        re.compile(r"experience\s*[:\-]?\s*(\d{1,2})\+?\s*(?:years?|yrs?)", re.IGNORECASE),
        re.compile(r"minimum\s+(\d{1,2})\s*(?:years?|yrs?)", re.IGNORECASE),
    ]

    values: list[int] = []
    for pattern in patterns:
        values.extend(int(match) for match in pattern.findall(text))

    return max(values) if values else 0
