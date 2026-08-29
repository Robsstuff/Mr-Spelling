# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML + CSS (matches the live site — no framework, no build step). [Inferred: no build
step was requested; the incumbent site is plain HTML and this preserves that.]

## Users

Two audiences, in order of who acts:
- **Primary Stage 1–2 classroom teachers** (the byline's own framing: "Free for classroom use",
  "curriculum-aligned") who land on the homepage deciding whether to trust and use a song in
  their lesson, then click into one rule page to grab the video + printable word list.
- **Students (ages ~5–8)** who watch the embedded video and read the word/rule/lyrics content
  on the rule page itself, usually with the teacher driving.

## Product Purpose

Mr Spelling teaches English spelling rules (plurals, vowel digraphs, r-controlled vowels,
suffixes, etc.) through short rap/song videos, each paired with a rule page: the video, the
words it teaches, a plain-English rule explanation, common exceptions, and full lyrics — plus a
free printable spelling-list PDF. [Inferred from CLAUDE.md + site content: "free for classroom
use", curriculum-aligned framing.]

## Positioning

A named teacher-performer character ("Mr Spelling") who teaches spelling rules as memorable
rap/song hooks rather than worksheets-first — the mechanism a generic phonics worksheet site
can't copy is the song itself plus the rule page built specifically to accompany it.

## Operating Context

- Every rule gets its own page under `lessons/*.html` (or a few legacy root-level pages),
  linked from the homepage's rules index.
- Each rule page: YouTube embed, word groups as chips, a rule-formula explanation box,
  exceptions box, full lyrics, and one or more downloadable spelling-list PDFs.
- Site is deployed as static GitHub Pages (no server, no build step) — any redesign must stay
  deployable the same way.
- **115 lesson pages currently exist**, built across at least three visibly different design
  eras in the live code (oldest: yellow/Bangers quiz-game pages per the folder's own now-stale
  CLAUDE.md; middle: dark navy/Bungee "rap" pages, e.g. `all-oll-ull.html`; newest: cream
  editorial/Bricolage Grotesque pages, e.g. `index.html` and 20 restyled lessons like
  `bossy-r.html`). This redesign treats the newest (cream editorial) as the system to inherit
  and elevate, per the live homepage. [Established from reading the actual files, not from
  either stale CLAUDE.md or stale prior memory — both describe superseded design systems.]

## Capabilities and Constraints

- No login, no accounts, no ads, no analytics observed in current code.
- Google Fonts loaded via `<link>` (Bricolage Grotesque + Figtree currently).
- Ko-fi donation link and YouTube subscribe link in a persistent top banner + footer.
- [Undecided: whether the 95 non-restyled lesson pages should ever be migrated to match — out
  of scope for this pass, flagged as a follow-up.]

## Brand Commitments

- Name: "Mr Spelling — Not Misspelling." (wordplay is load-bearing, appears in hero + footer).
- Existing photography: `assets/mrspelling-point.jpg`, `mrspelling-cheer.jpg`,
  `mrspelling-shaka.jpg` — real photos of the teacher character, used with `mix-blend-mode:
  multiply` against colour grounds. Treated as durable brand assets, not replaceable stock.
- Tagline energy: hip-hop MC framing ("dropping spelling knowledge with the energy of a
  hip-hop MC... turns tricky words into unforgettable bars") — confirmed in current About copy.

## Evidence on Hand

Real photography of the teacher character (3 images, see above). Real YouTube video IDs and
real lyrics/word lists per lesson (verbatim in current HTML — must be preserved verbatim, not
paraphrased, per explicit user instruction). No customer testimonials, pricing, or usage stats
beyond the homepage's own self-reported "20 spelling-rule songs" counter — do not invent new
claims of this kind.

## Product Principles

1. The song/video is the product; the page's job is to make it trustworthy to a scanning
   teacher in seconds and useful to a child reading along.
2. Every rule page is a teaching artifact, not a marketing page — clarity and legibility of the
   rule, exceptions, and lyrics outrank decoration.
3. Content is sacred: words, lyrics, rule text, and links carry over verbatim. Only presentation
   changes in this pass.
4. The site must stay a zero-build static deploy — no framework migration.

## Accessibility & Inclusion

Read aloud/along by young children — body text needs strong contrast and a generous size floor;
this was not fully true in the incumbent code (see redesign notes) and is fixed in this pass.
