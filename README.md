
# Job Alert Automation (Planning Engineer @ 8 AM KSA)

A GitHub Actions workflow that searches the web every day at **08:00 Asia/Riyadh** for **Planning Engineer** roles on popular job boards and emails you a daily digest.

> ⚠️ Notes: Results are collected via general web search to the specified job boards. Sites can change layout or block scraping. For higher reliability, consider an official API or a paid search API service.

## Quick Start (Step by Step)

### 1) Prepare Email Credentials (Gmail recommended)
1. Go to **Google Account → Security → 2‑Step Verification** and enable it.
2. Go to **Security → App Passwords**.
3. Create an app password (type: Mail, device: Other → "GitHub Actions").
4. Save the 16‑character password; you'll add it as a secret below.

> Using another SMTP? Set `SMTP_HOST`, `SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS` accordingly.

### 2) Create the GitHub Repository
1. On GitHub, click **New → Create repository** (e.g., `job-alert-automation`).
2. Clone it locally or upload the files in this folder:
   - `job_scraper.py`
   - `.github/workflows/daily-job-search.yml`
   - `requirements.txt` (optional)

### 3) Add Secrets (for email)
- Go to **Repo → Settings → Secrets and variables → Actions → New repository secret** and add:
  - `EMAIL_USER` → your email address (e.g., `you@gmail.com`)
  - `EMAIL_PASS` → the app password you generated
  - `EMAIL_RECEIVER` → where to receive the digest

### 4) (Optional) Add Variables (to customize filters)
- Go to **Repo → Settings → Secrets and variables → Actions → Variables** and add any of:
  - `JOB_QUERY` → default: `("Planning Engineer" OR "Project Planning Engineer")`
  - `JOB_REGIONS` → default: `Saudi Arabia,Remote`
  - `JOB_SITES` → default: `linkedin.com/jobs,indeed.com,bayt.com,gulftalent.com,glassdoor.com`
  - `RESULTS_LIMIT` → default: `40`
  - `TIME_FILTER` → default: `d` (hour=`h`, day=`d`, week=`w`, month=`m`)

### 5) Push the Files
- Commit and push the files to the default branch (`main`).
- The workflow is already scheduled for **05:00 UTC** (= **08:00 Asia/Riyadh**).

### 6) Test Manually Now
- Go to **Actions** tab → **Daily Job Search** → **Run workflow**.
- Check your inbox for the email. If nothing arrives, check the workflow logs:
  - SMTP login errors → verify `EMAIL_*` secrets.
  - No results → widen `JOB_SITES`/`JOB_REGIONS`, set `TIME_FILTER` to `w`.

### 7) Customize (Optional)
- Add more Gulf/Global sites to `JOB_SITES` separated by commas.
- Change query to include synonyms: `"Senior Planning Engineer"`, `"Planning & Scheduling"`, `"Primavera P6"`.
- Increase `RESULTS_LIMIT` for a longer email.

## How it Works
- GitHub Actions (UTC) triggers daily at 05:00.
- Python script runs a web search with time window (default: past day).
- Results are deduplicated, grouped by domain, and emailed as HTML.

## Troubleshooting
- **Gmail blocks sign‑in**: Ensure you used an **App Password** and SMTP SSL (465).
- **Too few results**: Expand `JOB_SITES`, add regions (`UAE,Qatar,Remote`), set `TIME_FILTER=w`.
- **Scraping blocked or unstable**: Use an official API or a search API provider, then replace `fetch_jobs()` accordingly.
