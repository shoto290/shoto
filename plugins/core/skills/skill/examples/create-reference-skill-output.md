---
name: api-conventions
description: API conventions for this codebase.
when_to_use: Use when creating, reviewing, or refactoring API endpoints, request validation, response formats, or error handling.
---

# API Conventions

When working on API endpoints:

1. Use resource-oriented route names.
2. Validate request input before calling domain logic.
3. Return errors in the shared `{ error: { code, message } }` shape.
4. Keep transport concerns out of service modules.

Read the surrounding API code before adding new conventions.
