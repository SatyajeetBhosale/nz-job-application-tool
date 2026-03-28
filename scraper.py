"""
scraper.py — Seek.nz Job Scraper
Searches for Change Manager jobs in New Zealand and saves results to jobs.json
"""

import json
import time
from playwright.sync_api import sync_playwright

# ── CONFIG ──────────────────────────────────────────────────────────────────
SEARCH_ROLES = ["change-manager"]          # Add more roles here later
LOCATION     = "New-Zealand"
MAX_JOBS     = 20                          # How many jobs to scrape per role
OUTPUT_FILE  = "jobs.json"
# ────────────────────────────────────────────────────────────────────────────


def build_search_url(role: str, location: str) -> str:
    """Build the Seek.nz search URL for a given role and location."""
    return f"https://www.seek.co.nz/{role}-jobs/in-{location}"


def scrape_job_listings(page, search_url: str) -> list:
    """
    Open the search results page and extract all job cards.
    Returns a list of jobs with basic info (title, company, location, link).
    """
    print(f"\n🔍 Searching: {search_url}")
    page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)  # Let the page settle

    jobs = []

    # Find all job card links on the page
    # Save HTML for inspection if needed
    html = page.content()
    with open("seek_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("💾 Page HTML saved to seek_debug.html for inspection")

    # Try multiple selectors — Seek.nz changes these occasionally
    job_cards = (
        page.query_selector_all("article[data-testid='job-card']") or
        page.query_selector_all("[data-automation='normalJob']") or
        page.query_selector_all("[data-job-id]") or
        page.query_selector_all("article")
    )

    if not job_cards:
        print("⚠️  No job cards found. Seek.nz may have changed its layout.")
        return jobs

    print(f"✅ Found {len(job_cards)} job cards")

    for card in job_cards[:MAX_JOBS]:
        try:
            # Extract job title
            title_el = card.query_selector("a[data-automation='jobTitle']")
            title = title_el.inner_text().strip() if title_el else "Unknown"

            # Extract job URL
            link = title_el.get_attribute("href") if title_el else None
            full_url = f"https://www.seek.co.nz{link}" if link else None

            # Extract company name
            company_el = card.query_selector("a[data-automation='jobCompany']")
            company = company_el.inner_text().strip() if company_el else "Unknown"

            # Extract location
            location_el = card.query_selector("a[data-automation='jobLocation']")
            location = location_el.inner_text().strip() if location_el else "Unknown"

            # Extract salary (not always present)
            salary_el = card.query_selector("[data-automation='jobSalary']")
            salary = salary_el.inner_text().strip() if salary_el else "Not listed"

            jobs.append({
                "title":     title,
                "company":   company,
                "location":  location,
                "salary":    salary,
                "apply_url": full_url,
                "description": "",   # Filled in next step
                "status":    "new"   # new / approved / skipped
            })

        except Exception as e:
            print(f"  ⚠️  Skipped a card due to error: {e}")
            continue

    return jobs


def scrape_job_description(page, job: dict) -> str:
    """
    Visit the individual job page and extract the full job description.
    """
    if not job["apply_url"]:
        return ""

    try:
        page.goto(job["apply_url"], wait_until="domcontentloaded", timeout=60000)
        time.sleep(1)

        # Seek.nz job description container
        desc_el = page.query_selector("[data-automation='jobDescription']")
        if desc_el:
            return desc_el.inner_text().strip()
        else:
            return "Description not found"

    except Exception as e:
        print(f"  ⚠️  Could not fetch description: {e}")
        return ""


def save_jobs(jobs: list, filepath: str):
    """Save jobs list to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved {len(jobs)} jobs to {filepath}")


def main():
    all_jobs = []

    with sync_playwright() as p:
        # Launch Chromium browser — visible mode bypasses Cloudflare bot detection
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()

        # Set a real browser user-agent so Seek doesn't block us
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        })

        for role in SEARCH_ROLES:
            url = build_search_url(role, LOCATION)
            jobs = scrape_job_listings(page, url)

            # For each job, fetch the full description
            for i, job in enumerate(jobs):
                print(f"  📄 Fetching description {i+1}/{len(jobs)}: {job['title']} @ {job['company']}")
                job["description"] = scrape_job_description(page, job)
                time.sleep(1)  # Be polite — don't hammer the server

            all_jobs.extend(jobs)

        browser.close()

    if all_jobs:
        save_jobs(all_jobs, OUTPUT_FILE)
        print(f"\n✅ Done! {len(all_jobs)} jobs saved to {OUTPUT_FILE}")
        print("Next step: run dashboard.py to review jobs")
    else:
        print("\n❌ No jobs found. Check your internet connection or try again.")


if __name__ == "__main__":
    main()
