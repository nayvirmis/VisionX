# VisionX

VisionX is a Chrome Extension and Flask API for sharing access to public X
profile feeds between authenticated VisionX users.

The project uses the official X API. Users connect and verify their X account
through OAuth 2.0 with PKCE, then selectively grant other VisionX users access
to view their public authored posts inside the X timeline. VisionX does not
request X passwords, extract browser cookies, or store X user access tokens.

## Repository Layout

```text
backend/       Flask API, database models, migrations, and tests
extension/     Manifest V3 Chrome Extension and JavaScript tests
docs/          Project documentation and clearly labeled historical report
scripts/       Local validation and packaging helpers
```

## Features

- VisionX registration and login with bcrypt password hashing
- Short-lived JWT access tokens and rotating refresh tokens
- X account verification through OAuth 2.0 Authorization Code with PKCE
- Explicit outgoing and incoming feed-sharing relationships
- Official X API retrieval of public authored posts
- Fifteen-minute server-side public feed cache
- Shared Valkey-backed rate limiting across API workers
- Safe DOM-based post rendering and reliable timeline restoration
- PostgreSQL, Docker Compose, Render, and GitHub Actions configuration

## Local Development

### Prerequisites

- Docker with Docker Compose
- An approved X Developer App configured as a Web App
- A Chrome-based browser

### Configure

```bash
cp backend/.env.example backend/.env
```

Set the required X credentials and secrets in `backend/.env`. The registered
X OAuth callback must exactly match `X_REDIRECT_URI`.

### Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Access-token signing secret, at least 32 characters |
| `CRON_SECRET` | Secret for the maintenance cleanup endpoint |
| `X_CLIENT_ID` / `X_CLIENT_SECRET` | X OAuth confidential client |
| `X_BEARER_TOKEN` | Application bearer token for public posts |
| `X_REDIRECT_URI` | Exact callback registered with X |
| `ALLOWED_ORIGINS` | Comma-separated trusted extension origins |
| `RATELIMIT_STORAGE_URI` | Redis-compatible shared rate-limit store |

### Start

```bash
docker compose up --build
```

The API will be available at `http://localhost:5000`. Migrations run when the
backend container starts.

If port `5000` is already in use, start with
`VISIONX_PORT=5050 docker compose up --build` and select
`http://localhost:5050` in the extension options.

### Load the Extension

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Select **Load unpacked** and choose the `extension/` directory.
4. Open the VisionX extension options and confirm the backend URL.
5. Copy the extension ID shown by Chrome into `ALLOWED_ORIGINS` as
   `chrome-extension://EXTENSION_ID`, then restart the backend.

## Development Checks

```bash
./scripts/check.sh
./scripts/package-extension.sh
```

Live X OAuth and feed retrieval require developer credentials and must be
verified manually before deployment.

## Documentation

- [Project report (PDF)](docs/VisionX_Project_Report.pdf)
- [Project report (LaTeX source)](docs/VisionX_Project_Report.tex)
- [Architecture and data model](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Privacy notice](PRIVACY.md)
- [Security policy](SECURITY.md)

## Deployment

`render.yaml` defines PostgreSQL, a private Key Value rate-limit store, and the
backend web service. It does not deploy automatically. Add the X credentials,
JWT secret, cron secret, and allowed extension origin in Render before creating
the services.

## Privacy and Platform Use

VisionX only retrieves public posts authored by the connected public X
account. Review [PRIVACY.md](PRIVACY.md) before use. Anyone deploying VisionX
is responsible for complying with the current X Developer Agreement, X
Developer Policy, and applicable law.

## Author

Suryadeep Singh Deswal

## License

MIT License. See [LICENSE](LICENSE).
