"""Agent 4. Fail-closed Playwright submission worker for verified ATS applications.

This runner never guesses application answers, never emails an unverified
recipient, and never marks an application submitted without page confirmation.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_ATS_HOSTS = {"jobs.ashbyhq.com", "job-boards.greenhouse.io", "boards.greenhouse.io", "jobs.lever.co"}
SUCCESS_PATTERNS = (
    "thank you for applying", "application submitted", "application received",
    "thanks for applying", "we've received your application",
)
HARD_REQUIRED = ("APPLICANT_NAME", "APPLICANT_EMAIL", "APPLICANT_PHONE")


def is_supported_ats(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and parsed.hostname in ALLOWED_ATS_HOSTS and bool(parsed.path.strip("/"))
    except Exception:
        return False


def is_ready(record: dict) -> tuple[bool, str]:
    """Exactly checked authoritative prerequisites; no fuzzy approval."""
    if record.get("status") != "PENDING" or record.get("agent") != 4:
        return False, "task not pending for Agent 4"
    if record.get("channel") not in ("ATS", "OFFICIAL_ATS", "ATS_FORM"):
        return False, "email/manual channel requires separate verified workflow"
    if not record.get("channel_verified") or not is_supported_ats(record.get("official_channel_url") or ""):
        return False, "official ATS channel not verified or unsupported"
    if not record.get("master_resume_verified") or not record.get("variant_resume_qa_passed"):
        return False, "resume chain not verified"
    if record.get("review_status") != "PASS" or record.get("qa_status") != "PASS":
        return False, "tailored resume QA not approved"
    if not record.get("format_pass") or not record.get("source_pdf_verified") or not record.get("source_facts_verified"):
        return False, "resume source/format/facts incomplete"
    if (record.get("internal_score") or 0) < 97:
        return False, "internal QA score below 97 (not an external ATS score)"
    if not record.get("uploaded") or not record.get("checksum_verified"):
        return False, "private resume asset missing or unverified"
    eligibility = record.get("eligibility") or ""
    if not eligibility.startswith("VERIFIED_") or any(w in eligibility for w in ("REVIEW", "UNVERIFIED", "GAP", "UNPROVEN")):
        return False, "applicant location/eligibility not fully verified"
    if record.get("application_status") in ("SUBMITTED", "SENT", "ATS_CONFIRMED"):
        return False, "job already marked submitted"
    if record.get("delivery_status") in ("SENT", "ATS_CONFIRMED", "DELIVERED", "ACKNOWLEDGED"):
        return False, "delivery already recorded"
    if record.get("blocked_recipient"):
        return False, "previously bounced recipient is blocked"
    return True, "READY"


def profile() -> dict:
    missing = [key for key in HARD_REQUIRED if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Missing applicant profile fields: " + ", ".join(missing))
    return {"name": os.environ["APPLICANT_NAME"], "email": os.environ["APPLICANT_EMAIL"], "phone": os.environ["APPLICANT_PHONE"]}


def download_verified_resume(record: dict, destination: Path) -> Path:
    """Download private PDF using branch-scoped *read-only* Neon S3 credentials."""
    import boto3
    s3 = boto3.client("s3", endpoint_url=os.environ["NEON_STORAGE_ENDPOINT"],
                      region_name=os.environ.get("NEON_STORAGE_REGION", "us-east-1"),
                      aws_access_key_id=os.environ["NEON_S3_READ_KEY_ID"],
                      aws_secret_access_key=os.environ["NEON_S3_READ_SECRET"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(record["storage_bucket"], record["storage_key"], str(destination))
    data = destination.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if not data.startswith(b"%PDF-") or len(data) < 5000 or digest != record["expected_sha256"]:
        destination.unlink(missing_ok=True)
        raise ValueError("PDF bytes / SHA-256 mismatch: submission blocked")
    return destination


def _fill_first(page, selectors: tuple[str, ...], value: str) -> bool:
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.count() and element.is_visible() and element.is_enabled():
                element.fill(value, timeout=2000)
                return True
        except Exception:
            continue
    return False


def _browser_apply(url: str, resume_file: Path, candidate: dict) -> tuple[str, str]:
    """Return (CONFIRMED | BEFORE_SUBMIT_HOLD | UNCERTAIN_AFTER_CLICK, proof)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US", accept_downloads=False)
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(1500)
            if not is_supported_ats(page.url):
                return "BEFORE_SUBMIT_HOLD", "ATS navigation redirected to unsupported host"
            html = page.locator("body").inner_text(timeout=8000).lower()
            if any(token in html for token in ("captcha", "verify you are human", "cloudflare challenge", "one-time password")):
                return "BEFORE_SUBMIT_HOLD", "CAPTCHA/OTP/human verification required"
            pieces = candidate["name"].strip().split(" ", 1)
            first, last = pieces[0], pieces[1] if len(pieces) > 1 else ""
            ok_name = _fill_first(page, ('input[name="_systemfield_name"]', 'input[name="name"]', 'input[autocomplete="name"]'), candidate["name"])
            if not ok_name:
                f = _fill_first(page, ('input[name="first_name"]', 'input[name="firstName"]', 'input[autocomplete="given-name"]'), first)
                l = _fill_first(page, ('input[name="last_name"]', 'input[name="lastName"]', 'input[autocomplete="family-name"]'), last)
                if not(f and l):
                    return "BEFORE_SUBMIT_HOLD", "name field mapping unavailable"
            if not _fill_first(page, ('input[type="email"]', 'input[name="_systemfield_email"]', 'input[name="email"]'), candidate["email"]):
                return "BEFORE_SUBMIT_HOLD", "email field mapping unavailable"
            if not _fill_first(page, ('input[type="tel"]', 'input[name="_systemfield_phone"]', 'input[name="phone"]'), candidate["phone"]):
                return "BEFORE_SUBMIT_HOLD", "phone field mapping unavailable"
            inputs = page.locator('input[type="file"]')
            if not inputs.count():
                return "BEFORE_SUBMIT_HOLD", "resume upload input unavailable"
            inputs.first.set_input_files(str(resume_file))
            # Stop on unanswered required questions. Never invent salary, visas,
            # relocation, demographics, citizenship, or employment history.
            for field in page.locator('input[required], textarea[required], select[required]').all():
                if not field.is_visible() or not field.is_enabled():
                    continue
                typ = (field.get_attribute("type") or "").lower()
                if typ in ("hidden", "submit", "file"):
                    continue
                value = field.input_value().strip() if typ not in ("checkbox", "radio") else ("yes" if field.is_checked() else "")
                if not value:
                    return "BEFORE_SUBMIT_HOLD", "unanswered mandatory question"
            buttons = page.get_by_role("button", name=re.compile(r"^submit( application)?$", re.I))
            if buttons.count() != 1 or not buttons.first.is_visible() or not buttons.first.is_enabled():
                return "BEFORE_SUBMIT_HOLD", "single explicit Submit Application button not found"
            # From here onwards a network error is AMBIGUOUS. Never retry blindly.
            before_url = page.url
            before_text = page.locator("body").inner_text(timeout=10000).lower()
            try:
                buttons.first.click(timeout=12000)
                page.wait_for_timeout(2500)
                excerpt = page.locator("body").inner_text(timeout=10000).lower()
                new_confirmation = any(pattern in excerpt and pattern not in before_text
                                       for pattern in SUCCESS_PATTERNS)
                # Confirmation must appear AFTER clicking Submit; no credit for static copy.
                if new_confirmation:
                    return "CONFIRMED", page.url + "#post-submit-confirmation"
                return "UNCERTAIN_AFTER_CLICK", "submit clicked, no authoritative confirmation on page"
            except Exception:
                return "UNCERTAIN_AFTER_CLICK", "submit click attempted; outcome unknown"
        finally:
            context.close()
            browser.close()


def run(dry_run: bool = True) -> str:
    import psycopg
    from psycopg.rows import dict_row
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL missing")
    sql = """
    SELECT t.id,t.job_url,t.agent,t.kind,t.status,t.attempts,t.max_attempts,
      a.channel,a.official_channel_url,a.channel_verified,a.master_resume_verified,
      a.variant_resume_qa_passed,a.delivery_status,a.recipient,
      j.eligibility,j.application_status,q.review_status,q.internal_score,
      q.format_pass,q.source_pdf_verified,b.qa_status,b.source_facts_verified,
      x.storage_bucket,x.storage_key,x.expected_sha256,x.uploaded,x.checksum_verified,
      EXISTS(SELECT 1 FROM vocahire_blocked_recipients blk
             WHERE lower(blk.email)=lower(coalesce(a.recipient,''))) AS blocked_recipient
    FROM vocahire_tasks t
    LEFT JOIN vocahire_applications a ON a.job_url=t.job_url
    LEFT JOIN vocahire_jobs j ON j.job_url=t.job_url
    LEFT JOIN LATERAL (SELECT review_status,internal_score,format_pass,source_pdf_verified
                       FROM vocahire_resume_qa WHERE job_url=t.job_url
                       ORDER BY created_at DESC,id DESC LIMIT 1) q ON TRUE
    LEFT JOIN LATERAL (SELECT qa_status,source_facts_verified
                       FROM vocahire_resume_branches WHERE job_url=t.job_url
                       ORDER BY created_at DESC,id DESC LIMIT 1) b ON TRUE
    LEFT JOIN vocahire_resume_assets x ON x.job_url=t.job_url
    WHERE t.agent=4 AND t.status='PENDING'
      AND coalesce(t.attempts,0)<coalesce(t.max_attempts,1)
      AND (t.next_attempt_at IS NULL OR t.next_attempt_at<=now())
    ORDER BY t.id LIMIT 20
    """
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=True) as conn:
        rows = conn.execute(sql).fetchall()
        ready = [row for row in rows if is_ready(row)[0]]
        if dry_run:
            print(f"Agent4 DRY_RUN: scanned={len(rows)}, eligible={len(ready)}")
            return "DRY_RUN"
        if not ready:
            print("Agent4 NO_READY_TASKS: zero submissions")
            return "NO_READY_TASKS"
        if os.environ.get("ALLOW_REAL_SUBMISSIONS") != "yes":
            raise RuntimeError("Real submission disabled: ALLOW_REAL_SUBMISSIONS != yes")
        person = profile()
        # One item per invocation, with an atomic lease. Never queue concurrent submissions.
        selected = None
        for row in ready:
            with conn.transaction():
                claimed = conn.execute("""UPDATE vocahire_tasks SET status='RUNNING',attempts=attempts+1,
                    lease_until=now()+interval '15 minutes',updated_at=now()
                    WHERE id=%s AND status='PENDING' RETURNING id""", (row["id"],)).fetchone()
                if claimed:
                    selected = row
                    break
        if not selected:
            return "ALREADY_CLAIMED"
        with tempfile.TemporaryDirectory(prefix="vocahire-") as scratch:
            try:
                file = download_verified_resume(selected, Path(scratch) / "resume.pdf")
            except Exception as e:
                # Retry is safe: no attempt to open or submit the form occurred.
                conn.execute("""UPDATE vocahire_tasks SET status='BLOCKED',last_error=%s,
                    lease_until=NULL,updated_at=now() WHERE id=%s""", (f"Resume unavailable/invalid: {str(e)[:160]}",selected["id"]))
                conn.commit()
                return "RESUME_BLOCKED"
            try:
                outcome, proof = _browser_apply(selected["official_channel_url"],file,person)
            except Exception:
                # Treat any exception conservatively as potentially post-click.
                outcome, proof = "UNCERTAIN_AFTER_CLICK", "browser exception; manual duplicate check needed"
        if outcome == "CONFIRMED":
            with conn.transaction():
                updated = conn.execute("""UPDATE vocahire_applications SET delivery_status='ATS_CONFIRMED',
                     confirmation_ref=%s,updated_at=now() WHERE job_url=%s AND channel_verified IS TRUE
                     AND (delivery_status IS NULL OR delivery_status NOT IN
                        ('SENT','ATS_CONFIRMED','DELIVERED','ACKNOWLEDGED'))""", (proof,selected["job_url"]))
                if updated.rowcount != 1:
                    raise RuntimeError("Application confirmation cannot be recorded safely")
                conn.execute("UPDATE vocahire_jobs SET application_status='SUBMITTED' WHERE job_url=%s",(selected["job_url"],))
                conn.execute("""UPDATE vocahire_tasks SET status='DONE',last_error=NULL,
                     lease_until=NULL,updated_at=now() WHERE id=%s""",(selected["id"],))
            return "ATS_CONFIRMED"
        # After any ambiguous click, block indefinitely pending human review.
        conn.execute("""UPDATE vocahire_tasks SET status='BLOCKED',last_error=%s,
            lease_until=NULL,updated_at=now() WHERE id=%s""",(f"{outcome}: {proof[:180]}",selected["id"]))
        conn.commit()
        return outcome


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit",action="store_true",help="Requires ALLOW_REAL_SUBMISSIONS=yes and all proof gates")
    opts = parser.parse_args()
    try:
        print(run(dry_run=not opts.submit))
    except Exception as error:
        # Do not echo secrets from DSN or storage credentials.
        print(f"Agent4 failed safely: {type(error).__name__}",file=sys.stderr)
        sys.exit(2)