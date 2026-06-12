# VisionX API

All API errors use:

```json
{
  "error": {
    "code": "machine_readable_code",
    "message": "Human-readable explanation."
  }
}
```

Protected routes require `Authorization: Bearer <access-token>`.

## Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and issue token pair |
| `POST` | `/api/auth/login` | Verify credentials and issue token pair |
| `POST` | `/api/auth/refresh` | Rotate a refresh token |
| `POST` | `/api/auth/logout` | Revoke a refresh token |
| `GET` | `/api/auth/me` | Return the current profile and X link |
| `DELETE` | `/api/auth/account` | Delete the account after password confirmation |

## X Account

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/x/oauth/start` | Create state/PKCE data and return X authorization URL |
| `GET` | `/api/x/oauth/callback` | Verify and link a public X identity |
| `GET` | `/api/x/account` | Return current X connection status |
| `DELETE` | `/api/x/account` | Disconnect X and clear cached posts |

## Sharing And Feeds

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/shares` | Share the caller’s feed with a VisionX username |
| `GET` | `/api/shares/outgoing` | List users who can view the caller’s feed |
| `GET` | `/api/shares/incoming` | List feeds available to the caller |
| `DELETE` | `/api/shares/{username}` | Revoke outgoing access |
| `GET` | `/api/feeds/{username}` | Return an authorized normalized public feed |

Successful feed responses contain `posts`, `source_user`, `x_username`,
`fetched_at`, `cached`, and `count`.

## Operations

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Database readiness |
| `POST` | `/api/maintenance/cleanup` | Remove expired records using `X-Cron-Secret` |
