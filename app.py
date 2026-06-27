import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from services.ai_service import analyze_resume_with_openai
from services.database import get_all_resumes, get_resume_by_id, init_db, save_resume
from services.parser import extract_text_from_file, parse_resume_text
from services.skill_matcher import compare_resume_to_job


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", DATA_DIR / "uploads"))
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

init_db()
UPLOAD_FOLDER.mkdir(exist_ok=True)


def allowed_file(filename):
    """Check that the uploaded file has a supported extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def prefer_ai_value(ai_data, local_data, key):
    """Use OpenAI output when present, otherwise keep the local fallback value."""
    value = ai_data.get(key) if ai_data else None
    if isinstance(value, list):
        return value if value else local_data.get(key, [])
    return value or local_data.get(key, "")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/parse", methods=["POST"])
def parse_resume():
    uploaded_file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please upload a resume file.")
        return redirect(url_for("index"))

    if not allowed_file(uploaded_file.filename):
        flash("Only PDF and DOCX files are supported.")
        return redirect(url_for("index"))

    safe_name = secure_filename(uploaded_file.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = app.config["UPLOAD_FOLDER"] / stored_name
    uploaded_file.save(file_path)

    try:
        resume_text = extract_text_from_file(file_path)
        local_result = parse_resume_text(resume_text)
        ai_result = analyze_resume_with_openai(resume_text, job_description)

        parsed_data = {
            "filename": safe_name,
            "name": prefer_ai_value(ai_result, local_result, "name"),
            "email": local_result.get("email", ""),
            "phone": local_result.get("phone", ""),
            "skills": prefer_ai_value(ai_result, local_result, "skills"),
            "education": prefer_ai_value(ai_result, local_result, "education"),
            "experience": prefer_ai_value(ai_result, local_result, "experience"),
            "projects": prefer_ai_value(ai_result, local_result, "projects"),
            "summary": prefer_ai_value(ai_result, local_result, "summary"),
            "job_description": job_description,
            "resume_text": resume_text,
        }

        fit_result = compare_resume_to_job(
            parsed_data["skills"],
            job_description,
            resume_text,
        )
        parsed_data.update(fit_result)

        resume_id = save_resume(parsed_data)
        return redirect(url_for("result", resume_id=resume_id))
    except Exception as error:
        flash(f"Could not parse resume: {error}")
        return redirect(url_for("index"))


@app.route("/result/<int:resume_id>", methods=["GET"])
def result(resume_id):
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash("Resume result not found.")
        return redirect(url_for("index"))
    return render_template("result.html", resume=resume)


@app.route("/resumes", methods=["GET"])
def resumes():
    all_resumes = get_all_resumes()
    return render_template("resumes.html", resumes=all_resumes)


@app.route("/resume/<int:resume_id>", methods=["GET"])
def detail(resume_id):
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash("Resume result not found.")
        return redirect(url_for("resumes"))
    return render_template("detail.html", resume=resume)


@app.route("/resume/<int:resume_id>/download-json", methods=["GET"])
def download_json(resume_id):
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash("Resume result not found.")
        return redirect(url_for("resumes"))

    json_text = json.dumps(resume, indent=2)
    filename = f"parsed_resume_{resume_id}.json"
    return Response(
        json_text,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(debug=True)
