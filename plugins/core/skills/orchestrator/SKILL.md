---
name: orchestrator
description: "The delegation-discovery principle the orchestrator agent runs on: for any needed capability, discover and prefer the best-fit installed subagent / workflow / skill over executing directly. A GENERIC routing principle — it carries NO fixed capability->delegate table. Preloaded as background knowledge; it writes no artifact and starts no task."
when_to_use: "Preloaded by the core:orchestrator agent as background routing knowledge. Invoke explicitly via /core:orchestrator or Skill({skill:\"core:orchestrator\"}) to (re)load the delegation-discovery principle. Deliberate / preload use only — not a match for vague free-form requests."
disable-model-invocation: true
user-invocable: false
---

# Orchestrator

This is the routing principle applied AFTER intent is resolved: once `core:alignment` has clarified what the user wants, decide HOW to deliver it. It builds on the foundation in `core:base` without restating those rules.

## The Principle

For every step of work, first DISCOVER what installed capability already covers it, then PREFER the best-fit delegate over executing directly. Composition beats re-implementation. This principle is deliberately GENERIC and carries NO fixed capability->delegate table: the installed set of skills, subagents, and workflows changes over time, so any hardcoded mapping goes stale and silently misroutes.

## Discover Before Acting

1. Name the capability the current step needs, in plain words.
2. Scan what is actually installed RIGHT NOW: the Skill tool's available-skills list (skills), the subagents available to the Task/Agent tool, and the workflows available to the Workflow tool. Treat these live lists as the source of truth — never a memorized roster.
3. Match the named capability to the closest-fit entry by reading its description / `when_to_use`. If several fit, pick the most specific; when a dedicated specialist exists (an authoring specialist for an artifact, an inventory lens for a survey, a review or evolve flow for those needs), prefer it over doing the work by hand.
4. If the job is at-scale fan-out / parallel multi-agent work, prefer a workflow over a single subagent.
5. Invoke the chosen delegate (Skill / Task-Agent / Workflow). Execute directly with your own tools only when NO installed skill, subagent, or workflow reasonably fits — and say so when you do.

## Why Generic

List-driven discovery stays correct as plugins are added, renamed, or removed; a hardcoded capability->delegate table would silently rot. The KINDS of needs worth routing — inventory/survey, exploration, design-engineering, evolve/multi-artifact change, review — are examples only, not an exhaustive or binding map. Always resolve the actual delegate against the live lists at the moment of need.

## Bounds

This skill is principle-only: it asks nothing and writes nothing. Honor the SIMPLE and safety rules from `core:base` by reference, and do not duplicate the intent-clarification job owned by `core:alignment`.
