# DevTools Testing Protocol for Mobile Responsiveness
## Rule-Scribe-Games Frontend GamePage Verification

---

## Quick Start: 5-Minute Mobile Audit

### 1. Open DevTools (Macintosh → Cmd+Shift+I | Windows → F12)

### 2. Activate Mobile Viewport
- Click **Device Toolbar** icon (top-left, next to "Elements" tab)
  - Shortcut: `Ctrl+Shift+M` (Windows) / `Cmd+Shift+M` (Mac)
- Select **iPhone 12 Pro** (390×844) from dropdown

### 3. Reload Page
- `Cmd+R` (Mac) / `F5` (Windows)
- **Wait** for fonts to load (watch Network tab)

### 4. Run Quick Tests
```javascript
// Paste into DevTools Console (Cmd+Option+J / F12 → Console)

// Test 1: Detect horizontal overflow
const hasOverflow = document.documentElement.scrollWidth > window.innerWidth;
console.log(hasOverflow ? '❌ OVERFLOW DETECTED' : '✓ No horizontal overflow');

// Test 2: Check hero image dimensions
const hero = document.querySelector('.game-hero-image');
console.log('Hero image:', {
  width: hero.offsetWidth,
  height: hero.offsetHeight,
  aspectRatio: (hero.offsetHeight / hero.offsetWidth).toFixed(2),
});

// Test 3: Verify font rendering
const content = document.querySelector('.markdown-content');
const style = getComputedStyle(content);
console.log('Content text:', {
  font: style.fontFamily,
  size: style.fontSize,
  lineHeight: style.lineHeight,
});
```

### 5. Take Screenshots
- Before fixes (for documentation)
- After fixes (for comparison)

---

## Comprehensive Testing Checklist

### Viewport Setup

**Target Devices** (test all three):
1. **Mobile (390×844)**: iPhone 12 Pro
2. **Small Mobile (375×667)**: iPhone SE
3. **Tablet (768×1024)**: iPad

### Section 1: Text Rendering

#### Test 1.1: Rules Text (`.markdown-content`)
```
Criteria:
☐ No horizontal scrollbar visible
☐ Text reads clearly without zooming
☐ Japanese characters (kanji, hiragana) are crisp
☐ Line breaks occur at word boundaries, not mid-character
☐ Font appears to be Zen Maru Gothic (thicker than serif default)
```

**DevTools Check**:
```javascript
const rules = document.querySelector('.markdown-content');
const computed = getComputedStyle(rules);
console.log({
  fontSize: computed.fontSize,
  fontFamily: computed.fontFamily,
  lineHeight: computed.lineHeight,
  overflowX: computed.overflowX,
  wordBreak: computed.wordBreak,
  width: rules.offsetWidth,
  scrollWidth: rules.scrollWidth,
  overflowing: rules.scrollWidth > rules.offsetWidth,
});
```

#### Test 1.2: Title Text (`h1.game-title`)
```
Criteria:
☐ Title fits within viewport (no overflow to the right)
☐ Font size readable (≥ 18px on mobile)
☐ No character clipping at edges
☐ Line-height adequate (not cramped)
```

**DevTools Check**:
```javascript
const title = document.querySelector('h1.game-title');
const rect = title.getBoundingClientRect();
console.log({
  title: title.textContent.substring(0, 30),
  left: Math.round(rect.left),
  right: Math.round(rect.right),
  viewportWidth: window.innerWidth,
  fits: rect.right <= window.innerWidth,
  fontSize: getComputedStyle(title).fontSize,
});
```

#### Test 1.3: Summary Text (`.summary-text`)
```
Criteria:
☐ 3-line summary displays fully
☐ Japanese text is readable (font ≥ 14px)
☐ Adequate spacing between lines
☐ No visual clipping
```

### Section 2: Image Rendering

#### Test 2.1: Hero Image Scaling
```
Criteria:
☐ Image fills width of viewport (100% width)
☐ Aspect ratio is portrait-friendly (4:3 on mobile, not 16:9)
☐ No distortion or stretching
☐ Border radius consistent
```

**DevTools Check**:
```javascript
const hero = document.querySelector('.game-hero-image');
const img = hero?.querySelector('img');
console.log({
  containerWidth: hero.offsetWidth,
  containerHeight: hero.offsetHeight,
  imgWidth: img?.offsetWidth,
  imgHeight: img?.offsetHeight,
  aspectRatio: (hero.offsetHeight / hero.offsetWidth).toFixed(2),
  objectFit: getComputedStyle(img).objectFit,
});
```

#### Test 2.2: Game Card Images (`.game-card`)
```
Criteria:
☐ Card background image displays (or at least card is visible)
☐ Opacity/blur effect applied so text is readable
☐ No layout shift when image loads
```

### Section 3: Button & Action Accessibility

#### Test 3.1: Header Actions Button Layout
```
Criteria:
☐ 5 buttons (Text-to-Speech, Twitter, Share, Edit, Regenerate) arranged in grid
☐ No overlap or truncation
☐ Each button ≥ 44px tall (touch target size)
☐ Spacing consistent (8px gaps)
☐ Labels visible or icons clear
```

**DevTools Check**:
```javascript
const actions = document.querySelectorAll('.header-actions button, .header-actions a');
console.log('Action buttons:', actions.length);
actions.forEach((btn, i) => {
  const rect = btn.getBoundingClientRect();
  console.log(i, {
    text: btn.textContent.substring(0, 20),
    width: Math.round(rect.width),
    height: Math.round(rect.height),
    minTouchTarget: rect.width >= 44 && rect.height >= 44,
  });
});
```

#### Test 3.2: External Links Grid
```
Criteria:
☐ Links (Amazon, Rakuten, Yahoo, etc.) arranged in 2-column grid on mobile
☐ Each link ≥ 44px tall
☐ Text doesn't overflow
☐ Hover/tap state visually distinct
```

### Section 4: Layout & Spacing

#### Test 4.1: Container Padding
```
Criteria:
☐ Game detail pane padding ≤ 16px on mobile (not 32px)
☐ Available content width = viewport - 32px padding = ~358px (for 390px mobile)
☐ No unnecessary empty space on sides
```

**DevTools Check**:
```javascript
const pane = document.querySelector('.game-detail-pane');
const computed = getComputedStyle(pane);
const rect = pane.getBoundingClientRect();
console.log({
  padding: computed.padding,
  width: rect.width,
  availableWidth: rect.width - parseFloat(computed.paddingLeft) - parseFloat(computed.paddingRight),
  exceeds100Percent: rect.right > window.innerWidth || rect.left < 0,
});
```

#### Test 4.2: Margins & Spacing
```
Criteria:
☐ Sections have adequate separation (≥ 16px margin between sections)
☐ No collapsed margins (margin collapse should not hide content)
☐ Consistent spacing throughout page
```

### Section 5: Grids & Complex Layouts

#### Test 5.1: Keywords Grid
```
Criteria:
☐ Keywords displayed in single column on mobile
☐ Each item ≥ 44px tall
☐ Text doesn't overflow keyword box
☐ Consistent styling across items
```

#### Test 5.2: Basic Info Grid (Players, Time, Age, Year)
```
Criteria:
☐ Single column layout on mobile
☐ Label on left, value on right (or stacked)
☐ Values readable without zoom
☐ Proper alignment
```

### Section 6: Typography Details

#### Test 6.1: Font Stack Verification
```javascript
// Check which font is actually rendering
const elements = {
  title: document.querySelector('h1.game-title'),
  content: document.querySelector('.markdown-content'),
  summary: document.querySelector('.summary-text'),
};

Object.entries(elements).forEach(([name, el]) => {
  const computed = getComputedStyle(el);
  console.log(`${name}:`, {
    font: computed.fontFamily,
    size: computed.fontSize,
    weight: computed.fontWeight,
    lineHeight: computed.lineHeight,
  });
});

// Verify fonts loaded
document.fonts.ready.then(() => {
  const loaded = Array.from(document.fonts)
    .map(f => f.family)
    .filter((f, i, a) => a.indexOf(f) === i);
  console.log('Loaded fonts:', loaded);
});
```

**Expected Output**:
```
title: {
  font: "Zen Maru Gothic, sans-serif",  // NOT Space Grotesk
  size: "20px",
  weight: "700",
  lineHeight: "28px",
}

content: {
  font: "Zen Maru Gothic, sans-serif",
  size: "15px",
  weight: "400",
  lineHeight: "27px",  // 1.8 × 15px
}

Loaded fonts: ["Space Grotesk", "Zen Maru Gothic"]
```

#### Test 6.2: Japanese Character Rendering
```javascript
// Check for common CJK rendering issues
const japaneseText = document.querySelector('.markdown-content');
const style = getComputedStyle(japaneseText);

const issues = [];
if (parseInt(style.fontSize) < 14) issues.push('Font too small for CJK');
if (parseFloat(style.lineHeight) < 1.6) issues.push('Line-height too tight');
if (!style.fontFamily.includes('Zen Maru') && !style.fontFamily.includes('Maru')) {
  issues.push('Not using CJK-optimized font');
}

console.log(issues.length ? '❌ Issues: ' + issues.join('; ') : '✓ Font rendering optimal');
```

### Section 7: Scrolling & Overflow

#### Test 7.1: Horizontal Scroll Test
```
Method 1 (Visual):
- Open DevTools
- View page on 390px viewport
- Scroll horizontally (swipe left/right)
- ❌ FAIL if horizontal scrollbar appears
- ✓ PASS if no horizontal scrolling possible

Method 2 (Console):
```javascript
console.log('Has horizontal scrollbar:', document.documentElement.scrollWidth > window.innerWidth);
console.log('Viewport width:', window.innerWidth);
console.log('Document width:', document.documentElement.scrollWidth);
```
"

#### Test 7.2: Detect All Overflow Elements
```javascript
// Comprehensive overflow detection
const overflowing = [];
document.querySelectorAll('*').forEach(el => {
  const style = getComputedStyle(el);
  if (style.display === 'none') return;

  if (el.scrollWidth > el.clientWidth) {
    overflowing.push({
      tag: el.tagName,
      class: el.className,
      content: el.textContent?.substring(0, 40),
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
      overflowX: style.overflowX,
    });
  }
});

console.table(overflowing);
if (overflowing.length === 0) {
  console.log('✓ No horizontal overflow detected!');
} else {
  console.log(`⚠ Found ${overflowing.length} overflowing elements`);
}
```

### Section 8: Responsive Breakpoints

#### Test 8.1: iPad Tablet Layout (768×1024)
```
Steps:
1. DevTools → Device Toolbar
2. Select "iPad" (768×1024)
3. Reload
4. Verify layout switches from mobile to tablet style
   ☐ Game list pane appears on left
   ☐ Detail pane on right
   ☐ No longer single-column
   ☐ Padding increases appropriately
```

#### Test 8.2: Desktop Layout (1024×768+)
```
Steps:
1. DevTools → Disable Device Toolbar (or select Desktop)
2. Reload
3. Verify desktop layout
   ☐ Wide two-column layout
   ☐ Proper padding (32px)
   ☐ Large images (16:9 aspect ratio)
   ☐ Multi-column grids
```

### Section 9: Performance & Load Time

#### Test 9.1: Font Loading
```
Steps:
1. DevTools → Network tab
2. Reload page
3. Filter: "fonts"
4. Verify:
   ☐ googleapis.com fonts load (Status 200)
   ☐ Fonts download in < 1 second
   ☐ Text not invisible while loading (FOUT acceptable, FOUC bad)
```

#### Test 9.2: Layout Shift
```javascript
// Detect Cumulative Layout Shift (CLS)
let cls = 0;
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      cls += entry.value;
      console.log('Layout shift:', entry.value, 'Total CLS:', cls.toFixed(3));
    }
  }
}).observe({ type: 'layout-shift', buffered: true });
```

**Good CLS**: < 0.1 (ideally < 0.05)

### Section 10: Touch Interaction

#### Test 10.1: Button Click Areas
```
Steps:
1. DevTools → Sensors → Emulate touch events
2. Tap each button:
   ☐ Highlighted/activated on tap
   ☐ No accidental activation of adjacent buttons
   ☐ Feedback is immediate
```

#### Test 10.2: Modal Dialogs
```
Steps:
1. Click "編集" (Edit) button
2. Modal should appear:
   ☐ Fills viewport (with padding)
   ☐ Close button accessible
   ☐ Scrollable if content exceeds viewport
   ☐ Form inputs ≥ 44px tall
```

---

## Automated Testing Scripts

### Script 1: Comprehensive Mobile Audit
```javascript
// Copy entire script into DevTools Console and run
(function mobileAudit() {
  console.group('📱 MOBILE RESPONSIVENESS AUDIT');

  const viewport = {
    width: window.innerWidth,
    height: window.innerHeight,
  };
  console.log('Viewport:', `${viewport.width}×${viewport.height}`);

  // 1. Overflow Detection
  const overflows = Array.from(document.querySelectorAll('*')).filter(el => {
    return el.scrollWidth > el.clientWidth && getComputedStyle(el).display !== 'none';
  });
  console.log(overflows.length === 0 ? '✓ No overflow' : `⚠ ${overflows.length} overflows`);

  // 2. Font Rendering
  const content = document.querySelector('.markdown-content');
  if (content) {
    const style = getComputedStyle(content);
    console.log('Content font:', {
      family: style.fontFamily,
      size: style.fontSize,
      lineHeight: style.lineHeight,
    });
  }

  // 3. Image Dimensions
  const hero = document.querySelector('.game-hero-image');
  if (hero) {
    console.log('Hero image:', {
      width: hero.offsetWidth,
      height: hero.offsetHeight,
      aspect: (hero.offsetHeight / hero.offsetWidth).toFixed(2),
    });
  }

  // 4. Button Accessibility
  const buttons = document.querySelectorAll('button, [role="button"], a.btn');
  const smallButtons = Array.from(buttons).filter(btn => {
    const rect = btn.getBoundingClientRect();
    return rect.width < 44 || rect.height < 44;
  });
  console.log(smallButtons.length === 0 ? '✓ Buttons ≥ 44px' : `⚠ ${smallButtons.length} buttons < 44px`);

  // 5. Spacing
  const pane = document.querySelector('.game-detail-pane');
  if (pane) {
    const style = getComputedStyle(pane);
    console.log('Container padding:', style.padding);
  }

  console.groupEnd();
})();
```

### Script 2: Text Overflow Detail Report
```javascript
// Detailed text overflow analysis
(function textOverflowReport() {
  console.group('📄 TEXT OVERFLOW ANALYSIS');

  const textContainers = [
    { selector: '.game-title', name: 'Title' },
    { selector: '.markdown-content', name: 'Rules' },
    { selector: '.summary-text', name: 'Summary' },
    { selector: '.rule-text', name: 'Rule text' },
  ];

  textContainers.forEach(({ selector, name }) => {
    const el = document.querySelector(selector);
    if (!el) return;

    const style = getComputedStyle(el);
    const overflowing = el.scrollWidth > el.offsetWidth;

    console.log(`${name}: ${overflowing ? '❌ OVERFLOWING' : '✓ OK'}`, {
      width: el.offsetWidth,
      scrollWidth: el.scrollWidth,
      fontSize: style.fontSize,
      wordBreak: style.wordBreak,
      overflowWrap: style.overflowWrap,
    });
  });

  console.groupEnd();
})();
```

### Script 3: Japanese Font Verification
```javascript
// Verify Japanese font stack is applied
(function verifyJapaneseFont() {
  console.group('🇯🇵 JAPANESE FONT VERIFICATION');

  const elements = [
    { selector: 'h1.game-title', name: 'Title' },
    { selector: '.markdown-content', name: 'Content' },
    { selector: '.summary-text', name: 'Summary' },
    { selector: 'p', name: 'Paragraph' },
  ];

  const zenMaruRegex = /Zen Maru|Maru Gothic|maru/i;
  const issues = [];

  elements.forEach(({ selector, name }) => {
    const el = document.querySelector(selector);
    if (!el) return;

    const font = getComputedStyle(el).fontFamily;
    const isJapaneseFont = zenMaruRegex.test(font);

    console.log(`${name}:`, {
      font,
      isCorrect: isJapaneseFont ? '✓' : '❌',
    });

    if (!isJapaneseFont && window.innerWidth < 768) {
      issues.push(`${name} not using Japanese font on mobile`);
    }
  });

  if (issues.length > 0) {
    console.warn('Issues found:', issues);
  } else {
    console.log('✓ All elements using correct Japanese font');
  }

  console.groupEnd();
})();
```

---

## Issue Identification & Remediation

### Issue: Horizontal Scrollbar Visible

**Diagnosis**:
```javascript
document.documentElement.scrollWidth > window.innerWidth
// if true → overflow exists
```

**Common Causes**:
1. Element with `width: 100% + padding` → use `box-sizing: border-box`
2. Image or hero container too wide → check max-width
3. Overflow-x: auto on parent → check which child is culprit

**Fix**:
```javascript
// Find the culprit
Array.from(document.querySelectorAll('*')).forEach(el => {
  if (el.scrollWidth > el.clientWidth) {
    console.log('Overflow element:', el.tagName, el.className);
    console.log('Width:', el.clientWidth, 'ScrollWidth:', el.scrollWidth);
  }
});
```

### Issue: Japanese Text Blurry/Illegible

**Diagnosis**:
```javascript
const text = document.querySelector('.markdown-content');
const style = getComputedStyle(text);
[style.fontSize, style.fontFamily, style.lineHeight, style.fontWeight];
// Check: fontSize ≥ 14px, fontFamily includes "Zen Maru", lineHeight ≥ 1.6
```

**Common Causes**:
1. Font-size < 14px → increase size
2. Font-family is English (Space Grotesk) → switch to Zen Maru Gothic
3. Font-weight too light (300-400) → increase to 500+
4. Line-height < 1.6 → increase to 1.8

**Fix**:
```css
.markdown-content {
  font-family: 'Zen Maru Gothic', sans-serif;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.8;
}
```

### Issue: Buttons Overlap or Truncate

**Diagnosis**:
```javascript
document.querySelectorAll('.header-actions button').forEach((btn, i) => {
  const rect = btn.getBoundingClientRect();
  console.log(`Button ${i}:`, {
    width: rect.width,
    height: rect.height,
    text: btn.textContent,
    tooSmall: rect.width < 44 || rect.height < 44,
  });
});
```

**Common Causes**:
1. Buttons in single row on narrow viewport
2. Font-size too small → text truncates
3. Padding removed → touch target too small

**Fix**:
```css
@media (max-width: 640px) {
  .header-actions {
    flex-wrap: wrap;
  }

  .header-actions button {
    flex: 1 1 calc(50% - 4px);
    min-height: 44px;
    font-size: 12px;
  }
}
```

---

## Before/After Comparison Checklist

### BEFORE (Issues Present)

- [ ] Horizontal scrollbar visible
- [ ] Title font appears thin/English (Space Grotesk)
- [ ] Rules text overflows container
- [ ] Hero image aspect ratio wrong (16:9 instead of 4:3)
- [ ] Header buttons wrap awkwardly
- [ ] Padding (32px) wastes space on 390px screen
- [ ] Japanese text appears blurry (small font, wrong font-family)
- [ ] Some text appears cut off

### AFTER (Fixes Applied)

- [ ] No horizontal scrollbar
- [ ] Title uses Zen Maru Gothic (thicker, more legible)
- [ ] Rules text wraps at word boundaries
- [ ] Hero image fills width, 4:3 aspect on mobile
- [ ] Buttons arranged in 2-column grid, all ≥ 44px
- [ ] Padding reduced to 16px on mobile
- [ ] Japanese text crisp and readable
- [ ] All text visible, no clipping

---

## Performance Metrics

After applying fixes, verify these metrics:

| Metric | Target | Method |
|--------|--------|--------|
| **FCP** (First Contentful Paint) | < 1.8s | Lighthouse / Performance tab |
| **LCP** (Largest Contentful Paint) | < 2.5s | Lighthouse / Performance tab |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Performance Observer API |
| **Font Load Time** | < 1s | Network tab (fonts) |
| **Button Touch Target** | ≥ 44×44px | Manual inspection |
| **Text Legibility** | No zoom needed | Visual check |

---

## Reference DevTools Keyboard Shortcuts

| Action | Windows | Mac |
|--------|---------|-----|
| Open DevTools | F12 | Cmd+Opt+I |
| Console | Ctrl+Shift+J | Cmd+Opt+J |
| Elements | Ctrl+Shift+C | Cmd+Shift+C |
| Device Toolbar | Ctrl+Shift+M | Cmd+Shift+M |
| Device Rotation | Ctrl+Shift+R | Cmd+Shift+R |
| Zoom (DevTools) | Ctrl+Plus/Minus | Cmd+Plus/Minus |
| Clear Cache | Ctrl+Shift+Delete | Cmd+Shift+Delete |

---

## Final Verification Workflow

1. **Setup**: Open DevTools, enable Device Toolbar, select iPhone 12 Pro (390×844)
2. **Reload**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R) to bypass cache
3. **Visual Check**: Scroll page, check for issues from Checklist (Section 10)
4. **Console Tests**: Run 3-4 scripts from "Automated Testing Scripts"
5. **Document**: Take screenshots before/after
6. **Compare**: Verify all "AFTER" criteria are met
7. **Deploy**: Run `task lint` → fix any warnings → commit CSS changes

