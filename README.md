# NZ Job Application Tool

An automated job search and resume tailoring tool for New Zealand jobs on Seek.nz. Built with Python, Playwright, Claude AI, and Streamlit.

---

## What It Does

| Step | Tool | What Happens |
|---|---|---|
| 1 | `scraper.py` | Searches Seek.nz and saves job listings to `jobs.json` |
| 2 | `tailor.py` | Uses Claude AI to tailor your resume for each job |
| 3 | `dashboard.py` | Review jobs and tailored resumes in a browser UI |
| 4 | `apply_bot.py` | Auto-applies to Seek Easy Apply jobs (optional) |

---

## Setup

### 1. Prerequisites
- Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- Git
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com)
- Microsoft Edge (for the apply bot)

### 2. Clone the repository
```bash
git clone https://github.com/SatyajeetBhosale/nz-job-application-tool.git
cd nz-job-application-tool
```

### 3. Create a virtual environment
```bash
python -m venv job-tool
job-tool\Scripts\activate        # Windows
source job-tool/bin/activate     # Mac/Linux
```

### 4. Install dependencies
```bash
pip install requests beautifulsoup4 playwright anthropic streamlit python-dotenv
playwright install chromium
```

### 5. Set up your API key
Copy `.env.example` to `.env` and add your Anthropic API key:
```bash
# Windows
python -c "f=open('.env','w',encoding='utf-8'); f.write('ANTHROPIC_API_KEY=your-key-here\n'); f.close()"
```

> ⚠️ Never commit your `.env` file — it is already in `.gitignore`

### 6. Add your resume
Replace the contents of `base_resume.md` with your own resume in Markdown format.

---

## Usage

### Step 1 — Scrape jobs
```bash
python scraper.py
```
- Opens a visible Edge browser (bypasses Cloudflare)
- Searches Seek.nz for your target role
- Saves results to `jobs.json`

To change the role or location, edit the config at the top of `scraper.py`:
```python
SEARCH_ROLES = ["change-manager"]   # change this
LOCATION     = "New-Zealand"
MAX_JOBS     = 20
```

### Step 2 — Tailor resumes
```bash
python tailor.py
```
- Reads each job from `jobs.json`
- Sends job description + your resume to Claude AI
- Saves tailored resumes to `output/` folder

### Step 3 — Review dashboard
```bash
streamlit run dashboard.py
```
- Opens in your browser automatically
- Review job description and tailored resume side by side
- Click **✅ Approve**, **⏭️ Skip**, or **✅ Applied** for each job
- Download tailored resume to upload on company sites

### Step 4 — Apply bot (optional)
```bash
python apply_bot.py
```
- Opens Edge browser
- You log in to Seek.nz manually (handles OTP and captcha)
- Bot detects Easy Apply vs External for each approved job
- Auto-fills and submits Easy Apply jobs
- Marks external jobs for manual application

> ⚠️ Most NZ jobs on Seek redirect to company ATS (Workday, Greenhouse). The bot handles Easy Apply only — external jobs must be applied to manually using the tailored resume from the dashboard.

---

## Project Structure

```
nz-job-application-tool/
├── scraper.py          # Seek.nz job scraper
├── tailor.py           # Claude AI resume tailor
├── dashboard.py        # Streamlit review dashboard
├── apply_bot.py        # Playwright apply bot
├── base_resume.md      # Your base resume (replace with your own)
├── ISSUES_LOG.md       # Common issues and fixes
├── .env.example        # API key template
├── .gitignore          # Protects .env and personal data
└── output/             # Tailored resumes (auto-generated, not committed)
```

---

## Known Issues & Fixes

See [ISSUES_LOG.md](ISSUES_LOG.md) for a full list of 14 issues encountered during development and how each was resolved.

Common ones:
- **Cloudflare blocking scraper** → use `headless=False`
- **PowerShell .env encoding** → create `.env` using Python, not `echo`
- **Session not maintained in apply bot** → log in manually before pressing Enter

---

## Tech Stack

| Library | Purpose |
|---|---|
| `playwright` | Browser automation for scraping and applying |
| `beautifulsoup4` | HTML parsing |
| `anthropic` | Claude AI for resume tailoring |
| `streamlit` | Review dashboard UI |
| `requests` | HTTP requests |

---

## Disclaimer

This tool is for **personal use only**. Automated scraping may conflict with Seek.nz's Terms of Service. Use responsibly.

---

## Author

**Satyajeet Bhosale** — Senior Agile Coach
| bsatyajeet30@gmail.com
