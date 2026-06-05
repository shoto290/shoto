---
name: api-design
description: 'Design durable HTTP/GraphQL API contracts: resource-centric REST, versioning, and consistent error envelopes.'
when_to_use: 'When designing or reviewing endpoints, request/response shapes, pagination, idempotency, or API versioning and evolution.'
---

# API Design

Design API contracts as long-term commitments. A consumer integrates once and depends on your shape for years — the contract is the product, not the implementation behind it. Every rule below protects that commitment.

For authentication and authorization rules, defer to the `secure-by-default` skill — do not re-teach auth here.

## Resource-Centric Design

Model endpoints around **resources (nouns)** addressed by the **HTTP verb**, not around actions.

- `GET /users/42` — fetch a user. `DELETE /orders/99` — delete an order. `POST /orders` — create.
- Never `POST /getUser`, `POST /deleteOrder`, `GET /createOrder`. The verb lives in the method, never in the path.
- Collections are plural nouns: `/users`, `/orders`. Sub-resources nest: `/users/42/orders`.
- A true action that is not CRUD (`/orders/99/refund`) is the rare exception — reach for it only when no resource models the state change.

The HTTP method already encodes intent. Verb endpoints duplicate that, break caching and proxies, and make the surface unpredictable.

## Idempotency

`GET`, `PUT`, and `DELETE` are naturally idempotent: repeating them yields the same end state. `POST` is not — retry it and you create two orders.

For any `POST` that **must be retry-safe** (payments, order creation, anything that moves money or state), require an **idempotency key**:

- The client generates a unique key per logical operation and sends it as `Idempotency-Key: <uuid>`.
- The server stores the key with the first result. A retry with the same key returns the **stored** result instead of re-applying the operation.
- This makes a request safe to retry after a network failure (where the client never saw the response) without double-charging or double-creating.

Without it, every dropped response on a `POST` is a potential duplicate.

## Pagination

Always paginate list endpoints, and **always return pagination metadata** (e.g. `next_cursor`, `has_more`, optionally a count) so the client knows how to continue.

Prefer **cursor-based** pagination over offset/page-number **at scale**:

- Offset (`?page=3&size=20` → `OFFSET 40`) breaks under concurrent writes: a row inserted or deleted between page loads shifts the window, so the client skips or repeats records.
- Cursors encode a stable position (e.g. the last seen sorted id/timestamp): `?limit=20&cursor=eyJpZCI6MTQwfQ`. New writes do not shift earlier pages.
- Offset is acceptable only for small, slow-changing datasets where a page jump UI is required.

## Versioning & Contract Stability

Treat the published contract as a long-term commitment:

- **Never remove a field.** **Never change a field's type or meaning.** Both silently break live consumers.
- **Add only optional fields** with safe defaults, so old clients keep working unchanged. This is the only non-breaking evolution.
- A genuine **breaking change requires a new version** (`/v2/...` or `Accept: application/vnd.api+json;version=2`).
- Keep only **2–3 active versions** at once, with a **documented deprecation timeline** (announce date, sunset date, migration notes). More than that is an unbounded maintenance tax.

## Consistent Error Envelope

Every error response — across every endpoint — shares **one schema**:

- `status` — the HTTP status code.
- `code` — a stable, machine-readable error code (`VALIDATION_FAILED`, not a prose string).
- `message` — a human-readable summary.
- `errors` — optional field-level validation details.
- `request_id` — a request/correlation id for tracing and support.

Rules:

- **Return all validation errors at once**, not one at a time — clients fix the whole form in one round trip.
- **Never leak stack traces, SQL, or internal file paths** to clients. Log those server-side; return the stable `code` and `request_id`.

## HTTP Status Discipline

Use the status line to communicate outcome. **Never return `200` for a failure.**

| Code | Meaning |
| :-- | :-- |
| 200 | OK — successful `GET`/`PUT`/`PATCH` with a body |
| 201 | Created — resource created (return it / its `Location`) |
| 204 | No Content — success with no body (e.g. `DELETE`) |
| 400 | Bad Request — malformed syntax / unparseable |
| 401 | Unauthorized — missing or invalid authentication |
| 403 | Forbidden — authenticated but not allowed |
| 404 | Not Found — resource does not exist |
| 409 | Conflict — state conflict (duplicate, version clash) |
| 422 | Unprocessable Entity — well-formed but semantically invalid |
| 429 | Too Many Requests — rate limited |
| 500 | Internal Server Error — unexpected server fault |

## REST vs GraphQL

- **REST** — default for stable, simple, **cacheable** contracts and resource-oriented domains. HTTP caching, proxies, and tooling work out of the box.
- **GraphQL** — reach for it when **many clients have heterogeneous data needs**, or to kill **over-fetching and under-fetching** (each client asks for exactly the fields it needs in one round trip). The cost: you must **enforce query depth and complexity limits**, or a single nested query can exhaust the server.

Pick REST unless the heterogeneity pain is real and present. Do not adopt GraphQL for a single, stable client.

## Worked Snippet — Error Envelope

A language-agnostic error response for a failed `POST /users` with two invalid fields:

```json
{
  "status": 422,
  "code": "VALIDATION_FAILED",
  "message": "The request could not be processed.",
  "errors": [
    { "field": "email", "code": "INVALID_FORMAT", "message": "Email is not a valid address." },
    { "field": "age", "code": "OUT_OF_RANGE", "message": "Age must be 18 or older." }
  ],
  "request_id": "req_01HZX9F3KQ2"
}
```

Every endpoint returns this exact shape on error — clients write one parser, not one per route.

## Pitfalls & Anti-Patterns

- **Verb endpoints** — `/getUser`, `/deleteOrder`. The method already carries the verb; keep paths as nouns.
- **`POST` for everything with no idempotency** — every retried request risks a duplicate. Use the right verb; add an idempotency key for unsafe retries.
- **Offset pagination at scale** — windows shift under concurrent writes, skipping or repeating rows. Use cursors.
- **`200` for errors** — clients and proxies treat it as success; failures vanish into the body. Use the right status code.
- **Inconsistent error shapes** — a different error body per endpoint forces N parsers and brittle clients. One envelope, everywhere.
- **Removing or retyping fields** — silently breaks live consumers. Add optional fields only; break only behind a new version.
- **Undocumented versioning** — consumers can't plan migrations against a version with no sunset date. Publish the deprecation timeline.
