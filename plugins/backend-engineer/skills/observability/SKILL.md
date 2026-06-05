---
name: observability
description: 'Make backends observable by default: the three pillars of logs, metrics, and traces with correlation IDs and SLO-driven alerting.'
when_to_use: 'When adding structured logging, metrics, or tracing, defining an SLO, setting up alerts, or debugging a distributed request.'
---

# Observability

Observability is the ability to answer "what is the system doing and why" from its outputs alone, without shipping new code. Build it in from the start — bolted-on observability is always incomplete. The discipline reduces to one rule: **every signal must carry enough context to reconstruct a single request end-to-end.**

## The Three Pillars

All three are required. Each answers a different question; none substitutes for another.

| Pillar | What it is | Answers |
| :-- | :-- | :-- |
| **Logs** | Discrete events with context, one per occurrence | "What happened at this exact point?" |
| **Metrics** | Quantitative measurements aggregated over time | "How much / how often / how fast, as a trend?" |
| **Traces** | One request's path across every service it touches | "Where did the time go and where did it fail?" |

Logs explain a single event. Metrics show trends and trigger alerts. Traces stitch a request across service boundaries. A system with only logs cannot trend; with only metrics cannot explain; with neither trace cannot follow a distributed request.

## Structured Logging

In production, emit **JSON with a consistent schema**, never freeform strings. A machine must parse, filter, and index every line.

- Required fields on every line: `timestamp`, `level`, `service`, `trace_id`, `message`, plus a `context` object.
- One schema across all services so a single query spans the fleet.
- In development, render human-readable (pretty-printed) logs for the console — the schema stays the same, only the formatter changes.
- No `"something went wrong"`. Messages are contextual and actionable: `"Payment declined for order 7833, attempt 2 of 4"`.

## Correlation / Trace IDs

A `trace_id` on **every log line** is non-negotiable. Generate it at the edge (ingress, API gateway) and propagate it through every downstream call (HTTP headers, message metadata). Without it, reconstructing one request across services is impossible — you are guessing from interleaved, unrelated lines.

With a `trace_id` you filter the entire fleet's logs to a single request and read its story in order, no matter how many services it crossed.

## Log Levels

| Level | Use for | In prod? |
| :-- | :-- | :-- |
| **DEBUG** | Fine-grained dev detail | No |
| **INFO** | Significant state changes (order placed, job started) | Yes |
| **WARN** | Degradation, recoverable / retried conditions | Yes |
| **ERROR** | Actionable failures needing attention | Yes |
| **FATAL** | Crash, process cannot continue | Yes |

Run at INFO and above in production. **Never log inside hot loops** — high-frequency code paths drown signal in noise and burn cost. Log the aggregate outcome, not each iteration.

## Worked Snippet

A single structured log line carrying a trace ID and actionable context:

```json
{
  "timestamp": "2026-06-03T14:22:07.481Z",
  "level": "ERROR",
  "service": "payments-api",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "message": "Payment declined for order 7833, attempt 2 of 4",
  "context": {
    "order_id": 7833,
    "attempt": 2,
    "max_attempts": 4,
    "gateway": "stripe",
    "decline_code": "insufficient_funds"
  }
}
```

One line: who (`service`), which request (`trace_id`), what (`message`), and everything needed to act (`context`). No secrets, no card number.

## The Golden Signals

Monitor these four for every service:

- **Latency** — track percentiles (**p50 / p95 / p99**), never averages. An average hides the slow tail where users actually suffer.
- **Traffic** — demand on the system (requests/sec, messages/sec).
- **Errors** — rate of failed requests, by class.
- **Saturation** — how full the system is (queue depth, connection pool, the most constrained resource).

## SLO-Driven Alerting

Alert on **business and user impact**, expressed as SLOs — not raw infrastructure metrics.

- Alert on: error rate breaching budget, p99 latency exceeding the SLO, availability dropping below target.
- Do **not** page on `CPU > 80%` or `memory > 70%`. High CPU with healthy latency and error rate is not a user problem — paging on it is alert fatigue, and fatigue gets real alerts ignored.
- Define an SLO per service (e.g. "99.9% of requests succeed under 300ms p99"), derive the error budget, and alert when the budget burns too fast.

Infra metrics belong on dashboards for diagnosis, not in your pager.

## Distributed Tracing

For multi-service systems, instrument with **OpenTelemetry** and export to a tracing backend (Jaeger, Tempo, or equivalent). A trace is a tree of spans; each span shows where time was spent. Spans reveal where latency actually lives — the slow downstream call, the lock contention, the N+1 query — which logs and metrics alone cannot localize across boundaries.

Propagate trace context on every outbound call so spans from different services join into one trace.

## Retention

Retain by **risk and cost, not "just in case"**. High-volume DEBUG/INFO logs get short windows; audit and security-relevant events get long ones. Aggregate metrics (cheap, small) retain far longer than raw logs (expensive, large). Set retention per signal class deliberately.

## Secrets and PII

**Never log secrets, tokens, passwords, or PII.** Logs propagate to indexes, backups, and third-party log sinks — a leaked credential in a log line is a breach. Scrub or omit at the logging boundary; never rely on downstream redaction. For the full secret/PII handling rules, defer to `secure-by-default`.

## Pitfalls

- **Unstructured logs** — freeform strings can't be queried or aggregated at scale. Emit JSON.
- **No trace IDs** — distributed debugging becomes guesswork. Propagate a `trace_id` everywhere.
- **Alerting on infra, not impact** — `CPU > 80%` pages are noise. Alert on SLOs and user impact.
- **Logging in hot loops** — drowns signal and burns cost. Log aggregates, not iterations.
- **No SLOs** — without them you alert on everything (fatigue) or nothing (blind). Define them.
- **Missing timestamp / service** — a log line without when and where it came from is unusable in a fleet. Make both mandatory.
