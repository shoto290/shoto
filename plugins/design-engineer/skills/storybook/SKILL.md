---
name: storybook
description: Authoring CSF3 Storybook stories for a design system.
---

# Storybook

Author Storybook stories in React + TypeScript using Component Story Format 3 (CSF3). Stories are the living documentation of the design system: every meaningful visual state is a story, every prop is a control.

## Story Authoring (CSF3)

Use a default-exported typed `Meta` and named `StoryObj` exports. Drive variants through `args`; expose props with `argTypes`; use `render` only when composition is needed.

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta = {
  title: "Components/Button",
  component: Button,
  tags: ["autodocs"],
  args: { children: "Click me", variant: "primary" },
  argTypes: {
    variant: { control: "select", options: ["primary", "secondary", "ghost"] },
    size: { control: "radio", options: ["sm", "md", "lg"] },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
export const Secondary: Story = { args: { variant: "secondary" } };
export const Loading: Story = { args: { loading: true } };
export const Disabled: Story = { args: { disabled: true } };
```

## Coverage Discipline

Write one story per meaningful state, not one per component:

- Default plus every variant, size, and tone.
- States: `disabled`, `loading`, `error`, `selected`, `focused`.
- Edge content: long text, empty, overflow, truncation, RTL.
- Interaction: use a `play` function (`@storybook/test`) to drive and assert behavior — click, type, expect — so stories double as interaction tests.

## Documentation

- Enable autodocs via `tags: ["autodocs"]`; let `argTypes` generate the controls table.
- Add a component description (JSDoc on the component or `parameters.docs.description.component`) and per-story descriptions for usage notes.
- Controls give live prop editing — keep `args`/`argTypes` accurate so the docs page is the canonical reference for the component's API.

## Organization

- `title` hierarchy mirrors the design system: `Components/Button`, `Forms/Input`, `Layout/Stack`.
- Co-locate `*.stories.tsx` next to the component it documents.
- Keep titles stable — they are the design-system navigation and deep-link targets.

## A11y & Visual

- Run the a11y addon (`@storybook/addon-a11y`) per story; fix contrast, roles, and label violations at the story level.
- Treat stories as the visual-regression surface: each distinct state should be a separate snapshot target (Chromatic or your VRT tool).

## Storybook MCP

When a Storybook MCP server is configured, exploit it — do not hand-author blind:

- **Introspect before building** — query the MCP for existing stories and components to discover what the design system already ships. Reuse over duplication: extend or compose an existing component instead of creating a new one.
- **Read the rendered catalog** — inspect the component catalog and each component's documented args/variants to match established API and naming conventions.
- **Verify states** — drive Storybook programmatically to confirm the stories you wrote render the intended states, then close the loop.

**Detect, then degrade gracefully.** Check whether the Storybook MCP is present and use it when it is; when it is absent, author stories normally from the source — never block on it.

**Setup is out of scope.** Configuring or installing the Storybook MCP server is deferred — route the user to the `core:mcp` skill (`Skill({ skill: "core:mcp" })`). This skill only documents how to USE the MCP once it exists.
