# Security Policy

## Supported Version

Only the latest commit on the default branch is supported.

## Reporting

Report security issues privately to the repository owner. Do not include
credentials, access tokens, session cookies, or personal data in a public
issue.

## Security Design

- Passwords are hashed with bcrypt.
- Access tokens are short-lived JWTs.
- Refresh tokens are opaque, hashed in the database, rotated on use, and
  revocable.
- OAuth state and PKCE verifiers are single-use and expire after ten minutes.
- X user tokens are discarded after account verification.
- CORS is restricted through `ALLOWED_ORIGINS`.
- Rate limits use a shared Redis-compatible store in production.
- Database pool size and overflow are bounded through environment settings.
- Maintenance routes require `CRON_SECRET`.
- Secrets are supplied through environment variables and are never committed.

Before deployment, rotate all secrets, use HTTPS, restrict extension origins,
enable managed database backups, and review dependency audit results.
