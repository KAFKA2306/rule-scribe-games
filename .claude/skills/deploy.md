# Skill: Deploy

## Trigger
Code/asset changes need to go live.

## Steps

```bash
git status
git add .
git commit -m "[type]: [description]"
git push
```

Types: `feat:`, `fix:`, `refactor:`, `docs:`

## Verify (~60s after push)
browser_subagent → visit production URL → confirm changes
