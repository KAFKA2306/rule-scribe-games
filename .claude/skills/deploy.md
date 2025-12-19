# Skill: Deploy

Commit, push, and verify Vercel deployment.

## When to Use

- After code/asset changes
- After database updates
- User says "deploy" or "push"

## Workflow

### 1. Check Status

```bash
git status
```

### 2. Commit

```bash
git add .
git commit -m "[type]: [description]"
```

Types: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

### 3. Push

```bash
git push
```

### 4. Verify (after ~60s)

```
browser_subagent: visit https://bodoge-no-mikata.vercel.app/[path]
```

## Troubleshooting

- Build fail: Check Vercel dashboard
- Cache: Hard refresh (Ctrl+Shift+R)
- API error: Check env vars in Vercel
