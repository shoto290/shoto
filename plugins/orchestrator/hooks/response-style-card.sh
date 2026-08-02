#!/bin/sh
if [ "${SHOTO_RESPONSE_STYLE_CARD:-}" = "0" ]; then
  exit 0
fi

event="${1:-UserPromptSubmit}"

card='[response-style] FINAL ANSWER CONTRACT - mirrors core:response-style, for your last message.\n1. Line 1 is the verdict: DONE / BLOCKED / FAILED + one clause. No preamble, no restatement of my request.\n2. Any answer reporting work on the tree MUST include a fenced mermaid block (flowchart LR), even a one-file delta: one node per touched file/area, prefixed + ~ -, labels quoted, max ~12. Exempt: a pure question, an alignment handback, a conversational reply - bare verdict line, no visual. Use exactly these classDef lines, no invented colors:\nclassDef add fill:#166534,stroke:#22c55e,color:#fff\nclassDef chg fill:#854d0e,stroke:#eab308,color:#fff\nclassDef del fill:#450a0a,stroke:#991b1b,color:#d4d4d4\nclassDef blocker fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:3px\nclassDef ctx fill:#27272a,stroke:#52525b,color:#a1a1aa\n3. Other facts go in a status table or an arrow flow A -> B -> C, never prose.\n4. Budget: 8 lines simple, 15 with a visual - counts prose and table lines, never the mermaid block. Numbers, not adjectives. This budget and rule 5 lift when I ask why / explain / in detail / walk me through / deep dive / show the code - then lead with the visual and expand beneath it.\n5. Cut: narration of the steps just taken, \"Let me know if\", apologies, unrequested next-step menus.\n6. BLOCKED/FAILED goes in line 1 with your leaning - never softened, never a footnote.\n7. A co-loaded contract contributes required CONTENT; this shape still wins. operator-profile overrides tone, register, language and emoji ONLY - it NEVER waives the verdict line or the mandatory visual.'

if [ "$event" = "SessionStart" ]; then
  printf '%b\n' "$card"
else
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$event" "$card"
fi
