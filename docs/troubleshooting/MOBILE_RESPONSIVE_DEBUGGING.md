# Mobile Responsive Design - Debugging & Fix Methodology

**Eval 7: Frontend Design - Mobile Responsiveness**

Users are reporting broken layouts on mobile: rules text overflows, images don't scale, Japanese text is illegible.

---

## Part 1: Systematic Diagnosis (8-Phase Approach)

### Phase 1: Environment Verification
**Action**: Confirm development environment setup
```bash
# Verify frontend is running on correct port
curl -s http://localhost:5173 | head -20

# Check Node/npm versions
node --version && npm --version

# Verify CSS is being served
curl -s http://localhost:5173 | grep -i "<link.*css"
```

**Expected**: HTTP 200, Node 18+, CSS <link> tags present

### Phase 2: Browser DevTools Mobile Inspection
**Action**: Use Chrome DevTools viewport simulation
```
1. Open http://localhost:5173 in Chrome
2. Press F12 → Device Toolbar (Ctrl+Shift+M)
3. Test breakpoints:
   - iPhone 12: 390px (mobile)
   - iPad: 768px (tablet threshold)
   - Desktop: 1024px+

4. Check for layout issues:
   - Does .game-detail-pane overflow horizontally?
   - Are images constrained to viewport width?
   - Do buttons stack vertically on <390px?
```

**Expected**: No horizontal scrolling, images scale, text readable at all breakpoints

### Phase 3: CSS Box Model Analysis
**Action**: Inspect computed styles in DevTools
```
Select .game-detail-pane → Styles panel:
- padding: Should be 32px on desktop, 16px on mobile
- max-width: Should be 100% on mobile (<768px)
- overflow-x: Should be visible (not hidden with clipping)

Select .markdown-content → Computed:
- word-wrap: Should be break-word
- overflow-wrap: Should be break-word
- white-space: Should be normal (NOT pre-wrap for long content)
```

**Problematic patterns**:
```css
/* BAD: Forces horizontal scroll on mobile */
.game-detail-pane {
  padding: 32px;  /* 64px total = 128px on <390px = overflow */
}

/* GOOD: Responsive padding */
.game-detail-pane {
  padding: 16px;  /* Mobile */
}
@media (min-width: 768px) {
  .game-detail-pane {
    padding: 32px;  /* Tablet+ */
  }
}
```

### Phase 4: Font Rendering Check
**Action**: Diagnose Japanese text legibility
```
In DevTools Console (F12 → Console):

// Check font loading
console.log(document.fonts.ready)

// Check applied fonts
document.querySelectorAll('*').forEach(el => {
  const font = window.getComputedStyle(el).fontFamily;
  if (font.includes('Zen Maru Gothic')) console.log(el, font)
})

// Check viewport meta tag
console.log(document.querySelector('meta[name="viewport"]'))
```

**Expected output**:
```
<meta name="viewport" content="width=device-width, initial-scale=1">
Font loaded: Zen Maru Gothic, Space Grotesk
```

**If Japanese text is illegible**:
- Check font-size < 12px (too small for Japanese)
- Check line-height < 1.5 (causes cramped text)
- Check font-weight: CJK needs weight 400-700, not 900

### Phase 5: Image Scaling Verification
**Action**: Check image responsiveness
```css
/* Current in index.css lines 707-726 */
.game-hero-image {
  width: 100%;
  max-width: 600px;
  aspect-ratio: 16/9;
}

.game-hero-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

**Test**:
1. Open DevTools, go to Network tab
2. Simulate throttling (Slow 3G)
3. Check image actually loads (no 404s)
4. Verify dimensions match viewport

**Mobile issues to watch**:
- Images larger than viewport width → add `max-width: 100%` to img
- Missing `loading="lazy"` → causes initial load delays
- aspect-ratio not respected → use padding-bottom fallback

### Phase 6: Overflow & Text Wrapping Analysis
**Action**: Find text that breaks layout
```css
/* DANGER: Pre-formatted text can overflow */
.rule-text {
  white-space: pre-wrap;  /* ← Breaks on long words */
}

/* SOLUTION: Add word-wrapping */
.rule-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

/* DANGER: Grid without min-width: 0 */
.keywords-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));  /* ← 200px is too large for mobile */
}

/* SOLUTION: Reduce minmax on mobile */
.keywords-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile: 1 column */
}
@media (min-width: 640px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
```

### Phase 7: Scroll & Touch Behavior
**Action**: Test scrollability and touch
```javascript
// Check if scrollable pane is constrained correctly
const pane = document.querySelector('.game-detail-pane');
console.log({
  scrollHeight: pane.scrollHeight,
  clientHeight: pane.clientHeight,
  canScroll: pane.scrollHeight > pane.clientHeight
});

// Check if overflow-y is set
console.log(window.getComputedStyle(pane).overflowY);
```

**Issues**:
- `overflow: hidden` without `overflow-y: auto` → content unreachable
- `max-height: 100vh` without scroll → buttons/content cut off
- Touch scrolling jank → add `webkit-overflow-scrolling: touch`

### Phase 8: Comprehensive Mobile Viewport Test
**Action**: Test all breakpoints systematically
```
Breakpoints to test (in DevTools):
- 320px (old phones): Base mobile
- 375px (iPhone 11): Standard mobile
- 390px (iPhone 12): Target mobile
- 428px (iPhone 14+): Large mobile
- 768px (iPad): Tablet threshold
- 1024px (iPad Pro): Tablet
- 1280px+: Desktop
```

**Checklist per breakpoint**:
- [ ] No horizontal scrolling
- [ ] Text readable (font-size ≥ 12px)
- [ ] Images contained within viewport
- [ ] Buttons clickable (≥ 44px height)
- [ ] Japanese characters not cut off
- [ ] Touch targets 48px+ (iOS HIG)

---

## Part 2: Identified Issues & Solutions

### Issue 1: `.game-detail-pane` padding overflow
**Location**: `frontend/src/index.css` line 339
**Current code**:
```css
.game-detail-pane {
  padding: 32px;  /* 64px total width = impossible on 390px screen */
  border-radius: 16px;
  overflow-y: auto;
}
```

**Fix**:
```css
.game-detail-pane {
  padding: 16px;  /* Mobile: 32px total = 70% of 390px viewport ✓ */
  border-radius: 16px;
  overflow-y: auto;
}

@media (min-width: 768px) {
  .game-detail-pane {
    padding: 32px;  /* Tablet+: restore spacing */
  }
}
```

### Issue 2: Markdown content overflows
**Location**: `frontend/src/index.css` lines 499-513
**Current code**:
```css
.markdown-content {
  line-height: 1.8;
  color: var(--text-muted);
}
/* Missing word-wrap rules */
```

**Fix**:
```css
.markdown-content {
  line-height: 1.8;
  color: var(--text-muted);
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.markdown-content p,
.markdown-content li {
  word-break: break-word;  /* For long URLs, no spaces */
}

.markdown-content code {
  overflow-x: auto;  /* Code blocks can scroll horizontally */
  display: block;
  word-break: break-all;
}
```

### Issue 3: Keywords grid too wide on mobile
**Location**: `frontend/src/index.css` line 430-433
**Current code**:
```css
.keywords-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
/* minmax(200px) is 51% of 390px viewport = overflow */
```

**Fix**:
```css
.keywords-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile: stack vertically */
  gap: 12px;
}

@media (min-width: 640px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

@media (min-width: 1024px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
```

### Issue 4: Japanese font sizing too small
**Location**: `frontend/src/index.css` line 17-18
**Current code**:
```css
--font-main: 'Zen Maru Gothic', sans-serif;

/* Applied sizes often 13px or smaller */
.game-summary {
  font-size: 13px;  /* Too small for Japanese */
}
```

**Fix**:
```css
/* Mobile: Increase base Japanese font size */
body {
  font-size: 16px;  /* Base for readability */
  font-family: var(--font-main);
}

.game-summary {
  font-size: 15px;  /* Mobile readable */
  line-height: 1.6;  /* More breathing room */
}

@media (min-width: 768px) {
  .game-summary {
    font-size: 13px;  /* Can be tighter on desktop */
  }
}

/* Japanese-specific: Increase line-height */
.markdown-content {
  line-height: 1.9;  /* CJK needs extra spacing */
  letter-spacing: 0.02em;  /* Subtle letter-spacing for clarity */
}
```

### Issue 5: Grid columns too narrow, forced wrapping
**Location**: `frontend/src/index.css` line 453-457, 600-605
**Current code**:
```css
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
/* Both will shrink columns on mobile, causing text overflow */
```

**Fix**:
```css
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile: single column */
  gap: 16px;
}

@media (min-width: 640px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}

@media (min-width: 1024px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

.basic-info-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile: single column */
  gap: 12px;
}

@media (min-width: 640px) {
  .basic-info-grid {
    grid-template-columns: repeat(2, 1fr);  /* Tablet: 2 columns */
  }
}

@media (min-width: 1024px) {
  .basic-info-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
```

### Issue 6: Header layout breaks on mobile
**Location**: `frontend/src/index.css` line 100-125
**Current code**:
```css
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0 20px;
}

.brand h1 {
  font-size: 24px;  /* Too large for mobile */
}
```

**Fix**:
```css
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0 20px;
  flex-wrap: wrap;  /* Allow wrapping on tiny screens */
}

.brand h1 {
  font-size: 18px;  /* Mobile */
  line-height: 1.3;
}

@media (min-width: 768px) {
  .brand h1 {
    font-size: 24px;  /* Desktop */
  }
}
```

### Issue 7: Game detail pane header needs mobile stacking
**Location**: `frontend/src/index.css` line 343-359
**Current code**:
```css
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.detail-header h2 {
  font-size: 32px;  /* Too large for mobile */
}
```

**Fix**:
```css
.detail-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

@media (min-width: 768px) {
  .detail-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
  }
}

.detail-header h2 {
  font-size: 24px;  /* Mobile */
  line-height: 1.3;
}

@media (min-width: 768px) {
  .detail-header h2 {
    font-size: 32px;  /* Desktop */
  }
}
```

### Issue 8: Search form needs mobile stacking
**Location**: `frontend/src/index.css` line 152-156
**Current code**:
```css
.search-form {
  display: flex;
  gap: 12px;
  max-width: 600px;
}
/* May wrap but button might not resize properly */
```

**Fix**:
```css
.search-form {
  display: flex;
  gap: 12px;
  max-width: 100%;
  flex-wrap: wrap;
}

.search-form .search-input {
  flex: 1 1 100%;  /* Full width on mobile */
  min-width: 0;    /* Allow flex to shrink below content size */
}

.search-form .btn-primary {
  flex: 1 1 auto;
  min-width: 80px;
}

@media (min-width: 640px) {
  .search-form .search-input {
    flex: 1 1 auto;
  }
}
```

### Issue 9: Video container responsive
**Location**: `frontend/src/pages/GamePage.jsx` line 231-240
**Current code**:
```jsx
<div style={{
  position: 'relative',
  paddingBottom: '56.25%',
  height: 0,
  overflow: 'hidden',
  borderRadius: '12px'
}}
```

**Status**: ✓ Already correct (aspect-ratio ratio via paddingBottom)
**Verify**: Check on mobile that video loads and plays

### Issue 10: Button sizing for touch targets
**Location**: Multiple (button classes)
**Current code**:
```css
.btn-primary {
  padding: 0 24px;
  border-radius: 12px;
  font-weight: 700;
}
```

**Missing**: height declaration
**Fix**:
```css
.btn-primary {
  min-height: 44px;  /* iOS HIG touch target */
  padding: 10px 24px;  /* Fallback if height not applied */
  border-radius: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.share-btn,
.btn-ghost {
  min-height: 44px;
}
```

### Issue 11: App container max-width prevents mobile centering
**Location**: `frontend/src/index.css` line 85-92
**Current code**:
```css
.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}
```

**Mobile issue**: On very small screens, 20px padding eats into space
**Fix**:
```css
.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px;  /* Mobile */
  width: 100%;
}

@media (min-width: 640px) {
  .app-container {
    padding: 20px;
  }
}
```

### Issue 12: Affiliate box wrapping on mobile
**Location**: `frontend/src/index.css` line 555-598
**Current code**:
```css
.affiliate-box {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.affiliate-link {
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
}
```

**Fix** (already responsive, but verify touch target):
```css
.affiliate-link {
  font-size: 0.85rem;
  padding: 10px 16px;  /* Ensure ≥44px height */
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

---

## Part 3: CSS Fixes - Complete Mobile-First Overhaul

### New Mobile Breakpoints Strategy
```css
/* Mobile First: Base styles for <640px */
/* Tablet: 640px - 1023px */
/* Desktop: 1024px+ */

:root {
  /* Responsive spacing scale */
  --spacing-mobile: 12px;
  --spacing-tablet: 16px;
  --spacing-desktop: 20px;
}

/* Mobile base */
body {
  font-size: 16px;
}

@media (min-width: 768px) {
  body {
    font-size: 14px;  /* Can afford smaller on larger screens */
  }
}
```

### Master CSS Patch for index.css
Apply these changes in order:

**1. Japanese font sizing (after line 18)**:
```css
/* Add explicit CJK font sizing */
body {
  font-size: 16px;  /* Base for readability */
}

@media (min-width: 768px) {
  body {
    font-size: 14px;
  }
}
```

**2. Container responsiveness (replace lines 85-97)**:
```css
.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px;  /* Mobile */
  display: flex;
  flex-direction: column;
  height: auto;
  width: 100%;
}

@media (min-width: 640px) {
  .app-container {
    padding: 20px;
  }
}

.app-container.standalone {
  height: auto;
  min-height: 100vh;
}

@media (min-width: 768px) {
  .app-container {
    height: 100vh;
  }
}
```

**3. Detail pane padding (replace lines 334-341)**:
```css
.game-detail-pane {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow-y: auto;
  padding: 16px;  /* Mobile */
  backdrop-filter: blur(10px);
}

@media (min-width: 768px) {
  .game-detail-pane {
    padding: 32px;
  }
}
```

**4. Header responsiveness (replace lines 343-359)**:
```css
.detail-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 16px;
}

@media (min-width: 768px) {
  .detail-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
    padding-bottom: 20px;
  }
}

.detail-header h2 {
  margin: 0;
  font-size: 24px;  /* Mobile */
  line-height: 1.3;
  background: linear-gradient(to right, #fff, #aaa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

@media (min-width: 768px) {
  .detail-header h2 {
    font-size: 32px;
  }
}
```

**5. Markdown content word-breaking (replace lines 499-513)**:
```css
.markdown-content {
  line-height: 1.8;
  color: var(--text-muted);
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: var(--text-main);
  margin-top: 24px;
  word-break: break-word;
}

.markdown-content strong {
  color: var(--text-main);
}

.markdown-content code {
  overflow-x: auto;
  display: inline-block;
  max-width: 100%;
  word-break: break-all;
}

.markdown-content pre {
  overflow-x: auto;
  white-space: pre-wrap;
}
```

**6. Keywords grid mobile-first (replace lines 429-433)**:
```css
.keywords-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile */
  gap: 12px;
}

@media (min-width: 640px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

@media (min-width: 1024px) {
  .keywords-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
```

**7. Cards grid mobile-first (replace lines 453-457)**:
```css
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile */
  gap: 16px;
}

@media (min-width: 640px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (min-width: 1024px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}
```

**8. Basic info grid mobile-first (replace lines 600-605)**:
```css
.basic-info-grid {
  display: grid;
  grid-template-columns: 1fr;  /* Mobile */
  gap: 12px;
}

@media (min-width: 640px) {
  .basic-info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .basic-info-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
```

**9. Button touch targets (replace/augment lines 176-198)**:
```css
.btn-primary {
  background: var(--accent);
  color: #000;
  border: none;
  padding: 10px 24px;
  min-height: 44px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.1s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 16px;
  min-height: 44px;
  border-radius: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

**10. Affiliate links touch targets (update lines 566-577)**:
```css
.affiliate-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  min-height: 44px;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: 600;
  color: white;
  transition: all 0.2s;
  font-size: 0.85rem;
}
```

---

## Part 4: DevTools Testing Checklist

### Chrome DevTools Mobile Inspection Workflow

**Step 1: Enable Device Toolbar**
```
F12 → Press Ctrl+Shift+M → Select iPhone 12 (390px)
```

**Step 2: Test Layout Integrity**
```
Checklist:
[ ] No horizontal scrolling (scroll bar at bottom)
[ ] .game-detail-pane content fits 100% width
[ ] Images scale to viewport (not fixed width)
[ ] Text doesn't get clipped
[ ] No off-screen elements (Inspector shows no red overflow)
```

**Step 3: Inspect Critical Elements**
```
// In DevTools Console, run:
const checks = {
  paneWidth: document.querySelector('.game-detail-pane').offsetWidth,
  windowWidth: window.innerWidth,
  overflows: document.querySelectorAll('*').filter(el =>
    el.scrollWidth > el.clientWidth
  ).length,
  images: document.querySelectorAll('img').map(img => ({
    src: img.src,
    width: img.offsetWidth,
    maxWidth: window.getComputedStyle(img).maxWidth,
  }))
};
console.table(checks);
```

**Step 4: Test Japanese Text Rendering**
```
[ ] No cut-off characters (compare with desktop)
[ ] Line height sufficient (1.6+)
[ ] Font loads (not system fallback)
[ ] Font size ≥ 15px for body text
```

Commands:
```javascript
// Check fonts loaded
document.fonts.ready.then(() => {
  console.log('All fonts loaded');
  document.querySelectorAll('*').forEach(el => {
    const font = window.getComputedStyle(el).fontFamily;
    if (font.includes('Zen')) console.log(el.textContent.substring(0, 20), font);
  });
});

// Check font sizes
document.querySelectorAll('[lang="ja"], .markdown-content, .game-summary').forEach(el => {
  console.log(el.textContent.substring(0, 20), window.getComputedStyle(el).fontSize);
});
```

**Step 5: Viewport Meta Tag Verification**
```javascript
const meta = document.querySelector('meta[name="viewport"]');
console.log(meta.getAttribute('content'));
// Expected: "width=device-width, initial-scale=1"
```

**Step 6: Responsive Image Test**
```
Network tab → Slow 3G throttling
[ ] Images load (no red 404 icons)
[ ] Aspect ratio maintained (no layout shift)
[ ] Load time < 2s per image
```

**Step 7: Touch Target Size Verification**
```javascript
document.querySelectorAll('button, a[class*="btn"], .share-btn').forEach(btn => {
  const rect = btn.getBoundingClientRect();
  const size = `${Math.round(rect.width)}x${Math.round(rect.height)}px`;
  const ok = rect.width >= 44 && rect.height >= 44 ? '✓' : '✗';
  console.log(`${ok} ${btn.textContent.substring(0, 20)} → ${size}`);
});
```

**Step 8: Scroll Performance Check**
```javascript
// Check for scroll jank
window.addEventListener('scroll', () => console.time('scroll'));

// On mobile iOS, enable smooth scrolling
document.querySelector('.game-detail-pane').style.webkitOverflowScrolling = 'touch';
```

---

## Part 5: Implementation Checklist

### Before Deploying
1. **Run Linting**:
   ```bash
   task lint:frontend
   ```
   Expected: No CSS warnings about fixed widths, no text overflow warnings

2. **Build & Preview**:
   ```bash
   task build
   task preview
   ```

3. **Mobile Testing Sequence**:
   - Open `http://localhost:4173` in Chrome DevTools mobile mode (390px)
   - Load a game with long Japanese rules
   - Scroll to bottom
   - Verify no text overflow, images scale, buttons are clickable

4. **Font Loading Verification**:
   - Open DevTools Network tab
   - Filter by font (type: font)
   - Verify `Zen Maru Gothic` loads (not 404)
   - Check load time < 1s

5. **Lighthouse Mobile Audit**:
   ```
   DevTools → Lighthouse → Mobile → Run audit
   Target scores:
   - Performance: > 80
   - Accessibility: > 90 (text contrast, button sizes)
   - Best Practices: > 90
   ```

6. **Cross-browser Testing**:
   - Safari iOS: Check text rendering, scroll smoothness
   - Chrome Android: Check image scaling, touch targets
   - Firefox mobile: Check layout stability

### Git Workflow
```bash
# Create feature branch
git checkout -b fix/mobile-responsiveness

# Make CSS changes to frontend/src/index.css

# Test locally
task dev

# Commit
git add frontend/src/index.css
git commit -m "fix: mobile responsiveness - padding, font sizing, grid layouts

- Reduce .game-detail-pane padding from 32px to 16px on mobile
- Increase Japanese base font size to 16px for readability
- Convert fixed-width grids to mobile-first (1fr → multi-col at 640px+)
- Add word-break rules to .markdown-content
- Ensure 44px minimum touch targets for buttons
- Stack detail-header flexbox on mobile
- Fix overflow-wrap for Japanese text"

# Push and create PR
git push -u origin fix/mobile-responsiveness
```

---

## Part 6: Common Mobile Issues Reference

### Text Overflow Prevention
```css
/* If text overflows horizontally */
selector {
  word-wrap: break-word;        /* Wrap long words */
  overflow-wrap: break-word;    /* Fallback */
  hyphens: auto;                /* Break at hyphens */
  word-break: break-word;       /* For CJK */
}
```

### Grid Responsiveness Pattern
```css
/* Mobile-first pattern */
.grid {
  display: grid;
  grid-template-columns: 1fr;   /* Mobile: 1 column */
  gap: 12px;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);  /* Tablet: 2 columns */
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));  /* Desktop */
  }
}
```

### Image Responsiveness
```css
img {
  max-width: 100%;     /* Never exceed viewport */
  height: auto;        /* Preserve aspect ratio */
  display: block;      /* Remove inline spacing */
}

.image-container {
  width: 100%;
  aspect-ratio: 16/9;  /* Maintain ratio */
}
```

### Japanese Text Optimization
```css
body {
  font-size: 16px;     /* Readable on mobile */
  line-height: 1.6;    /* Room to breathe */
  letter-spacing: 0.02em;  /* Subtle clarity */
}

/* CJK-specific */
:lang(ja) {
  line-height: 1.8;    /* Extra space for vertical density */
}
```

### Touch Target Sizing
```css
button, a, input {
  min-width: 44px;     /* iOS Human Interface Guidelines */
  min-height: 44px;
  padding: 10px 16px;  /* Minimum safe padding */
}
```

---

## Part 7: Performance Optimization for Mobile

### Viewport Meta Tag (in index.html)
Ensure present:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

### Image Optimization
```jsx
// In GamePage.jsx, ensure img has:
<img
  src={...}
  alt={...}
  loading="lazy"  // ← Prevents off-screen load blocking
  width="390"     // ← Optional: helps browser allocate space
  height="220"
/>
```

### CSS Optimization
```css
/* Avoid */
position: fixed;     /* Jank on mobile scroll */
transform: rotate(); /* Causes repaints */

/* Prefer */
position: relative;
will-change: contents;  /* Optimize composite layer */
```

### Font Optimization
```css
/* In index.css, already good */
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700&display=swap');

/* Could add: */
font-display: swap;  /* Show fallback while loading */
```

---

## Conclusion

**Systematic debugging approach**:
1. Identify mobile viewport size and test at 390px (iPhone 12)
2. Use Chrome DevTools Device Toolbar to simulate
3. Inspect computed styles for padding, overflow, font-size
4. Apply mobile-first CSS with responsive breakpoints
5. Test Japanese text rendering and touch targets
6. Verify no horizontal scroll, images scale, text readable

**High-impact fixes** (apply first):
- [ ] Reduce `.game-detail-pane` padding to 16px on mobile
- [ ] Increase base `body` font-size to 16px
- [ ] Convert fixed-width grids to `grid-template-columns: 1fr`
- [ ] Add `word-wrap: break-word` to `.markdown-content`
- [ ] Ensure all buttons have `min-height: 44px`

**Validation**:
- Run `task lint:frontend` and `task build`
- Test in Chrome mobile mode (390px), Safari iOS, Chrome Android
- Run Lighthouse audit, target >80 performance on mobile
- Verify Zen Maru Gothic font loads in Network tab

