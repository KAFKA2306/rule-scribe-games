# Mobile Responsiveness Debugging & Fix Guide
## Frontend Design - GamePage Mobile Issues

---

## Executive Summary

The game detail page (`frontend/src/pages/GamePage.jsx`) has responsive CSS but exhibits **four critical mobile breakpoints**:

1. **Text Overflow**: Rules content exceeds viewport width (no `word-break`, `overflow-wrap`)
2. **Image Scaling**: Hero images don't respect mobile containers; aspect-ratio not recalculated for small screens
3. **Japanese Font Rendering**: Font-size too small on mobile; line-height insufficient for character legibility
4. **Layout Rigidity**: Fixed padding (32px) on `.game-detail-pane` consumes >25% of mobile viewport width

**Root Cause**: CSS written with desktop-first assumptions; media queries exist but don't target content layout comprehensively.

---

## Systematic Debugging Methodology

### Phase 1: DevTools Setup (Chrome/Safari)

#### Step 1.1: Activate Mobile Viewport
```
1. Open DevTools (F12 / Cmd+Option+I)
2. Click "Toggle Device Toolbar" (Ctrl+Shift+M / Cmd+Shift+M)
3. Select preset: iPhone 12 Pro (390×844px)
4. Reload page
```

#### Step 1.2: Identify Layout Violations
```
Inspect .game-detail-pane
  └─ Computed width: Should be 390px, check if overflow hidden
  └─ Padding: 32px on each side = 64px total (16% of viewport!)

Inspect .markdown-content
  └─ Max-width: Not set → content flows freely
  └─ Word-break: normal (default) → overflow on long words

Inspect img (hero, game cards)
  └─ Width: 100% (good)
  └─ Height: Calculated from aspect-ratio (problematic on mobile)
```

#### Step 1.3: Font Rendering Audit
Open DevTools → Elements → Inspect Japanese text
```
h1.game-title
  └─ Font-size: 28px (desktop-optimized)
  └─ Font-family: Space Grotesk (English font!)
  └─ Line-height: Not explicitly set → 1.2 default (too tight for CJK)

.markdown-content
  └─ Font-size: Inherited (14-16px)
  └─ Font-family: Zen Maru Gothic (correct, but sizing inadequate)
  └─ Line-height: 1.8 (good for English, marginal for Japanese)
```

### Phase 2: Console-Based Analysis

#### Step 2.1: Viewport & Container Metrics
```javascript
// Run in DevTools Console
const content = document.querySelector('.game-detail-pane');
const hero = document.querySelector('.game-hero-image img');
const rules = document.querySelector('.markdown-content');

console.log('Viewport:', window.innerWidth, window.innerHeight);
console.log('Content width:', content.offsetWidth, 'padding:', getComputedStyle(content).padding);
console.log('Hero width:', hero.offsetWidth, 'height:', hero.offsetHeight);
console.log('Rules overflow:', rules.scrollWidth > rules.offsetWidth ? 'YES' : 'NO');

// Detect text overflow
const allText = document.querySelectorAll('p, span, div');
allText.forEach(el => {
  if (el.scrollWidth > el.offsetWidth) {
    console.warn('Overflow:', el.textContent.substring(0, 50));
  }
});
```

#### Step 2.2: Font Stack Verification
```javascript
// Check which font is actually rendered
const title = document.querySelector('h1.game-title');
const computed = getComputedStyle(title);
console.log('Font:', computed.fontFamily);
console.log('Size:', computed.fontSize);
console.log('Weight:', computed.fontWeight);
console.log('Line-height:', computed.lineHeight);

// Check if Zen Maru Gothic loaded
console.log('Fonts loaded:', document.fonts.ready.then(() =>
  Array.from(document.fonts).map(f => f.family)
));
```

#### Step 2.3: Box Model Inspection
```javascript
// Detailed box model for critical elements
['game-detail-pane', 'game-hero-image', 'markdown-content', 'rules-section'].forEach(cls => {
  const el = document.querySelector('.' + cls);
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const style = getComputedStyle(el);

  console.log(`${cls}:`, {
    width: rect.width,
    height: rect.height,
    padding: style.padding,
    margin: style.margin,
    overflowX: style.overflowX,
  });
});
```

### Phase 3: Network & Font Loading

#### Step 3.1: Check Font Loading
```
DevTools → Network → Filter: "fonts"
→ Should see googleapis.com requests for Space Grotesk + Zen Maru Gothic
→ Status: 200, Size: ~50-100KB combined
→ If fonts fail to load, title/content fall back to sans-serif (will look wrong)
```

#### Step 3.2: Monitor DOM Reflow
```
DevTools → Performance tab
→ Record page load + scroll interactions
→ Look for red marks (forced reflow events)
→ Check if markdown rendering causes cascading layout shifts
```

---

## CSS Fixes: Root Causes & Solutions

### Issue 1: Content Overflow on Small Screens

**Current CSS (index.css:339)**:
```css
.game-detail-pane {
  padding: 32px;
  /* ... */
}
```

**Problems**:
- Padding is 32px on desktop-sized screens but steals 64px from 390px mobile viewport (16%)
- `.markdown-content` has no `max-width` or `word-break` rules

**Fix**:
```css
/* Add to index.css after line 550 (within @media 768px block) */

@media (max-width: 640px) {
  .game-detail-pane {
    padding: 16px;  /* Reduce to 32px total horizontal space */
    background: var(--bg-card);
    border-radius: 12px;
    border: 1px solid var(--border);
  }

  .markdown-content,
  .rule-text {
    word-break: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
    word-spacing: -0.05em;  /* Tighten spacing for CJK */
  }

  .markdown-content {
    font-size: 15px;
    line-height: 1.9;  /* Increase for Japanese legibility */
  }

  .markdown-content h1,
  .markdown-content h2,
  .markdown-content h3 {
    margin-top: 16px;  /* Reduce from 24px */
    margin-bottom: 12px;
  }

  .markdown-content p {
    margin-bottom: 12px;
  }
}
```

### Issue 2: Image Scaling & Aspect Ratio Problems

**Current CSS (index.css:707-726)**:
```css
.game-hero-image {
  width: 100%;
  max-width: 600px;
  aspect-ratio: 16/9;
}
```

**Problems**:
- `max-width: 600px` on 390px mobile screen works, but image container doesn't respect responsive heights
- Aspect ratio of 16:9 is optimized for landscape; on mobile portrait, it wastes space

**Fix**:
```css
/* Replace .game-hero-image block (lines 707-726) */

.game-hero-image {
  margin: 0 auto 24px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  border: 1px solid var(--border);
}

@media (max-width: 640px) {
  .game-hero-image {
    margin: 0 -16px 16px -16px;  /* Bleed to edges */
    border-radius: 0;
    aspect-ratio: 4/3;  /* Portrait-optimized */
    max-width: none;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .game-hero-image {
    aspect-ratio: 16/9;
    max-width: 100%;
  }
}

@media (min-width: 1024px) {
  .game-hero-image {
    aspect-ratio: 16/9;
    max-width: 600px;
  }
}

.game-hero-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
```

### Issue 3: Japanese Font Rendering (Small & Illegible)

**Current CSS (index.css:1-19, 499-502)**:
```css
:root {
  --font-main: 'Zen Maru Gothic', sans-serif;
  --font-head: 'Space Grotesk', sans-serif;
}

.markdown-content {
  line-height: 1.8;
  color: var(--text-muted);
}
```

**Problems**:
- Title uses `Space Grotesk` (English font, not optimized for Japanese)
- No explicit font-size for body text on mobile
- Line-height of 1.8 is barely adequate for CJK; characters at small size become mushy
- Font-weight not specified for Japanese fonts (default weight may be too thin)

**Fix**:
```css
/* Add to index.css after :root block */

@media (max-width: 640px) {
  h1.game-title {
    font-size: 20px;  /* Scale down from 28px */
    line-height: 1.4;  /* Tighter for titles */
    font-weight: 700;
    font-family: var(--font-main);  /* Use Zen Maru for all text */
  }

  h3, h4 {
    font-size: 16px;  /* Down from 18px */
    line-height: 1.4;
  }

  p, span, div {
    font-family: var(--font-main);  /* Ensure Japanese font */
    font-size: 15px;  /* Minimum readable size for CJK */
    font-weight: 400;
    line-height: 1.8;  /* Adequate spacing for density */
  }

  .markdown-content {
    font-size: 15px;
    line-height: 1.9;
    word-spacing: 0.05em;
  }

  .summary-text {
    font-size: 15px;
    line-height: 1.8;
  }
}

@media (min-width: 768px) {
  h1.game-title {
    font-family: var(--font-head);  /* Use English font only on larger screens */
  }

  p, span, div {
    font-size: 14px;  /* Default */
  }
}
```

### Issue 4: Header Actions Overflow (Buttons Stack)

**Current Code (GamePage.jsx:202-210)**:
```jsx
<div className="header-actions">
  <TextToSpeech text={speechText} />
  <TwitterShareButton slug={slug} title={title} />
  <ShareButton slug={slug} />
  <button className="share-btn" onClick={() => setIsEditOpen(true)} title="編集">
    ✏️ 編集
  </button>
  <RegenerateButton title={title} onRegenerate={setGame} />
</div>
```

**Problem**: 5 buttons in a row on mobile → overflow or wrap awkwardly.

**Fix - Add to index.css**:
```css
@media (max-width: 640px) {
  .header-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }

  .header-actions button,
  .header-actions a {
    flex: 1 1 calc(50% - 4px);  /* 2-column grid on mobile */
    min-width: 60px;
    padding: 8px 12px;
    font-size: 12px;
  }

  .share-btn {
    padding: 8px 12px;
    height: auto;
  }
}
```

### Issue 5: Grid Layouts Break on Mobile

**Current CSS (index.css:429-432, 453-456, 601-605)**:
```css
.keywords-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.basic-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}
```

**Problem**: `minmax(200px, 1fr)` on a 390px screen creates single column correctly, but gaps too wide relative to content.

**Fix**:
```css
@media (max-width: 640px) {
  .keywords-grid,
  .cards-grid,
  .basic-info-grid {
    grid-template-columns: 1fr;  /* Single column */
    gap: 8px;
  }

  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 8px;
  }

  .keyword-item,
  .card-item,
  .info-item {
    padding: 12px;
    font-size: 13px;
  }

  .keyword-item strong,
  .card-item strong {
    font-size: 13px;
  }

  .info-item strong {
    font-size: 11px;
  }

  .info-item span {
    font-size: 14px;
  }
}
```

---

## Implementation Checklist

### Step 1: Update index.css

**File**: `/home/kafka/projects/rule-scribe-games/frontend/src/index.css`

1. Add all `@media (max-width: 640px)` blocks at end of file (after line 1010)
2. Add font family fixes after `:root` block
3. Update `.game-hero-image` block with responsive breakpoints

### Step 2: Verify Layout

```bash
# Start dev server
task dev:frontend

# Open browser
# iPhone 12 Pro (390×844) in DevTools
# Reload and check:
# - No horizontal scrolling
# - Text readable without zoom
# - Images fit container
# - Buttons visible, not overlapped
```

### Step 3: Test Japanese Text Rendering

- [ ] Titles display with Zen Maru Gothic on mobile
- [ ] Line-height adequate for kanji/hiragana/katakana
- [ ] No character clipping
- [ ] Summary text (3行でわかる要約) reads clearly

### Step 4: Test on Multiple Devices

| Device | Viewport | Test Points |
|--------|----------|------------|
| iPhone 12 Pro | 390×844 | Rules text, images, buttons |
| iPhone SE | 375×667 | Tightest constraint |
| iPad Mini | 768×1024 | Tablet breakpoint |
| Android (SM-A12) | 360×800 | Short viewport |

---

## DevTools Verification Scripts

### Script 1: Detect All Overflow Issues
```javascript
const overflowElements = [];
document.querySelectorAll('*').forEach(el => {
  const computed = getComputedStyle(el);
  const scrollWidth = el.scrollWidth;
  const offsetWidth = el.offsetWidth;
  const scrollHeight = el.scrollHeight;
  const offsetHeight = el.offsetHeight;

  if (scrollWidth > offsetWidth || scrollHeight > offsetHeight) {
    overflowElements.push({
      tag: el.tagName,
      class: el.className,
      content: el.textContent?.substring(0, 30),
      scrollWidth,
      offsetWidth,
      scrollHeight,
      offsetHeight,
      overflow: `${computed.overflow}/${computed.overflowX}/${computed.overflowY}`,
    });
  }
});

console.table(overflowElements);
if (overflowElements.length === 0) console.log('✓ No overflow detected');
else console.log(`⚠ ${overflowElements.length} overflow issues found`);
```

### Script 2: Validate Font Rendering
```javascript
const fontTests = {
  titleFont: getComputedStyle(document.querySelector('h1.game-title')).fontFamily,
  contentFont: getComputedStyle(document.querySelector('.markdown-content')).fontFamily,
  fontSize: getComputedStyle(document.querySelector('.markdown-content')).fontSize,
  lineHeight: getComputedStyle(document.querySelector('.markdown-content')).lineHeight,
  fontWeight: getComputedStyle(document.querySelector('p')).fontWeight,
};

console.table(fontTests);

// Check if fonts loaded
document.fonts.ready.then(() => {
  const loaded = Array.from(document.fonts).map(f => f.family);
  console.log('Loaded fonts:', loaded);
});
```

### Script 3: Measure Spacing
```javascript
['game-detail-pane', 'game-hero-image', 'markdown-content'].forEach(cls => {
  const el = document.querySelector('.' + cls);
  const rect = el.getBoundingClientRect();
  const computed = getComputedStyle(el);

  console.log(`${cls}:`, {
    viewportWidth: window.innerWidth,
    elementWidth: Math.round(rect.width),
    widthPercent: Math.round((rect.width / window.innerWidth) * 100) + '%',
    padding: computed.padding,
    margin: computed.margin,
    availableWidth: Math.round(rect.width),
  });
});
```

---

## CSS Media Query Strategy

### Mobile-First Approach (Recommended)

Instead of starting with desktop CSS and scaling down, reverse the order:

**Current (Desktop-First - ANTI-PATTERN)**:
```css
/* Base CSS targets desktop */
.game-detail-pane {
  padding: 32px;
}

/* Media query tries to fix mobile */
@media (max-width: 640px) {
  .game-detail-pane {
    padding: 16px;
  }
}
```

**Better (Mobile-First)**:
```css
/* Base CSS targets mobile */
.game-detail-pane {
  padding: 16px;
}

/* Media query scales up for desktop */
@media (min-width: 768px) {
  .game-detail-pane {
    padding: 32px;
  }
}
```

### Recommended Breakpoints

```css
/* Mobile: < 640px (default) */
@media (max-width: 640px) { }

/* Tablet: 641px - 1023px */
@media (min-width: 641px) and (max-width: 1023px) { }

/* Desktop: ≥ 1024px */
@media (min-width: 1024px) { }
```

---

## Font Rendering Best Practices

### CJK Character Rendering on Mobile

**Problem**: Japanese text appears blurry/muddy at small sizes.

**Root Causes**:
1. Font-weight too light (300-400) → characters lose definition
2. Line-height too tight (< 1.6) → characters overlap visually
3. Letter-spacing too tight → dense, illegible clusters
4. Font-size below 14px on mobile → anti-aliasing artifacts

**Solution Stack**:
```css
.japanese-text {
  font-family: 'Zen Maru Gothic', -apple-system, sans-serif;  /* System fallback */
  font-size: 15px;  /* Minimum for mobile */
  font-weight: 500;  /* Slightly heavier */
  line-height: 1.8;  /* Generous spacing */
  letter-spacing: 0.02em;  /* Subtle expansion */
  -webkit-font-smoothing: antialiased;  /* Render hint */
  -moz-osx-font-smoothing: grayscale;
}
```

### Font Preloading

Update `frontend/src/main.jsx` to preload fonts:
```jsx
// Add before <App /> render
if (typeof window !== 'undefined') {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = 'style';
  link.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Zen+Maru+Gothic:wght@400;500;700&display=swap';
  document.head.appendChild(link);
}
```

---

## Container Query Alternative (Future)

If supporting only modern browsers (Chrome 105+, Safari 16+):

```css
/* Define container */
.game-detail-pane {
  container-type: inline-size;
  container-name: detail;
}

/* Rules apply based on container width, not viewport */
@container detail (max-width: 640px) {
  .markdown-content {
    font-size: 15px;
    padding: 0;
  }
}
```

Benefits: Responsive logic tied to component size, not viewport.

---

## Accessibility Considerations

### Mobile A11y

1. **Touch Targets**: Buttons ≥ 44px × 44px (current 32px height is too small)
   ```css
   @media (max-width: 640px) {
     .share-btn {
       min-height: 44px;
       min-width: 44px;
     }
   }
   ```

2. **Color Contrast**: Ensure text on `--text-muted` backgrounds meets WCAG AA (4.5:1)
   - Test with: WebAIM Contrast Checker

3. **Text Zoom**: Ensure layout doesn't break at 200% zoom
   - Test: DevTools → More Tools → Rendering → Emulate CSS media feature prefers-color-scheme

---

## Summary of Fixes Applied

| Issue | Root Cause | Fix | Location |
|-------|-----------|-----|----------|
| Text overflow | No `word-break` | Add `break-word`, `overflow-wrap` | New `@media 640px` block |
| Image scaling | Desktop aspect-ratio | Use `aspect-ratio: 4/3` on mobile | `.game-hero-image` |
| Japanese illegible | Small font-size, English font-family | Font 15px+, use `Zen Maru Gothic` | Font rules + mobile block |
| Padding waste | 32px on 390px screen | Reduce to 16px | `.game-detail-pane @media 640px` |
| Button overflow | 5 buttons in flex row | 2-column grid layout | `.header-actions @media 640px` |
| Grid too wide | `minmax(200px, 1fr)` on 390px | Single column + 8px gap | Grid media queries |

---

## Testing Checklist (Post-Implementation)

```bash
# 1. Visual Regression Test
task dev:frontend
→ Open GamePage in mobile viewport
→ Compare before/after screenshots

# 2. Ruff Linting
task lint

# 3. Playwright E2E (if configured)
task test

# 4. Manual Testing Matrix
iPhone 12 Pro (390×844) - Rules text readable? Images fit? No scrollbars?
iPhone SE (375×667) - Tightest constraint. Any cutoff?
iPad (768×1024) - Tablet layout applied correctly?
Android small (360×800) - Font rendering legible?

# 5. Performance
DevTools → Performance → Record load
→ Check for layout shifts during rendering
→ Font loading should not block paint (display=swap in @import)
```

---

## Prevention Strategies

### 1. Design System Audit
Review all component sizes against mobile constraints:
- Max content width: `calc(100% - 32px)` on desktop, `calc(100% - 16px)` on mobile
- Min touch target: 44px × 44px
- Min font-size for CJK: 14px
- Min line-height for CJK: 1.6

### 2. Automated Testing
Add Playwright test for mobile viewport:
```javascript
// frontend/tests/mobile-responsiveness.spec.js
test('GamePage responsive on mobile (390px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/games/splendor');

  // Check no horizontal overflow
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth;
  });
  expect(overflow).toBe(false);

  // Check font size
  const fontSize = await page.locator('.markdown-content').evaluate(el =>
    getComputedStyle(el).fontSize
  );
  expect(parseInt(fontSize)).toBeGreaterThanOrEqual(14);
});
```

### 3. Continuous Monitoring
- Set up Lighthouse CI to flag mobile accessibility scores < 90
- Track Core Web Vitals (Cumulative Layout Shift) on mobile
- Monitor font loading performance (FCP should not exceed 2.5s)

---

## References

- [MDN: Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [Google Fonts: Best Practices](https://fonts.google.com/metadata/fonts)
- [W3C: CSS Containment (Container Queries)](https://www.w3.org/TR/css-contain-3/)
- [WebAIM: Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Apple HIG: Spacing Guidelines](https://developer.apple.com/design/human-interface-guidelines/ios/visual-design/typography/)

