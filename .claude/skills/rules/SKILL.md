---
name: rules
description: Executive rules and project constitution. Use to understand project-wide principles, coding standards, architectural decisions, non-negotiable rules, and decision-making guidelines. Keywords: rules, principles, standards, constitution, policy.
---

# Executive Rules

Project constitution and non-negotiable rules that override standard heuristics.

## Goal

Define project-wide principles and enforce consistency.

## Rules

- Rules override standard defaults
- Explain rationale, not just directives
- Document architectural constraints
- Keep principles accessible

## Parallel Execution

Rules constrain all parallel agents equally. Reference in forked sessions:
```
/fork backend: Work within rules constraints
/fork frontend: Work within rules constraints
/fork qa: Verify rules compliance (all agents)
/tasks
```

Use `/fork` when:
- Multiple agents need same rule constraints
- Rules act as guardrails for parallel work
- All agents must validate against constitution
