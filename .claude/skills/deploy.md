# Skill: Deploy

## Trigger
Code/asset changes need to go live.

## Steps

### 1. Commit
```bash
git add .
git commit -m "[type]: [description]"
git push
```
Types: `feat:` `fix:` `refactor:` `docs:` `chore:`

### 2. Verify (wait ~60s)
browser_subagent → https://bodoge-no-mikata.vercel.app → Ctrl+Shift+R → screenshot
