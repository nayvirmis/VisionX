# Privacy Notice

VisionX stores the minimum data needed to provide its sharing workflow:

- VisionX username, email address, bcrypt password hash, and login timestamps
- Refresh-token hashes and revocation metadata
- Feed-sharing relationships between VisionX accounts
- The connected public X account ID, username, display name, and profile image
- Short-lived cached copies of public posts authored by connected accounts

## X Account Connection

VisionX uses X OAuth 2.0 Authorization Code with PKCE and requests only
`tweet.read` and `users.read`. The temporary X access token is used to verify
the connected account through `/2/users/me` and is then discarded. VisionX
does not request `offline.access`, store X access or refresh tokens, read
browser cookies, or request an X password.

Protected X accounts are not supported. Feed retrieval uses an application
bearer token and is limited to public authored posts.

## Retention and Control

- OAuth linking states expire after ten minutes and are single-use.
- Public feed cache entries expire after fifteen minutes.
- Revoked VisionX refresh tokens cannot be reused.
- Disconnecting an X account removes its identity and cached posts.
- Deleting a VisionX account removes its shares, tokens, X connection, and
  cached data through cascading database relationships.

## Deployment Responsibility

This repository does not operate a hosted service. A person or organization
that deploys it becomes responsible for its privacy policy, security controls,
contact details, legal compliance, and X platform compliance.
