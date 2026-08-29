# Mr Spelling Website — Claude Instructions

This folder contains the Mr Spelling GitHub Pages website (https://robsstuff.github.io/Mr-Spelling/).
Each spelling rule song gets a companion HTML page built and pushed here.

**This file was rewritten 2026-08-30** after a full-site redesign. It previously documented a
yellow/Bangers design that no longer exists anywhere on the live site — if you're reading a
cached/old copy of this file, throw it out and trust this one, or better, trust the live files
directly (`index.html`, any `lessons/*.html`).

---

## Design system (cream editorial — current, as of the 2026-08-30 redesign)

All colors are CSS custom properties in `assets/site.css` — use `var(--token)`, never a literal
hex, in any new page.

| Token | Value | Role |
|---|---|---|
| `--cream` | `#FDF8EE` | page background |
| `--ink` | `#1C1626` | text, borders, dark surfaces |
| `--ink-soft` / `--ink-faint` | `#564C63` / `#8A8096` | secondary/tertiary text — never literal gray |
| `--terracotta` / `-deep` | `#A32916` / `#7C1F0F` | primary action, links, word-group 1 (`.c1`) |
| `--teal` / `-deep` | `#0E9C88` / `#0B7C6C` | secondary/hover, word-group 2 (`.c2`) |
| `--violet` | `#6B46E5` | category/meta labels, word-group 3 (`.c3`) |
| `--marigold` / `-deep` | `#F2B705` / `#C99400` | rare whole-site highlight (hero sticker, logo) — not a word-group color |
| `--tint-sky/lavender/rose/mint` | pale tints | chip/card backgrounds |
| `--shadow-1/2/3` | `3/6/11px` hard ink-offset | the owned elevation signature — deliberate, not per-element habit |

Fonts: **Bricolage Grotesque** (display/headings) + **Figtree** (body). Load via the standard
Google Fonts `<link>` (see any current page's `<head>`) — never Bangers/Boogaloo/Bungee/Permanent
Marker/Nunito/Poppins, all retired.

Shared stylesheets (link both on every lesson page): `assets/site.css` (tokens, reset, icons,
`.beat` scroll-motion, browser-surface theming) + `assets/lesson.css` (page-header, cat-nav,
word-chip, rule-box, exceptions-box, lyrics-box, download-card, and every other lesson-page
component). See `DESIGN.md` for the full system reference and the `.pattern-card` rule-box
component.

**Never use an emoji or a unicode arrow glyph (`&rarr;`, `&darr;`, `&#8592;`) as a UI icon.** Use
the inline SVG icon set (back-arrow, download, play) — copy the pattern from any current page's
back-link/download-btn.

**No em-dashes anywhere** (`—` or `&mdash;`), in code or content. Use a colon, comma, or period
instead. The whole site was swept clean of these 2026-08-30 at the user's explicit request — a
new em-dash reintroduces the "AI writing" tell they specifically flagged.

**No kicker/eyebrow line stacked above a heading** (the old `.section-eyebrow` pattern). If a
section heading needs a short meta tag (like a curriculum cross-reference), put it inline beside
the heading in a `.section-heading-row` as a `.heading-tag` pill — see
`lessons/all-oll-ull.html`'s "UFLI Lesson 43" tag for the pattern. Most of the time there's no
unique info in the old eyebrow text at all — just delete it and let the heading stand alone.

---

## BEFORE BUILDING ANY NEW PAGE — mandatory first step

Read `lessons/bossy-r.html` in full (the current canonical template for a "rich" lesson page —
video, word groups, rule box, exceptions, lyrics) and `lessons/letter-b.html` (the canonical
template for a "sparse" lesson page — video, one description paragraph, PowerPoint link, lyrics).
Copy structure and class names from whichever matches the new page's content, then write only
the content into it. Do not invent new component classes without checking `DESIGN.md` first —
most rule shapes (formula chips, r-pair grids, numbered steps) already have a component.

---

## Inputs to collect before starting

| Input | Required | Example |
|-------|----------|---------|
| YouTube video URL | Yes | `https://www.youtube.com/watch?v=CJ83O4VWnME` |
| Rule name | Yes | "The FLOSS Rule" |
| Output filename | Yes (or derive) | `floss-rule.html` |
| Rule description | Yes | One plain-English paragraph |
| Word list(s) | If applicable | grouped by pattern, 2-3 groups typical |
| Rule formula/pattern | If applicable | e.g. "A + LL → 'aw' sound" |
| Exceptions | If applicable | word + one-sentence note each |
| Song lyrics | Yes (or "Lyrics coming soon." placeholder) | Raw text OR path to `.docx` |
| Spelling list PDF(s) | If applicable | via the existing DOCX → PDF workflow (see project memory) |

If lyrics are not provided directly, fetch from YouTube transcript:
```bash
pip install youtube-transcript-api
python -c "
from youtube_transcript_api import YouTubeTranscriptApi
t = YouTubeTranscriptApi.get_transcript('VIDEO_ID')
for seg in t: print(seg['text'])
"
```
Then clean: remove timestamp markers, de-duplicate repeated captions, fix obvious transcription
errors from context.

---

## NON-NEGOTIABLE RULES — never slip these

- **No emojis or unicode-glyph icons in HTML.** Use the SVG icon set. (Emoji inside a quiz page's
  JS `WORDS` array data, e.g. `emoji:"🐱"`, is fine — that's game content, not a UI icon.)
- **No em-dashes.** Colon, comma, or period instead.
- **Verbatim lyrics/content only.** No paraphrasing, no summarising, no added context — presentation
  changes, content doesn't.
- **Never placeholder or guess a URL.** If a PowerPoint Drive/Slides link is unavailable, use:
  `<!-- REPLACE: PowerPoint link -->`
- **Word-group colors are always c1 → terracotta, c2 → teal, c3 → violet, in that order.** Don't
  invent new group colors; marigold is reserved for the whole-site highlight role.
- **Interactive quiz pages** (`plural-rule-1.html`, `floss-rule.html`, `sound-of-vowels.html` are
  the current examples): keep the JS logic (`WORDS` array, `getWrongs`/scoring, DOM wiring)
  completely untouched when restyling — only recolor via the shared CSS tokens.

---

## Step-by-step build process

### Step 1 — Gather inputs
Ask the user for everything in the inputs table above.

### Step 2 — Derive filename
- Plural rules: `plural-rule-N.html` (root level, matching existing convention)
- Named rules: slugify and place under `lessons/` — "Bossy R" → `lessons/bossy-r.html`

### Step 3 — Write the HTML page
1. Copy `lessons/bossy-r.html` (rich) or `lessons/letter-b.html` (sparse) as the starting point
2. Link `../assets/site.css` and `../assets/lesson.css` (already correct if copied from a
   current page — do not inline a new `<style>` block for shared components)
3. Add any genuinely new rule-shape CSS to `assets/lesson.css` itself if it's reusable, or a
   small page-specific `<style>` block only for one-off content (e.g. a syllable-demo diagram)
4. Build sections in order: header → nav → video → words (if applicable) → rule → exceptions (if
   applicable) → lyrics → footer
5. Add `beat` / `beat-group` / `beat-child` classes to card-level elements and chip rows (see any
   current page) to pick up the scroll-motion grammar automatically

### Step 4 — Update `index.html`
Add a new `<a class="chip">` to the "Lessons" `.chip-row` group in the Spelling Rules section.

### Step 5 — Update `lessons/index.html` and `videos.html`
Both are card/list generators over the full catalogue — add the new entry following the existing
row pattern (see current file for the exact markup).

### Step 6 — Commit and push
```bash
git add lessons/<new-page>.html index.html lessons/index.html videos.html
git commit -m "Add [Rule Name] page"
git push
```

---

## Verification Checklist

Before marking a page done, confirm:

- [ ] Page loads — header, subtitle, sticky nav all visible, no console errors
- [ ] Video plays (correct YouTube video ID in embed URL)
- [ ] If a quiz: first word loads, correct answer advances, wrong answer shakes and stays
- [ ] Rule box displays correctly (formula chips / pattern cards in the right c1/c2/c3 colors)
- [ ] Lyrics display — chorus/verse/intro/outro styled, no colored `border-left` on verse blocks
- [ ] No em-dashes, no unicode-arrow icons, no stacked eyebrow-above-heading
- [ ] Back link returns to the right place (`../index.html` from `lessons/`, `index.html` from root)
- [ ] `index.html` and `lessons/index.html` and `videos.html` all show the new page
- [ ] Pushed to GitHub — live at `https://robsstuff.github.io/Mr-Spelling/`

---

## Key files reference

| File | Purpose |
|------|---------|
| `assets/site.css` | Design tokens, reset, icons, motion, browser-surface theming — link on every page |
| `assets/lesson.css` | Shared lesson-page components (header, nav, word-chip, rule-box, exceptions, lyrics, downloads) |
| `assets/site.js` | Scroll-reveal motion (`.beat` classes) — link before `</body>` on every page |
| `lessons/bossy-r.html` | Canonical "rich" lesson-page template (video/words/rule/exceptions/lyrics) |
| `lessons/letter-b.html` | Canonical "sparse" lesson-page template (video/description/powerpoint/lyrics) |
| `plural-rule-1.html` | Canonical interactive-quiz-page template |
| `DESIGN.md` | Full design-system reference, written from the built world |
| `PRODUCT.md` | Durable product context (users, purpose, constraints) |
| `index.html` | Homepage — add new chip to Spelling Rules group |
| `lessons/index.html`, `videos.html` | Full-catalogue listing pages — add new entries here too |

GitHub repo: https://github.com/Robsstuff/mr-spelling
Live site: https://robsstuff.github.io/Mr-Spelling/
