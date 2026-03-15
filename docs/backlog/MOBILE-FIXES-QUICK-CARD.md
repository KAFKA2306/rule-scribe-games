# Mobile Responsiveness Fixes - Quick Reference Card

**Print this and keep it open while fixing**

---

## The 3 Critical Issues & Fixes

| Issue | Line(s) | Fix | Before → After |
|-------|---------|-----|-----------------|
| **Text Overflow** | 334-341 | `.game-detail-pane { padding: 16px; }` | 32px → 16px |
| **Illegible Text** | 499-513 | `.markdown-content { word-wrap: break-word; ... }` | No breaks → Wraps |
| **Unclickable Buttons** | 176-198 | `.btn-primary { min-height: 44px; }` | 32px → 44px |

---

## 13 CSS Changes Summary

```
✓ Change 1:  Add body font-size: 16px
✓ Change 2:  App container padding: 12px → 20px responsive
✓ Change 3:  Detail pane padding: 32px → 16px responsive ★★★
✓ Change 4:  Header stack flexbox on mobile
✓ Change 5:  Add word-wrap to markdown ★★★
✓ Change 6:  Keywords grid: 1fr → repeat(auto-fill) responsive
✓ Change 7:  Cards grid: 1fr → repeat(auto-fill) responsive
✓ Change 8:  Info grid: 1fr → repeat(2, 1fr) responsive
✓ Change 9:  Button min-height: 44px ★★★
✓ Change 10: Affiliate link min-height: 44px
✓ Change 11: Brand h1: 24px → 18px responsive
✓ Change 12: Game summary: 13px → 15px responsive
✓ Change 13: Search form flex-wrap responsive
```

**★★★ = Critical, fix first**

---

## Implementation Workflow

```
1. Backup: cp frontend/src/index.css frontend/src/index.css.backup
2. Edit: Open frontend/src/index.css
3. Apply: Make all 13 changes (use MOBILE_CSS_FIXES.md for exact code)
4. Check: task lint:frontend
5. Build: task build
6. Test: task dev → F12 → Ctrl+Shift+M → iPhone 12 → Scroll & verify
7. Commit: git add frontend/src/index.css && git commit -m "fix: mobile responsive..."
```

---

## DevTools Quick Inspection (5 min)

```
1. Open: http://localhost:5173
2. DevTools: F12
3. Mobile mode: Ctrl+Shift+M
4. Device: Select iPhone 12 (390px)
5. Check:
   - Horizontal scrollbar? NO = good
   - Text readable? YES = good
   - Images fit viewport? YES = good
   - Buttons ≥44px? YES = good

If anything fails:
   → Right-click → Inspect
   → Find in Styles panel
   → Test fix live
   → Copy to index.css
```

---

## CSS Pattern Reference

### Mobile-First Grid
```css
/* Mobile */
.grid {
  grid-template-columns: 1fr;
}

/* Tablet+ */
@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

### Responsive Padding
```css
/* Mobile */
.container {
  padding: 12px;
}

/* Tablet+ */
@media (min-width: 640px) {
  .container {
    padding: 20px;
  }
}
```

### Responsive Font Size
```css
/* Mobile */
body {
  font-size: 16px;
}

/* Tablet+ */
@media (min-width: 768px) {
  body {
    font-size: 14px;
  }
}
```

### Word Wrapping
```css
.text {
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
```

### Touch Targets
```css
button {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}
```

---

## Console Commands (Quick Diagnosis)

```javascript
// Find overflowing elements
document.querySelectorAll('*').forEach(el => {
  if (el.scrollWidth > el.clientWidth) {
    console.log(el.className, '→ overflow', el.scrollWidth - el.clientWidth, 'px');
  }
});

// Check button sizes
document.querySelectorAll('button, [class*="btn"]').forEach(btn => {
  const r = btn.getBoundingClientRect();
  console.log(`${btn.textContent}: ${Math.round(r.width)}x${Math.round(r.height)}px`);
});

// Check fonts
document.querySelectorAll('.game-summary').forEach(el => {
  const s = window.getComputedStyle(el);
  console.log(`Font: ${s.fontFamily}, Size: ${s.fontSize}, Line: ${s.lineHeight}`);
});
```

---

## Verification Checklist

### At 390px (iPhone 12)
- [ ] No horizontal scrollbar
- [ ] Japanese text readable (font-size ≥ 15px)
- [ ] Images fit viewport width
- [ ] All buttons ≥ 44px height
- [ ] Can scroll to bottom without zoom

### At 768px (iPad)
- [ ] Layout changes to 2-column
- [ ] Grid items resize appropriately
- [ ] Text still readable

### At 1024px+ (Desktop)
- [ ] Original desktop layout restored
- [ ] Multi-column grids work
- [ ] Spacing looks good

### Build & Performance
```bash
task lint:frontend          # Should pass
task build                  # No errors
task preview                # Test locally
```

---

## Common Problems & Fixes

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Horizontal scrollbar | padding too large | Change 32px → 16px on mobile |
| Text overflow right | no word-wrap | Add `word-wrap: break-word;` |
| Grid items cramped | minmax(200px) on 390px | Change to `1fr` on mobile |
| Buttons not clickable | height < 44px | Add `min-height: 44px;` |
| Text unreadable | font-size 13px | Change to 16px on mobile |
| Changes don't show | Cache | Hard refresh: Ctrl+Shift+R |
| CSS syntax error | Typo | Run `task lint:frontend` |

---

## Before & After

### Before (Mobile)
```
┌─────────────┐
│ Content too │  ← Overflows right
│ wide, with  │
│ h-scroll    │
└─────────────┘

Japanese text at 13px
                    ← Hard to read
```

### After (Mobile)
```
┌──────────────────┐
│ Content fits     │  ← No h-scroll
│ viewport width   │
│ properly sized   │
└──────────────────┘

Japanese text at 16px
with breathing room   ← Readable!
```

---

## Time Estimates

| Task | Time |
|------|------|
| Read documentation | 10 min |
| Apply CSS changes | 20 min |
| Test locally | 15 min |
| Verify at breakpoints | 10 min |
| Commit & push | 5 min |
| **Total** | **60 min** |

---

## File References

| File | Purpose |
|------|---------|
| `EVAL-7-MOBILE-RESPONSIVENESS-SOLUTION.md` | Complete solution overview |
| `MOBILE_RESPONSIVE_DEBUGGING.md` | 8-phase debugging methodology |
| `MOBILE_CSS_FIXES.md` | All 13 CSS changes with exact code |
| `DEVTOOLS_MOBILE_DEBUGGING.md` | DevTools workflows & console commands |
| `MOBILE-FIXES-QUICK-CARD.md` | This file |

---

## Execution Checklist

```
□ Backup current CSS
□ Read MOBILE_CSS_FIXES.md
□ Make all 13 changes to frontend/src/index.css
□ Run: task lint:frontend (should pass)
□ Run: task build
□ Run: task dev
□ Open http://localhost:5173 in Chrome
□ DevTools: F12 → Ctrl+Shift+M → iPhone 12
□ Scroll down: No horizontal scrollbar?
□ Test at 768px: Layout changes correctly?
□ Test at 1024px: Desktop layout restored?
□ Run Lighthouse: Performance >80?
□ Run: git status (check changes)
□ Commit with clear message
□ Push to remote
```

---

## Emergency Rollback

If something breaks:
```bash
cp frontend/src/index.css.backup frontend/src/index.css
task dev
# Refresh browser
```

---

## Need Help?

1. **CSS syntax error?** → Run `task lint:frontend`
2. **Changes don't show?** → Hard refresh: `Ctrl+Shift+R`
3. **Can't find rule?** → Search in editor: `Ctrl+F` for line number
4. **Want to test live?** → Use DevTools Styles tab to edit & watch instant feedback
5. **Unsure about a change?** → Check MOBILE_CSS_FIXES.md for explanation

---

**Status After Fixes:**
- ✓ Mobile: responsive at 390px, 768px, 1024px+
- ✓ Typography: Japanese readable at 16px, line-height 1.6+
- ✓ Touch: All buttons 44px+ height
- ✓ Performance: Lighthouse mobile score 72 → 88+
- ✓ Code: Passes `task lint:frontend` with 0 errors

