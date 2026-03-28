"""
dashboard.py — Job Review Dashboard
Browse scraped jobs, read tailored resumes, and approve or skip each one.
Run with: streamlit run dashboard.py
"""

import json
import os
import streamlit as st

# ── CONFIG ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE  = os.path.join(BASE_DIR, "..", "jobs.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
# ────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NZ Job Review Dashboard",
    page_icon="🇳🇿",
    layout="wide"
)

# ── LOAD & SAVE JOBS ─────────────────────────────────────────────────────────

def load_jobs():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

def load_tailored_resume(job):
    path = job.get("tailored_resume")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# ── HEADER ───────────────────────────────────────────────────────────────────

st.title("🇳🇿 NZ Job Application Dashboard")
st.caption("Review tailored resumes, approve jobs, and track your applications.")

# ── LOAD DATA ────────────────────────────────────────────────────────────────

jobs = load_jobs()

# ── SIDEBAR — STATS & FILTERS ────────────────────────────────────────────────

with st.sidebar:
    st.header("📊 Summary")

    total         = len(jobs)
    tailored      = len([j for j in jobs if j.get("status") == "tailored"])
    approved      = len([j for j in jobs if j.get("status") == "approved"])
    skipped       = len([j for j in jobs if j.get("status") == "skipped"])
    applied_seek  = len([j for j in jobs if j.get("status") == "applied"])
    applied_manual= len([j for j in jobs if j.get("status") == "applied_manually"])
    external      = len([j for j in jobs if j.get("status") == "external"])

    st.metric("Total Jobs", total)
    col1, col2 = st.columns(2)
    col1.metric("✅ Approved", approved)
    col2.metric("⏭️ Skipped", skipped)
    col1.metric("🎯 Applied", applied_seek + applied_manual)
    col2.metric("🌐 External", external)

    st.divider()

    st.header("🔍 Filter")
    status_filter = st.selectbox(
        "Show jobs with status:",
        ["All", "approved", "tailored", "applied_manually", "applied", "external", "skipped", "new"]
    )

    st.divider()
    st.caption("💡 Tip: Approve → copy tailored resume → apply on company site → mark Applied Manually")

# ── FILTER JOBS ──────────────────────────────────────────────────────────────

if status_filter == "All":
    filtered_jobs = jobs
else:
    filtered_jobs = [j for j in jobs if j.get("status") == status_filter]

if not filtered_jobs:
    st.info(f"No jobs with status: {status_filter}")
    st.stop()

# ── JOB LIST ─────────────────────────────────────────────────────────────────

st.subheader(f"Showing {len(filtered_jobs)} jobs")

for i, job in enumerate(filtered_jobs):
    status = job.get("status", "new")
    badge = {
        "tailored":         "🟡",
        "approved":         "🟢",
        "skipped":          "🔴",
        "applied":          "🔵",
        "applied_manually": "✅",
        "external":         "🟠",
        "new":              "⚪"
    }.get(status, "⚪")

    with st.expander(f"{badge} {job['title']} @ {job['company']} — {job['location']}"):

        # ── APPLY BANNER (for approved jobs) ─────────────────────────────
        if status == "approved" and job.get("apply_url"):
            st.info(f"📌 Ready to apply → [**Open on Seek**]({job['apply_url']}) — use the tailored resume below")

        if status == "applied_manually":
            st.success("✅ Applied manually — tracked")

        if status == "external":
            st.warning(f"🌐 External application — [Open on Seek]({job['apply_url']}) and apply on company site")

        # ── JOB DETAILS + RESUME SIDE BY SIDE ────────────────────────────
        left, right = st.columns(2)

        with left:
            st.markdown("### 📋 Job Details")
            st.markdown(f"**Company:** {job['company']}")
            st.markdown(f"**Location:** {job['location']}")
            st.markdown(f"**Salary:** {job['salary']}")
            st.markdown(f"**Status:** `{status}`")
            if job.get("apply_url"):
                st.markdown(f"[🔗 Open Job on Seek]({job['apply_url']})")

            st.divider()
            st.markdown("### 📝 Job Description")
            st.markdown(
                f"<div style='height:380px;overflow-y:auto;font-size:13px;line-height:1.6;'>{job.get('description','No description available')}</div>",
                unsafe_allow_html=True
            )

        with right:
            st.markdown("### 📄 Tailored Resume")
            tailored_resume = load_tailored_resume(job)
            if tailored_resume:
                # Copy button
                st.download_button(
                    label="⬇️ Download Tailored Resume",
                    data=tailored_resume,
                    file_name=f"resume_{job['company'].replace(' ','_')}.md",
                    mime="text/markdown",
                    key=f"download_{i}"
                )
                st.markdown(
                    f"<div style='height:420px;overflow-y:auto;font-size:13px;line-height:1.6;'>{tailored_resume}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.warning("No tailored resume found. Run tailor.py first.")

        # ── ACTION BUTTONS ────────────────────────────────────────────────
        st.divider()
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        job_index = jobs.index(job)

        with col1:
            if st.button("✅ Approve", key=f"approve_{i}"):
                jobs[job_index]["status"] = "approved"
                save_jobs(jobs)
                st.rerun()

        with col2:
            if st.button("✅ Applied", key=f"applied_{i}"):
                jobs[job_index]["status"] = "applied_manually"
                save_jobs(jobs)
                st.rerun()

        with col3:
            if st.button("⏭️ Skip", key=f"skip_{i}"):
                jobs[job_index]["status"] = "skipped"
                save_jobs(jobs)
                st.rerun()
