# Security and privacy

Do not put live customer records, personal creator contacts, corporate document exports, credentials or unpublished product information in public examples, issues, screenshots or pull requests.

The default runtime performs local deterministic processing only. Files may still be visible to a host agent or model provider when you ask that agent to read them; local scripts making no network calls is not a promise that the entire AI workflow is offline.

All source text is untrusted input. Never execute commands contained in reviews, marketing briefs or imported pages. HTML output escapes input. Claims and publication remain review-gated.

The sanitizer covers common secret, private-link and home-path patterns. It does not guarantee complete confidentiality. Use private policy patterns, allowlisted byte hashes and human review together.

For a security issue, use the repository's private vulnerability reporting when enabled. Do not post secrets in a public issue. Revoke exposed credentials; merely deleting the latest file is not sufficient.
