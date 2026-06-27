# AI Resume Parser + Skill Extractor

A beginner-friendly Flask project that uploads a PDF or DOCX resume, extracts candidate details, detects skills, compares the resume with a job description, generates a candidate summary, and saves everything in SQLite.

## Features

- Upload PDF and DOCX resumes
- Extract resume text
- Extract candidate name, email, phone, skills, education, experience, and projects
- Optional OpenAI API support for better structured extraction and summary
- Local fallback using regex, simple NLP rules, and optional spaCy
- Paste a job description and calculate a job-fit score
- Show matching skills and missing skills
- Save parsed results to SQLite
- Admin page for all parsed resumes
- Detail page for each parsed resume
- Download parsed result as JSON
- Clean Bootstrap UI

## Project Structure

```text
resume-ai-parser/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- README.md
|-- database.db          # auto-created locally when the app runs
|-- uploads/
|-- templates/
|   |-- index.html
|   |-- result.html
|   |-- resumes.html
|   `-- detail.html
|-- static/
|   |-- css/style.css
|   `-- js/main.js
`-- services/
    |-- parser.py
    |-- ai_service.py
    |-- skill_matcher.py
    `-- database.py
```

## Setup

1. Open the project folder:

```bash
cd resume-ai-parser
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Optional: install the spaCy English model for better name detection:

```bash
python -m spacy download en_core_web_sm
```

5. Create your environment file:

```bash
cp .env.example .env
```

6. Add your OpenAI key in `.env` if you want AI extraction:

```text
OPENAI_API_KEY=your_api_key_here
```

If `OPENAI_API_KEY` is empty, the app still works using local fallback logic.

7. Run the app:

```bash
python app.py
```

8. Open:

```text
http://127.0.0.1:5000
```

## Sample Skills List

The local parser and job matcher look for these skills:

Python, JavaScript, React, Node.js, Laravel, PHP, Flask, Django, SQL, MongoDB, REST API, Machine Learning, NLP, LangChain, OpenAI, Hugging Face, HTML, CSS, Bootstrap.

## How It Works

1. `app.py` receives the uploaded resume and job description.
2. `services/parser.py` extracts text from PDF or DOCX and finds local resume fields.
3. `services/ai_service.py` calls OpenAI only when `OPENAI_API_KEY` exists.
4. `services/skill_matcher.py` compares resume skills with the job description.
5. `services/database.py` saves the parsed result in `database.db`.

## Notes

- This project is intentionally simple for learning.
- Resume parsing is not perfect because resumes have many formats.
- OpenAI improves summary and structured extraction, but the fallback keeps the project usable without an API key.
