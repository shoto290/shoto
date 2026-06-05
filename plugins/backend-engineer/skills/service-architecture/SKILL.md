---
name: service-architecture
description: 'Structure backend code with senior judgment: layered repository/service/controller separation, DI, and DDD bounded contexts.'
when_to_use: 'When laying out a service, drawing module boundaries, deciding monolith vs microservice, or asking where logic belongs.'
---

# Service Architecture

Concrete backend layering for where code goes and how modules split. This skill applies the patterns; the generic boundary, interface-depth, and scale judgment lives elsewhere. For deep-vs-shallow interfaces and evolutionary/scale tradeoffs defer to `scalable-architecture`. For SOLID/DRY/KISS/YAGNI defer to `solid-dry-kiss-yagni`.

## Layered Separation

Three layers, one direction of dependency. Each does exactly one job.

- **Controller (skinny)** — parse and validate the HTTP request, delegate to one service call, map the result to a response. Nothing else. No business rules, no transactions, no queries.
- **Service** — all business logic: orchestration, transaction boundaries, invariant enforcement, calls to repositories and other services. This is where decisions live.
- **Repository** — persistence behind an interface. Translates domain objects to and from storage. Knows the database; nothing above it does.

Business logic NEVER leaks into a controller. If a controller branches on domain state, computes a price, or opens a transaction, that code belongs in a service. The controller's body should read like a single sentence: take input, call service, return output.

## Repository Pattern

Code against a repository **interface**, not the ORM directly. The interface speaks the domain: `findById`, `save`, `findByEmail` — not `queryBuilder`, `createQueryRunner`, or raw rows.

This buys two things: **persistence ignorance** (the service layer never imports ORM types, so swapping Postgres for a document store touches one implementation, not every service) and **testability** (a service takes the interface and gets a fake in tests, no database needed). The ORM is an implementation detail confined to the concrete repository class.

## Dependency Injection

Inject dependencies as **interfaces through the constructor**. A service declares what it needs; the wiring layer supplies it.

- Never `new` a dependency inside a service — that hardcodes the implementation and defeats both mocking and swapping.
- No global service locators or static singletons reached from inside business logic — they hide the dependency graph and make tests stateful.
- Constructor injection makes dependencies explicit, the object fully formed once built, and the test seam obvious.

## Organize By Domain, Not By Layer

Top-level structure follows **business domains** (bounded contexts), not technical layers. Prefer `billing/`, `catalog/`, `shipping/` — each owning its model, repositories, and services — over global `controllers/`, `services/`, `repositories/` folders that scatter one feature across the tree.

Technical layering happens **within** a context, not across the whole codebase. A bounded context is a consistency and ownership boundary: its model means one specific thing inside it, and it exposes a deliberate surface to other contexts rather than letting them reach into its internals.

## DDD Aggregates

An **aggregate** is a cluster of objects treated as one unit, fronted by an **aggregate root**. The root is:

- The **unit of persistence** — repositories load and save whole aggregates, never child entities on their own.
- The **invariant guard** — all changes go through root methods, which enforce the rules that must always hold (an order's total matches its lines; a cart cannot exceed its limit).

Outside code never mutates a child entity directly. It calls a method on the root, and the root decides what changes. This keeps invariants in one place instead of smeared across callers.

## Modular Monolith Vs Microservices

**Default to a modular monolith** with strong internal boundaries: one deployable, clear bounded contexts, communication through each context's public surface. You get domain separation without distributed-systems tax.

Extract a service into its own deployable only when a concrete force demands it:

- **Organizational ownership** — a separate team needs an independent release cadence.
- **Asymmetric scaling** — one context's load profile differs so sharply it must scale on its own.
- **Release-coordination pain** — deploys are blocked on unrelated parts of the system.

Do not split for fashion, résumés, or imagined future scale. Premature microservices trade in-process calls for network calls, transactions for sagas, and stack traces for distributed tracing — and the costly retreat back to a monolith is a well-worn industry path. When the split judgment is about scale and reversibility, defer to `scalable-architecture`.

## Thin Abstractions Only

Apply these patterns where they **cut** complexity, not reflexively. One persistence path and no tests asking for a seam? A repository interface is ceremony — use the ORM directly until a second implementation or a test forces the abstraction. A factory that only wraps `new` adds a layer and hides nothing. Add the seam when a real need arrives (per YAGNI; defer to `solid-dry-kiss-yagni`).

## Worked Snippet

Controller → service → repository, wired by constructor injection. Language-agnostic / TypeScript-ish.

```ts
interface UserRepository {
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

class RegisterUserService {
  constructor(
    private readonly users: UserRepository,
    private readonly mailer: Mailer,
  ) {}

  async register(email: string, password: string): Promise<User> {
    if (await this.users.findByEmail(email)) {
      throw new EmailAlreadyTakenError(email);
    }
    const user = User.create(email, password);
    await this.users.save(user);
    await this.mailer.sendWelcome(user);
    return user;
  }
}

class UserController {
  constructor(private readonly registerUser: RegisterUserService) {}

  async post(req: Request, res: Response) {
    const { email, password } = parseRegisterBody(req);
    const user = await this.registerUser.register(email, password);
    return res.status(201).json(toUserResponse(user));
  }
}
```

The controller only parses, delegates, and maps. The service holds the rule (no duplicate email) and orchestration. The repository is an interface, so the service mocks cleanly and the ORM stays out of the business layer.

## Pitfalls

- **Business logic in controllers** — branching on domain state or computing results in the HTTP layer. Move it into a service.
- **Anemic pass-through services** — a service whose every method just forwards one repository call adds a layer without adding behavior. Either it should hold real logic or it should not exist.
- **Cross-domain repository calls** — the `billing` service reaching into the `catalog` repository. Go through the other context's service surface, never its persistence.
- **ORM types leaking into the service layer** — entities decorated with ORM annotations, query builders, or row shapes flowing upward. The service should see domain objects only.
- **Factories that only wrap `new`** — abstraction with no decision inside it. Delete it; call the constructor.
- **Premature microservices** — splitting before ownership, scaling, or release pain forces it. Stay a modular monolith until a concrete force appears.
- **God services** — one service accumulating logic from many contexts. Split along bounded-context lines.
