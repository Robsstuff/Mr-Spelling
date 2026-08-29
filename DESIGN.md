# Design — Mr Spelling (elevated cream-editorial system)

<!-- impeccable:design-doc -->

Written from the built world (`index.html`, `lessons/bossy-r.html`, `lessons/all-oll-ull.html`,
`assets/site.css`, `assets/lesson.css`). This is the system to reuse when rolling the redesign
out to the rest of the 115 lesson pages.

## Lineage

Inherited, not replaced: the live site's own newest direction (homepage + 20 lesson pages
restyled Aug 22, cream/Bricolage Grotesque) was the established world. This pass elevated that
world's execution — real type/shadow/motion system, drawn icons, fixed contrast and legibility
defects — rather than introducing a new aesthetic. Two older, now-superseded eras still exist in
the live repo's other ~95 lesson pages (dark navy/Bungee "rap" era; yellow/Bangers "quiz-game"
era per the folder's own stale `CLAUDE.md`) — out of scope for this pass.

## Tokens (`assets/site.css :root`)

| Role | Token | Value |
|---|---|---|
| Ground | `--cream` | `#FDF8EE` |
| Ground (alt) | `--cream-deep` | `#F6EDD9` |
| Ink | `--ink` / `--ink-soft` / `--ink-faint` | `#1C1626` / `#564C63` / `#8A8096` |
| Primary action | `--terracotta` / `-deep` | `#A32916` / `#7C1F0F` (deepened from the incumbent `#C23B27` for AA contrast on every pale tint) |
| Secondary / hover | `--teal` / `-deep` | `#0E9C88` / `#0B7C6C` |
| Category / meta | `--violet` | `#6B46E5` |
| Highlight (rare) | `--marigold` / `-deep` | `#F2B705` / `#C99400` |
| Pale tints | `--tint-sky/lavender/rose/mint` | chip and card grounds — never raw white |
| Elevation | `--shadow-1/2/3` | `3/6/11px` hard ink-offset — the owned signature, not a per-element habit |

Fonts: Bricolage Grotesque (display, inherited) / Figtree (body, inherited).

## Word-group color convention (every lesson page)

Three named roles, consistent across the whole catalogue so it reads as one system once rolled
out: **c1 = terracotta**, **c2 = teal**, **c3 = violet**. Marigold is held back as the rarer
whole-site highlight (hero sticker, logo mark) — never used for word groups.

## Components introduced this pass

- **`.pattern-card` / `.pattern-grid`** — replaces the old page-specific "formula chip" and
  "r-pair" one-offs with a single reusable rule-explanation component (letters, sound, examples)
  in the c1/c2/c3 palette. Use this for every lesson page's rule box.
- **Icon set** — inline stroke SVGs (arrow, download, play, mug) replacing unicode glyphs
  (`&rarr;`, `&darr;`) and emoji. Keep the stroke weight (2.3) and viewBox (24) consistent when
  adding more.
- **`.beat` / `.beat-group` / `.beat-child`** (`assets/site.js`) — the one authored motion
  grammar: elements "beat in" on scroll, word-chip groups stagger like a drum pattern. Fully
  visible with no JS and under `prefers-reduced-motion`.
- **Heading pattern** — no kicker/eyebrow line stacked above an `<h2>` (removed six redundant
  ones from the incumbent lesson-page code, e.g. "SPELLING WORDS" above "Words in This Song").
  Meta info that carries real signal (a curriculum cross-reference like "UFLI Lesson 43") rides
  as a `.heading-tag` pill inline beside the heading instead.

## Known, reviewed detector findings (not fixed — judgment calls, not defects)

- **`cream-palette`** (all 3 files): the detector flags cream/beige as a generic AI default. Here
  it's the inherited, already-shipped brand ground, not a fresh reach-for-safety choice —
  keeping it is the correct call per "established world: inherit it," not a miss.
- **`em-dash-overuse`** (`bossy-r.html`): all 24 are in the site owner's original verbatim
  lyrics/copy, preserved exactly per the explicit "same content" instruction — not AI-generated
  prose introduced by this pass, so not something this pass should rewrite.
- **`cramped-padding`** on `.hero`: a static per-element check that flags the outer `<section>`
  for having no padding of its own, without resolving that its inner `.hero-inner` wrapper
  carries a generous 56px inset — the standard section→padded-wrapper pattern. Screenshot-
  verified: nothing is actually flush against the border.
- **`flat-type-hierarchy`**: reduced from 11 distinct sizes to 8 in this pass; fully satisfying a
  strict 1.25-ratio-between-every-step rule would need a much more invasive rewrite across many
  small UI-text roles (nav, chips, stat strip) for a "warning"-level finding — judged not worth
  the risk of new regressions this round. Worth another pass if the rollout script makes it cheap
  to apply site-wide.

## Rollout to the remaining ~113 lesson pages

Every lesson page in `lessons/*.html` shares one structure (video → words → rule → exceptions →
lyrics) per the folder's content, just with different words/rule text/lyrics. The two pages built
this pass (`bossy-r.html`, `all-oll-ull.html`) are the reference template — the repo already has
precedent for scripted page generation (`build_video_pages.py`), so the fastest safe rollout is a
script that reads each page's existing content (words, rule pattern, exceptions, lyrics — already
structured, consistent HTML) and re-emits it into this template, rather than hand-editing 113
files. Not run in this pass — do this only after the direction is approved.
