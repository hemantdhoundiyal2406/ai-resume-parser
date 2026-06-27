import re

from services.parser import SAMPLE_SKILLS


STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "have",
    "that",
    "the",
    "this",
    "with",
    "will",
    "your",
    "you",
    "our",
    "using",
    "role",
    "work",
    "team",
    "experience",
}


def compare_resume_to_job(resume_skills, job_description, resume_text=""):
    """Compare extracted resume skills with skills mentioned in the job description."""
    job_description = job_description or ""
    if not job_description.strip():
        return {
            "matching_skills": [],
            "missing_skills": [],
            "job_fit_score": None,
        }

    required_skills = extract_skills_from_text(job_description)
    resume_skill_set = {normalize_skill(skill) for skill in resume_skills or []}
    resume_text_lower = resume_text.lower()

    matching_skills = []
    missing_skills = []
    for skill in required_skills:
        normalized = normalize_skill(skill)
        if normalized in resume_skill_set or skill.lower() in resume_text_lower:
            matching_skills.append(skill)
        else:
            missing_skills.append(skill)

    job_fit_score = calculate_fit_score(
        matching_skills,
        required_skills,
        resume_text,
        job_description,
    )

    return {
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "job_fit_score": job_fit_score,
    }


def extract_skills_from_text(text):
    """Find sample skills in a block of text."""
    lower_text = text.lower()
    return [skill for skill in SAMPLE_SKILLS if skill.lower() in lower_text]


def normalize_skill(skill):
    """Normalize skill names before comparing them."""
    return re.sub(r"[^a-z0-9]+", "", skill.lower())


def calculate_fit_score(matching_skills, required_skills, resume_text, job_description):
    """
    Calculate a simple 0-100 score.
    Skills are the main signal, and keyword overlap gives a small backup signal.
    """
    keyword_score = keyword_overlap_score(resume_text, job_description)

    if required_skills:
        skill_score = len(matching_skills) / len(required_skills)
        score = (skill_score * 0.75) + (keyword_score * 0.25)
    else:
        score = keyword_score

    return round(score * 100)


def keyword_overlap_score(resume_text, job_description):
    """Estimate similarity using simple word overlap for beginner-friendly fallback."""
    resume_words = important_words(resume_text)
    job_words = important_words(job_description)
    if not job_words:
        return 0

    overlap = resume_words.intersection(job_words)
    return min(len(overlap) / len(job_words), 1)


def important_words(text):
    """Return meaningful words and ignore very common filler words."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text.lower())
    return {word for word in words if word not in STOPWORDS}
