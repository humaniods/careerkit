-- Review this additive migration before applying it to production.
-- No existing status, resume master, or application rows are modified.
CREATE TABLE IF NOT EXISTS vocahire_resume_assets (
    job_url TEXT PRIMARY KEY,
    storage_bucket TEXT NOT NULL DEFAULT 'vocahire-private-resumes',
    storage_key TEXT NOT NULL UNIQUE,
    expected_sha256 TEXT NOT NULL CHECK (expected_sha256 ~ '^[0-9a-f]{64}$'),
    source_library_file_id TEXT,
    uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    checksum_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
