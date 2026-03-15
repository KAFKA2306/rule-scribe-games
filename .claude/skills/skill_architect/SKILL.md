# Skill Architect

The Skill Architect is a meta-skill designed to guide the Antigravity agent in creating, modifying, and maintaining high-quality, professional-grade skills.

## Goal
Standardize skill creation to ensure every skill is modular, well-documented, and includes built-in verification mechanisms.

## Core Instructions
- **Single Responsibility**: Every new skill must have one clearly defined purpose. If a skill grows too large, split it into sub-skills.
- **Mandatory Structure**: 
    - `SKILL.md`: The primary instruction file.
    - `scripts/`: Automation scripts (Python/Bash).
    - `resources/`: Templates, lookup tables, or static data.
    - `examples/`: "Gold Standard" examples of inputs and expected outputs.
- **Verification-First**: Every skill must include instructions for generating a `walkthrough.md` to prove success.
- **Naming Convention**: Use `snake_case` for skill directory names.

## Workflow for Creating a Skill
1. **Define the Purpose**: Clearly state the single responsibility of the skill.
2. **Bootstrap Infrastructure**: Use `bootstrap_skill.py` to create the directory structure.
3. **Populate SKILL.md**: Use the template in `resources/skill_template.md`.
4. **Draft Automation**: Create at least one script in `scripts/` if the task can be automated.
5. **Add Examples**: Provide at least two diverse examples in `examples/`.

## Best Practices
- **Use H3 and H4 headers** in `SKILL.md` for readability.
- **Bullet points** should be concise and actionable.
- **Version the skills** if major architectural changes occur.
