---
name: database-craft
description: 'Model data and write queries with senior judgment: normalization, indexing, and transaction isolation tradeoffs.'
when_to_use: 'When designing schemas, tuning slow queries, fixing N+1, planning zero-downtime migrations, or choosing SQL vs NoSQL.'
---

# Database Craft

Treat the database as the source of truth, not a dumb store. Most data problems are decided at design time — the schema, the constraints, the indexes — long before the first slow query shows up. Make those decisions deliberately.

## Normalize By Default

Design to **3NF**: every non-key column depends on the key, the whole key, and nothing but the key. No repeating groups, no derived columns that can drift from their source, no values that belong in their own table.

Denormalize **only on profiling evidence** that reads are blocked by joins or aggregations a normalized model cannot serve fast enough. Never denormalize speculatively — every duplicated value is a future consistency bug you now own. When you do denormalize, document the source of truth and how the copy stays in sync.

## Indexing

Index the columns the query planner actually walks:

- Columns in `WHERE`, `JOIN`, and `ORDER BY` clauses.
- Composite indexes ordered by selectivity and matched to the query's leftmost-prefix usage.

Guardrails:

- **Confirm with `EXPLAIN` before adding an index.** A sequential scan on a hot path is the signal; the plan tells you the truth, guesses do not.
- **Avoid over-indexing.** Every index is write amplification — each `INSERT`/`UPDATE`/`DELETE` maintains it. Drop indexes no query uses.
- **Beware low-selectivity columns** (booleans, status enums with two values). An index that matches half the rows is rarely worth using; the planner will skip it anyway.

## Integrity At The Database

Enforce invariants where the data lives, not only in application code:

- **Primary keys** on every table; **foreign keys** for every reference, with an intentional cascade policy (`RESTRICT`, `CASCADE`, or `SET NULL` — chosen, not defaulted).
- **Unique** constraints for natural keys; **check** constraints for value rules (`price >= 0`, valid enum membership).

Application validation is the second line of defense — fast feedback and good messages — never the only one. Two services, a script, or a future migration will all hit the same table; the database is the one gate they all pass through.

## Transactions & Isolation

Pick the **lowest isolation level that is correct** for the operation — higher levels cost concurrency and invite deadlocks.

| Level | Prevents | Still allows |
| :-- | :-- | :-- |
| `READ COMMITTED` | dirty reads | non-repeatable reads, phantoms |
| `REPEATABLE READ` | dirty + non-repeatable reads | phantoms (in standard SQL) |
| `SERIALIZABLE` | dirty, non-repeatable, phantoms | nothing — full isolation |

Reach for `SERIALIZABLE` only when an invariant spans multiple rows read then written (balance checks, inventory decrements). Keep transactions short — hold no locks across network calls or user think-time.

## Eliminate N+1 Queries

The classic killer: load N parents, then fire one query per parent for its children.

- **Detect** it in the ORM query log — the same parameterized statement repeated once per row is the tell.
- **Fix** with eager loading / batch loading (`IN (...)` over the collected keys) or a single `JOIN`. Fetch the set in one round trip, not one round trip per element.

## Connection Pooling

Opening a connection is expensive; never open one per request. Reuse a **bounded pool**:

- **Max size** tuned to the database's connection ceiling and the app's concurrency — bigger is not better; it just moves the queue from app to database.
- **Acquire timeout** so a starved request fails fast instead of hanging.
- **Idle eviction** to release connections the pool no longer needs.

Watch for **pool exhaustion**: requests blocking on connection acquisition usually means a leaked connection (not returned to the pool) or a transaction held open too long — not a pool that is too small.

## Scaling Order

Scale in this order, stopping as soon as the load is handled:

1. **Vertical** — more CPU/RAM/IO. Simplest, no code change, buys real headroom.
2. **Read replicas** — offload read traffic. Mind **replication lag**: do not read-your-writes off a replica right after writing to the primary, or the user sees stale data. Route those reads to the primary.
3. **Sharding** — split data across nodes. Effectively **irreversible**; the **shard key** decides every future query's fan-out. Plan it before you need it. For where the scale boundary actually sits, defer to the `scalable-architecture` skill.

## SQL vs NoSQL

A tradeoff, not a religion:

- **Relational (SQL)** — strong consistency, joins, transactions, ad-hoc queries, schema-enforced integrity. The default for data with relationships and correctness requirements.
- **Document / key-value (NoSQL)** — high write throughput, horizontal scale, flexible schema, simple access patterns known up front. Pays for it with weaker consistency and no joins.

Choose by access pattern and consistency need, not by hype. Mixing both (relational core + a cache or document store at the edge) is normal.

## Zero-Downtime Migrations

Use **expand / contract** so old and new code run side by side:

1. **Expand** — add the new column as nullable or with a default. Adding a nullable column is cheap; it does not rewrite the table.
2. **Backfill in batches** — fill the new column in bounded chunks (e.g. 1,000 rows), each its own transaction. **Never** one giant transaction — it locks the table, bloats the log, and blocks writes.
3. **Switch reads** — point the application at the new column once it is fully populated.
4. **Contract** — drop the old column after a release confirms nothing reads it.

**Never lock a large table** in a single migration. Add constraints and indexes concurrently where the engine supports it.

```sql
-- Parameterized query: never interpolate user input into SQL.
-- (For injection-safe construction, defer to the secure-by-default skill.)
SELECT id, email FROM users WHERE org_id = $1 AND status = $2;

-- Batched backfill sketch: bounded chunks, one transaction each, loop until done.
UPDATE users
SET region = legacy_region
WHERE region IS NULL
  AND id IN (
    SELECT id FROM users WHERE region IS NULL ORDER BY id LIMIT 1000
  );
-- Repeat until 0 rows affected. Sleep briefly between batches to spare replication.
```

## Pitfalls

- **Denormalizing without evidence** — duplicated data you now have to keep in sync, solving a problem you never measured.
- **No foreign keys** — orphaned rows and silent referential rot; the database stops protecting you.
- **N+1 in production** — fine on 10 dev rows, a meltdown on 100k. Always check the ORM query log.
- **Over-indexing** — write throughput dies under index maintenance for indexes no query uses.
- **Table-locking migrations** — a single `ALTER` or one-shot backfill that locks a hot table is an outage.
- **Reading your own writes off a lagging replica** — the user updates something and sees the old value. Route read-after-write to the primary.
- **Sharding with no key strategy** — a bad shard key forces cross-shard fan-out on every query and cannot be undone without a full re-shard.
