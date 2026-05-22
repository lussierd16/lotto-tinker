# Security Policy

## Scope

This is a small, single-purpose project: a daily-updating static dashboard backed by a Python data-fetch script and a public GraphQL API. There is no user authentication, no database, no PII, and no server-side compute beyond a scheduled GitHub Action.

The realistic threat surface is:

- Supply-chain integrity of pinned GitHub Actions and any future Python dependencies
- The build script (`BuildDashboard.py`), which runs in CI with `contents: write` permissions
- The generated `index.html` blob, which embeds JSON from an external API into a `<script>` tag

## Reporting a Vulnerability

If you discover a security issue, please **do not open a public GitHub issue**.

Instead, use GitHub's private vulnerability reporting:

1. Go to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Fill in the form with reproduction steps and impact

You can expect an initial acknowledgment within 7 days. Because this is a personal project maintained in spare time, fix timelines depend on severity and complexity.

## Supported Versions

Only the `main` branch is supported. Forks are responsible for their own security posture.

## Hardening Already in Place

- All third-party GitHub Actions are pinned to full commit SHAs (not floating tags)
- Workflow permissions follow least-privilege (`contents: read` by default, `contents: write` only on the publish job)
- Dependabot monitors GitHub Actions dependencies weekly
- CodeQL analyzes Python, JavaScript/TypeScript, and Actions workflows on every push, PR, and weekly schedule
- `set -euo pipefail` on all multi-line `run:` blocks so silent failures don't ship to production
- No `pip` dependencies in the runtime path — stdlib only
