# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in **wip**, please report it responsibly via LinkedIn DM:

- **LinkedIn:** [Mahesh Naik](https://www.linkedin.com/in/kamaheshnaik/)

Please **do not** open a public GitHub issue for security vulnerabilities.

## What to Include

When reporting, please provide:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fixes (if applicable)

## Response Expectations

- **Acknowledgement:** within 7 days of your report
- **Status update:** within 30 days with an assessment and timeline
- **Fix:** we aim to address confirmed vulnerabilities promptly

## Scope

**wip** is an early-stage project (v0.1.0) and has not undergone a formal security audit. The tool runs locally and interacts with:

- Local git repositories (read-only)
- Local config/data files (`~/.wip/`)
- Optional LLM API calls (API keys read from environment variables)

## Responsible Disclosure

We ask that you:

- Give us reasonable time to address the issue before public disclosure
- Avoid accessing or modifying other users' data
- Act in good faith to avoid disruption
