---
name: resilience
description: 'Graceful failure: circuit breakers, timeouts, retries.'
---

# Resilience

Concrete stability patterns for the moment a dependency fails or slows down. Distributed systems fail partially — one slow downstream call, not a clean crash. The whole discipline reduces to one rule: **a failing or slow dependency must never take the caller down with it.** These are the mechanical patterns; for the higher-level isolate-failures and robustness judgment defer to `scalable-architecture`.

## Timeout Everything

Every external or network call gets a finite, explicit timeout. No call inherits the default infinite wait of its client library. A request with no deadline does not fail — it hangs, holds a connection, and lets one slow downstream exhaust your thread pool. Fail fast instead.

- Set both a **connect** timeout and a **read/response** timeout on every client.
- The timeout budget shrinks down the call chain: if your handler must answer in 2s, a downstream call cannot be given 2s.
- A timeout is the trigger that feeds the circuit breaker and the retry policy below.

## Circuit Breaker

After **N consecutive failures** (timeouts or errors) to one dependency, **open** the circuit: stop calling it and immediately return a cached or default response. This stops a slow dependency from cascading — without a breaker, every request piles into the same dead call and drains the pool.

Three states:

- **Closed** — calls flow normally; count consecutive failures.
- **Open** — fail fast, return fallback, do not touch the dependency. Start a cooldown timer.
- **Half-open** — after cooldown, allow one probe request. Success closes the circuit; failure re-opens it.

Scope one breaker per dependency, never one global breaker — a dead recommendations service must not open the circuit to your database.

## Bulkhead

Isolate resources so one saturated dependency cannot starve the whole process. Give each downstream dependency its **own thread pool or connection pool** (the ship's-bulkhead metaphor: one flooded compartment does not sink the vessel). Without bulkheads, a single slow dependency consumes every worker and your healthy endpoints go down with the sick one.

- Separate connection pools per database / external service.
- Bounded, dedicated worker pools per dependency class.
- Cap concurrent in-flight calls to each dependency.

## Idempotent Retries With Backoff

Retry **only idempotent operations** (GET, PUT, DELETE, naturally repeatable reads). For non-idempotent operations (a payment, a charge, an order submission), a blind retry double-applies — send an **idempotency key** so the server deduplicates a replay instead.

Rules for every retry:

- **Exponential backoff + jitter** — `delay = base * 2^attempt`, plus random jitter so retries from many clients do not align into a synchronized thundering herd.
- **Cap the attempts** (e.g. 3) and cap the max delay. Unbounded retries are a self-inflicted denial of service.
- Do not retry on `4xx` client errors — they will fail identically. Retry only transient faults (timeout, `503`, connection reset).

## Graceful Degradation

When a **non-critical** dependency fails, return a reduced response, not a `500`. A product page whose recommendations service is down should still render the product — drop the recommendations carousel. Partial functionality beats total failure. Decide per dependency which are load-bearing for the response and which are optional; the optional ones get a fallback, not an exception that bubbles to the client.

## Backpressure And Load Shedding

When inbound load exceeds capacity, reject excess work rather than collapse. An unbounded queue under overload grows until memory dies and latency goes to infinity for everyone.

- **Bound every queue.** A full bounded queue is a signal, not a problem.
- **Shed load** at the edge — reject or `429` excess requests fast so accepted requests still meet their latency budget.
- Apply backpressure upstream (pause consuming) so producers slow down instead of overflowing.

## Test These Explicitly

A resilience pattern you have not tested does not work. Assume it is broken until a test proves otherwise — for the full approach see `backend-testing`.

- Verify the **breaker opens** after exactly N induced failures and returns the fallback while open.
- Verify the breaker **recovers** via half-open after the cooldown.
- Verify a **timeout actually aborts** the call (inject a delay longer than the timeout and assert it fails fast, not hangs).
- Verify a retried non-idempotent call with an idempotency key applies **once**.

## Worked Snippet

A call wrapped with timeout, per-dependency circuit breaker, and bounded backoff retry (pseudocode):

```
function callPricing(req):
    if breaker.isOpen():
        return cachedPriceOr(default)          # fail fast, degrade

    for attempt in 0..MAX_RETRIES:             # MAX_RETRIES capped, e.g. 3
        try:
            res = http.get(pricingUrl, req,
                           connectTimeout=200ms,
                           readTimeout=800ms)   # timeout everything
            breaker.recordSuccess()
            return res
        catch (Timeout | ServerError) as e:    # transient only
            breaker.recordFailure()            # opens after N consecutive
            if breaker.isOpen():
                break
            sleep(min(BASE * 2^attempt, MAX_DELAY) + random_jitter())
        catch ClientError:
            throw                              # 4xx: do not retry

    return cachedPriceOr(default)              # graceful degradation
```

Note the call runs on the pricing dependency's own bounded pool (bulkhead) and the request is a read, so retrying is safe; a charge would carry an idempotency key instead.

## Pitfalls

- **No timeouts** — the dependency does not fail, it hangs, holds connections, and exhausts the pool under load.
- **Retrying non-idempotent calls** — replaying a payment double-charges. Use an idempotency key or do not retry.
- **Retry storms** — retries with no backoff, no jitter, or no cap turn a brief blip into a self-inflicted DDoS as aligned clients hammer a recovering service.
- **One dependency taking down the whole service** — no bulkhead means a single slow downstream starves every worker and your healthy paths die too.
- **Untested resilience** — assuming the breaker opens or the timeout aborts without a test that proves it. Almost always misconfigured until verified.
