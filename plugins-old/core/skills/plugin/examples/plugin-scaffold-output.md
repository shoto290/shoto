<plugin-name>/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── <skill-name>/
        └── SKILL.md

<plugin-name>/.claude-plugin/plugin.json:
{
  "name": "<plugin-name>",
  "description": "<one-line description of what this plugin does>",
  "version": "1.0.0",
  "author": { "name": "<author>" }
}

<plugin-name>/skills/<skill-name>/SKILL.md:
---
description: <what this skill does + when Claude should run it>
---

# <skill name>

<body — what Claude should do when this skill is invoked>
