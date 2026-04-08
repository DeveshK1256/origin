from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from services.fake_job_detector import FakeJobDetector
from services.file_extractors import (
    allowed_resume_extension,
    extract_text_from_uploaded_file,
)
from services.job_matching import analyze_job_description, calculate_job_match
from services.job_recommender import recommend_jobs_for_resume
from services.resume_ai import generate_resume_ai_assets
from services.resume_parser import parse_resume_text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")]
CORS(app, resources={r"/api/*": {"origins": cors_origins}})

fake_job_detector = FakeJobDetector()


def json_error(message: str, status_code: int = 400, details: Any = None):
    payload: dict[str, Any] = {"error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "ok",
            "service": "AI Recruitment Intelligence API",
            "version": "1.0.0",
        }
    )


@app.route("/api/resume/parse", methods=["POST"])
def resume_parse():
    if "resume" not in request.files:
        return json_error("No resume file uploaded. Use form field name 'resume'.")

    resume_file = request.files["resume"]
    if not resume_file.filename:
        return json_error("Uploaded file is empty.")

    if not allowed_resume_extension(resume_file.filename):
        return json_error("Unsupported file type. Allowed: PDF, DOCX, TXT.")

    try:
        resume_text = extract_text_from_uploaded_file(resume_file)
        if not resume_text.strip():
            return json_error("Could not extract readable text from the uploaded file.")

        parsed_resume = parse_resume_text(resume_text)
        recommended_jobs = recommend_jobs_for_resume(parsed_resume, limit=6)
        return jsonify(
            {
                "resume": parsed_resume,
                "resume_score": parsed_resume["resume_score"],
                "recommended_jobs": recommended_jobs,
            }
        )
    except ValueError as exc:
        return json_error(str(exc))
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error("Resume parsing failed.", status_code=500, details=str(exc))


@app.route("/api/job/analyze", methods=["POST"])
def job_analyze():
    payload = request.get_json(silent=True) or {}
    job_description = (payload.get("job_description") or "").strip()

    if not job_description:
        return json_error("Missing 'job_description' in request body.")

    try:
        analysis = analyze_job_description(job_description)
        return jsonify(analysis)
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error("Job description analysis failed.", status_code=500, details=str(exc))


@app.route("/api/job/match", methods=["POST"])
def job_match():
    """
    Supports:
    1) multipart/form-data with fields:
       - resume (file)
       - job_description (text)
    2) application/json with fields:
       - job_description
       - resume_text (optional)
       - resume_parsed (optional)
    """
    resume_data = None
    job_description = ""

    if request.content_type and "multipart/form-data" in request.content_type:
        job_description = (request.form.get("job_description") or "").strip()
        if "resume" in request.files and request.files["resume"].filename:
            resume_file = request.files["resume"]
            if not allowed_resume_extension(resume_file.filename):
                return json_error("Unsupported resume type. Allowed: PDF, DOCX, TXT.")
            resume_text = extract_text_from_uploaded_file(resume_file)
            resume_data = parse_resume_text(resume_text)
    else:
        payload = request.get_json(silent=True) or {}
        job_description = (payload.get("job_description") or "").strip()

        if isinstance(payload.get("resume_parsed"), dict):
            resume_data = payload["resume_parsed"]
        elif payload.get("resume_text"):
            resume_data = parse_resume_text(payload["resume_text"])

    if not job_description:
        return json_error("Missing 'job_description'.")

    if resume_data is None:
        return json_error(
            "Missing resume input. Provide 'resume' file, 'resume_text', or 'resume_parsed'."
        )

    try:
        job_data = analyze_job_description(job_description)
        match_result = calculate_job_match(resume_data, job_data)
        return jsonify(
            {
                "match": match_result,
                "job_analysis": job_data,
            }
        )
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error("Job matching failed.", status_code=500, details=str(exc))


@app.route("/api/fake-job/detect", methods=["POST"])
def fake_job_detect():
    payload = request.get_json(silent=True) or {}
    job_url = (payload.get("job_url") or "").strip()
    job_text = (payload.get("job_text") or "").strip()

    if not job_url and not job_text:
        return json_error("Provide at least one of: 'job_url' or 'job_text'.")

    try:
        result = fake_job_detector.analyze(job_url=job_url, fallback_text=job_text)
        return jsonify(result)
    except ValueError as exc:
        return json_error(str(exc))
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error(
            "Fake job detection failed.",
            status_code=500,
            details=str(exc),
        )


@app.route("/api/jobs/recommend", methods=["POST"])
def recommend_jobs():
    payload = request.get_json(silent=True) or {}
    resume_data = payload.get("resume_parsed")
    resume_text = payload.get("resume_text")

    if not isinstance(resume_data, dict):
        if resume_text:
            resume_data = parse_resume_text(str(resume_text))
        else:
            return json_error("Provide 'resume_parsed' or 'resume_text' for recommendation.")

    try:
        recommendations = recommend_jobs_for_resume(resume_data, limit=8)
        return jsonify({"recommended_jobs": recommendations})
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error("Job recommendation failed.", status_code=500, details=str(exc))


@app.route("/api/resume-ai/generate", methods=["POST"])
def resume_ai_generate():
    payload = request.get_json(silent=True) or {}
    source_mode = (payload.get("source_mode") or "scratch").strip().lower()
    job_description = (payload.get("job_description") or "").strip()
    scratch_profile = payload.get("scratch_profile") or {}
    resume_data = payload.get("resume_parsed")
    resume_text = payload.get("resume_text")

    if source_mode not in {"scratch", "existing"}:
        return json_error("Invalid 'source_mode'. Use 'scratch' or 'existing'.")

    if not job_description:
        return json_error("Missing 'job_description'.")

    if source_mode == "existing" and not isinstance(resume_data, dict):
        if resume_text:
            resume_data = parse_resume_text(str(resume_text))
        else:
            return json_error("For existing mode, provide 'resume_parsed' or 'resume_text'.")

    try:
        result = generate_resume_ai_assets(
            source_mode=source_mode,
            job_description=job_description,
            scratch_profile=scratch_profile if source_mode == "scratch" else None,
            resume_parsed=resume_data if source_mode == "existing" else None,
        )
        return jsonify(result)
    except ValueError as exc:
        return json_error(str(exc))
    except Exception as exc:  # pragma: no cover - fallback guard
        return json_error("Resume AI generation failed.", status_code=500, details=str(exc))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
