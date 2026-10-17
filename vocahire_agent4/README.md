# VocaHire Agent 4 — Safe ATS Submission Worker

**Status:** Implementation staged. Does **not** automatically submit applications. The runner defaults to read-only `dry-run` and requires verified source facts, employer eligibility, a reviewed tailored resume, the exact PDF checksum and a confirmed official ATS application URL. Every candidate must pass the `is_ready()` safety gate. Email sending is deliberately unsupported until authoritative mailbox verification is implemented.

## Deployment model

- Existing Vercel `vocahire-agents` project continues hosting its discovery cron and status dashboard. Do not replace it with Playwright.
- GitHub Actions provides a short-lived Chromium worker with serial concurrency and one application per approved dispatch.
- Neon `vocahire` is the queue of record, with `vocahire_tasks`, `vocahire_applications`, `vocahire_resume_qa`, `vocahire_resume_branches`, `vocahire_jobs`, and blocked recipients.
- A **private** Neon Object Storage bucket `vocahire-private-resumes` holds the actual PDF bytes. `migration.sql` adds an additive metadata manifest table; neither a ChatGPT `sandbox:/...` path nor a Library file ID is a runtime PDF path.

## Setup (required before any live submission)

1. Verify and execute `migration.sql` against Neon. This migration has **not** been applied automatically.
2. Upload the *approved* PDF to private Neon Object Storage, then calculate its SHA-256 and verify downloaded bytes match. Only then set `uploaded=true` and `checksum_verified=true` in `vocahire_resume_assets` for the exact job URL.
3. Complete final truthful JD QA and score, and explicitly approve required fields and remote/work-authorization eligibility. Until then, leave `REVIEW_PENDING` and blocked queue records unchanged.
4. Create the `vocahire-applications` GitHub Environment with required approvals where appropriate, and set the listed repository secrets (`VOCAHIRE_DATABASE_URL`, `VOCAHIRE_STORAGE_ENDPOINT`, read-only S3 credentials, and verified applicant details). Never commit credentials or personal resume PDFs to GitHub.
5. Merge/install into a dedicated VocaHire GitHub repository (do not merge to an unrelated project). Activate the workflow from the default branch.
6. Run a **dry-run** first. Confirm eligible count and queue. Trigger **submit-one** only with application details known. CAPTCHA, OTP, unknown required questions, domain changes, or ambiguous post-click outcomes block the task for human review.

## States and receipts

- The worker records `ATS_CONFIRMED` only when the page displays an affirmative confirmation after the submit click.
- Unknown post-click outcomes are `BLOCKED`; re-submission is **not automatic**, preventing duplicates.
- Earlier hard-bounced addresses remain excluded by exact case-insensitive mailbox comparison.
- `97` is an internal QA target, not an authentic third-party ATS match percentage.

## Current integrity blocker (2026-10-17)

Library downloads produced the following SHA-256 values, which **differ from values saved in `vocahire_resume_branches.variant_sha256`**:

| Role | Verified library PDF SHA-256 |
| --- | --- |
| Bolna AI Solutions Engineer | `2c0ec8a3b5b2d8203f4f00e3d4072671aa930d7861d9df7911fe430f1f23c257` |
| ElevenLabs Applied AI Engineer | `6cb8b0cd0a73a4961f8fa578ca827ec5c10779389927a3c4876cd2e4918084ad` |

Do **not** mark `PASS` until deciding which exact PDF is authoritative and re-verifying all facts/JD requirements. The immutable master PDF hash is `a24c0a39612da54bab203c463ffe0c9ea326077b49af4165f05675f0934261a3` (retrieved Library master reference). No original file was modified.