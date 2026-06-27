import json
import os


def analyze_resume_with_openai(resume_text, job_description=""):
    """
    Ask OpenAI to extract structured resume data.
    If the API key or package is missing, return None so the app can use fallback logic.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""
You are an AI resume parser. Extract useful candidate information from the resume.
Return only valid JSON with these keys:
name, skills, education, experience, projects, summary.

Rules:
- skills, education, experience, and projects must be JSON arrays of strings.
- summary must be a short recruiter-friendly paragraph.
- Do not invent details that are not supported by the resume.

Resume text:
{resume_text[:12000]}

Job description, if provided:
{job_description[:5000]}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return clean JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return parse_json_response(content)
    except Exception:
        return None


def parse_json_response(content):
    """Parse OpenAI JSON, including common markdown fenced JSON output."""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json", "", 1).strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None

    return {
        "name": data.get("name", ""),
        "skills": ensure_list(data.get("skills")),
        "education": ensure_list(data.get("education")),
        "experience": ensure_list(data.get("experience")),
        "projects": ensure_list(data.get("projects")),
        "summary": data.get("summary", ""),
    }


def ensure_list(value):
    """Make sure template fields always receive a list."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
