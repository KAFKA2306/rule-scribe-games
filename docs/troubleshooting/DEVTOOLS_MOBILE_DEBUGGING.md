# DevTools Mobile Debugging Guide

**Quick Reference for Chrome DevTools Mobile Inspection**

Systematically debug mobile responsive issues on the game detail page using Chrome's built-in DevTools.

---

## Quick Start (5 minutes)

### Step 1: Open DevTools & Enable Mobile Mode
```
1. Open http://localhost:5173 in Chrome
2. Press F12 (Windows) or Cmd+Option+I (Mac)
3. Press Ctrl+Shift+M (Windows) or Cmd+Shift+M (Mac) to toggle Device Toolbar
4. Select "iPhone 12" from dropdown (390px width)
```

### Step 2: Identify Overflow Issues
```
Scan the page visually:
✓ No horizontal scrollbar? → Layout is responsive
✗ Horizontal scrollbar? → Content overflowing parent container
```

### Step 3: Inspect Problem Elements
```
1. Right-click on overflowing content
2. Select "Inspect" (opens DevTools at that element)
3. Look for:
   - padding/margin too large
   - width set to fixed px
   - max-width not set
   - overflow: hidden with overflow content
```

### Step 4: Check Computed Styles
```
In DevTools Elements panel:
1. Select element
2. Go to "Styles" tab (right panel)
3. Look for problematic values:
   ✗ width: 600px (fixed width on mobile)
   ✗ padding: 32px (too large)
   ✓ padding: 16px (mobile-appropriate)
   ✓ width: 100% (responsive)
```

### Step 5: Test Layout Changes in Real-Time
```
In DevTools Styles panel:
1. Find problematic rule
2. Click to edit the value
3. Change (e.g., padding: 32px → 16px)
4. Watch page update live
5. If fixed, apply to actual CSS file
```

---

## Detailed Inspection Workflows

### Workflow 1: Fixing Text Overflow

**Problem**: Japanese text runs off the right edge of screen

**Step 1: Find Overflowing Element**
```
1. Open DevTools Console (F12 → Console tab)
2. Run:
   document.querySelectorAll('*').forEach(el => {
     if (el.scrollWidth > el.clientWidth) {
       console.log(el.className, '→ overflow', el.scrollWidth - el.clientWidth, 'px');
     }
   });
3. This lists all elements wider than their container
```

**Step 2: Inspect Parent Container**
```
Example output:
game-detail-pane → overflow 64px
rule-text → overflow 120px

Inspect the root cause:
1. DevTools Elements → click on overflowing element
2. In Styles panel, check:
   width: ? (should be auto or 100%, not fixed)
   padding: ? (should be mobile-friendly)
   white-space: ? (should be normal, not pre or nowrap)
```

**Step 3: Find the CSS Rule**
```
In Styles panel, hover over rule to see source file:
- If showing index.css line 499, that's .markdown-content
- Check line 499 for word-wrap rules

If word-wrap is missing:
   ✗ NO: word-wrap: break-word;
   ✓ YES: word-wrap: break-word;
         overflow-wrap: break-word;
         hyphens: auto;
```

**Step 4: Apply Fix**
```
1. Edit index.css line 499 (or relevant section)
2. Add word-break rules:
   word-wrap: break-word;
   overflow-wrap: break-word;
3. Save file (should auto-reload with Vite)
4. Verify in DevTools that overflow is gone
```

---

### Workflow 2: Fixing Image Scaling

**Problem**: Images are either too small or overflow the viewport

**Step 1: Check Image Dimensions**
```
In DevTools Console:
document.querySelectorAll('img').forEach(img => {
  console.log({
    src: img.src.substring(0, 50),
    actual: `${img.offsetWidth}x${img.offsetHeight}px`,
    viewport: `${window.innerWidth}x${window.innerHeight}px`,
    overflow: img.offsetWidth > window.innerWidth ? 'YES' : 'NO'
  });
});

Output example:
{
  src: "https://...catan-cover.webp",
  actual: "900x500px",      ← Actual rendered size
  viewport: "390x844px",    ← Mobile viewport
  overflow: "YES"           ← Image too wide!
}
```

**Step 2: Identify CSS Container**
```
1. Right-click overflowing image → Inspect
2. Look for parent elements:
   <div class="game-hero-image">  ← Container
     <img ... />                  ← Image element
   </div>
3. Check .game-hero-image in DevTools Styles:
   width: 100%    ✓
   max-width: 600px  ← TOO LARGE for 390px!
```

**Step 3: Inspect Computed Styles**
```
In Styles panel, check img element:
✓ width: 100% ✓ height: auto → Should scale down
✗ width: 900px → Image refuses to scale
✗ aspect-ratio: missing → May cause layout shift

For .game-hero-image container:
✓ max-width: 100% → Fits viewport
✗ max-width: 600px → Too large on mobile
```

**Step 4: Apply Responsive Max-Width**
```
In DevTools, test fix live:
1. Edit .game-hero-image styles
2. Change max-width: 600px to max-width: 100%
3. Image should shrink to fit viewport
4. If correct, update index.css:
   .game-hero-image {
     max-width: 100%;  /* Changed from 600px */
   }

If image becomes pixelated:
   - Add: width: 100%; (may help)
   - Check: object-fit: cover; (prevents distortion)
   - Add: @media (min-width: 768px) { max-width: 600px; }
```

---

### Workflow 3: Checking Font Rendering & Size

**Problem**: Japanese text is too small or cut off

**Step 1: Verify Font Loads**
```
In DevTools Network tab:
1. Filter: type is "font"
2. Look for "Zen Maru Gothic"
3. Check:
   ✓ Status 200 (loaded successfully)
   ✗ Status 404 (missing font)
   ✗ Status 0 (blocked/timeout)

If 404 or 0:
   - Font URL may be wrong in index.css line 1
   - Verify: @import url('https://fonts.googleapis.com/...')
   - Check CORS headers
```

**Step 2: Check Applied Font**
```
In DevTools Console:
// Check which font is actually applied
document.querySelectorAll('body, .game-summary, .markdown-content').forEach(el => {
  const font = window.getComputedStyle(el).fontFamily;
  const size = window.getComputedStyle(el).fontSize;
  console.log(`${el.tagName}.${el.className} → ${font} @ ${size}`);
});

Expected output:
body → "Zen Maru Gothic", sans-serif @ 16px
.game-summary → "Zen Maru Gothic", sans-serif @ 15px
.markdown-content → "Zen Maru Gothic", sans-serif @ 16px

If showing "sans-serif" instead of "Zen Maru Gothic":
   ✗ Font failed to load
   ✓ Fallback font is being used (readable but not ideal)
```

**Step 3: Measure Font Size**
```
In DevTools Elements → Styles:
1. Inspect text element (e.g., .game-summary)
2. Hover over font-size rule to see actual value
3. Compare to mobile readability standards:
   ✗ < 12px → Too small (especially for CJK)
   ✓ 14-16px → Readable on mobile
   ✓ 18-24px → Good for headings

Japanese text typically needs 1-2px larger than Latin:
   Latin body: 14px → Japanese body: 16px
```

**Step 4: Check Line Height**
```
In Styles panel, look for line-height:
✗ line-height: 1.3 → Too cramped for Japanese
✓ line-height: 1.6 → Readable breathing room
✓ line-height: 1.8+ → Optimal for CJK

To test:
1. Edit in DevTools: change line-height: 1.5 → 1.8
2. Watch text spacing improve
3. If looks better, update index.css
```

---

### Workflow 4: Testing Touch Target Sizes

**Problem**: Buttons are too small to click on mobile (< 44px)

**Step 1: Measure Button Sizes**
```
In DevTools Console:
document.querySelectorAll('button, a[class*="btn"], .share-btn').forEach(btn => {
  const rect = btn.getBoundingClientRect();
  const minSize = Math.min(rect.width, rect.height);
  const status = minSize >= 44 ? '✓' : '✗';
  console.log(
    `${status} ${btn.textContent.substring(0, 20)} → ${Math.round(rect.width)}x${Math.round(rect.height)}px`
  );
});

Output example:
✓ Share → 60x44px ✓ OK
✗ Edit → 35x32px ✗ TOO SMALL
✓ Regenerate → 120x48px ✓ OK
```

**Step 2: Inspect Small Button**
```
1. Right-click the "35x32px" button → Inspect
2. In Styles panel, check:
   height: ? (should be ≥ 44px)
   padding: ? (contributes to clickable area)
   line-height: ? (sometimes replaces height)
   display: flex; align-items: center; (helps sizing)
```

**Step 3: Apply Fix**
```
Add to button class:
min-height: 44px;  /* iOS HIG minimum */
display: inline-flex;
align-items: center;
justify-content: center;
padding: 10px 16px;  /* Fallback if height not set */

Test in DevTools:
1. Edit button styles live
2. Add: min-height: 44px;
3. Button should expand to proper size
4. Apply fix to index.css
```

---

### Workflow 5: Testing Grids & Flex Layouts

**Problem**: Grid items are too narrow, text wraps awkwardly

**Step 1: Inspect Grid**
```
1. Right-click on grid element (e.g., .keywords-grid)
2. Inspect → Styles panel
3. Look for grid-template-columns:
   ✗ repeat(auto-fill, minmax(200px, 1fr))
     → On 390px viewport: 390 / 200 = 1.95 columns
     → Forces 2 columns with cramped items
   ✓ 1fr  → Single column on mobile
```

**Step 2: Test Mobile-First Grid**
```
In DevTools Styles, edit live:
1. Find: grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))
2. Change to: grid-template-columns: 1fr
3. Watch items stack into single column
4. Text should breathe
```

**Step 3: Add Tablet Breakpoint**
```
In index.css, update grid:
.keywords-grid {
  grid-template-columns: 1fr;  /* Mobile */
}

@media (min-width: 640px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

Test in DevTools:
1. Open responsive mode
2. Resize viewport from 390px → 640px
3. Watch grid change from 1 column to 2-3 columns
4. Items should resize smoothly
```

---

### Workflow 6: Testing Scroll Behavior

**Problem**: Content is cut off, user can't scroll to see it

**Step 1: Check Overflow Properties**
```
In DevTools Console:
const pane = document.querySelector('.game-detail-pane');
console.log({
  scrollHeight: pane.scrollHeight,
  clientHeight: pane.clientHeight,
  canScroll: pane.scrollHeight > pane.clientHeight,
  overflowY: window.getComputedStyle(pane).overflowY,
  overflowX: window.getComputedStyle(pane).overflowX
});

Expected output (if content is long):
{
  scrollHeight: 2400,        ← Actual content height
  clientHeight: 600,         ← Visible height
  canScroll: true,           ← Content exceeds visible area
  overflowY: "auto",         ← Scrollbar should appear
  overflowX: "visible"       ← No horizontal scroll
}

If canScroll is false but content is cut off:
   ✗ max-height is set too small
   ✗ overflow: hidden is blocking scroll
```

**Step 2: Measure Content Height**
```
In DevTools:
1. Select content element (e.g., .game-detail-pane)
2. Look at Styles → Box Model diagram
3. Note the content height
4. Compare to viewport height:
   Content 2400px > Viewport 844px → Should scroll ✓
   Content 600px < Viewport 844px → Fits without scroll ✓
```

**Step 3: Enable Scroll If Needed**
```
If content is cut off, in Styles panel add:
overflow-y: auto;        /* Allow vertical scroll */
overflow-x: hidden;      /* Prevent horizontal scroll */
max-height: 100vh;       /* Or use flex layout */

On iOS, add for smooth scrolling:
-webkit-overflow-scrolling: touch;
```

---

## Console Commands Cheat Sheet

```javascript
// 1. Find elements overflowing horizontally
document.querySelectorAll('*').forEach(el => {
  if (el.scrollWidth > el.clientWidth) {
    console.warn(`Overflow: ${el.className}`, el.scrollWidth - el.clientWidth, 'px');
  }
});

// 2. Check all button sizes
document.querySelectorAll('button, [class*="btn"]').forEach(btn => {
  const r = btn.getBoundingClientRect();
  const ok = Math.min(r.width, r.height) >= 44 ? '✓' : '✗';
  console.log(`${ok} ${r.width}x${r.height}px - ${btn.textContent}`);
});

// 3. Check font sizes
document.querySelectorAll('body, .game-summary, h1, h2, h3').forEach(el => {
  console.log(`${el.tagName} → ${window.getComputedStyle(el).fontSize}`);
});

// 4. Check applied fonts
document.querySelectorAll('*').forEach(el => {
  const font = window.getComputedStyle(el).fontFamily;
  if (font.includes('Zen')) console.log(el.tagName, font);
});

// 5. Check viewport width
console.log(`Viewport: ${window.innerWidth}x${window.innerHeight}px`);

// 6. Check scrollable elements
document.querySelectorAll('[style*="overflow"]').forEach(el => {
  console.log(el.className, window.getComputedStyle(el).overflow);
});

// 7. Measure image sizes
document.querySelectorAll('img').forEach(img => {
  console.log(`${img.src.split('/').pop()} → ${img.offsetWidth}x${img.offsetHeight}px`);
});

// 8. Check padding of containers
['app-container', 'game-detail-pane', 'game-list-pane'].forEach(cls => {
  const el = document.querySelector('.' + cls);
  if (el) {
    const style = window.getComputedStyle(el);
    console.log(`${cls} padding: ${style.padding}`);
  }
});

// 9. List all CSS custom properties (CSS variables)
console.log(
  Array.from(document.styleSheets[0].cssRules)
    .filter(r => r.style)
    .map(r => r.style.getPropertyValue('--spacing-mobile'))
);

// 10. Check media query breakpoints
window.matchMedia('(min-width: 640px)').addListener(e => {
  console.log('640px breakpoint:', e.matches ? 'active' : 'inactive');
});
```

---

## Breakpoint Testing Guide

Test at these common viewport sizes:

| Device | Width | Test | Notes |
|--------|-------|------|-------|
| Old Phone | 320px | Extreme mobile | Rarely used now |
| iPhone 11/12 | 375px | Standard mobile | Common user size |
| iPhone 14 | 390px | Target size | Most common current |
| Galaxy S22 | 360px | Android mobile | Common variant |
| iPad | 768px | Tablet threshold | Breakpoint test |
| iPad Pro | 1024px | Large tablet | Secondary breakpoint |
| Desktop | 1280px+ | Full desktop | Base desktop layout |

**In DevTools**:
1. Open Device Toolbar (Ctrl+Shift+M)
2. Click on device dropdown → "Edit custom devices"
3. Create device "Target 390px" with width 390, height 844
4. Test each breakpoint by resizing viewport

---

## Quick Fixes Reference

| Problem | Console Check | CSS Fix | Verify |
|---------|---------------|---------|--------|
| Text overflow | `el.scrollWidth > el.clientWidth` | Add `word-wrap: break-word;` | No horizontal scroll |
| Image too wide | `img.offsetWidth > window.innerWidth` | Add `max-width: 100%;` | Image fits viewport |
| Font too small | `fontSize < 14px` | Change to `16px` on mobile | Readable without zoom |
| Button too small | `btn height < 44px` | Add `min-height: 44px;` | Easily clickable |
| Grid cramped | `grid-template-columns: repeat(auto-fill, minmax(200px))` | Change to `1fr` on mobile | Single column stacking |
| Content cut off | `scrollHeight > clientHeight && overflowY != "auto"` | Add `overflow-y: auto;` | Can scroll to content |

---

## Performance Testing

### Lighthouse Mobile Audit
```
1. DevTools → Lighthouse tab
2. Device: Mobile
3. Throttling: Typical 4G
4. Run audit

Target scores:
- Performance: > 80
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90

Check metrics:
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1
```

### Network Throttling
```
1. DevTools → Network tab
2. Throttling dropdown (default: "No throttling")
3. Select: "Slow 3G"
4. Reload page
5. Watch request waterfall
6. Look for:
   - Large images blocking render
   - Fonts loading late
   - Scripts delaying interaction
```

---

## Tips & Tricks

### Tip 1: Edit CSS Live & Persist
```
In DevTools Styles:
1. Edit CSS value
2. Page updates instantly
3. To persist: Copy entire rule to index.css
4. Save file, reload page to verify
```

### Tip 2: Toggle Media Queries
```
In DevTools:
1. Menu → Three dots → More tools → Rendering
2. Check "Emulate CSS media feature prefers-reduced-motion"
3. Or manually resize viewport to cross breakpoints
```

### Tip 3: Simulate Touch
```
In DevTools:
1. Menu → More tools → Sensors
2. Check "Emulate CSS media feature hover: none"
3. Hover effects become taps
4. Verify touch-friendliness
```

### Tip 4: Dark Mode Toggle
```
In DevTools:
1. Menu → More tools → Rendering
2. Check "Emulate CSS media feature prefers-color-scheme"
3. Select: "prefers-color-scheme: dark"
4. Verify contrast on dark background
```

### Tip 5: Screenshot at Breakpoint
```
In DevTools:
1. Set desired viewport size
2. Press Ctrl+Shift+P (Mac: Cmd+Shift+P)
3. Type: "Screenshot"
4. Select "Capture screenshot"
5. Image saved to Downloads
```

---

## When to Use DevTools vs Code Editor

| Task | DevTools | Code Editor |
|------|----------|-------------|
| **Quick testing** | ✓ Edit live, instant feedback | ✗ Requires save & reload |
| **Finding bugs** | ✓ Inspect actual rendered element | ✗ Text search only |
| **Measuring sizes** | ✓ Click to measure, see pixel values | ✗ Can't measure at runtime |
| **CSS syntax help** | ✗ No autocomplete | ✓ Excellent autocomplete |
| **Permanent fixes** | ✗ Lost on page reload | ✓ Persists to file |
| **Testing responsive** | ✓ Built-in viewport simulator | ✗ Need to resize window |

**Workflow**: Use DevTools to find & test, then apply fixes to code editor.

---

## Troubleshooting DevTools Issues

**Q: DevTools shows computed styles different from CSS file?**
A: Browser cache. Press `Ctrl+Shift+Delete` to clear, then hard refresh (`Ctrl+Shift+R`).

**Q: Edits in DevTools don't persist?**
A: They don't. Copy the fixed values back to `index.css` and save.

**Q: Font not loading in DevTools but works on desktop?**
A: Cache issue. In Network tab, disable cache (checkbox) and reload.

**Q: Can't click buttons in mobile mode?**
A: Enable "Emulate CSS media feature hover: none" to test touch behavior.

**Q: Viewport changes don't trigger media queries?**
A: Cold restart. Close DevTools and reopen (F12).

---

## Next Steps

1. **Identify issues** using DevTools workflows above
2. **Test fixes** live in DevTools Styles panel
3. **Apply fixes** to `frontend/src/index.css`
4. **Verify** fixes with DevTools again (hard refresh)
5. **Run Lighthouse** to confirm performance gain
6. **Commit** changes with clear message

