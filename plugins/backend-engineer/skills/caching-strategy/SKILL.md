---
name: caching-strategy
description: Add caching deliberately — choose a strategy by access pattern (cache-aside, read-through, write-through, write-behind), plan invalidation first, prevent the thundering herd, pick the right eviction policy, and layer caches across the stack. Use when introducing or debugging a cache.
when_to_use: Trigger phrases like 'add a cache', 'use Redis', 'cache invalidation', 'this endpoint is slow / hits the DB too much', 'set a TTL', 'cache stampede / thundering herd', or 'CDN/edge caching'.
---

# Caching Strategy

A cache trades freshness for speed. Add one only when you can answer two questions up front: how does this data get read and written, and how does a stale entry get corrected. Get those wrong and a cache turns a slow system into a fast wrong system.

## Choose By Access Pattern

The read/write shape dictates the pattern. Pick one per data set.

| Pattern | How It Works | Fits | Cost |
| :-- | :-- | :-- | :-- |
| **Cache-aside** (lazy) | App reads cache; on miss, reads DB and populates. App writes go to DB and invalidate the key. | Read-heavy, miss-tolerant data. The default. | First read after a miss is slow. |
| **Read-through** | Cache itself loads from the DB on a miss, behind one interface. | Same as cache-aside when a library/proxy owns loading. | Couples you to the cache provider's loader. |
| **Write-through** | Writes hit the cache and the DB together, synchronously. | Consistency-critical data — cache never lags the DB. | Higher write latency; every write pays cache + DB. |
| **Write-behind** | Writes hit the cache, flush to the DB asynchronously. | Write-heavy, loss-tolerant data (counters, metrics). | A crash before flush loses data. **Never for financial / transactional data.** |

Default to cache-aside. Reach for write-through only when readers must never see a value older than the last write. Reach for write-behind only when losing the last few writes is acceptable.

## Plan Invalidation First

Invalidation is the hard part — design it before you cache a single key. Three mechanisms:

- **TTL** — entries expire after a fixed time. Simple, self-healing, tolerates bounded staleness. The right default for most data.
- **Event-driven** — a write explicitly deletes or rewrites the affected keys. Accurate, but complex: every write path must know every key it touches, or you leak stale data.
- **Key versioning** — embed a version in the key (`user:42:v7`); bump the version to make all old keys unreachable. Good for bulk invalidation without scanning.

Tune the TTL to the data's tolerance for staleness. Too long and readers see stale values long after a change; too short and the hit rate collapses — the cache fills, expires, and refetches before it ever earns its keep, so it becomes pure overhead. When in doubt, start with a TTL and layer event-driven invalidation only on the keys that demand accuracy.

## Prevent The Thundering Herd

When a hot key expires, every concurrent reader misses at once and stampedes the DB with identical queries — a cache stampede (thundering herd) that can take the database down precisely when load is highest. Two defenses:

- **Per-key lock** — the first caller to miss acquires a short-lived lock and refreshes the key; everyone else waits for the new value (or briefly serves the stale one). Only one DB query per expiry.
- **Probabilistic early refresh** — refresh the key *before* it expires, with a probability that rises as expiry nears. The herd never forms because the value is renewed while still live.

Apply protection to hot keys specifically; cold keys rarely stampede and the bookkeeping is not free.

## Pick The Eviction Policy

When the cache hits its memory limit it evicts to make room. The policy must match the workload or it will throw out exactly the data you need under load.

- **LRU** (least recently used) — the general default. Keeps what was touched most recently.
- **LFU** (least frequently used) — better for skewed popularity where a stable hot set is read far more than the long tail.
- Match the policy to access reality: a pure-recency policy on a workload with a stable hot set evicts hot data during a burst of one-off reads.

## Layer Caches Across The Stack

Caches stack, each with different latency and consistency. Use the layer closest to the consumer that can still serve correct data.

| Layer | Holds | Notes |
| :-- | :-- | :-- |
| **Browser** | Per-user responses, assets | `Cache-Control` + `ETag` for revalidation. |
| **Edge / CDN** | Static and semi-dynamic responses | Shared across users — lowest latency, weakest freshness control. |
| **Application** | Sessions, computed results | Redis or in-process; where most deliberate caching lives. |
| **Database query cache** | Repeated query results | Closest to source; smallest staleness window. |

**Never cache user-specific or sensitive data at a shared layer** (edge/CDN). A shared cache serves one user's response to another. Mark authenticated responses `Cache-Control: private` so only the user's own browser stores them.

## Worked Snippet — Cache-Aside With Stampede Protection

```text
function getUser(id):
    key = "user:" + id
    value = cache.get(key)
    if value is not null:
        return value

    lockKey = "lock:" + key
    if cache.acquireLock(lockKey, ttl=5s):
        try:
            value = db.query("SELECT * FROM users WHERE id = ?", id)
            cache.set(key, value, ttl=300s)
            return value
        finally:
            cache.releaseLock(lockKey)
    else:
        wait(50ms)
        return getUser(id)
```

The first caller on a miss holds the lock and refreshes; concurrent callers wait briefly and re-read instead of all hitting the DB. One query per expiry, not thousands.

## Operate It

- Set an explicit **memory limit** so the cache evicts predictably instead of being OOM-killed.
- **Warm** critical caches at startup so the first users after a deploy or restart do not all miss at once.
- Monitor the **hit/miss ratio**. A hit rate below ~80% signals a bad strategy, a wrong TTL, or a cache that is not earning its cost — investigate, do not just grow it.
- **Never cache error responses** — a transient 500 cached for the TTL turns one failure into a sustained outage.

For the deeper judgment of measuring the bottleneck before scaling — whether a cache is even the right fix — defer to `scalable-architecture`.

## Pitfalls

- **Caching without an invalidation plan** — the staleness bug you ship with no way to correct it. Plan invalidation first.
- **Write-behind for money** — async flush loses the last writes on a crash; never use it for financial or transactional data.
- **No stampede protection on hot keys** — a hot-key expiry stampedes and can take the DB down. Add a lock or early refresh.
- **Wrong eviction policy** — recency-only on a stable-hot-set workload evicts your hot data under load. Match policy to access pattern.
- **Caching private data at the edge** — a shared cache leaks one user's data to another. Mark authenticated responses `Cache-Control: private`.
- **Caching errors** — turns a transient failure into a TTL-long outage.
- **Flying blind** — no hit/miss metrics means you cannot tell a working cache from dead weight. Always measure.
