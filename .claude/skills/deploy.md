# Skill: Deploy to Vercel

Commit changes, push to GitHub, and verify deployment on Vercel.

## When to Use
- After making code or asset changes
- After database updates that need frontend verification
- When user says "deploy" or "push"

## Workflow

### 1. Check Status
```bash
git status
```

### 2. Stage and Commit
```bash
git add .
git commit -m "[type]: [description]"
```

Commit types:
- `feat:` New feature or game
- `fix:` Bug fix
- `refactor:` Code improvement
- `docs:` Documentation
- `chore:` Maintenance

### 3. Push
```bash
git push
```

### 4. Wait for Vercel
Vercel auto-deploys on push. Wait ~60 seconds for build.

### 5. Verify
Use browser_subagent to visit production URL and confirm changes are live:
- Main site: `https://rule-scribe-games.vercel.app`
- Alias: `https://bodoge-no-mikata.vercel.app`

### 6. Report
Confirm deployment success with screenshot or DOM content check.

## Common Issues
- Build fails: Check Vercel logs via dashboard
- Assets not updated: Hard refresh (Ctrl+Shift+R) or check cache headers
- API errors: Verify environment variables in Vercel dashboard
