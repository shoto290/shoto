---
name: backend-testing
description: Test backends strategically — the test pyramid (many unit, fewer integration, few E2E), testing behavior not implementation, mocking at boundaries, real-dependency integration tests with testcontainers, triaging flaky tests, and explicitly testing resilience patterns. Use when writing or reviewing backend tests or a test strategy.
when_to_use: Trigger phrases like 'write tests for this service', 'unit vs integration vs E2E', 'mock this dependency', 'set up testcontainers', 'fix a flaky test', 'how much coverage', or 'test the retry/circuit breaker'.
---

# Backend Testing

Tests exist to let you change code with confidence. The whole discipline reduces to one rule: **assert observable behavior at the right level, fast and deterministically.** A suite that is slow, flaky, or coupled to implementation is a liability, not an asset.

## The Test Pyramid

Spend your test budget by level. Most value comes from many fast tests near the base.

| Level | Volume | Scope | Dependencies |
| :-- | :-- | :-- | :-- |
| Unit | Many | One unit of business logic | All boundaries mocked |
| Integration | Fewer | Wiring across the unit and its real infra | Real DB; external APIs stubbed |
| E2E | Few | Critical end-to-end user paths only | Full stack |

Reject the **inverted pyramid** (mostly E2E, few unit). It is slow, flaky, and gives vague failures — a red E2E tells you something broke, not what. Push every assertion to the lowest level that can prove it: business rules belong in unit tests, wiring belongs in integration, and only the handful of paths where a broken flow is catastrophic earn an E2E.

## Test Behavior, Not Implementation

Assert the **observable outcome and the enforced rule**, not the mechanics that produced it.

- Good: "an order over the credit limit is rejected with `LimitExceeded`."
- Bad: "`creditService.check()` was called once with `(orderId, amount)`."

The second test fails the moment you refactor internals even though behavior is unchanged — so it punishes exactly the work tests should protect. Verify the return value, the persisted state, the emitted event, or the error type. Reserve "was this called" assertions for genuine side effects you cannot observe any other way (an email was sent, a payment was charged).

## Mock at Boundaries

In **unit tests**, mock at the unit's boundaries — repositories, external service clients, clocks, queues — and drive logic through fakes. Keep real DB connections out of unit tests: they are slow, order-dependent, and flaky, which is the opposite of what a unit test must be. A unit test runs in milliseconds, in any order, in isolation.

Mock the boundary, never the thing under test. If a test mocks so much that it only re-asserts the mock setup, it tests nothing — see Pitfalls.

## Integration Tests With Testcontainers

Wiring bugs — SQL dialect quirks, transaction boundaries, serialization, migrations — only surface against the real engine. Use **testcontainers** to spin up real PostgreSQL/Redis/Kafka in Docker for integration tests.

Prefer real dependencies over **in-memory fakes** (H2, SQLite) unless the fake *is* your production engine. Fakes pass on behavior production rejects: an H2 query that fails on real Postgres ships green. Stub only the things you do not own and cannot run cheaply (third-party HTTP APIs) with a contract-faithful stub.

Isolate test state so tests stay independent: a fresh schema per run plus a transaction rollback or truncation per test. Shared mutable state across tests is a top cause of flakiness.

## TDD vs Test-After

- **TDD (contract-first)** for intricate business logic — branching rules, calculations, state machines. Writing the test first forces you to define the contract and catches edge cases before they ship.
- **Test-after is fine** for trivial CRUD and glue where the behavior is obvious. Do not perform ceremony where there is no design to discover.

## Triage Flaky Tests Immediately

A flaky test erodes trust in the whole suite — once people ignore red, real bugs hide behind the noise. Fixing flakes outranks writing new tests. Common causes and fixes:

| Cause | Fix |
| :-- | :-- |
| `sleep`/timing assumptions | Explicit waits / poll-until-condition |
| Real external calls | Stub the boundary |
| Shared mutable state | Per-test isolation (fresh state, rollback) |
| Unordered collections | Assert on sets, not positions |

Quarantine a flake only as a stopgap with a tracking ticket — never as the resolution.

## Test Resilience Patterns Explicitly

Resilience that is never tested is a hope, not a guarantee. Assert the behavior directly:

- **Circuit breaker** opens after N consecutive failures and short-circuits while open.
- **Timeout** aborts a slow call within the budget instead of hanging.
- **Retry** is only applied to idempotent operations, with bounded attempts and backoff.

Cross-reference the `resilience` skill for the patterns themselves; this skill covers proving they work.

## Worked Snippet — Service Unit Test With a Mocked Repository

A service unit test asserts a business rule against a mocked repository — no DB, no network, deterministic (language-agnostic pseudocode):

```
test "transfer rejected when balance is insufficient":
  accounts = MockAccountRepository()
  accounts.find("A").returns(Account(id: "A", balance: 50))
  service = TransferService(accounts)

  result = service.transfer(from: "A", to: "B", amount: 100)

  assert result.isError()
  assert result.error == "InsufficientFunds"
  assert accounts.save.wasNotCalled()   # side effect we cannot otherwise observe
```

The test names a rule, drives it through a mocked boundary, and asserts the observable outcome (error type) plus the one side effect that has no return value (nothing was persisted). It says nothing about *how* the balance was checked — a refactor of the internals keeps it green.

## Pitfalls

- **Inverted pyramid** — leaning on E2E for logic that a unit test could prove. Slow, flaky, vague failures.
- **Mocking everything** — when mocks dominate, the test re-asserts its own setup and proves nothing.
- **Real deps with no stubbing** — hitting live external APIs makes tests slow and non-deterministic; stub the boundary.
- **In-memory fakes masking prod bugs** — H2/SQLite pass behavior real Postgres rejects. Use testcontainers.
- **Leaving flaky tests unfixed** — erodes trust and hides real bugs; triage over new tests.
- **Testing implementation details** — call-spying that breaks on every refactor instead of asserting outcomes.
- **Never testing resilience** — breakers, timeouts, and retries assumed to work but never asserted.

For the senior judgment on what is worth testing at all — coverage as a means, not a target — defer to `senior-mindset`.
