"""
tailor.py — Resume Tailor
Reads each job from jobs.json, sends it to Claude AI with the base resume,
and saves a tailored resume as a Markdown file in the output/ folder.
"""

import json
import os
import re

import anthropic

# ── CONFIG ──────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE       = os.path.join(BASE_DIR, "..", "jobs.json")
BASE_RESUME     = os.path.join(BASE_DIR, "base_resume.md")
OUTPUT_FOLDER   = os.path.join(BASE_DIR, "output")
# ────────────────────────────────────────────────────────────────────────────

# Load API key from .env file — handles UTF-16 encoding from Windows PowerShell
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    raw = open(env_path, 'rb').read()
    # Strip BOM and null bytes caused by UTF-16 encoding
    cleaned = raw.replace(b'\xff\xfe', b'').replace(b'\xfe\xff', b'').replace(b'\x00', b'')
    for line in cleaned.decode('utf-8').strip().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in .env file. Please check your setup.")
    exit(1)

client = anthropic.Anthropic(api_key=api_key)


def load_jobs(filepath: str) -> list:
    """Load jobs from jobs.json."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_base_resume(filepath: str) -> str:
    """Load the base resume markdown."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def safe_filename(text: str) -> str:
    """Convert text to a safe filename."""
    return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")[:40]


def tailor_resume(job: dict, base_resume: str) -> str:
    """
    Send the job description and base resume to Claude AI.
    Returns a tailored resume as Markdown text.
    """
    prompt = f"""You are an expert resume writer helping a senior professional tailor their resume for a specific job.

## Job Details
**Title:** {job['title']}
**Company:** {job['company']}
**Location:** {job['location']}

## Job Description
{job['description']}

## Candidate's Base Resume
{base_resume}

## Your Task
Rewrite the resume to strongly align with this specific job. Follow these rules:
1. Do NOT invent or add any new experience, skills, or qualifications that are not in the base resume
2. Rewrite the Overview and Summary sections to mirror the language and priorities of the job description
3. Reorder bullet points so the most relevant experience appears first
4. Use keywords from the job description naturally throughout
5. De-emphasise bullet points that are not relevant to this role
6. Keep the same structure and formatting (Markdown)
7. Keep all facts, dates, company names, and numbers exactly as they are

Return only the tailored resume in Markdown format. No explanations or commentary."""

    print(f"  🤖 Sending to Claude AI...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def save_tailored_resume(content: str, job: dict, folder: str):
    """Save the tailored resume to the output folder."""
    os.makedirs(folder, exist_ok=True)

    company = safe_filename(job['company'])
    title   = safe_filename(job['title'])
    filename = f"resume_{company}_{title}.md"
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def main():
    print("📄 Loading jobs and base resume...")
    jobs        = load_jobs(JOBS_FILE)
    base_resume = load_base_resume(BASE_RESUME)

    # Only process jobs with status "new" or "approved"
    jobs_to_tailor = [j for j in jobs if j.get("status") in ("new", "approved") and j.get("description")]

    print(f"✅ Found {len(jobs_to_tailor)} jobs to tailor\n")

    for i, job in enumerate(jobs_to_tailor):
        print(f"[{i+1}/{len(jobs_to_tailor)}] Tailoring for: {job['title']} @ {job['company']}")

        try:
            tailored = tailor_resume(job, base_resume)
            filepath = save_tailored_resume(tailored, job, OUTPUT_FOLDER)

            # Update job status
            job["status"]          = "tailored"
            job["tailored_resume"] = filepath

            print(f"  ✅ Saved: {filepath}\n")

        except Exception as e:
            print(f"  ❌ Failed: {e}\n")
            continue

    # Save updated statuses back to jobs.json
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print("✅ All done! Check the output/ folder for tailored resumes.")


if __name__ == "__main__":
    main()
