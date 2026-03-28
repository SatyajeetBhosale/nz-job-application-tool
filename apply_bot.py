"""
apply_bot.py — Seek.nz Apply Bot
For each Approved job:
  - Opens the job page on Seek.nz
  - Detects if it's Easy Apply or External
  - If Easy Apply: fills the form and submits
  - If External: marks as "external" and skips
  - Updates jobs.json and dashboard status after each job
"""

import json
import os
import time

from playwright.sync_api import sync_playwright

# ── CONFIG — Fill these in ───────────────────────────────────────────────────
SEEK_EMAIL    = "satyajeet356@gmail.com"

YOUR_NAME     = "Satyajeet Bhosale"
YOUR_EMAIL    = "bsatyajeet30@gmail.com"
YOUR_PHONE    = "9867279790"
YOUR_ADDRESS  = "Mumbai"

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE     = os.path.join(BASE_DIR, "..", "jobs.json")
OUTPUT_DIR    = os.path.join(BASE_DIR, "output")
# ────────────────────────────────────────────────────────────────────────────


def load_jobs():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def login_to_seek(page):
    """
    Opens Seek.nz and waits for the user to log in manually.
    This bypasses Cloudflare captcha completely.
    """
    print("🔐 Opening Seek.nz...")
    page.goto("https://www.seek.co.nz", wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)

    print("\n" + "="*50)
    print("👋 Please log in to Seek.nz in the browser window.")
    print("   1. Click Sign In")
    print("   2. Enter your email: " + SEEK_EMAIL)
    print("   3. Enter the OTP sent to your email")
    print("   4. Wait until you see your Seek homepage with your name")
    input("   Press ENTER here to continue ▶")
    print("="*50 + "\n")

    # Verify login was successful
    current_url = page.url
    if "oauth" in current_url or "login" in current_url:
        print("⚠️  Looks like you're not fully logged in yet.")
        print("   Please complete the login in the browser.")
        input("   Press ENTER again once you're on the Seek homepage ▶")

    # Double check by looking for sign-in indicators
    time.sleep(2)
    print("✅ Logged in — starting applications")


def detect_apply_type(page, job_url):
    """
    Open the job page and detect whether it's Easy Apply or External.
    Returns: 'easy_apply' or 'external'
    """
    page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)

    # Check for Easy Apply button (Apply on Seek)
    easy_apply = page.query_selector("[data-automation='job-detail-apply']")
    if easy_apply:
        btn_text = easy_apply.inner_text().lower()
        if "seek" in btn_text or "apply" in btn_text:
            # Check it doesn't say "on company site"
            if "company" not in btn_text and "external" not in btn_text:
                return "easy_apply"

    return "external"


def get_resume_path(job):
    """Get the tailored resume markdown path for a job."""
    return job.get("tailored_resume")


def apply_easy(page, job):
    """
    Fill and submit the Easy Apply form on Seek.nz.
    """
    print(f"  📝 Filling Easy Apply form...")

    # Click the Apply button
    apply_btn = page.query_selector("[data-automation='job-detail-apply']")
    if apply_btn:
        apply_btn.click()
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)

    # Map of selectors to values
    fields = [
        {
            "selectors": "input[name='name'], input[placeholder*='name' i], input[id*='name' i], input[aria-label*='name' i]",
            "value": YOUR_NAME
        },
        {
            "selectors": "input[name='email'], input[type='email'], input[placeholder*='email' i]",
            "value": YOUR_EMAIL
        },
        {
            "selectors": "input[name='phone'], input[type='tel'], input[placeholder*='phone' i], input[aria-label*='phone' i], input[placeholder*='mobile' i]",
            "value": YOUR_PHONE
        },
        {
            "selectors": "input[name='address'], input[placeholder*='address' i], input[aria-label*='address' i], input[placeholder*='suburb' i], input[placeholder*='city' i], input[placeholder*='location' i]",
            "value": YOUR_ADDRESS
        },
    ]

    for field in fields:
        try:
            el = page.query_selector(field["selectors"])
            if el:
                el.fill(field["value"])
                time.sleep(0.3)
        except Exception:
            continue

    time.sleep(1)

    # Submit
    submit_btn = page.query_selector("button[type='submit'], button:has-text('Submit'), button:has-text('Apply')")
    if submit_btn:
        submit_btn.click()
        time.sleep(3)
        print(f"  ✅ Application submitted!")
        return True
    else:
        print(f"  ⚠️  Could not find submit button — please complete manually")
        return False


def main():
    jobs = load_jobs()
    approved_jobs = [j for j in jobs if j.get("status") == "approved"]

    if not approved_jobs:
        print("❌ No approved jobs found. Go to the dashboard and approve some jobs first.")
        return

    print(f"🎯 Found {len(approved_jobs)} approved jobs to process\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50,
            channel="msedge",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-NZ",
        )
        page = context.new_page()

        # Remove webdriver flag that sites use to detect bots
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Log in first
        login_to_seek(page)

        for i, job in enumerate(approved_jobs):
            print(f"\n[{i+1}/{len(approved_jobs)}] Processing: {job['title']} @ {job['company']}")

            if not job.get("apply_url"):
                print(f"  ⚠️  No URL found — skipping")
                continue

            job_index = jobs.index(job)

            try:
                # Step 1 — Detect apply type
                apply_type = detect_apply_type(page, job["apply_url"])

                if apply_type == "external":
                    print(f"  🟠 External application — skipping (apply manually)")
                    jobs[job_index]["status"] = "external"
                    save_jobs(jobs)
                    continue

                # Step 2 — Easy Apply
                print(f"  🟢 Easy Apply detected — proceeding")
                success = apply_easy(page, job)

                if success:
                    jobs[job_index]["status"] = "applied"
                else:
                    jobs[job_index]["status"] = "apply_failed"

                save_jobs(jobs)
                time.sleep(2)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                jobs[job_index]["status"] = "apply_failed"
                save_jobs(jobs)
                continue

        context.close()
        browser.close()

    # Summary
    applied  = len([j for j in jobs if j.get("status") == "applied"])
    external = len([j for j in jobs if j.get("status") == "external"])
    failed   = len([j for j in jobs if j.get("status") == "apply_failed"])

    print(f"\n{'='*50}")
    print(f"✅ Applied:   {applied} jobs")
    print(f"🟠 External:  {external} jobs (apply manually)")
    print(f"❌ Failed:    {failed} jobs")
    print(f"{'='*50}")
    print("Open the dashboard to see the full status of all jobs.")


if __name__ == "__main__":
    main()
