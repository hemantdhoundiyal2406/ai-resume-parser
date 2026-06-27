import re
from pathlib import Path


try:
    import fitz
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import spacy
except ImportError:
    spacy = None


SAMPLE_SKILLS = [
    "Python",
    "JavaScript",
    "React",
    "Node.js",
    "Laravel",
    "PHP",
    "Flask",
    "Django",
    "SQL",
    "MongoDB",
    "REST API",
    "Machine Learning",
    "NLP",
    "LangChain",
    "OpenAI",
    "Hugging Face",
    "HTML",
    "CSS",
    "Bootstrap",
]

SECTION_HEADINGS = [
    "summary",
    "objective",
    "skills",
    "technical skills",
    "education",
    "academic background",
    "qualifications",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "projects",
    "personal projects",
    "academic projects",
    "certifications",
]

_NLP = None


def get_nlp():
    """Load spaCy when available. If the model is missing, use regex fallback."""
    global _NLP
    if _NLP is not None:
        return _NLP

    if spacy is None:
        _NLP = None
        return _NLP

    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        _NLP = None
    return _NLP


def extract_text_from_file(file_path):
    """Read text from a PDF or DOCX resume."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def extract_text_from_pdf(file_path):
    """Extract text from every page in a PDF file."""
    if fitz is None:
        raise ImportError("PyMuPDF is required to read PDF files. Install requirements.txt.")

    text_parts = []
    with fitz.open(file_path) as document:
        for page in document:
            text_parts.append(page.get_text())
    return clean_text("\n".join(text_parts))


def extract_text_from_docx(file_path):
    """Extract text from every paragraph in a DOCX file."""
    if Document is None:
        raise ImportError("python-docx is required to read DOCX files. Install requirements.txt.")

    document = Document(file_path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return clean_text("\n".join(paragraphs))


def clean_text(text):
    """Normalize whitespace so later regex and section parsing are easier."""
    text = text.replace("\r", "\n").replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_resume_text(text):
    """Run local parsing. This is used when OpenAI is missing or as a backup."""
    text = clean_text(text)
    result = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "projects": extract_projects(text),
    }
    result["summary"] = build_local_summary(result)
    return result


def extract_email(text):
    """Find the first email address in the resume."""
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def extract_phone(text):
    """Find a likely phone number. This supports common international formats."""
    phone_pattern = r"(\+?\d[\d\s().-]{8,}\d)"
    matches = re.findall(phone_pattern, text)
    for match in matches:
        digits = re.sub(r"\D", "", match)
        if 10 <= len(digits) <= 15:
            return match.strip()
    return ""


def extract_name(text):
    """Use spaCy PERSON detection first, then fall back to the first clean line."""
    nlp = get_nlp()
    if nlp:
        doc = nlp(text[:1200])
        for entity in doc.ents:
            if entity.label_ == "PERSON" and 1 <= len(entity.text.split()) <= 4:
                return entity.text.strip()

    for line in text.splitlines()[:12]:
        line = line.strip(" -|")
        if not line:
            continue
        lower_line = line.lower()
        has_contact_info = "@" in line or re.search(r"\d{5,}", line)
        looks_like_heading = any(word in lower_line for word in ["resume", "curriculum", "email", "phone"])
        if not has_contact_info and not looks_like_heading and 1 <= len(line.split()) <= 5:
            return line
    return "Unknown Candidate"


def extract_skills(text):
    """Return sample skills that are mentioned in the resume."""
    found_skills = []
    lower_text = text.lower()
    for skill in SAMPLE_SKILLS:
        if skill.lower() in lower_text:
            found_skills.append(skill)
    return found_skills


def get_lines(text):
    """Split resume text into clean, non-empty lines."""
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip()]


def is_section_heading(line):
    """Check whether a line looks like a resume section heading."""
    normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
    return normalized in SECTION_HEADINGS or normalized.endswith(" experience")


def extract_section(text, wanted_headings):
    """Collect lines after a heading until the next known resume heading."""
    lines = get_lines(text)
    collected = []
    inside_section = False

    for line in lines:
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        if normalized in wanted_headings:
            inside_section = True
            continue

        if inside_section and is_section_heading(line):
            break

        if inside_section:
            collected.append(line)

    return collected[:12]


def extract_education(text):
    """Extract education from a section, or find lines with common degree words."""
    section = extract_section(text, {"education", "academic background", "qualifications"})
    if section:
        return section

    degree_words = [
        "bachelor",
        "master",
        "b.tech",
        "b.e.",
        "m.tech",
        "mba",
        "bca",
        "mca",
        "university",
        "college",
        "institute",
        "degree",
        "diploma",
    ]
    return keyword_lines(text, degree_words, limit=8)


def extract_experience(text):
    """Extract work experience from a section, or find likely experience lines."""
    section = extract_section(
        text,
        {"experience", "work experience", "professional experience", "employment"},
    )
    if section:
        return section

    experience_words = ["company", "developer", "engineer", "intern", "manager", "worked", "experience"]
    return keyword_lines(text, experience_words, limit=10)


def extract_projects(text):
    """Extract projects from a projects section or project-like lines."""
    section = extract_section(text, {"projects", "personal projects", "academic projects"})
    if section:
        return section

    return keyword_lines(text, ["project", "built", "created", "developed"], limit=10)


def keyword_lines(text, keywords, limit=8):
    """Return lines that contain any of the provided keywords."""
    matches = []
    for line in get_lines(text):
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in keywords):
            matches.append(line)
        if len(matches) >= limit:
            break
    return matches


def build_local_summary(result):
    """Create a simple summary without using any external AI service."""
    name = result.get("name") or "The candidate"
    skills = result.get("skills") or []
    education_count = len(result.get("education") or [])
    experience_count = len(result.get("experience") or [])
    project_count = len(result.get("projects") or [])

    if skills:
        skill_text = ", ".join(skills[:6])
        summary = f"{name} has resume evidence for skills including {skill_text}."
    else:
        summary = f"{name} has a resume that could be parsed locally, but no sample skills were detected."

    details = []
    if education_count:
        details.append(f"{education_count} education item(s)")
    if experience_count:
        details.append(f"{experience_count} experience item(s)")
    if project_count:
        details.append(f"{project_count} project item(s)")

    if details:
        summary += " The resume also includes " + ", ".join(details) + "."

    return summary
