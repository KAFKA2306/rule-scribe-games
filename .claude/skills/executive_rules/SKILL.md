# Executive Rules

This skill acts as the "Project Constitution" or the "Executive Branch" of the Antigravity agent's decision-making process. These rules are non-negotiable and override standard heuristics.

## Goal
Enforce a "Gold Standard" of agentic behavior: proactivity, extreme verification, and total transparency.

## Executive Orders (The Rules)
1.  **Always Verify**: No task is complete without a verifiable walkthrough showing proof of success (recordings, command output, or screenshots).
2.  **Autonomous Design**: When a plan is approved, execute it to completion with minimal interruption, unless a critical blocker is encountered.
3.  **Modular Excellence**: Every new capability must be a skill. Never hardcode complex logic into the primary conversation path; encapsulate it in `_agent/skills/`.
4.  **Clean Room Protocol**: Keep the workspace tidy. Delete scratch scripts and temporary files immediately after verification.
5.  **Transparent Planning**: Every major action must be preceded by an `implementation_plan.md` that standardizes file paths and impact analysis.
6.  **Continuous Improvement**: Every walkthrough should end with a "Lessons Learned" or "Optimization Potential" section to feed back into the Project Knowledge.

## Workflow
- **Initial Interaction**: Check for alignment with Executive Orders.
- **Skill Creation**: Use the `skill_architect` to expand the agent's capabilities.
- **Verification**: Run exhaustive tests to prove compliance with Rule #1.

## Best Practices
- Refer to these rules when the user's intent is ambiguous.
- Use these rules to justify high-quality, proactive decisions.
