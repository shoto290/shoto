// evolve-plan: read-only inventory of an existing setup, classification of a
// requested capability into artifact entries, and a dependency-ordered plan.
// JavaScript only. The script only coordinates agents — it never touches the
// filesystem or shell directly, and it asks the user nothing (the wrapper owns
// every AskUserQuestion). All reads happen inside read-only Explore agents.

export const meta = {
  name: 'evolve-plan',
  description: 'Read-only evolve planner — inventory existing skills/subagents/hooks/MCP, classify a requested capability into artifact entries, and emit a dependency-ordered plan with conflicts, restart flags, and a test plan.',
  whenToUse: 'Invoked by the evolve wrapper skill to produce a structured PLAN before any approval gate. Read-only: it never authors or edits files.',
  phases: [
    { title: 'Inventory', detail: 'Parallel read-only Explore agents map skills, subagents, hooks/settings, and plugins/MCP under targetRoot' },
    { title: 'Classify', detail: 'One agent maps the capability to create/update/reuse entries via the decision matrix' },
    { title: 'Plan', detail: 'One agent surfaces conflicts, orders by dependency, flags restarts, and writes a test plan' },
  ],
}

// ─── Schemas ───
const INVENTORY_SCHEMA = {
  type: 'object',
  required: ['surface', 'items'],
  properties: {
    surface: { type: 'string', enum: ['skills', 'subagents', 'hooks', 'plugins'] },
    items: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'path', 'summary'],
        properties: {
          name: { type: 'string' },
          path: { type: 'string' },
          summary: { type: 'string' },
          detail: { type: 'string' },
        },
      },
    },
    constraints: { type: 'array', items: { type: 'string' } },
  },
}

const CLASSIFY_SCHEMA = {
  type: 'object',
  required: ['entries'],
  properties: {
    entries: {
      type: 'array',
      items: {
        type: 'object',
        required: ['artifactType', 'action', 'name', 'why'],
        properties: {
          artifactType: { type: 'string', enum: ['skill', 'subagent', 'hook', 'mcp', 'plugin'] },
          action: { type: 'string', enum: ['create', 'update', 'reuse'] },
          name: { type: 'string' },
          why: { type: 'string' },
        },
      },
    },
  },
}

const PLAN_SCHEMA = {
  type: 'object',
  required: ['entries', 'testPlan'],
  properties: {
    capability: { type: 'string' },
    entries: {
      type: 'array',
      items: {
        type: 'object',
        required: ['artifactType', 'action', 'name', 'targetPath', 'spec', 'why', 'restartRequired'],
        properties: {
          artifactType: { type: 'string', enum: ['skill', 'subagent', 'hook', 'mcp', 'plugin'] },
          action: { type: 'string', enum: ['create', 'update', 'reuse'] },
          name: { type: 'string' },
          targetPath: { type: 'string' },
          spec: { type: 'string' },
          why: { type: 'string' },
          restartRequired: { type: 'boolean' },
          needsSecret: { type: 'boolean' },
          order: { type: 'integer' },
        },
      },
    },
    conflicts: { type: 'array', items: { type: 'string' } },
    restartRequired: { type: 'boolean' },
    testPlan: { type: 'array', items: { type: 'string' } },
  },
}

// ─── Parse args once ───
const RAW = (typeof args === 'string' && args.trim()) || ''
if (!RAW) return { error: 'No input provided. Pass a JSON args string from the evolve wrapper.' }

let input
try {
  input = JSON.parse(RAW)
} catch (e) {
  return { error: 'args is not valid JSON: ' + (e && e.message ? e.message : String(e)) }
}

const capability = (input && input.capability) || ''
const targetRoot = (input && input.targetRoot) || ''
const repoType = (input && input.repoType) || 'normal'
const surfaces = Array.isArray(input && input.surfaces) && input.surfaces.length
  ? input.surfaces
  : ['skill', 'subagent', 'hook', 'mcp']

if (!capability || !targetRoot) {
  return { error: 'evolve-plan requires { capability, targetRoot } in args.' }
}

// ─── Inventory (read-only, one Explore agent per surface) ───
phase('Inventory')

const INVENTORY_TASKS = [
  {
    surface: 'skills',
    prompt:
      'Read-only inventory. Do NOT modify any file.\n\n' +
      'Scan every skill under ' + targetRoot + ' (skills/*/SKILL.md). For each, read the YAML frontmatter and capture: name, description, argument-hint, disable-model-invocation, user-invocable, context, agent. Note whether the body implements a create/update flow (look for "detect intent", "create flow", "update flow"). List description overlaps that could conflict with new auto-triggering artifacts.\n\n' +
      'Return surface="skills" with one item per skill (name, path, summary, detail) and any constraints. Structured output only.',
  },
  {
    surface: 'subagents',
    prompt:
      'Read-only inventory. Do NOT modify any file.\n\n' +
      'Scan every subagent under ' + targetRoot + ' (agents/*.md). For each, read the frontmatter and capture: name, description, tools, model. Flag whether each description is broad (auto-trigger risk) or narrow (focused).\n\n' +
      'Return surface="subagents" with one item per agent (name, path, summary, detail) and any constraints. Structured output only.',
  },
  {
    surface: 'hooks',
    prompt:
      'Read-only inventory. Do NOT modify any file.\n\n' +
      'Read settings.json and settings.local.json under ' + targetRoot + ' (and .claude/ if present). Parse the hooks block: for each hook capture event, matcher, type, and command/prompt. List permissions.allow and permissions.deny entries as constraints, and flag any global config that would conflict with the requested capability.\n\n' +
      'Return surface="hooks" with one item per hook (name, path, summary, detail) and constraints holding the permission entries. Structured output only.',
  },
  {
    surface: 'plugins',
    prompt:
      'Read-only inventory. Do NOT modify any file.\n\n' +
      'Scan plugin manifests under ' + targetRoot + ' (.claude-plugin/plugin.json) and any MCP config (.mcp.json, mcpServers in plugin.json or settings). For each plugin/MCP server capture its name, path, and what it provides.\n\n' +
      'Return surface="plugins" with one item per plugin/MCP server (name, path, summary, detail) and any constraints. Structured output only.',
  },
]

const inventoryResults = (await parallel(
  INVENTORY_TASKS.map(task => () =>
    agent(task.prompt, {
      label: 'inventory:' + task.surface,
      phase: 'Inventory',
      agentType: 'Explore',
      schema: INVENTORY_SCHEMA,
    })
  )
)).filter(Boolean)

if (!inventoryResults.length) {
  return { error: 'Inventory returned nothing — could not read the existing setup.', capability, targetRoot }
}
log('Inventoried ' + inventoryResults.length + ' surface(s)')

const inventoryJson = JSON.stringify(inventoryResults)

// ─── Classify: map the capability to artifact entries ───
phase('Classify')

const classified = await agent(
  '## Classifier\n\n' +
  'Repo type: ' + repoType + '. Target root: ' + targetRoot + '.\n' +
  'Requested capability:\n' + capability + '\n\n' +
  'Surfaces in scope: ' + surfaces.join(', ') + '.\n\n' +
  'Existing inventory (read-only):\n' + inventoryJson + '\n\n' +
  'Map the capability to one or more artifact entries using these rules:\n' +
  '- Reusable workflow with a /name entry point → skill.\n' +
  '- Static project knowledge Claude should know in the background → skill (user-invocable: false).\n' +
  '- Specialized delegate with sandboxed tools / token isolation → subagent.\n' +
  '- Automatic enforcement (format-on-save, block edits, validate bash) or session-start context → hook.\n' +
  '- External service/tool integration Claude queries directly → mcp.\n' +
  '- Whole-plugin packaging/distribution → plugin.\n' +
  'Update vs create: if an existing artifact covers ≥70% of the need → update; if it would need a near-rewrite → create new; if two together cover it → reuse + a small extension. Never duplicate functionality.\n\n' +
  'Return entries[] of { artifactType, action: create|update|reuse, name, why }. Structured output only.',
  { label: 'classify', phase: 'Classify', schema: CLASSIFY_SCHEMA }
)

if (!classified || !Array.isArray(classified.entries) || !classified.entries.length) {
  return {
    error: 'Classification produced no entries.',
    capability,
    targetRoot,
    inventory: inventoryResults,
  }
}
log('Classified ' + classified.entries.length + ' entry(ies)')

// ─── Plan: resolve conflicts, order by dependency, flag restarts, write tests ───
phase('Plan')

const planned = await agent(
  '## Planner\n\n' +
  'Repo type: ' + repoType + '. Target root: ' + targetRoot + '.\n' +
  'Capability:\n' + capability + '\n\n' +
  'Classified entries:\n' + JSON.stringify(classified.entries) + '\n\n' +
  'Existing inventory:\n' + inventoryJson + '\n\n' +
  'Produce the final PLAN:\n' +
  '- Surface every overlap/conflict explicitly. If an existing artifact covers ≥70% of an entry, prefer update or reuse over create — never duplicate.\n' +
  '- For each entry, resolve a concrete targetPath under ' + targetRoot + ' (skills under skills/<name>/, subagents under agents/<name>.md, hooks in settings.json). For a normal repo use .claude/ paths instead.\n' +
  '- Write a full authoring spec[] string per entry detailed enough that an autonomous smith can author/edit the files with NO further questions: name, type, description/trigger, argument-hint if any, tools/model for subagents, event/matcher/command for hooks, body/section outline.\n' +
  '- Order entries by dependency (order field, ascending): reuse first, then updates, then creates with a skill before any agent that wraps it; hooks last unless they block something else.\n' +
  '- Set restartRequired per entry (new top-level skill dir, new subagent file, or any settings.json hook change → true; in-place edits to an existing SKILL.md → false) and a top-level restartRequired if any entry needs it.\n' +
  '- Set needsSecret true for any hook that requires secrets/auth and for any mcp entry.\n' +
  '- Write a testPlan[] of concrete commands/checks (manual invocation, end-to-end trigger, reuse-still-works check).\n\n' +
  'Return the PLAN object. Structured output only.',
  { label: 'plan', phase: 'Plan', schema: PLAN_SCHEMA }
)

if (!planned || !Array.isArray(planned.entries) || !planned.entries.length) {
  return {
    capability,
    targetRoot,
    repoType,
    entries: classified.entries,
    conflicts: [],
    restartRequired: false,
    testPlan: [],
    note: 'Planner produced no refined plan; returning the raw classification.',
    inventory: inventoryResults,
  }
}
log('Planned ' + planned.entries.length + ' entry(ies)')

return {
  capability,
  targetRoot,
  repoType,
  entries: planned.entries,
  conflicts: planned.conflicts || [],
  restartRequired: planned.restartRequired === true,
  testPlan: planned.testPlan || [],
}
