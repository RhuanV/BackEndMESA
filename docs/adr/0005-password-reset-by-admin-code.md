# 0005 — Password reset via admin-issued code

**Status:** Accepted

## Context

Users who forget their password need a recovery path. The deployment has no
email/SMTP infrastructure and we did not want to introduce one (extra service,
stored user emails, deliverability concerns).

## Decision

An **administrador** (or desenvolvedor) issues a single-use recovery code for a
user via `POST /users/{user_id}/recovery-code`. The plaintext code is returned
once for the admin to relay out-of-band; only its hash is stored. The user then
resets their password on the login page ("Esqueci minha senha") via the public
`POST /password-reset` with username + code + new password.

Security properties:
- Codes are random, hashed at rest (same context as passwords), single-use and
  expire in ~30 minutes.
- Issuing a new code invalidates prior active codes for that user.
- A code is burned after a small number of failed attempts.
- Reset responses are generic (do not reveal whether a username/code exists).
- The protected DEV_USER cannot be targeted by this flow.

## Consequences

- No email dependency; recovery works entirely in-app + out-of-band relay.
- Requires a trusted administrator to deliver the code to the right person.
- Adds one table, `password_reset_codes` (migration 0017).
