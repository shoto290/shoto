---
name: craft-security
description: Secure-by-default engineering - validate all input, least privilege, safe defaults, injection and secrets defense.
when_to_use: Preloaded so code is written secure by construction, and composed by the security review lens to judge whether a change is safe against hostile input and misuse. Covers input validation, authorization on every path, injection, SSRF, path traversal, XSS, deserialization, secrets, and data protection.
user-invocable: false
disable-model-invocation: true
---

# Craft Security

Security is a property you build in while writing code, not a review bolted on later. Every input is hostile until proven otherwise; every permission is denied until explicitly granted. This is the discipline for writing safe code and the lens for judging whether code is safe.

## Validate and sanitize all external input

Anything crossing a trust boundary is untrusted: request bodies, query and path parameters, headers, cookies, uploaded files, environment values, and third-party responses.

- Validate at the edge, the moment data enters — not deep inside the logic.
- Allowlist what is valid; never denylist what is bad. You cannot enumerate every attack.
- Normalize before validating (decode, trim, canonicalize) so a check cannot be bypassed by encoding.
- Enforce type, length, range, and format — reject anything that does not match the expected shape.

## Least privilege and deny by default

- Grant the minimum scope, permission, or role needed — nothing speculative.
- New routes, files, and resources start inaccessible and are opened deliberately.
- Issue narrow, short-lived credentials scoped to one job; never reuse an admin credential for routine work.
- On error, fail closed: deny access rather than letting the request through.

## Authorize on every path

- Authenticate first (who is this), then authorize (may they do this) — separate checks.
- Enforce authorization on the server for every protected action, on every request. A hidden UI control is not a control.
- Never trust a client-supplied identifier (role, user id, tenant) without re-checking it against the session server-side.
- Guard every entry point; an unauthenticated or unchecked path is a way in.

## Injection and untrusted-sink defense

- Use parameterized queries or prepared statements for every data-store call. Never concatenate untrusted input into SQL, NoSQL, or LDAP.
- Never pass untrusted input to a shell, an eval, or a dynamic template. Prefer argument arrays over a command string.
- Encode output for the specific sink it lands in — HTML, attribute, URL, or shell each need their own escaping — to prevent XSS.
- Never deserialize untrusted data into arbitrary types; restrict to known, safe shapes.
- For any server-issued request built from user input, validate the target against an allowlist to prevent SSRF, and resolve file paths against a base directory to prevent traversal.

## Secrets and sensitive data

- Never hardcode secrets in source and never log them.
- Load secrets from environment or a secret store at runtime; never commit them.
- Redact tokens, passwords, and keys before anything reaches logs or telemetry.
- Encrypt sensitive data in transit and at rest; hash passwords with a strong, salted key-derivation function.
- Keep sensitive values out of error messages, URLs, and query strings — return a generic error and log details server-side.

## Pass/fail checklist

- [ ] Every external input is validated and sanitized at the edge with an allowlist.
- [ ] Permissions, tokens, and roles follow least privilege and deny-by-default.
- [ ] Authorization is checked server-side on every protected path.
- [ ] Data-store access is parameterized; no untrusted input reaches a shell, eval, or template.
- [ ] SSRF, path traversal, XSS, and insecure deserialization are each guarded.
- [ ] No secret is hardcoded, logged, or committed; secrets load from env or a store.
- [ ] Sensitive data is encrypted and never appears in errors, URLs, or logs.
- [ ] On failure the code fails closed and leaks no internals to the caller.
