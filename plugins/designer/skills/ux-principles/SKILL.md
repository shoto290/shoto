---
name: ux-principles
description: 'Apply senior UX judgment - usability heuristics, Laws of UX, and ethical, inclusive decision-making.'
when_to_use: 'When making product/UX decisions, critiquing a flow, justifying a design choice, or prioritizing usability.'
---

# UX Principles

## Usability First

- Make the obvious choice obvious — Krug's *Don't Make Me Think*: every screen should answer "what is this and what do I do here?" without effort.
- Reduce the questions a user must ask themselves; each unanswered question is friction that erodes trust.
- Support scanning, not reading — clear visual hierarchy, meaningful headings, conventional layouts; users satisfice, they don't optimize.
- Apply Norman's primitives (*The Design of Everyday Things*): affordances (what an element lets you do), signifiers (cues that reveal it), feedback (confirm every action), mapping (controls match their effects), constraints (prevent invalid actions).

## Laws of UX

Reach for the law that fits the problem (Yablonski, *Laws of UX*):

- **Hick's Law** — fewer, well-grouped choices speed decisions; cut or stage options.
- **Fitts's Law** — make important targets large and close; size primary actions, give touch targets room.
- **Jakob's Law** — users expect your product to work like the others they know; match conventions before inventing.
- **Miller's Law** — chunk information into small, meaningful groups (~5-9 units).
- **Aesthetic-Usability Effect** — polished design is perceived as more usable and earns goodwill for minor flaws.
- **Peak-End Rule** — users judge an experience by its peak and its end; design those moments deliberately.
- **Doherty Threshold** — keep system response under ~400ms (or show progress) to keep users engaged.
- **Law of Proximity / Common Region** — group related elements by spacing and shared containers; let layout convey relationships.

## Cognitive Load

- Minimize what users must hold in working memory; offload state into the interface (Weinschenk, *100 Things Every Designer Needs to Know About People*).
- Favor recognition over recall — show options instead of forcing users to remember them.
- Use progressive disclosure: reveal complexity only when it's needed, keep the default path simple.
- Provide sensible defaults so the common case requires no decision; defaults are the most-used setting.

## Decision-Making

- Start from the user need and the job-to-be-done, not the feature or the visual; ask what the user is trying to accomplish.
- State assumptions explicitly so they can be challenged before they ship as bugs.
- Weigh tradeoffs out loud — usability vs. effort, flexibility vs. clarity — and name which you chose and why.
- Prefer the simplest solution that works (SIMPLE); complexity must earn its place.

## Communicating Design

- Articulate the *why* behind every choice — a decision you can't explain you can't defend (Greever, *Articulating Design Decisions*).
- Tie each decision to a user goal and a constraint, not to taste; speak to outcomes stakeholders care about.
- Frame critique around the problem being solved, so feedback targets the goal rather than personal preference.
- Translate design rationale into the listener's language — business, engineering, support — when justifying to stakeholders.

## Ethics & Inclusion

- Design for real people in real contexts, not the idealized user; account for stress, distraction, and low literacy.
- Refuse dark patterns and manipulation — no forced continuity, confirmshaming, or hidden costs (Monteiro, *Ruined by Design*).
- Treat accessibility as a baseline, not a feature: contrast, keyboard, screen-reader, and motion preferences from the start (Gilbert, *Inclusive Design*).
- Take responsibility for impact — if a design can harm, that harm is a design decision, and it's yours to own.

## Pitfalls

- Designing for yourself — you are not the user; validate against real behavior, not your own intuition.
- Novelty over convention — clever, unfamiliar patterns break Jakob's Law and cost users relearning.
- Hidden costs and dark patterns — short-term metrics bought with long-term trust.
- Decoration over clarity — visual flourish that adds noise instead of communicating.
- Ignoring edge users — the people on slow networks, assistive tech, or unusual paths are users too.
