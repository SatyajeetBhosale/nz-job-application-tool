# Issues & Fixes Log — NZ Job Application Tool

---

### Issue 1 — Python not found in terminal
**Error:** `Python was not found; run without arguments to install from the Microsoft Store`
**Cause:** Windows has a fake Python alias pointing to Microsoft Store.
**Fix:** Installed Python manually from python.org with **"Add to PATH"** checked. Used full path `C:\Users\Satyajeet Bhosale\AppData\Local\Programs\Python\Python314\python.exe` for all commands.

---

### Issue 2 — pip install command split across two lines
**Error:** `playwright: The term 'playwright' is not recognized as the name of a cmdlet`
**Cause:** Copy-pasting long commands wraps across lines in PowerShell — second part runs as a separate command.
**Fix:** Always paste commands as one single line. Press End key to confirm cursor is at the end before pressing Enter.

---

### Issue 3 — Seek.nz scraper found no jobs (Timeout)
**Error:** `playwright._impl._errors.TimeoutError: Page.goto: Timeout 30000ms exceeded`
**Cause:** `wait_until="networkidle"` too strict — page never fully settled within 30 seconds.
**Fix:** Changed to `wait_until="domcontentloaded"` and increased timeout to 60 seconds.

---

### Issue 4 — Seek.nz scraper found no jobs (Cloudflare block)
**Error:** Scraper ran but returned 0 jobs. Debug HTML showed Cloudflare blocking page.
**Cause:** Playwright headless browser detected as a bot by Cloudflare.
**Fix:** Changed `headless=True` to `headless=False` — visible browser bypasses Cloudflare detection.

---

### Issue 5 — .env file encoding error (UnicodeDecodeError)
**Error:** `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0`
**Cause:** PowerShell's `echo` command saves files in **UTF-16** encoding, not UTF-8. Starts with BOM byte `0xff`.
**Fix:** Removed `load_dotenv()` entirely. Wrote custom code to read `.env` as raw bytes, strip null bytes and BOM, then decode as UTF-8. Created new `.env` using Python directly:
```
python -c "f=open('.env','w',encoding='utf-8'); f.write('ANTHROPIC_API_KEY=your-key\n'); f.close()"
```

---

### Issue 6 — .env file encoding error (embedded null character)
**Error:** `ValueError: embedded null character`
**Cause:** Even after editing, the file retained UTF-16 null bytes between each character.
**Fix:** Same as Issue 5 — rewrote file using Python with explicit `encoding='utf-8'`.

---

### Issue 7 — base_resume.md not found
**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'base_resume.md'`
**Cause:** Script looked for file relative to where the command was run (`D:\AgileOS`) not where the script lives (`D:\AgileOS\job-tool-app`).
**Fix:** Used `os.path.dirname(os.path.abspath(__file__))` to always resolve paths relative to the script's own location.

---

### Issue 8 — API key invalid (401 error)
**Error:** `authentication_error: invalid x-api-key`
**Cause:** API key got corrupted during the UTF-16 encoding mess — spaces were introduced into the key when rewriting the file.
**Fix:** Generated a new API key at console.anthropic.com. Recreated `.env` cleanly using Python.

---

### Issue 9 — Insufficient API credits (400 error)
**Error:** `Your credit balance is too low to access the Anthropic API`
**Cause:** New Anthropic account had no credits loaded.
**Fix:** Added $5 credit at console.anthropic.com → Plans & Billing.

---

### Issue 10 — Apply bot: Execution context destroyed (login page)
**Error:** `playwright._impl._errors.Error: Execution context was destroyed, most likely because of a navigation`
**Cause:** Page redirected during login while Playwright was still querying elements on the old page.
**Fix:** Added `page.wait_for_selector()` before querying fields and `page.wait_for_load_state("domcontentloaded")` after clicking submit.

---

### Issue 11 — Apply bot: Captcha not loading on Seek login page
**Error:** Browser opened but Seek.nz captcha/login page didn't render.
**Cause:** Playwright's default browser fingerprint detectable as a bot by Cloudflare.
**Fix:**
- Added `--disable-blink-features=AutomationControlled` launch flag
- Set realistic `user_agent`, `viewport`, and `locale` via browser context
- Added `navigator.webdriver = undefined` init script to hide bot fingerprint
- Switched from Chromium to **Microsoft Edge** (`channel="msedge"`) — faster and more trusted by sites

---

### Issue 12 — Apply bot: Session not maintained after manual login
**Error:** `Navigation interrupted by another navigation to oauth/integration` — Seek redirected to login again after user had already logged in.
**Cause:** After pressing Enter, the bot navigated to a job page but Seek detected no active session and redirected to OAuth.
**Fix:**
- Changed login approach to fully manual — bot opens seek.co.nz homepage, user logs in themselves
- Added session verification check after Enter is pressed — if URL still contains "oauth" or "login", prompts user to complete login before continuing

---

### Issue 13 — Apply bot: Easy Apply form submit button not found
**Error:** `⚠️ Could not find submit button — please complete manually`
**Cause:** After clicking Apply, page navigated to a new form page but bot tried to interact before page fully loaded.
**Fix:** Added `page.wait_for_load_state("domcontentloaded")` after clicking the Apply button before trying to fill the form.

---

### Issue 14 — Most jobs redirect to external company websites
**Observation:** Seek Easy Apply rarely available — most NZ jobs redirect to Workday, Greenhouse, or company ATS.
**Impact:** Fully automated apply bot doesn't work for most jobs.
**Fix/Workaround:** Shifted to semi-automated workflow:
- Bot handles scraping and resume tailoring (automated)
- User applies manually on company site using the tailored resume (manual)
- Dashboard updated with:
  - Prominent **"Open on Seek"** apply link
  - **⬇️ Download Tailored Resume** button
  - **✅ Applied Manually** button to track status

---

## Key Lessons

| Lesson | Detail |
|---|---|
| Always use full Python path | Windows PATH issues are common — use full path to avoid errors |
| Never use PowerShell echo for .env | It saves UTF-16 — always use Python to write .env files |
| Cloudflare blocks headless browsers | Use `headless=False` and Edge for scraping real sites |
| Use absolute file paths in scripts | Relative paths break depending on where you run the command |
| API keys expire/get corrupted | Generate a fresh key if auth fails, store safely in .env |
| NZ Seek jobs mostly use company ATS | Easy Apply is rare — design for semi-automated workflow |
