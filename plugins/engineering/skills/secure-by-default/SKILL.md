---
name: secure-by-default
description: Secure-by-default coding - validate input, least privilege, safe defaults.
---

# Secure by Default

Treat security as a property you build in while writing code, not a review you bolt on later. Every input is hostile until proven otherwise; every permission is denied until explicitly granted. The rules below are framework-agnostic — apply them in any language.

## Never trust external input

Anything crossing a trust boundary is untrusted: request bodies, query and path params, headers, cookies, environment variables, files on disk, and third-party API responses.

- Validate at the edge, the moment data enters — not deep inside business logic.
- Allowlist what is valid; never try to denylist what is bad. You cannot enumerate every attack.
- Normalize before validating (decode, trim, canonicalize) so a check cannot be bypassed by encoding.

```ts
const Body = z.object({ email: z.string().email(), age: z.number().int().min(0).max(120) });
const input = Body.parse(req.body); // reject anything that does not match the shape
```

## Injection defense

- Use parameterized queries / prepared statements for every database call. Never string-concatenate SQL, NoSQL, or LDAP filters.
- Encode output for the specific sink it lands in (HTML, attribute, URL, shell). The right escape depends on the destination.
- Never pass untrusted input to a shell, `eval`, or a dynamic template. Prefer argument arrays over a shell string.

```ts
db.query('SELECT * FROM users WHERE id = $1', [userId]); // never `... WHERE id = ${userId}`
```

## Least privilege

- Grant the minimum scope, permission, or role needed — nothing speculative.
- Issue narrow, short-lived tokens scoped to one job; do not reuse an admin credential for routine work.
- Deny by default. New routes, files, and resources start inaccessible and are opened deliberately.

## Safe defaults

- Ship secure configuration out of the box; the default mode is the locked-down mode.
- Fail closed: on error, deny access rather than letting the request through.
- Never leak internals in errors — no stack traces, SQL, or paths to the client. Log details server-side, return a generic message.
- Enforce HTTPS, set `Secure` + `HttpOnly` + `SameSite` cookies, and configure CORS to an explicit allowlist, not `*`.

## Secret handling

- Never hardcode secrets in source and never log them.
- Load secrets from environment variables or a secret store at runtime.
- Never commit secrets. This repo's protected files are off-limits: `.env`, `.env.*`, `*.pem`, `*.key`, `*.cert`, and `secrets/` (see AGENTS.md).
- Redact tokens, passwords, and keys before anything reaches logs or telemetry.

```ts
const apiKey = process.env.API_KEY; // not a literal in the file
logger.info('charged user', { userId }); // never log apiKey or the card number
```

## Authn/authz

- Authenticate first (who is this), then authorize (may they do this) — they are separate checks.
- Enforce authorization on the server for every protected action, on every request. A hidden UI button is not a control.
- Never trust a client-supplied identifier (role, `userId`, tenant) without re-checking it against the session server-side.

## Dependencies & data

- Keep dependencies patched; track and remediate known vulnerabilities promptly.
- Minimize sensitive data retained — collect only what you need, delete it when its purpose ends.
- Hash passwords with a strong, salted KDF (argon2, scrypt, or bcrypt). Never store them reversibly or hash with plain SHA/MD5.

## Pass/fail checklist

- [ ] Every external input is validated at the edge with an allowlist.
- [ ] All database access uses parameterized queries.
- [ ] No untrusted input reaches a shell, `eval`, or dynamic template.
- [ ] Output is encoded for its specific sink.
- [ ] Permissions, tokens, and roles follow least privilege and deny-by-default.
- [ ] Errors fail closed and never leak internals to the client.
- [ ] HTTPS, secure cookies, and an explicit CORS allowlist are in place.
- [ ] No secret is hardcoded, logged, or committed; secrets load from env/store.
- [ ] Authorization is checked server-side on every protected request.
- [ ] Passwords are hashed with a strong salted KDF and dependencies are patched.
