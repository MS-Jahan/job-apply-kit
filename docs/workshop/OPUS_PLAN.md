# OPUS_PLAN: workshop deck and guide redesign (beginner-friendly and cross-platform)

Status: plan only. Nothing else in the repo was changed. An implementer can follow it from top to bottom.
Inputs read: `docs/workshop/{PLAN,GUIDE,SLIDES_SPEC,SECURITY_REVIEW,example-config}.md`,
`docs/workshop/slides/index.html`, `docs/workshop/opencode/{REVIEW,DECISIONS}.md`, `README.md`,
`docs/BOOTSTRAP.md`, `docs/help/{00-config,01-prerequisites,02-google-setup,03-browser-setup,08-compatibility}.md`,
`docs/EXTERNAL_TOOLS.md` (§§2–5), `skills/job-apply-core/OPERATIONS.md` §0,
`skills/job-apply-core/scripts/{jak_config.py,browser_setup.py}`, `browser-debug-*.bat`, `.gitignore`.
Evidence screenshots (local only): `/tmp/claude-1000/deck-{1280,1920}-{5,11,20}.png`, `/tmp/claude-1000/deck-390-{5,11}.png`.

Hard constraints (apply to every task):
- The deck stays ONE file, `docs/workshop/slides/index.html`, with inline CSS and JS. No CDN, no web fonts, no `src`/`href` pointing at http(s), no `fetch`.
- No personal data. Use `<you>`, `<repo-url>`, `you@gmail.com` and `+880...` placeholders only.
- Every platform-specific claim must cite a repo file. Anything not found in the repo is marked **(verify)**.
- Keep 30 slides, the "Slide N of 30" counter, the section tracker, speaker notes (`N`), overview (`O`), help (`?`), hash deep links and swipe.

---

## A. Diagnosis: what is wrong now

Measured with Playwright on `index.html#N`, waiting 450 ms after each load. "Empty" = (slide bottom − bottom of the last visible child) / slide height.

| Viewport / scheme | #1 | #5 | #11 | #14 | #20 | #26 | #28 |
|---|---|---|---|---|---|---|---|
| 1280×720 light: empty bottom | 46% | 35% | 36% | 51% | 29% | 52% | 33% |
| 1920×1080 dark: empty bottom | 46% | 35% | 36% | 51% | 29% | 52% | 33% |

| # | Area | Problem | Evidence (selector / line in `slides/index.html`) |
|---|---|---|---|
| A1 | Layout math | Content is top-aligned. `.slide{display:block}` (l.35–37) has no vertical distribution, so 29–52% of every card sits empty below the content. | Table above; screenshots `deck-1280-11.png` and `deck-1920-5.png`. |
| A2 | Layout math | The stage is a fixed 1280×672 box (l.34), which is **not 16:9** (1.905). JS scales it by `min(w/1320, h/800)` (l.442). The magic 1320/800 ignores the real chrome height (44 px + 64 px, l.33). Result: the card uses 90% of the width at 1280×720 (1152 px), and type does not grow with the free space. | `scale(0.9)` at 1280×720, `scale(1.35)` at 1920×1080 |
| A3 | Typography | Body type is 28 px in a 1280 stage, so about 25 px on screen at 1280×720. Five short bullets therefore fill only half the card. Titles are 44 px and wrap to two lines on most slides (#5, #11, #20), which breaks the one-line action-title rule in `SLIDES_SPEC.md` l.63. | screenshots |
| A4 | Typography | Buttons don't inherit the font. `#bar button` (l.70) renders in Arial while the rest of the deck uses system-ui. | "Prev"/"Next" glyphs in `deck-1280-11.png` |
| A5 | Colour / contrast | Contrast technically passes AA (light muted `#4d6172` on white = 6.4:1), but the light page bg `#f4f6f8` against the white card `#fff` gives almost no figure/ground. Regular weight in `.small` (22 px, muted) and muted code pills on `#eef2f5` make the deck look washed out. Light mode turns on automatically through `prefers-color-scheme` (l.13), so presenters on light-mode laptops get the pale theme without choosing it. | `deck-1280-20.png` |
| A6 | Vertical rhythm | Margins are ad hoc: `.35rem` li, `.8rem` table, `.7rem` pre, `.9rem` h2. There's no spacing scale, and the gap between title and content is larger than the gap between content and footer. | l.39–63 |
| A7 | Information design | Almost every slide is "title + bullets", and the same visual weight is used for everything. Counts and outcomes are written as text, not shown as numbers or cards: #11 lists 13 steps as plain text, and #26 shows 61→4 as a lone 56 px number. Tables are small (22 px) and leave about half the card blank. | #5, #11, #26 |
| A8 | SVG bugs | Diagram rects contain a malformed attribute, `fill="none""` (double quote), on l.161–166, 210–212 and 359–361. Boxes are outlines only and every node has the same weight, so the "You" step is not emphasized. Diagrams are fixed at 230 px height (l.65). | l.161 etc. |
| A9 | Cross-platform | Only Linux paths and commands appear: `~/.config/...` (#20), `./doctor.sh` (#14, #30), `curl http://...` (#15). Windows users get one line, "install Git Bash". There's no `py -3`, no `%USERPROFILE%` path, no `curl.exe`, and no shortcut names. `OPERATIONS.md` §0 l.28 forbids bare `python`, yet the GUIDE says `python doctor.py`. | #14, #15, #20, #30; GUIDE l.143, 392, 452 |
| A10 | Facts drift | Slide #14 and GUIDE say "Node 18+". `BOOTSTRAP.md` §2.2 says "latest LTS via a version manager (nvm)", because chrome-devtools-mcp needs Node 20.19+. | `BOOTSTRAP.md` §2.2 |
| A11 | Nav chrome (desktop) | The tracker (10 pills) and the bottom bar (section, deck title, counter) repeat the section name twice. The bottom bar is 56 px tall plus an 8 px gap, which takes 9% of a 720 px screen. The progress bar (6 px) and tracker are separate strips. | l.24–31, 68–75 |
| A12 | Nav chrome (mobile 390×844) | The fixed `#tracker` (l.26) covers the slide title: the first title line is clipped under it and a horizontal scrollbar shows (tracker scrollWidth 625 > 390). `#viewport` becomes `position:static` with only `.5rem` padding (l.100), so nothing reserves room for the fixed strip. | `deck-390-11.png` |
| A13 | Beginner language | Jargon appears in titles: "dork", "harness", "OAuth client", "debug-mode", "Truth gates", "Caveman". It is explained only in the GUIDE glossary at the end. | titles #7, #12, #18 |
| A14 | Print | Print relies on `.slide{display:block}` with no fixed page box. Slides print at content height (half-empty pages), and SVG strokes use the screen accent. | l.118–127 |

---

## B. Design system spec

### B1. Principles
1. **Fill the stage.** Every slide uses one of 8 layout templates (B6). Each template distributes content over the full body height. Done means no empty vertical band larger than 15% of the slide height.
2. **One message per slide.** The title states the claim. The body shows the evidence as table, steps, number or diagram, and the speaker notes carry the detail.
3. **Dark is the default.** Light is opt-in: the `T` key or `?theme=light`, remembered. The OS light/dark preference is ignored (F2). Reason: projectors wash out light themes, which is the "pale" complaint.
4. **One brand accent (green).** Amber is used only for warnings and red only for danger, as in `SLIDES_SPEC.md` addendum rule 4. **Per-section accent decision:** sections do NOT get their own hues. The section cue is a numbered eyebrow ("04 · SETUP") plus the tracker chip. Reason: adding 10 hues would break colour meaning (green = go/tip) and fail colour-blind users. The single exception is the OS-tab badge colours in B5, which are neutral greys with an icon glyph.

### B2. Tokens (exact hex; WCAG ratios computed against the surface they sit on)

```css
:root{ /* DARK = default */
  --bg:#0b1220;        /* page */
  --surface:#121b2d;   /* slide card */
  --surface-2:#1a2740; /* step cards, table header, code bg */
  --line:#2a3a57;
  --fg:#f1f5f9;        /* titles      15.7:1 on surface */
  --body:#dbe3ec;      /* body text   13.3:1 */
  --muted:#a7b4c6;     /* captions     8.2:1 (was #9fb0c0) */
  --accent:#34d399;    /* brand green  9.0:1 */
  --accent-ink:#052e1f;/* text on accent fill 7.7:1 */
  --accent-soft:rgba(52,211,153,.14);
  --amber:#fbbf24;     /* 10.3:1 */  --amber-soft:rgba(251,191,36,.12);
  --red:#f87171;       /*  6.2:1 */  --red-soft:rgba(248,113,113,.12);
  --code:#a5f3fc;      /* inline code 13.8:1 */
  --shadow:0 1px 0 rgba(255,255,255,.04) inset,0 20px 40px -20px rgba(0,0,0,.6);
}
:root[data-theme="light"]{
  --bg:#e9edf3; --surface:#ffffff; --surface-2:#eef2f7; --line:#cfd8e3;
  --fg:#0f172a; --body:#1e293b; --muted:#475569;          /* 17.9 / 14.6 / 7.6 :1 */
  --accent:#047857; --accent-ink:#ffffff; --accent-soft:rgba(4,120,87,.10); /* 5.5:1; white on accent 5.5:1 */
  --amber:#92400e; --amber-soft:rgba(146,64,14,.08);      /* 7.1:1 */
  --red:#b91c1c;   --red-soft:rgba(185,28,28,.08);        /* 6.5:1 */
  --code:#0e7490;                                          /* 5.4:1 */
  --shadow:0 1px 2px rgba(15,23,42,.06),0 12px 32px -12px rgba(15,23,42,.18);
}
/* NO prefers-color-scheme block: dark always, light only by explicit choice (see F2). */
```
Light bg `#e9edf3` against the white card gives clear figure/ground, which fixes A5. Body text uses `--body`, not `--muted`. `--muted` is reserved for captions of 3.4cqh or larger.

### B3. Type scale (system stack only; sizes in container units of the slide)

```css
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Helvetica Neue",Arial,sans-serif}
button,input{font:inherit}                 /* fixes A4 */
code,pre,kbd{font-family:ui-monospace,"Cascadia Mono","Segoe UI Mono",Consolas,Menlo,monospace}
/* 1cqh = 1% of slide height. min(...,cqw) caps on very wide screens. */
.slide{--t-eyebrow:min(2.6cqh,1.5cqw); --t-title:min(7.2cqh,4.1cqw); --t-h3:min(5cqh,2.9cqw);
       --t-body:min(4.6cqh,2.6cqw); --t-small:min(3.4cqh,1.95cqw); --t-table:min(4cqh,2.3cqw);
       --t-code:min(3.7cqh,2.1cqw); --t-stat:min(22cqh,12cqw); --t-stat-label:min(4cqh,2.3cqw)}
.eyebrow{font-size:var(--t-eyebrow);letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:var(--accent)}
.slide h1{font-size:min(9.5cqh,5.4cqw);line-height:1.05;font-weight:800;letter-spacing:-.02em}
.slide h2{font-size:var(--t-title);line-height:1.1;font-weight:750;letter-spacing:-.015em;text-wrap:balance;max-width:28ch}
.slide p,.slide li{font-size:var(--t-body);line-height:1.35;color:var(--body)}
```
The resulting sizes at the stage heights in B4:

| Slide height | Title | Body | Table | Code |
|---|---|---|---|---|
| ~616 px (1280×720) | 44 px | 28 px | 25 px | 23 px |
| ~956 px (1920×1080) | 69 px | 44 px | 38 px | 35 px |

Titles must fit on **one line at 1280×720**. If a title wraps, either shorten it or let `text-wrap:balance` give two even lines, then drop the eyebrow on that slide. Acceptance: title height ≤ 2 × line-height.

### B4. Stage, scaling and fill strategy (replaces `fit()` and the fixed 1280×672 box)

```css
:root{--top:34px;--bot:52px;--gut:clamp(8px,1.4vw,28px)}
html,body{height:100%;margin:0;background:var(--bg);color:var(--body)}
body{overflow:hidden}
#viewport{position:fixed;inset:var(--top) 0 var(--bot) 0;display:grid;place-items:center;padding:var(--gut)}
#stage{position:relative;width:100%;height:100%;
  max-width:calc((100vh - var(--top) - var(--bot) - 2*var(--gut)) * 2.1);   /* never wider than 21:9 */
  max-height:calc((100vw - 2*var(--gut)) * .75)}                            /* never taller than 4:3 */
.slide{position:absolute;inset:0;display:none;container-type:size;
  background:var(--surface);border:1px solid var(--line);border-radius:min(2.4cqh,18px);box-shadow:var(--shadow);
  padding:6cqh 5.5cqw 5cqh;overflow:hidden;
  grid-template-rows:auto minmax(0,1fr) auto;row-gap:3.2cqh}
.slide.active{display:grid;animation:fade .2s ease-out}
.s-head{display:flex;flex-direction:column;gap:1.2cqh}
.s-body{display:flex;flex-direction:column;justify-content:center;gap:2.8cqh;min-height:0}
.s-body.fill{justify-content:stretch}            /* tables/grids stretch rows to fill */
.s-body.fill>*{flex:1 1 auto}
.s-foot{font-size:var(--t-small);color:var(--muted);display:flex;gap:1.5cqw;align-items:center}
@supports not (height:1cqh){ .slide{font-size:28px} } /* fallback: old browsers show px sizes; still centred */
```
Fill rules:
- **Fill, don't centre a small block.** Tables use `.fill` with `tr{height:calc(100%/rows)}`. Step grids use `grid-auto-rows:1fr`. Diagrams use `height:100%` with `preserveAspectRatio="xMidYMid meet"`.
- **≤ 3 bullets:** switch to the `split` layout (text left, visual or callout right) or the `focus` layout. A bare list of 3 lines may never be the whole body.
- **Short content:** raise type with a `.s-body.big` modifier (`--t-body:min(5.6cqh,3.1cqw)`) rather than leaving space.
- `#bar` and `#tracker` merge into **two thin rows** (B8), which gives about 10% more stage height.
- The JS `fit()` scaling is removed (no transform), so text renders at real pixel sizes and stays crisp.

### B5. Components (exact CSS)

```css
/* Step cards */
.steps{display:grid;grid-template-columns:repeat(var(--n,3),1fr);gap:2cqw;grid-auto-rows:1fr}
.step{background:var(--surface-2);border:1px solid var(--line);border-radius:1.6cqh;padding:3cqh 2cqw;display:flex;flex-direction:column;gap:1.4cqh}
.step .num{width:7cqh;height:7cqh;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:var(--t-h3)}
.step h3{font-size:var(--t-h3);color:var(--fg);line-height:1.15}
.step p{font-size:var(--t-small)}
.step .who{margin-top:auto;font-size:var(--t-eyebrow);text-transform:uppercase;letter-spacing:.1em;color:var(--muted)} /* "AGENT DOES IT" / "YOU DO IT" */
/* Stat */
.stat{display:flex;align-items:baseline;gap:2cqw}
.stat b{font-size:var(--t-stat);line-height:.9;font-weight:850;color:var(--accent);font-variant-numeric:tabular-nums}
.stat span{font-size:var(--t-stat-label);color:var(--body)}
/* Table */
.slide table{width:100%;border-collapse:separate;border-spacing:0;font-size:var(--t-table)}
.slide thead th{background:var(--surface-2);color:var(--fg);text-align:left;font-weight:700;padding:1.6cqh 1.4cqw;border-bottom:2px solid var(--accent)}
.slide td{padding:1.4cqh 1.4cqw;border-bottom:1px solid var(--line);vertical-align:middle}
.slide tbody tr:nth-child(even) td{background:color-mix(in srgb,var(--surface-2) 45%,transparent)}
/* Callouts: icon + label + colour (never colour only) */
.callout{display:grid;grid-template-columns:auto 1fr;gap:1.2cqw;align-items:start;padding:2.2cqh 1.8cqw;border-radius:1.4cqh;border:1px solid;font-size:var(--t-small)}
.callout::before{font-size:var(--t-h3);line-height:1}
.callout.tip{background:var(--accent-soft);border-color:var(--accent)}  .callout.tip::before{content:"✔";color:var(--accent)}
.callout.warn{background:var(--amber-soft);border-color:var(--amber)}   .callout.warn::before{content:"⚠";color:var(--amber)}
.callout.danger{background:var(--red-soft);border-color:var(--red)}     .callout.danger::before{content:"⛔"}
.callout b:first-child{display:block;text-transform:uppercase;letter-spacing:.08em;font-size:var(--t-eyebrow)}
/* Code */
.slide code{font-size:.86em;color:var(--code);background:var(--surface-2);border:1px solid var(--line);border-radius:.4em;padding:.05em .35em;overflow-wrap:anywhere}
.slide pre{font-size:var(--t-code);background:var(--surface-2);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:1.2cqh;padding:2cqh 1.6cqw;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--fg)}
.slide pre .c{color:var(--muted)}   /* comment span */
.slide pre .k{color:var(--accent);font-weight:700} /* AND/OR keywords */
kbd{font-size:.8em;border:1px solid var(--line);border-bottom-width:3px;border-radius:.35em;padding:.05em .4em;background:var(--surface-2);color:var(--fg)}
/* Chips (keywords, sources) */
.chips{display:flex;flex-wrap:wrap;gap:1.2cqh 1cqw}
.chip{font-size:var(--t-small);padding:.6cqh 1.2cqw;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);color:var(--fg)}
/* OS tabs */
.os{display:flex;flex-direction:column;gap:1.4cqh}
.os-tabs{display:inline-flex;gap:.4cqw;padding:.5cqh;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);align-self:flex-start}
.os-tabs button{font-size:var(--t-small);padding:.8cqh 1.6cqw;border-radius:999px;border:0;background:transparent;color:var(--muted);cursor:pointer}
.os-tabs button[aria-selected="true"]{background:var(--accent);color:var(--accent-ink);font-weight:700}
[data-os-panel]{display:none}
:root:not([data-os]) [data-os-panel~="win"],
:root[data-os="win"] [data-os-panel~="win"],
:root[data-os="mac"] [data-os-panel~="mac"],
:root[data-os="linux"] [data-os-panel~="linux"]{display:block}
.os-sub{font-size:var(--t-eyebrow);text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6cqh} /* "POWERSHELL" / "GIT BASH" */
```
OS tabs markup (one global choice, which every tab group on every slide follows):
```html
<div class="os">
  <div class="os-tabs" role="tablist" aria-label="Operating system">
    <button role="tab" data-os="win">⊞ Windows</button><button role="tab" data-os="mac"> macOS</button><button role="tab" data-os="linux">🐧 Linux</button>
  </div>
  <div data-os-panel="win"><p class="os-sub">PowerShell</p><pre>…</pre><p class="os-sub">Git Bash</p><pre>…</pre></div>
  <div data-os-panel="mac"><pre>…</pre></div>
  <div data-os-panel="linux"><pre>…</pre></div>
</div>
```
Glyph rule: use only BMP glyphs that system fonts carry. U+F8FF () renders only on Apple devices, so use the text label "macOS" without the glyph. ⊞ and 🐧 are optional, and the text label is always present.

OS JS (add to the IIFE):
```js
var OS_KEY="jak-os";
function detectOS(){var p=((navigator.userAgentData&&navigator.userAgentData.platform)||navigator.platform||"").toLowerCase();
  return /win/.test(p)?"win":/mac|iphone|ipad/.test(p)?"mac":"linux";}
function getOS(){try{var v=localStorage.getItem(OS_KEY);if(v==="win"||v==="mac"||v==="linux")return v;}catch(e){}return detectOS();}
function setOS(v,save){document.documentElement.setAttribute("data-os",v);
  document.querySelectorAll(".os-tabs button").forEach(function(b){b.setAttribute("aria-selected",String(b.dataset.os===v));});
  if(save){try{localStorage.setItem(OS_KEY,v);}catch(e){}}}
document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest(".os-tabs button");if(b){e.stopPropagation();setOS(b.dataset.os,true);}});
setOS(getOS(),false);
```
Key handler change: at the top of `keydown`, `if(e.target.closest&&e.target.closest(".os-tabs")&&(e.key===" "||e.key==="Enter"))return;` so Space on a tab does not also advance the slide. The theme toggle works the same way: key `T`, stored under `jak-theme`, wrapped in try/catch, applied as `data-theme` on `<html>`. Add both keys to the help overlay.

### B6. Layout templates (`data-layout` on `<section>`)

| Template | Body structure | Use when |
|---|---|---|
| `hero` | h1 at 9.5cqh + subtitle + 3 chips row; content vertically centred in the full card | #1 |
| `focus` | one large statement box (`.rule`, 6cqh type) + 3 icon tiles below | #3, #29 |
| `table` | `.s-body.fill` table, rows stretch; optional 1-line `.s-foot` | #5, #10, #20 (left), #25 |
| `split` | `grid-template-columns:1.1fr .9fr;gap:4cqw;align-items:stretch` | text + visual/callout/OS panel |
| `steps` | `.steps` with `--n:3` or `--n:4`, cards stretch to full height | #6, #11, #17, #18, #22 |
| `stat` | `.stat` left (61 → 4) + stacked bar + legend right | #26 |
| `diagram` | SVG at `height:100%` of body; optional 1-line caption | #4, #9, #27 |
| `code-os` | `split`: left = 3 numbered steps; right = `.os` tabs with `pre` | #12, #14, #15, #30 |
| `grid` | `display:grid;grid-template-columns:repeat(var(--c),1fr);grid-auto-rows:1fr;gap:2cqh 2cqw` of cards | #19, #24, #28 |

### B7. Diagram style (the 3 SVGs: #4 pipeline, #9 architecture, #27 human-in-the-loop)
- `viewBox="0 0 1200 420"`, `width:100%;height:100%`, `preserveAspectRatio="xMidYMid meet"`, plus `<title>` and `aria-labelledby`.
- Nodes are `rect rx=18`, `fill:var(--surface-2)` (via `class="node"`), with `stroke:var(--line)` at width 2. The **human node** (#4 step 6, #27 "You review" and "You send") uses `class="node you"`: `fill:var(--accent-soft);stroke:var(--accent);stroke-width:3`.
- A numbered badge circle (r=22, accent fill, accent-ink number) sits on the top-left of each node.
- Label text is 30 units, weight 700, `fill:var(--fg)`. Sub-label text is 22 units, `fill:var(--muted)`. Minimum font size inside an SVG is 20 units.
- Arrows are `stroke:var(--muted)`, width 3, with the marker `path{fill:var(--muted)}`, which is less loud than the nodes.
- Remove the malformed `fill="none""` attributes (A8). Use classes and no inline colour attributes, so the theme switch and print work.
- #4 is laid out as 2 rows × 3 nodes (Scan → De-dupe → Template / Draft → Record → **You**) with a U-turn arrow. This gives larger nodes at 16:9. A source-chip row (FB, LinkedIn, BDJobs, Discord, Screenshots) feeds node 1.
- #9 has 3 columns. Each column has a header node plus a "Needs:" chip under it (Google sign-in / debug browser / PDF tools), so the mapping to setup is visible.
- #27 has 3 nodes, and the last two are `.you`. Under "You review", 4 tiny check icons read: company, role, phone, body.

### B8. Nav chrome
- **Top strip (34 px):** a 3 px progress line along the very top edge, inside the same element. Below it is the tracker of 10 section chips, 12 px, upper-case. The current chip is filled `--accent`/`--accent-ink`, and past chips get `--muted` text with a ✓ prefix.
- **Bottom bar (52 px):** `← Prev` on the left, then the section eyebrow ("04 · SETUP"), the deck title in the centre (hidden < 900 px), the counter **"Slide N of 30"** (20 px bold, `aria-live="polite"`), then `Next →`. Buttons are 40 px tall and inherit the font.
- **Remove the duplication:** the section name appears once in the slide's eyebrow and once in the tracker chip. The bar shows `N / 30` context only through the counter, plus the eyebrow text.
- **Overview grid (`O`):** use the same tokens. Cards show the eyebrow number and title, and the current card gets an accent ring.
- **Notes panel (`N`):** `--surface-2` bg, `--fg` text, 18 px, max-width 70ch, placed above the bar.
- **Help (`?`):** add `T` (theme) and an "OS tabs: click Windows / macOS / Linux" line.

### B9. Mobile (≤ 700 px wide, e.g. 390×844)
```css
@media (max-width:700px){
  body{overflow:auto}
  #top{position:sticky;top:0;height:auto}                 /* tracker no longer overlaps content (A12) */
  #tracker{overflow:hidden}                               /* show only the current chip + "4/10" */
  #tracker span:not(.on){display:none}
  #viewport{position:static;padding:12px 16px 72px}
  #stage{max-width:none;max-height:none;height:auto}
  .slide{position:relative;inset:auto;container-type:inline-size;padding:20px 18px;row-gap:14px}
  .slide.active{display:grid}
  .slide{--t-title:26px;--t-body:18px;--t-small:15px;--t-table:15px;--t-code:13px;--t-h3:19px;--t-stat:72px;--t-eyebrow:11px}
  .split,.steps,.grid{grid-template-columns:1fr !important}
  .slide table{min-width:0}                               /* stack rows instead of horizontal scroll */
  .slide table thead{display:none}
  .slide table tr{display:grid;grid-template-columns:1fr;padding:8px 0;border-bottom:1px solid var(--line)}
  .slide table td{border:0;padding:2px 0}
  .slide table td:first-child{font-weight:700;color:var(--fg)}
  svg.diagram{height:auto;max-height:60vh}
  #bar{position:fixed;bottom:0;height:56px}
  #decktitle,#sectionLabel{display:none}
}
```
Rules: no horizontal page scroll (`scrollWidth === innerWidth`), titles must not be covered by the top strip, and the counter must stay visible.

### B10. Print
```css
@page{size:13.333in 7.5in;margin:0}
@media print{
  :root{/* force light tokens */}
  body{overflow:visible;background:#fff}
  #top,#bar,#notesPanel,#overview,#help,.os-tabs{display:none!important}
  #viewport,#stage{position:static;max-width:none;max-height:none;padding:0}
  .slide{display:grid!important;position:relative;width:13.333in;height:7.5in;break-after:page;box-shadow:none;border:0;border-radius:0;animation:none}
  [data-os-panel]{display:block!important}                 /* print all three OS variants */
  [data-os-panel]::before{content:attr(data-os-label);font-weight:700;font-size:.7em;color:#475569}
  aside.notes{display:none!important}
}
```
When three OS panels make a print slide overflow, the `code-os` slides print with `pre{font-size:2.6cqh}`. This is acceptable, and it is what the T10 check verifies.

---

## C. Slide-by-slide change list (30 slides)

Timing column = minutes, summing to 45. "Notes +" = what to add or change in `<aside class="notes">`. Titles keep the `SLIDES_SPEC.md` wording unless "NEW" is shown, with the reason given. Each new title is 8–14 words and contains no jargon.

| # | Section | Title (final) | Layout | Content: cut / add | OS variants | Notes + | Min |
|---|---|---|---|---|---|---|---|
| 1 | Intro | Stop doing the daily job-hunt grind by hand | hero | Subtitle: "Job Apply Kit · 45-minute beginner workshop · Windows, macOS, Linux". 3 chips: "Agent scans", "Agent drafts", "You send". Foot: take-home `docs/workshop/GUIDE.md`. | none | Ask for a show of hands: Windows / Mac / Linux. Explain that setup slides have OS tabs, top right. | 1 |
| 2 | Intro | After this session you can run the kit yourself | split | Left: 3 numbered outcome cards (Explain it · Set it up · Run + review). Right: "Bring" card listing laptop, Google account, your CV (PDF or Google Doc), and logins for FB/LinkedIn/BDJobs (`docs/help/01-prerequisites.md`). | none | Cut "who it fits" to one line. | 1 |
| 3 | Intro | The agent fills and stages applications, but never submits | focus | Big rule box. 3 tiles: Emails → Gmail drafts · Forms → stop at Submit · You → press every button. Foot: "One exception: BDJobs portal Apply, only inside `bdjobs-full-run`" (README "Never-submit"). | none | Unchanged; say it twice. | 1 |
| 4 | Intro | Six automated steps turn job posts into reviewed drafts | diagram | Redraw per B7 (2×3, source chips, "You" highlighted). Remove the `.small` sources line, since it is now in the SVG. | none | Unchanged. | 1 |
| 5 | Manual | Every manual job-search habit has an automated counterpart | table (fill) | Columns: Source · You do · Agent skill. Five rows stretch. `.s-foot`: "Daily group visits stay manual · saved LinkedIn posts → `check-linkedin-saved`". | none | Move the groups/LinkedIn-saved remark into the visible foot. | 1.5 |
| 6 | Manual | Saving Facebook posts while scrolling feeds the automation | steps (n=3) | Cards: ① Join 20–30 job groups (search "career", "job vacancy") · ② Save every job post while scrolling · ③ Agent reads your last ~20–25 saved items. `.who` badges: YOU / YOU / AGENT. Tip callout: "Save first, apply later." | none | Unchanged. | 1.5 |
| 7 | Manual | **NEW:** Short LinkedIn search queries find fresh posts; long ones return nothing | split | Left: `pre` with the example query, AND/OR in `.k`. Below it, 3 mini-steps: Posts tab · Sort by Latest · add `(Remote OR Hybrid)`. Right: warn callout (length limit) plus a tip: "Ask any chat model to write queries from your CV." Word "dork" moves to notes only. | none | Define "dork = a short search query with AND/OR". | 1.5 |
| 8 | Manual | BDJobs keywords find jobs that category browsing misses | split | Left: chip cloud of 8 title variants from GUIDE §2.2. Right: 2 reason cards: "Jobs get posted in the wrong category" and "Top results can be paid ads, so scroll past them". | none | Unchanged. | 1.5 |
| 9 | Arch | Email drafting, browser automation and CV generation work together | diagram | 3 columns per B7 with "Needs:" chips. Remove the `.small` line. | none | Unchanged. | 2 |
| 10 | Arch | Say one phrase and the matching skill runs | table (fill) | 6 rows (split LinkedIn and LinkedIn-saved apart). This is an allowed exception to the ≤5-row rule because the rows are short. Foot tip: "Type `run`, then `@`, and pick the skill folder." | none | Start newcomers on FB saved. | 2 |
| 11 | Setup | **NEW:** Setup is thirteen steps in four phases; the agent does most | steps (n=4) | Phase cards: **A Install** (1 agent app, 2 model, 3 clone, 4 first prompts, 5 tools) · **B Connect** (6 debug browser, 7 Google) · **C Personalise** (8 CV, 9 config, 10 templates, 11 review PDFs) · **D Go** (12 check setup, 13 fresh session + run). Each step line gets a tiny AGENT/YOU tag. Foot: "Details: `docs/help/` 01–08". | none | Reason for the new title: phases are easier to remember than 13 items. | 1.5 |
| 12 | Setup | **NEW:** Install one agent app, then clone the kit into your home folder | code-os | Left: ① Install OpenCode (free models) or Claude Code · ② Open a terminal (Windows: **Git Bash** from the Start menu) · ③ Clone. Right OS tabs. **Win, PowerShell:** `winget install --id SST.OpenCodeDesktop -e` or `winget install Anthropic.ClaudeCode` (`BOOTSTRAP.md` §2.6), `winget install --id Git.Git -e` **(verify: Git for Windows winget id is not in repo docs)**. **Win, Git Bash:** `cd ~ && git clone <repo-url> job-apply-kit && cd job-apply-kit`. **macOS/Linux:** `npm i -g opencode-ai@latest` (`BOOTSTRAP.md` §2.6) + same `git clone` line in Terminal. | yes | Reason for the new title: clone and app install were hidden in one bullet, and beginners need commands. Model choice moves to #23. Point at `C:\Users\<you>\job-apply-kit`. | 2 |
| 13 | Setup | Two prompts start the whole setup | focus | Two big chat bubbles (prompt 1, prompt 2). Footer: "The agent then follows `docs/BOOTSTRAP.md`; on Windows it runs kit commands in Git Bash (`OPERATIONS.md` §0)." OpenCode app: *Add Project*; Claude Code: run `claude` inside the folder. | none | Have attendees photograph it. | 1.5 |
| 14 | Setup | Python, Node, PDF tools and Git Bash are the prerequisites | code-os | Left: 4 cards: Python 3.9+ · Node latest LTS via nvm (**fix A10**) · tectonic + poppler (PDFs) · agent-browser. Windows card: Git for Windows. Right OS tabs. **Win, PowerShell:** `winget install Python.Python.3.12`, `winget install --id tectonic.tectonic -e`, `winget install --id oschwartz10612.Poppler -e`, Node = nvm-windows setup exe then `nvm install lts` (`BOOTSTRAP.md` §2.1–2.3). **Win, Git Bash:** `npm install -g agent-browser@latest`, then `py -3 doctor.py --mode all`. **macOS:** `brew install python@3.12 poppler`, `nvm install --lts`, tectonic drop-sh (`BOOTSTRAP.md` §2.3), `./doctor.sh --mode all`. **Linux:** `sudo apt install python3 python3-pip poppler-utils`, `nvm install --lts`, `./doctor.sh --mode all`. Callout tip: "You don't type these; the agent does. They're here so you recognise them." | yes | Explain why Git Bash: PowerShell breaks unix-style commands (`OPERATIONS.md` §0). Say "MISSING lines name their own fix". Never use bare `python` on Windows; use `py -3` (`OPERATIONS.md` l.28). | 2.5 |
| 15 | Setup | A debug-mode browser lets the agent use your logged-in sessions | code-os | Left steps: ① Agent creates a desktop shortcut · ② **Close all browser windows** · ③ Double-click the shortcut · ④ Log in once to FB, LinkedIn, BDJobs, Google. Right OS tabs: shortcut name plus check command. **Win:** `JAK Google Chrome (debug).lnk` on Desktop (or `OneDrive\Desktop`); launcher `browser-debug-chrome.bat` / `browser-debug-brave.bat` in the kit folder; check `curl.exe http://127.0.0.1:9222/json/version`. **macOS:** `JAK Google Chrome (debug).command`; check `curl http://127.0.0.1:9222/json/version`. **Linux:** `jak-chrome-debug.desktop`; same curl. Sources: `browser_setup.py` l.162–219, `BOOTSTRAP.md` §3. Warn callout (cookies). | yes | Add: "If you see only `about:blank`, your normal browser was still open." | 2 |
| 16 | Google | Google Cloud gives the agent safe access to Gmail, Drive and Sheets | split | Left: 3 service tiles: Gmail → drafts · Drive → PDFs · Sheets → tracker rows. Right: "You create" stat list: **1** project · **3** APIs · **1** sign-in key file. Chip: "Free · no billing". | none | Unchanged. | 1 |
| 17 | Google | Three enabled APIs are all the project needs | steps (n=4) | Breadcrumb cards: ① console.cloud.google.com → New project `job-apply-kit` · ② Select it in the top bar · ③ APIs & Services → Library · ④ Enable Gmail, Drive, Sheets ("Manage" = already on). Placeholder slot for a screenshot if available (`<figure class="shot" data-todo>`; it is optional, and with no image it shows an empty dashed frame of 0 height. Do NOT ship an empty frame). | none | Unchanged. | 1.5 |
| 18 | Google | **NEW:** A downloaded Desktop sign-in key file completes Google access | steps (n=3) | ① Consent screen: External, 4 scopes, yourself as test user, stay in Testing · ② Credentials → OAuth client ID → Desktop app → Download JSON · ③ Give the file path to the agent, which stores it in the token folder (OS tabs show path, see D3). Callout tip: "`gmail.send` is left out on purpose." | yes (path only) | Reason for the new title: replaces the jargon "OAuth client". The notes keep the word OAuth with a one-line definition. | 2 |
| 19 | Google | Four Google gotchas cause most setup failures | grid (c=2) | 4 cards with icons: 🔒 Never share the JSON or tokens · ⏳ **7 days** unused = sign in again (stat style) · 🔗 IDs are in the URLs (`/folders/<ID>`, `/d/<ID>/edit`) · ✨ Missing folder or Sheet? the agent creates them (`sheet_init.py`). | none | Unchanged. | 1.5 |
| 20 | Config | One config file outside the repo holds everything personal | split | Left: table (5 groups, fill). Right: "Where it lives" OS card. **Win:** `C:\Users\<you>\.config\job-apply-kit\config.md` (`%USERPROFILE%\.config\...`). **macOS:** `/Users/<you>/.config/job-apply-kit/config.md`. **Linux:** `/home/<you>/.config/job-apply-kit/config.md`. Plus "Template: `config.example.md` · override: `JAK_CONFIG`" (`jak_config.py` l.42–51, `00-config.md`). | yes | Add the tip: "Say: Ask me questions to fill the config." | 1.5 |
| 21 | Config | A real config shows how search terms and filters look | split | Left: larger `pre` (`--t-code`) of the example. Right: 3 annotation cards with arrows: "Your job titles" (bdjobs_terms) · "Short queries, one per line" (linkedin_queries) · "Filters: 5 yrs, BDT, remote ok". | none | Unchanged. | 1.5 |
| 22 | Config | Templates are built once, then every PDF must be reviewed | steps (n=3) | ① `/create-template` proposes role categories · ② Builds CV + resume + cover letter (PDF, Markdown, LaTeX) into `<kit folder>/templates` (D3) · ③ **You** read every PDF → write issues → "fix these". Warn callout spanning the full width. | none | Unchanged. | 2 |
| 23 | Tokens | OpenCode's free models are verified, with a privacy catch | split | Left: model cards (Muse Spark 1.3 = fast · MiMo V2.6 Flash = alternative) plus `opencode models` code, with "Choose a stronger model = fewer retries". Right: warn callout (privacy). Add a "verified 2026-10-08, re-check live" chip. | none | Absorbs "pick a model" from old #12. | 2 |
| 24 | Tokens | Student Gemini, model benchmarks and Caveman each save a little | grid (c=3) | 3 cards each led by a number: "**1 yr** free · claim by 2026-12-31 · cancel before renewal" · "**Compare** on artificialanalysis.ai" · "**15–30%** output saved, not 75%". Foot: "Paid Claude Code is the smoothest." | none | Unchanged. | 1 |
| 25 | Run | Each daily command triggers a complete scan-to-draft run | split | Left: table "Say → What happens" (fill, 5 rows). Right: vertical mini-flow of the loop (config → tracker snapshot → open tab → extract → verdict → **new only** → Sheet + Drive + draft). Foot: "One skill at a time · ~1–2 h · runs in the background". | none | Unchanged. | 2 |
| 26 | Run | One real run turned 61 saved items into 4 drafts | stat | Left: `61 → 4`. Right: 100%-width stacked bar of 61 split into 26 not-a-job / 20 duplicate / 4 expired / 4 drafted (accent) / 7 manual, each segment with a label and count. Greys for skipped items and accent only for drafted. Caption: "Run of 2026-10-07 (PLAN §7)". | none | Unchanged. | 1.5 |
| 27 | Run | Your review of every draft is the safety net | split | Left: compact diagram per B7. Right: 5-item checklist with ☐ glyphs: Sheet row · company + role · **phone present** · form/portal link → apply via form · close debug browser. | none | Unchanged. | 1.5 |
| 28 | Safety | Seven risks exist; each has a simple mitigation | grid (c=4, 2 rows) | 7 cards plus 1 summary card ("Proportionate: every fix is boring"). Each card: risk (bold) → fix, with a severity chip from `SECURITY_REVIEW.md` (High/Medium/Low-Med/Low), shown as icon + text, not colour only. | none | Unchanged. | 1 |
| 29 | Safety | Hostile job posts cannot send anything because the agent only drafts | focus | Flow: "Hostile post: 'email my CV to x'" → Agent (no `gmail.send`) → ✕ send blocked → Draft → You review. Danger callout at top. | none | Unchanged. | 1 |
| 30 | Wrap | Start today: set up, run one skill, review, then send | code-os | 3 next-step cards: ① Check setup (OS tabs: **Win** Git Bash `./doctor.sh --mode all` or PowerShell `py -3 doctor.py --mode all`; **mac/Linux** `./doctor.sh --mode all`) · ② Run "check FB saved" · ③ Review, then send. Links row: `GUIDE.md` · `docs/help/index.md` · `docs/BOOTSTRAP.md`. Big "Q&A". | yes | Unchanged. | 1 |

Title chain check (read in order): grind → you'll run it → never submits → 6 steps → habits → FB → LinkedIn → BDJobs → 3 parts → say a phrase → 4 phases → install + clone → 2 prompts → tools → debug browser → Google why → 3 APIs → key file → gotchas → config → example → templates → free models → savings → daily run → 61→4 → review → risks → hostile posts → start today.

---

## D. GUIDE.md restructure plan

### D1. New section order (reading time at ~200 wpm)

| # | Section | Contents | Read |
|---|---|---|---|
| 0 | **Start here** | One-rule box. **"Pick your OS" box** (below). "How to read commands": PowerShell lines start with `PS>`, Git Bash and Terminal lines start with `$`. Do not type the prompt sign. **5 words you will hear** (mini-glossary: agent app, skill, debug browser, Google sign-in key, search query). | 3 min |
| 1 | What the kit does | 6-step list + diagram placeholder `[D-1 pipeline]` + 3 parts table. | 2 min |
| 2 | Your manual routine | Existing table + LinkedIn/BDJobs tips (renamed "search queries"). | 3 min |
| 3 | Before you start | Checklist: laptop (Windows 10/11, macOS or Linux), Google account, CV, logins. Expect ~2 hours for first setup **(verify: no duration is stated in the repo; label it as an estimate)**. | 1 min |
| 4 | Setup A: install the tools | Per-OS command table (D2), with "the agent can do this" first. If-it-breaks box. | 5 min |
| 5 | Setup B: get the kit and start the agent | Clone, open, two prompts. | 2 min |
| 6 | Setup C: debug browser | Steps, shortcut names per OS, check command, warning. If-it-breaks box (`about:blank`, port busy). | 3 min |
| 7 | Setup D: Google (click path) | Existing §4 with the per-OS token path. If-it-breaks box (7-day expiry, wrong account). | 5 min |
| 8 | Setup E: CV and config | Path table excerpt + groups table + `jak_config.py` commands per OS. | 3 min |
| 9 | Setup F: templates and review | Existing steps 10–11 + warning. | 2 min |
| 10 | Check your setup | `doctor` per OS; "green means go"; how to read MISSING/WARN. | 1 min |
| 11 | Daily run | Existing §7 + the loop diagram placeholder `[D-2 run loop]`. | 3 min |
| 12 | Review checklist | Existing §8. | 1 min |
| 13 | Free or cheap tokens | Existing §6 (table trimmed to 4 columns max). | 3 min |
| 14 | Safety and privacy | Existing §10 + the 7 risks table from `SECURITY_REVIEW.md` (risk → what you do). | 2 min |
| 15 | If it breaks (all OSes) | Consolidates old §9: a symptom → fix table with an OS column. | 3 min |
| A | Appendix: paths per OS | Table D3 (full). | ref |
| B | Appendix: glossary | Full glossary (existing 5 terms + agent app, MCP, token file, workspace, PATH, Git Bash, PowerShell, winget, Homebrew, nvm). | ref |
| C | Appendix: FAQ | Existing 10 Q&As; commands rewritten per OS. | ref |
| D | Appendix: worked example | Existing. | ref |

"Pick your OS" box (top of the guide, verbatim):
> **Pick your OS. Each step below has a row for it.**
> - **Windows 10/11:** install **Git for Windows**, then use **Git Bash** for every kit command. Use **PowerShell** only for `winget install …` lines. Python is `py -3`, never `python`. Your home folder is `C:\Users\<you>` (`%USERPROFILE%`). *(Sources: `skills/job-apply-core/OPERATIONS.md` §0, `docs/BOOTSTRAP.md` §0.)*
> - **macOS:** use the **Terminal** app. Install tools with **Homebrew** (`brew`). Python is `python3`. Home is `/Users/<you>`.
> - **Linux:** use your terminal and your package manager (`apt`/`dnf`/`pacman`). Python is `python3`. Home is `/home/<you>`. This is the author's own platform and the smoothest (`docs/help/08-compatibility.md`).
> - **Not sure?** Ask the agent: *"Which OS am I on?"* It runs `python3 -c "import platform; print(platform.system())"` (Windows: `py -3 -c …`).

"If it breaks" box format (one per setup section):
```md
> **If it breaks**
> | You see | Do this |
> |---|---|
> | `'npx' is not recognized` | Close the agent app and open it again from a NEW terminal (`docs/EXTERNAL_TOOLS.md` §5.1) |
```

### D2. Per-step OS command tables (copy into sections 4, 6, 8 and 10)

**Section 4: install tools.** Every line comes from `docs/BOOTSTRAP.md` §2 unless marked otherwise.

| Tool | Windows PowerShell | macOS Terminal | Linux Terminal |
|---|---|---|---|
| Git (Git Bash) | `winget install --id Git.Git -e` **(verify)** | preinstalled or `brew install git` **(verify)** | distro package **(verify)** |
| Python 3.9+ | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt install python3 python3-pip` |
| Python packages | Git Bash: `py -3 -m pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` | same as macOS |
| Node (latest LTS) | nvm-windows setup exe (github.com/nvm-windows/nvm), then `nvm install lts` + `nvm use <version>` | nvm: `nvm install --lts` | nvm: `nvm install --lts` |
| agent-browser | Git Bash: `npm install -g agent-browser@latest` | `npm install -g agent-browser@latest` | same |
| tectonic | `winget install --id tectonic.tectonic -e` | drop-sh one-liner from tectonic-typesetting.github.io | same as macOS |
| pdfinfo (poppler) | `winget install --id oschwartz10612.Poppler -e` | `brew install poppler` | `sudo apt install poppler-utils` |
| pandoc (optional) | `winget install --exact --id JohnMacFarlane.Pandoc` | `brew install pandoc` **(verify, docs say "OS package")** | distro package |
| Agent app | `winget install --id SST.OpenCodeDesktop -e` · or `irm https://claude.ai/install.ps1 \| iex` | `npm i -g opencode-ai@latest` · Claude Code: see code.claude.com/docs/en/setup | same as macOS |

Windows Git Bash first line, per `OPERATIONS.md` l.21–22: `export PATH="$(cygpath "$APPDATA/npm"):$PATH"`.

**Sections 5/6/8/10: kit commands.**

| Step | Windows Git Bash | Windows PowerShell (fallback) | macOS / Linux |
|---|---|---|---|
| Clone | `cd ~ && git clone <repo-url> job-apply-kit && cd job-apply-kit` | `cd $env:USERPROFILE; git clone <repo-url> job-apply-kit; cd job-apply-kit` | `cd ~ && git clone <repo-url> job-apply-kit && cd job-apply-kit` |
| Register MCP + PATH | `./install.sh` | `py -3 install.py` | `./install.sh` |
| Find browsers | `py -3 skills/job-apply-core/scripts/browser_setup.py --list` | same | `python3 skills/job-apply-core/scripts/browser_setup.py --list` |
| Make shortcut | `py -3 skills/job-apply-core/scripts/browser_setup.py --browser chrome --create` | same | `python3 … --browser chrome --create` |
| Check debug port | `curl http://127.0.0.1:9222/json/version` | `curl.exe http://127.0.0.1:9222/json/version` | `curl http://127.0.0.1:9222/json/version` |
| Check config | `py -3 skills/job-apply-core/scripts/jak_config.py --check` | same | `python3 skills/job-apply-core/scripts/jak_config.py --check` |
| Check setup | `./doctor.sh --mode all` | `py -3 doctor.py --mode all` | `./doctor.sh --mode all` |
| Update kit later | `./install.sh --update` | `py -3 install.py --update` | `./install.sh --update` |

Sources: `README.md` (Install, Updating), `docs/BOOTSTRAP.md` §§3–4, `docs/help/01-prerequisites.md`, `OPERATIONS.md` l.28. PowerShell `curl` is an alias in Windows PowerShell 5.1, so use `curl.exe` there. `BOOTSTRAP.md` §3 says "Windows: `curl.exe`".

### D3. Path table per OS (Appendix A; excerpts in §§6–9)

| What | Windows | macOS | Linux | Source |
|---|---|---|---|---|
| Kit folder (recommended clone spot) | `C:\Users\<you>\job-apply-kit` (Git Bash: `~/job-apply-kit`) | `/Users/<you>/job-apply-kit` | `/home/<you>/job-apply-kit` | README "Install" (`git clone <this-repo> job-apply-kit`; the location is our recommendation) |
| Config file | `C:\Users\<you>\.config\job-apply-kit\config.md` (`%USERPROFILE%\.config\job-apply-kit\config.md`) | `/Users/<you>/.config/job-apply-kit/config.md` | `/home/<you>/.config/job-apply-kit/config.md` | `jak_config.py` l.42–51 (`~` expanded per OS); override `JAK_CONFIG` |
| Google key + token folder | `C:\Users\<you>\.config\job-apply-kit\google\` | `~/.config/job-apply-kit/google/` | `~/.config/job-apply-kit/google/` | `jak_config.py` l.89; `00-config.md` (`google_token_dir`) |
| Workspace (run state) | the folder the agent runs in, i.e. the kit folder, or `JAK_WORKSPACE` | same | same | `jak_config.py` l.84 |
| Templates | `<kit folder>\templates\` (git-ignored) | `<kit folder>/templates/` | same | `jak_config.py` l.87; `.gitignore` |
| Run history | `<kit folder>\JDs\`, `<kit folder>\output\` (git-ignored) | same | same | `00-config.md`, `.gitignore` |
| Debug launcher | `<kit folder>\browser-debug-chrome.bat` / `browser-debug-brave.bat` | `<kit folder>/browser-debug-chrome.sh` | same as macOS | `browser_setup.py` l.162; repo root `.bat` files |
| Desktop shortcut | `%USERPROFILE%\Desktop\JAK Google Chrome (debug).lnk` (falls back to `OneDrive\Desktop`) | `~/Desktop/JAK Google Chrome (debug).command` | `~/Desktop/jak-chrome-debug.desktop` | `browser_setup.py` l.202–219 (note: `docs/help/03-browser-setup.md` says "JAK <label> (debug)" for all OSes; the Linux name differs in code) |
| Claude Code MCP config | `%USERPROFILE%\.claude.json` | `~/.claude.json` | `~/.claude.json` | `docs/EXTERNAL_TOOLS.md` l.310 |
| OpenCode MCP config | `%USERPROFILE%\.config\opencode\opencode.json` **(verify)** | `~/.config/opencode/opencode.json` | same | `docs/AGENTS.md` |
| Python command | `py -3` | `python3` | `python3` | `OPERATIONS.md` l.28 |
| Git Bash binary | `%ProgramFiles%\Git\bin\bash.exe` or `%LocalAppData%\Programs\Git\bin\bash.exe` (NOT `System32\bash.exe`, which is WSL) | n/a | n/a | `OPERATIONS.md` l.13–16 |

### D4. Diagrams and screenshots placeholders (GUIDE)
Use plain Markdown `> [Figure D-n: …]` lines until images exist. Images are stored under `docs/workshop/img/` and must be checked for PII before commit.

| ID | Where | What |
|---|---|---|
| D-1 | §1 | Pipeline (export of the slide #4 SVG; reuse the inline SVG) |
| D-2 | §11 | Run loop (from slide #25 right column) |
| S-1 | §4 | Windows Start menu showing "Git Bash" |
| S-2 | §6 | Desktop with the "JAK Google Chrome (debug)" shortcut |
| S-3 | §6 | Terminal output of `curl … /json/version` |
| S-4 | §7 | Cloud Console: New project dialog |
| S-5 | §7 | API Library with the three APIs |
| S-6 | §7 | Consent screen scopes + Test users |
| S-7 | §7 | Create OAuth client → Desktop app → Download JSON |
| S-8 | §10 | `doctor` output with OK / MISSING lines |

### D5. Language rules for GUIDE
- Sentences ≤ 20 words. One action per numbered step. Start each step with a verb.
- Define each jargon word on first use, inline in brackets: "debug browser (a normal browser started with a special switch so the agent can see your tabs)".
- Every command has an OS label. No bare `python`; no `~` path without its Windows twin.
- Replace "harness" with "agent app (OpenCode or Claude Code)" throughout. Replace "dork" with "search query" (keep "dork" once, in the glossary).
- Fix A10 in the GUIDE too: "Node 18+" becomes "Node, latest LTS, installed with nvm" (`BOOTSTRAP.md` §2.2).

---

## E. Ordered implementation tasks

Shared Playwright harness. Save as `/tmp/claude-1000/check.js`; this is not committed. It is run via the `browser_run_code_unsafe` tool or `npx playwright`.
```js
async (page) => {
  const base='file:///mnt/DABCEB02BCEAD851/Projects/job-apply-kit/docs/workshop/slides/index.html';
  const ext=[]; page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))ext.push(r.url())});
  const res=[];
  for (const [w,h] of [[1280,720],[1920,1080]]) for (const theme of ['dark','light']) {
    await page.setViewportSize({width:w,height:h});
    for (let n=1;n<=30;n++){
      await page.goto(base+'?theme='+theme+'#'+n); await page.reload(); await page.waitForTimeout(450);
      res.push(await page.evaluate(([w,h,n,theme])=>{
        const s=document.querySelector('.slide.active'), r=s.getBoundingClientRect();
        const kids=[...s.querySelectorAll(':scope > :not(aside)')].map(e=>e.getBoundingClientRect()).filter(b=>b.height>0);
        // collect all leaf-ish visible boxes inside body to find vertical empty bands
        const boxes=[...s.querySelectorAll('h1,h2,p,li,tr,pre,svg,.step,.stat,.callout,.chip,.card,img,figure')]
          .filter(e=>e.offsetParent!==null).map(e=>e.getBoundingClientRect()).filter(b=>b.height>0)
          .map(b=>[Math.max(b.top,r.top),Math.min(b.bottom,r.bottom)]).sort((a,b)=>a[0]-b[0]);
        let cur=r.top+parseFloat(getComputedStyle(s).paddingTop), maxGap=0;
        for (const [t,b] of boxes){ if(t>cur) maxGap=Math.max(maxGap,t-cur); cur=Math.max(cur,b); }
        maxGap=Math.max(maxGap, r.bottom-parseFloat(getComputedStyle(s).paddingBottom)-cur);
        const title=s.querySelector('h1,h2'), lh=parseFloat(getComputedStyle(title).lineHeight);
        return {w,h,theme,n,gapPct:Math.round(maxGap/r.height*100),
          overflow:s.scrollHeight>s.clientHeight+1||s.scrollWidth>s.clientWidth+1,
          titleLines:Math.round(title.getBoundingClientRect().height/lh),
          counter:document.getElementById('counter').textContent,
          cardShare:Math.round(r.height/innerHeight*100)};
      },[w,h,n,theme]));
    }
  }
  return JSON.stringify({ext,bad:res.filter(x=>x.gapPct>15||x.overflow||x.titleLines>2||x.counter!==`Slide ${x.n} of 30`)});
}
```
Pass condition for the deck checks: `ext.length===0 && bad.length===0`.

| ID | Files | Exact change | Acceptance check |
|---|---|---|---|
| T1 | `slides/index.html` | Replace the `:root` block (l.8–19) with the B2 tokens. Add `[data-theme]` handling, the `T` key and `?theme=` param, and a stored `jak-theme` (try/catch). Default dark. | `grep -c 'prefers-color-scheme' index.html` = 0. Playwright with emulateMedia light and no stored theme → `getComputedStyle(body).backgroundColor === 'rgb(11, 18, 32)'`. Press `T` → light bg `rgb(233, 237, 243)`; it persists after reload. |
| T2 | same | Implement B4 stage CSS. Delete the `fit()` function, the `transform` calls and the 1320/800 constants (l.441–442, 492, 494). Restructure every `<section>` into `.s-head` (`.eyebrow` + h1/h2), `.s-body`, optional `.s-foot`, `aside.notes`. Eyebrow text = `NN · SECTION`. | `grep -n 'scale(' index.html` → none. At 1280×720, card height ≥ 82% of `innerHeight` (`cardShare ≥ 82`). |
| T3 | same | Add the B3 type scale and the B5 component CSS (steps, stat, table, callout, code, kbd, chips, os tabs). `button{font:inherit}`. | `getComputedStyle(document.querySelector('#next')).fontFamily` contains `system-ui`. Body `p,li` computed size ≥ 27 px at 1280×720 and ≥ 42 px at 1920×1080. |
| T4 | same | Add the OS tabs JS + CSS (B5). Add the keydown guard. No-JS default = Windows panel visible. | (a) Fresh context with `navigator.platform` "Win32" (Playwright `userAgent` override + `addInitScript` to stub `navigator.platform`) → `html[data-os=win]`. (b) Click "macOS" on #14, go to #20 → the macOS panel is visible. Reload → still mac. (c) `addInitScript(()=>{Storage.prototype.getItem=()=>{throw 1}})` → no console error, default applied. (d) Space with focus on a tab button does not change the counter. |
| T5 | same | Rebuild the 3 SVGs per B7. Remove all `fill="none""`. Use class-based colours. | `grep -c 'fill="none""' index.html` = 0. Each `svg.diagram` has `<title>`. SVG bbox height ≥ 55% of slide height on #4/#9 at 1280×720. |
| T6 | same | Rewrite slide bodies per section C (layouts, content, new titles #7, #11, #12, #18). Add the per-OS content on #12, #14, #15, #18, #20, #30 using exactly the commands in C and D2. | Shared harness: `bad.length===0` (gap ≤ 15%, no overflow, title ≤ 2 lines, counter correct) for all 30 slides × 2 sizes × 2 themes. `document.querySelectorAll('.slide').length===30`. |
| T7 | same | Nav chrome per B8: merge progress + tracker into `#top`, bar layout, eyebrow, past-section ✓, overview/notes/help restyle, help lists `T`. | `#counter` text matches `/^Slide \d{1,2} of 30$/` on every slide (harness). `#top` height ≤ 36 px and `#bar` ≤ 56 px at 1280×720. `?` overlay contains "T". |
| T8 | same | Mobile CSS per B9. | At 390×844 for all 30 slides: `document.documentElement.scrollWidth === innerWidth`. The title's `getBoundingClientRect().top` ≥ `#top` bottom (not covered). `#counter` is visible (`elementFromPoint` at its centre is the counter). Screenshots of #5, #11, #14, #20 saved to `/tmp/claude-1000/` and inspected. |
| T9 | same | `prefers-reduced-motion` keeps the animation off. Contrast: run axe-like checks manually. | Playwright `emulateMedia({reducedMotion:'reduce'})` → `getComputedStyle(slide).animationName === 'none'`. Contrast spot-check script: for each `p,li,td,code,.eyebrow,.callout` on 6 slides, compute the ratio of computed `color` vs the nearest opaque bg; all ≥ 4.5 (≥ 3 for text ≥ 24 px bold). |
| T10 | same | Print CSS per B10. | `page.pdf({width:'13.333in',height:'7.5in'})` → 30 pages (`pdfinfo` reports `Pages: 30`). Visual check of pages 14 and 20 shows all three OS variants with labels and no clipping. |
| T11 | same | Network + PII + JS errors. | Harness `ext.length===0`. `grep -nE '(src|href)="https?:|@import|url\(https?:|fetch\(|XMLHttpRequest' index.html` → none. `page.on('pageerror')` count = 0 over all 30 slides. PII: `JAK_PII_PATTERNS=<private file> python3 tests/test_no_pii.py` passes (file kept outside repo, `tests/test_no_pii.py` docstring). Plus generic: `grep -nP '\b01[3-9][0-9]{8}\b|\+880[0-9]{6,}|\b(?!you@)[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[a-z]{2,}' docs/workshop/{GUIDE.md,example-config.md,slides/index.html}` → only `you@gmail.com`/`you@example.com` placeholders. `grep -n 'github.com/[A-Za-z0-9-]*/job-apply-kit' docs/workshop/` → none (use `<repo-url>`). |
| T12 | `GUIDE.md` | Restructure per D1–D5: Pick-your-OS box, OS tables D2, path table D3, if-it-breaks boxes, figure placeholders D4, glossary split, Node LTS fix, `py -3` everywhere. | `grep -nE '(^|[^y] )python (doctor|install)\.py' GUIDE.md` → none (only `py -3 …` or `python3 …`). `grep -c 'C:\\Users\\<you>' GUIDE.md` ≥ 3. `grep -c 'Node 18' GUIDE.md` = 0. Each of sections 4, 6, 7, 8 contains a line starting `> **If it breaks**`. Every command block in §§4–10 sits under an OS label (manual read). |
| T13 | `example-config.md` | Add a 3-row "Where this file lives" table (Win/mac/Linux) from D3. No other change. | `grep -c '%USERPROFILE%' example-config.md` ≥ 1. |
| T14 | `SLIDES_SPEC.md` | Append a "v3 changes" section listing new titles #7, #11, #12, #18, the layout templates, OS tabs, theme rule (dark default) and the ≤15% gap rule. Do not delete v2 text. | `grep -c 'v3' SLIDES_SPEC.md` ≥ 1. |
| T15 | `opencode/REVIEW.md` (append) | Run the final review checklist below and record Blockers / Majors / Minors with evidence. | The file contains a "v3 review" heading with 0 Blockers and 0 Majors. |

Task order and dependencies: T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 for the deck. T12–T14 can run in parallel after T6, because the GUIDE commands must match the slides. T15 runs last.

### Final review checklist (partner-review style)
- [ ] **Story:** reading only the 30 titles tells the whole case (C title chain). Have a non-technical reader paraphrase it back in 3 sentences.
- [ ] **Titles chain:** each title is a claim, not a topic. Each is 8–14 words, one line at 1280×720 (two balanced lines max), with no jargon in titles.
- [ ] **One message per slide:** the body proves the title; nothing on the slide argues a second point. Detail lives in notes or the GUIDE.
- [ ] **Evidence:** every number (6, ~20–25, 13, 3, 4, 7 days, 15 columns, 61/26/20/4/4/7, 15–30%, 2026-12-31, 7 risks) traces to `PLAN.md`, `GUIDE.md` or `SECURITY_REVIEW.md`. Every OS command traces to a file in D2/D3. Every **(verify)** is either resolved by checking the official source or left visibly marked.
- [ ] **Cross-platform:** each setup slide (#12, #14, #15, #18, #20, #30) shows Windows, macOS and Linux. Windows shows both PowerShell (installs) and Git Bash (kit commands). `py -3` is used, never bare `python`.
- [ ] **Beginner test:** a Windows user who has never used Git Bash can follow GUIDE §§0–10 without asking. Dry-run it with one such person if possible.
- [ ] **Layout:** harness `bad` empty; mobile and print checks pass; screenshots eyeballed at 1280×720 dark and light.
- [ ] **Safety and privacy:** no PII; no network loads; never-submit rule on #3, #27, #29 and in the GUIDE's top box.
- [ ] **Ask:** slide #30 ends with one concrete next action (check setup → run FB saved → review, then send) plus Q&A.

---

## F. Risks and open questions (with the decision taken)

| # | Question / risk | Decision (default) |
|---|---|---|
| F1 | Container query units (`cqh`) need Chrome 105+, Safari 16+, Firefox 110+. | Accept. Keep the `@supports not` px fallback (B4). Workshop laptops in 2026 are well above these versions. |
| F2 | Dark default vs a presenter's light OS (the light theme was auto-applied before, which is the "pale" complaint). | Always start dark. Light only by explicit choice (`T` key or `?theme=light`, stored in `jak-theme`). No `prefers-color-scheme` auto-switch. Print forces light tokens. |
| F3 | Per-section colour accents requested vs colour discipline. | One accent. Sections are cued by the numbered eyebrow + tracker (B1.4). |
| F4 | The Git for Windows winget id (`Git.Git`) and macOS/Linux git, pandoc and Claude Code install lines are not in repo docs. | Show them marked **(verify)** in the GUIDE. On slides, show only the Windows `Git.Git` line, with "(verify)" in the notes. The implementer verifies against the official winget/vendor pages before the workshop and, if confirmed, adds them to `docs/BOOTSTRAP.md` in a separate change. |
| F5 | The real repo URL identifies the author. | Use `<repo-url>` in all files. The presenter writes the URL on the board or chat live. |
| F6 | `docs/help/01-prerequisites.md` says "`py -3` (or `python`)" and `BOOTSTRAP.md` §0 says `python doctor.py`, which conflicts with `OPERATIONS.md` l.28 (never bare `python` on Windows). | Workshop material follows `OPERATIONS.md` (`py -3`). Log the doc inconsistency in REVIEW.md as a follow-up and do not edit the help docs in this task. |
| F7 | `01-prerequisites.md` claims `curl` works "as written" in PowerShell; `BOOTSTRAP.md` §3 says `curl.exe`. | Use `curl.exe` for PowerShell, and plain `curl` in Git Bash, macOS and Linux. |
| F8 | Linux shortcut name in code (`jak-chrome-debug.desktop`) differs from the docs ("JAK <label> (debug)"). | Slides and GUIDE follow the code (`browser_setup.py` l.219). Log it as a docs follow-up. |
| F9 | Node: "18+" (README, 01-prereq) vs "latest LTS via nvm" (BOOTSTRAP §2.2). | Teach "latest LTS via nvm". Mention winget `OpenJS.NodeJS.LTS` (01-prereq) only as a fallback in the GUIDE "If it breaks" box. |
| F10 | Three OS panels can overflow print or small screens. | Print uses smaller code (B10). On screen only one panel is visible. Keep each panel to ≤ 5 lines and move the full lists to the GUIDE. |
| F11 | `Space`/`Enter` on OS tab buttons conflict with slide navigation. | Guard in the keydown handler (B5). Tabs are mouse/touch-first, and arrow keys still navigate slides. |
| F12 | Emoji/glyph rendering differs per OS (🐧, ⊞, ⏳). | Glyphs are decorative and always paired with text. If a glyph renders as tofu on Windows in testing, drop it. |
| F13 | Screenshots for the GUIDE (S-1…S-8) may leak account names. | Take them in a fresh test Google account or blur names. Never commit before the PII test (T11) passes. If none are ready, ship the placeholders. |
| F14 | The "~2 hours first setup" estimate is not in the repo. | Label it "estimate" in GUIDE §3, or omit it if the presenter disagrees. Do not put it on slides. |
| F15 | `slides/index.v1.html` is still present. | Leave it untouched (out of scope). Do not link it from the new deck. |
