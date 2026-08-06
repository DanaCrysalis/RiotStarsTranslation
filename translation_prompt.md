# Riot Stars — Translation Prompt

Paste this at the top of a translation session, then paste `glossary.md`, then paste the chunk(s)
listed for that session below it.

---

## ROLE

You are translating the Japanese script of **Riot Stars** (Hect, PS1, SLPS-00829, 1997) into
English for a fan translation patch. The output is not prose for a reader — it is a **byte-exact
replacement for a line in a tokenised script dump** that will be reinserted into the game binary by
`riotscript.py` / `riotbattle.py`. A translation that reads beautifully but breaks the tag stream or
overflows its slot is worthless.

The order of requirements is:

1. **Fits the byte budget.** A chunk that overflows will not build.
2. **Format correctness.** Tags, charset, column and row limits.
3. **Translation quality.**

Requirement 1 is new to this revision and it is not a formality. The first chunk translated came in
at **9,433 bytes against an 8,192-byte slot** on the first pass and had to be cut by 16%. Assume
this will happen to you. Budget first, then write.

---

## 0. SESSION WORKFLOW — HOW MUCH TO DO AT ONCE

### 0.1 The two script stores

| File | Tool | Unit of work | Constraint |
|---|---|---|---|
| `SCRIPT.BIN` (main script, 44 banks) | `riotscript.py` | a slice of `script_unique.txt` | effectively unconstrained (69% free) **except bank 41 (353 bytes)** |
| `TACTICS/HEXMAP.BIN` (battle script, 44 chunks) | `riotbattle.py` | **one or more whole chunks of `battle_dump.txt`** | hard 8,192-byte slot per chunk (chunk 43: see §0.4) |

For the main script, take **40–60 lines of `script_unique.txt` per session**, highest count first;
the dedupe means each line translated once propagates up to 126 times.

For the battle script, work in **whole chunks**, never partial ones, because the byte budget is
per-chunk and cannot be checked on a fragment.

### 0.2 Budget ratio — the number that decides everything

For a battle chunk:

```
tag_bytes      = (8192 − headroom) − 2 × japanese_char_count
english_budget = (8192 − tag_bytes) ÷ 2          # characters, not bytes
budget_ratio   = english_budget ÷ japanese_char_count
```

`headroom` is printed in the `=== CHUNK n` header. Japanese character count is the dump line with
all `{...}` stripped.

Measured reality from chunk 0: a first, natural, literal draft runs about **2.1×** the Japanese
character count. A disciplined draft — contractions (`don’t`, `it’s`, `I’ll`), no filler, merged
short lines — runs about **1.7×**. So:

| Budget ratio | Verdict |
|---|---|
| **≥ 2.5** | comfortable, translate literally without thinking about bytes |
| **1.7 – 2.5** | write tight from the first draft; expect one re-cut pass |
| **1.5 – 1.7** | terse from the start, contractions mandatory, expect two passes |
| **< 1.5** | **probably infeasible.** Flag it, do not quietly mangle the script |

**Above about 4.0 the byte budget stops mattering and the box geometry takes over.** The tier E
session (chunks 10, 11, 12, 14, 34, 35, 40 — ratios 8.4 to 77.9) landed with 6,000–7,900 bytes of
slack in every chunk and never once had to cut for bytes. Every single compromise in that session
was forced by **24 columns × 4 rows**, not by the slot. So at a high ratio, do not relax: draft
straight to the geometry, check columns per segment as you write, and spend the free bytes on
`{FFFE}` breaks rather than on longer words. See §3.2.

### 0.3 Chunk schedule

**44** chunks carry dialogue, 43,161 Japanese characters total. **9 chunks are done — 0, 33 and
the whole of tier E — 4,365 characters; 35 chunks and 38,796 characters remain.** Chunk 43 is
translated but cannot ship until the slot is widened (§0.4), so it is not counted as done. Work in
numeric order within a tier so character voices stay adjacent.

**Chunk 33 was invisible until 2026-08-05.** `find_script_bounds` keyed on `{FC51}` alone and
chunk 33 opens every message with `{FC50}`, so it never reached the dump. The detector now accepts
either marker (`findings.md` §23). If a chunk count anywhere in this document disagrees with
`assemble.py status`, trust `status`.

| Tier | Ratio | Chunks | Per session | Sessions |
|---|---|---|---|---|
| **A** | < 1.6 | ~~43~~ ⚠️, 5, 16, 32 | 1 | 3 |
| **B** | 1.6 – 2.5 | ~~0~~ ✅, 7, 8, 19, 30 | 1 | 4 |
| **C** | 2.5 – 4.0 | 2, 6, 13, 17, 23, 24, 25, 26, 31, 36, 37, 38 | 2 | 6 |
| **D** | 4.0 – 6.5 | 1, 3, 4, 9, 15, 18, 20, 21, 22, 27, 28, 29, 39, 41, 42 | 3–4 | 5 |
| **E** | > 6.5 | ~~10, 11, 12, 14, 34, 35, 40, 33~~ ✅ | all 7 | ~~1~~ 0 |

**18 sessions remaining.** Tier E went in a single session as scheduled and confirmed the batching
assumption: at ratios above 6.5, seven chunks is a comfortable session, and the limiting factor is
how many distinct character voices you have to hold at once, not volume. Per-chunk figures:

| Chunk | JP chars | Headroom | Ratio | | Chunk | JP chars | Headroom | Ratio |
|---|---|---|---|---|---|---|---|---|
| **43** | **2357** | **1071** | **1.23** ⚠️ | | 25 | 1039 | 5161 | 3.48 |
| 5 | 2132 | 2241 | 1.53 | | 36 | 986 | 5765 | 3.92 |
| 32 | 2116 | 2593 | 1.61 | | 37 | 985 | 5299 | 3.69 |
| 16 | 2100 | 2467 | 1.59 | | 3 | 870 | 5617 | 4.23 |
| **0** | **1914** | **2827** | **1.74** ✅ | | 21 | 863 | 5663 | 4.28 |
| 19 | 1745 | 3269 | 1.94 | | 22 | 799 | 5731 | 4.59 |
| 7 | 1598 | 3433 | 2.07 | | 28 | 772 | 5807 | 4.76 |
| 8 | 1471 | 3873 | 2.32 | | 9 | 760 | 5975 | 4.93 |
| 30 | 1358 | 3897 | 2.43 | | 4 | 734 | 5995 | 5.08 |
| 23 | 1258 | 4521 | 2.80 | | 20 | 732 | 5493 | 4.75 |
| 24 | 1210 | 4819 | 2.99 | | 1 | 719 | 6151 | 5.28 |
| 6 | 1165 | 4877 | 3.09 | | 42 | 698 | 6225 | 5.46 |
| 17 | 1144 | 5005 | 3.19 | | 27 | 677 | 6145 | 5.54 |
| 2 | 1140 | 4911 | 3.15 | | 39 | 623 | 6479 | 6.20 |
| 13 | 1092 | 5269 | 3.41 | | 15 | 621 | 6373 | 6.13 |
| 26 | 1085 | 5115 | 3.36 | | 29 | 612 | 6163 | 6.03 |
| 38 | 1080 | 5115 | 3.37 | | 18 | 611 | 6453 | 6.28 |
| 31 | 1051 | 5177 | 3.46 | | 41 | 593 | 6565 | 6.53 |
| **10** | **463** | **6847** | **8.39** ✅ | | **12** | **453** | **6783** | **8.49** ✅ |
| **14** | **418** | **6941** | **9.30** ✅ | | **34** | **313** | **7257** | **12.59** ✅ |
| **11** | **295** | **7273** | **13.33** ✅ | | **35** | **59** | **7779** | **66.92** ✅ |
| **40** | **52** | **8001** | **77.92** ✅ | | **33** | **398** | **6779** | **9.52** ✅ |

Shipped sizes, for calibration: chunk 10 — 2,159 / 8,192. 11 — 1,567. 12 — 2,405. 14 — 2,203.
34 — 1,591. 35 — 557. 40 — 313. 33 — 2,151.

### 0.4 Chunk 43 — spike done, verdict: infeasible in 8,192 bytes

The spike ran on 2026-08-05. The answer is **repoint**, and the abridgement option is off the table.

- A faithful translation is **11,181 bytes** — 2,989 over. Every other rule passes.
- An abridgement that already deletes 13 sentences reaches only **8,941 bytes**, still 749 over,
  at a ratio of 1.41. Closing that gap means deleting speaker turns, which §2.1 forbids.
- Both files are parked in `pending/`, which deliberately does not match `chunk_NNN.txt`, so the
  patch stays buildable and chapter 43 falls through to Japanese.

The engine fix is specified in **`pending/slot-extension.md`** and traced in `findings.md` §23:
chunk 43's slot moves down to `chunk+0x23000`, giving 16,384 bytes. It needs eleven patched words
in `KOUSEI.EXE` — a per-map conditional on the read, **and a relocation of the 8,192-byte RAM
script buffer at `0x80154F40`**, which has only 12 bytes of clearance above it. Do not apply the
disc-side change on its own.

Once the slot exists, `git mv pending/chunk_043.txt tl/battle/chunk_043.txt` and teach
`riotbattle.py` the per-chunk `SCRIPT_LO`/`SCRIPT_SLOT`.

### 0.5 Where the output goes — the patch must be buildable at any moment

Translation is spread over ~20 sessions, so the project is laid out so that **whatever is finished
can be assembled and tested immediately**. Untranslated chunks and lines fall through to the
original Japanese; the game is always playable.

```
riot-tl/
  original/    SCRIPT.BIN  HEXMAP.BIN              pristine, never modified
  dumps/       script_dump.txt  battle_dump.txt    pristine dumps (regenerate: assemble.py refresh)
               script_unique.txt  battle_unique.txt
  tl/battle/   chunk_000.txt … chunk_043.txt       ONE FILE PER BATTLE CHUNK
  tl/script/   batch_001.tsv, batch_002.tsv …      main-script translations, JP→EN pairs
  build/                                           everything assemble.py writes
  tools/       assemble.py riotscript.py riotbattle.py riotfont.py savetool.py
  translation_prompt.md  glossary.md
```

**Battle output — `tl/battle/chunk_NNN.txt`.** One file per chunk, three digits, zero padded. The
file is that chunk exactly as it appears in `battle_dump.txt`: the `=== CHUNK n @ …` header line,
then every body line in the same order and the same count, then `{PAD n}`. Only readable text
differs. The header may be omitted, but the filename number then has to be right, so keep it.

**Script output — `tl/script/batch_NNN.tsv`.** Tab-separated, one line per unique message:

```
<count>	<japanese source message>	<english replacement>
```

The count column is optional and ignored — it is there because it is already in
`script_unique.txt` and pasting it back is easier than stripping it. The Japanese column is the
**lookup key**, so it must be copied byte-for-byte from `script_unique.txt`, tags and all. This is
what makes propagation work: one translated line replaces every one of its up-to-126 occurrences.
Lines starting with `#` are comments.

Never edit `dumps/` by hand and never hand-edit anything in `build/` — both are regenerated.

### 0.6 Assembling and testing

```
python3 tools/assemble.py status     progress, byte headroom per finished chunk
python3 tools/assemble.py check      validate everything translated so far, build nothing
python3 tools/assemble.py merge      write build/{script,battle}_dump_merged.txt
python3 tools/assemble.py build      merge, then reinsert into build/SCRIPT.BIN and build/HEXMAP.BIN
python3 tools/assemble.py all        check + build + riotbattle checkedit
python3 tools/assemble.py refresh    re-dump from original/ (only after changing the originals)
```

`merge` splices each finished chunk into the pristine dump and leaves everything else untouched, so
`build` always produces a complete, valid pair of binaries. It refuses to write if any chunk is
over its slot, any tag stream has changed, or any illegal character is present.

`assemble.py check` **is** the self-check in §7. Run it before emitting a batch, not after.

**If the session does not have the repo** — only the dumps, `riotbattle.py` and these two documents
were pasted in, which has now happened once — do not answer §7 from memory. Reimplement the checks
against `riotbattle.bytes_from_body` (byte budget, tag parity, charset, 24-column runs with
`{FC00}` counted as 7, 4-row pages, line-count and `{PAD}` identity), plant a deliberate violation
to prove the checker fails when it should, and **flag in the output that the real `assemble.py
check` still has to be run before merging.** A stand-in checker is evidence, not clearance.

### 0.7 Per-session procedure

1. Read `glossary.md`. Do not invent a form that is already fixed there.
2. Compute the budget for each chunk in the batch **before writing anything**.
3. Draft, at the tightness §0.2 prescribes for that ratio.
4. Save to `tl/battle/chunk_NNN.txt` or `tl/script/batch_NNN.tsv` and run
   `python3 tools/assemble.py check`. Do not eyeball column counts.
5. If over budget, cut and re-verify. Report the final byte figure and slack in FLAGS.
6. Emit the three sections of §6. Append new glossary entries to `glossary.md` before the next
   session.
7. `python3 tools/assemble.py build` and play the result. A chunk that reads well in a text editor
   and badly on a 24×4 box is a common and cheap mistake to catch.

---

## 1. INPUT FORMAT

Each line is one message: readable Japanese interleaved with tags in braces.

```
{FB00}{=01}{=76}{=00}{=00}{FCB0}{=00}{=00}{=00}{=01}{FC51}よくいらっしゃった！{FFFE}宮廷軍の方たちですな。{FC30}{FFFF}
```

**Tag types — all are opaque binary. Never invent, delete, reorder, or reformat one.**

| Tag | Meaning |
|---|---|
| `{XXXX}` | a 2-byte engine control code |
| `{=HH}` / `{=HHHH…}` | raw argument bytes (note: `riotscript` splits these per byte, `riotbattle` coalesces runs — copy whatever form the source line uses) |
| `{HDR:…}` | bank header blob — never touch |
| `{PAD n}` / `{PRE n}` | free-space bookkeeping — never touch |
| `=== BANK n` / `=== CHUNK n` | structural headers — never touch |
| `#` lines | comments |

`{PAD n}` will be wrong after you translate — reproduce it verbatim anyway. `insert` ignores the
value and re-pads to the slot; re-dump afterwards to refresh it.

### Control codes you must reason about

| Code | Meaning | Rule |
|---|---|---|
| `{FFFE}` | **hard line break** | The engine has **no word wrap**. Every break is authored. You may move, add, or delete these to re-flow English. Each one costs 2 bytes. |
| `{FCC0}` | **page break** — clears the box | You may add one when English overruns the visible rows. |
| `{FC30}` | end of text, wait for input | Keep. Do not add. |
| `{FFFF}` | end of message | Keep, keep it last. |
| `{FC51}` / `{FC50}` | speaker channel (two portrait slots) | Marks who is talking. A `{FC50}`↔`{FC51}` alternation is a back-and-forth conversation — use it to keep voices straight. Note that a third party can borrow a channel mid-scene (chunk 0: Rendol speaks on Rimul's `{FC51}`). |
| `{FB00}{=..}{=..}{=..}{=..}` | set portrait / speaker id | Keep verbatim. |
| `{FB01}`, `{FFFD}`, `{FCB0}`, `{FFF8}`, `{FCA7}`, `{FCB6}`… | timing, flags, event triggers | Keep verbatim, in place. |

**The `{FCC0}{FFFE}` pattern.** Most battle pages open with a break immediately after the page
clear, which appears to leave a blank top row. Preserve it exactly; do not "tidy" it. If an in-game
check ever proves the row is wasted, deleting those breaks frees ~2 bytes each and one row per page
— but that is a project-wide decision, not a per-line one.

### Runtime variable inserts — these are words in the sentence

| Tag | Substitutes |
|---|---|
| `{FC00}{=0000}` | the player's chosen name (≤ 7 characters — budget for 7) |
| `{FFEC}{=00}{=03}` | an item name (shop dialogue) |
| `{FFEC}{=00}{=01}` | a number / price |
| `{FFDA}{=00}{=xx}` | "you received item xx" event |

English word order will often not match. **You may move an insert tag within its own sentence** to
put it where English wants it. You may not duplicate or drop it. If a sentence is only grammatical
in Japanese because of the insert's position (`{FFEC}ジュエルになるが、いいノロか？`), restructure
the English around it rather than leaving a stranded fragment.

---

## 2. TRANSLATION POLICY — LITERAL, THEN TIGHT

**Default: translate literally.** Preserve sentence order, clause order, register, and the speaker's
manner. Do not smooth, do not condense for taste, do not "improve", do not add explanation the
Japanese does not contain, do not localise idioms into unrelated English idioms.

**Depart from literal only when** the literal rendering is not correct English, or when the byte
budget forces it:

- Japanese ellipsis of subjects/objects that English requires → supply the pronoun.
- Politeness levels with no English lexical equivalent (です/ます, ですな, ぞ, のう) → carry in
  **register and word choice**, not in added words. `歓迎しますぞ！` → `You are most welcome！`,
  not `We heartily welcome you to our fine city！`
- Constructions that are ungrammatical if traced word-for-word (〜てしまう, 〜ておく, double
  negatives, topic-comment inversions).
- Onomatopoeia and grunts with no English form (`ムムッ`, `ふっ`) → the fixed equivalent in the
  glossary.

### 2.1 Compression, in the order you should reach for it

When a chunk is over budget, cut in this order. Stop as soon as you fit.

1. **Contractions.** `don’t`, `it’s`, `I’ll`, `we’ve`, `can’t`, `that’s`. Costs nothing in meaning,
   saves 1 character each, and often suits the register better than the expanded form.
2. **Merge short lines**, deleting the `{FFFE}` between them. 2 bytes each, and the 24-column box
   holds roughly two of the original 12-column lines.
3. **Drop redundant glosses** the Japanese carries for its own reasons — `待ち時間（Ｗａｉｔ）`
   needs only `Ｗａｉｔ　ｔｉｍｅ`.
4. **Shorter synonym for a long word**, where the register survives: `aid` for `reinforcements`.
5. **Implication instead of statement**, for a stated-but-obvious element: `hand it in` for
   `hand it to our superior officer`. **Flag every one of these.**
6. **Reorder clauses** so the English fits the columns. Flag it.

Never cut by deleting a sentence, a speaker turn, or a plot fact. If only that would work, the
chunk is infeasible — say so.

### 2.2 Voice

**Voice must stay consistent per character**, across chunks and across sessions. That is what
`glossary.md` is for. Two things depend on it:

- **Verbal tics.** The hobbit shopkeeper ends nearly every sentence with `ノロ`; the frog merchant
  says `ゲロゲロ` and speaks in clipped katakana. These are characterisation, not noise. Each has
  **one fixed English treatment**, recorded in the glossary. Never mix treatments.
- **Duplicated lines.** `script_unique.txt` shows 82% duplication — the same message appears up to
  126 times. Identical Japanese must get **byte-identical English** every time, or the propagation
  step breaks. (The battle script is ~1% duplicated, so this bites mainly on the main script — but
  stock phrases like `命拾いしたな` recur across chunks and must match.)

---

## 3. HARD FORMAT CONSTRAINTS

### 3.1 Character set — full-width Latin only

English text must be written using **full-width Unicode characters**, not ASCII. The font hook maps
the full-width SJIS codes to custom 8-pixel glyphs; ASCII bytes are not mapped and will not render.

**Permitted characters — nothing outside this set:**

```
Ａ-Ｚ  (U+FF21-FF3A)      ａ-ｚ  (U+FF41-FF5A)      ０-９  (U+FF10-FF19)
　 (U+3000 space)
、 。 ， ． ： ； ？ ！ ー ‐ ／ 〜 ‘ ’ “ ” （ ） ＋ − ＝ ％ ＆ ＊ ＠
```

Consequences to internalise:

- Apostrophes are **’** (U+2019), never `'`. `don’t`, `Rimul’s`.
- Quotes are **“ ”** (U+201C/U+201D). Japanese `『…』` → `“…”`.
- Comma is **，** and full stop is **．** (the full-width forms).
- **There is no ellipsis character and no `・`.** Japanese `・・・` becomes **．．．** (three
  full-width stops). **Match the source's dot count exactly** — `・・・・・` is five, `・・・。`
  is four. Japanese `〜` may stay as `〜`.
- **No `○`, `□`, `△`, `×`.** Button prompts become `Ｃｉｒｃｌｅ　ｂｕｔｔｏｎ`,
  `Ｓｑｕａｒｅ　ｂｕｔｔｏｎ`, etc.
- No `#`, `$`, `"`, `'`, `-`(ASCII), `[`, `]`, `<`, `>`, `|`, `_`. Use `‐` for a hyphen.

### 3.2 Line and page geometry

The battle box (KOUSEI.EXE) has been widened to **24 columns × 4 visible rows**.

- **≤ 24 characters between `{FFFE}` breaks.** Count characters, not bytes; every permitted
  character above counts as 1 column. A `{FC00}` name insert counts as **7**.
- **≤ 4 lines per page** — i.e. at most three `{FFFE}` between `{FCC0}`/`{FC51}`/`{FC30}`
  boundaries. If English needs a fifth line, insert a `{FCC0}` page break.
- **Break at word boundaries.** The engine's own wrap is a character wrap and would split words.
- Prefer breaking at clause boundaries so the line reads naturally on its own.
- Do not leave a line ending in a lone one- or two-letter word if it can be avoided.
- **Aim for ≤ 23, not ≤ 24.** 24 is the hard limit and a line at exactly 24 has no room for a later
  one-character fix — a changed name, an added apostrophe — without a re-flow. Tier E was written
  to 23 throughout and the longest run shipped was 23.
- **Count as you draft, not afterwards.** A 12-column Japanese segment usually lands between 15 and
  23 English columns, so the source's own break structure is close to right for a 24-column box and
  should normally be preserved segment for segment. Reach for a merge only where the Japanese was
  split mid-clause for the old 12-column box; reach for an added break where one English clause
  will not fit, which is cheap (2 bytes) at any ratio above about 2.5.
- **Four rows is the wall.** When four rows of 23 will not hold the page, add a `{FCC0}` rather than
  cutting sense — but check first whether the page already ends with an empty segment
  (`…{FFFE}{FC30}`), because a page with a leading blank *and* a trailing blank plus four text rows
  is the one shape that has never appeared in the source and may not fit. Prefer three text rows in
  that case.

The main script (SCRIPT.BIN, MAIN1.EXE side) has **not yet been widened**. Until it is, translate to
the same 24-column target and flag the file as pending; `riotfont.py rewrap` can re-flow later.
**Unknown:** whether the class/unit description window is 3 or 4 rows. Until confirmed, keep
description entries to 2 text lines plus the `Ｇｅｍ　Ｔｙｐｅ` line and flag any that need more.

### 3.3 Byte budget

Every permitted character is **2 bytes** in Shift-JIS. `{XXXX}` tags cost 2 bytes; `{=HH…}` costs
half its hex digits.

- **SCRIPT.BIN**: 69% free space, ~14–40 KB slack per bank. Effectively unconstrained. **Exception:
  bank 41 has 353 bytes free** — if you are handed bank 41, translate tightly and flag it.
- **HEXMAP.BIN (battle)**: 8,192-byte fixed slot per chunk. The inserter hard-fails on overflow, and
  a chunk that overflows would push the unit table at `+0x27000` and black-screen the map. Compute
  the budget per §0.2 before drafting and verify per Appendix A before emitting.
- Aim to land with **≥ 50 bytes of slack** where the ratio allows it, so a later typo fix does not
  force a full re-cut. Chunk 0 shipped with 29 and that is uncomfortably close.

---

## 4. GLOSSARY PROTOCOL

The glossary lives in **`glossary.md`**, not in this file. Paste it into every session.

Rules:

1. **Check the glossary before rendering any name.** If it is there, use that form exactly.
2. **If it is not there, add it** — with the Japanese, the chosen English, and a one-line reason
   (romanisation choice, meaning, fixed-width cap, etc.).
3. **Never silently change an existing entry.** If a later line proves an earlier choice wrong
   (a character turns out to be female, a "place" turns out to be a person), say so explicitly,
   give the corrected entry, and list every previously-translated line that needs revisiting.
4. **Names of ambiguous katakana**: prefer the reading the source most plausibly intended
   (`カイン` → `Kain` or `Cain`; `ドースン` → `Dawson`), pick one, and note the alternative.
5. **Length caps.** Some names live in fixed-width tables: unit names ≤ 16 half-width chars, class
   names and monster names ≤ 20, the player name ≤ 7. If a glossary entry is destined for one of
   those tables, note the cap and keep the entry within it.
6. **Entries in the PROVISIONAL section are not decisions.** Promote one to the main table the first
   time you actually render it, and say so.
7. **Output the new/changed glossary entries at the end of every response**, even if empty, and
   append them to `glossary.md` before the next session.

---

## 5. WORKED EXAMPLES

**Source**
```
{FCA7}{=0000FA1100000000}{FCB0}{=00040001}{FC51}探せっ！{FFFE}このあたりに{FFFE}逃げ込んだはずだ！{FFFE}{FC30}
```
**Correct**
```
{FCA7}{=0000FA1100000000}{FCB0}{=00040001}{FC51}Ｓｅａｒｃｈ！{FFFE}Ｔｈｅｙ　ｍｕｓｔ　ｂｅ　ｎｅａｒｂｙ！{FFFE}{FC30}
```
Two Japanese lines merged into one English line because the first was split mid-sentence to fit the
old 12-column box; `探せっ！` keeps its own line because that break was deliberate. The trailing
empty `{FFFE}` before `{FC30}` is preserved — it was in the source. One `{FFFE}` deleted, 2 bytes
recovered.

**Source**
```
{FC51}{FFFD}{FC00}{=0000}です。{FFFE}{FC30}
```
**Correct**
```
{FC51}{FFFD}Ｉ’ｍ　{FC00}{=0000}．{FFFE}{FC30}
```
The name insert moves to the end because English puts the copula first. Tag count unchanged.

**Source**
```
{FC50}{FFFD}いいか、{FFFE}私が戻るまで{FFFE}持ち場を　離れるなよ！{FFFE}{FCC0}敵を前にしての　逃亡は{FFFE}死罪だからな！！{FFFE}わかったなっ！！{FFFE}{FC30}
```
**Correct**
```
{FC50}{FFFD}Ｌｉｓｔｅｎ，{FFFE}Ｄｏｎ’ｔ　ｌｅａｖｅ　ｙｏｕｒ　ｐｏｓｔ{FFFE}ｕｎｔｉｌ　Ｉ　ｒｅｔｕｒｎ！{FFFE}{FCC0}Ｆｌｉｇｈｔ　ｂｅｆｏｒｅ　ｔｈｅ　ｅｎｅｍｙ{FFFE}ｍｅａｎｓ　ｄｅａｔｈ！！{FFFE}Ｇｏｔ　ｔｈａｔ！！{FFFE}{FC30}
```
Structure identical, page break preserved, `死罪` rendered as the short `means death` rather than
`is punished by the death penalty` — 9 characters saved with no loss of sense.

**Source** (chunk 14 — a name insert costs 7 columns)
```
{FC50}第９軍の{FC00}{=0000}{FFFE}隊長ですね？{FC30}
```
**Correct**
```
{FC50}Ｃａｐｔａｉｎ　{FC00}{=0000}　ｏｆ　ｔｈｅ{FFFE}９ｔｈ　Ａｒｍｙ，　ａｒｅ　ｙｏｕ　ｎｏｔ？{FC30}
```
The insert moves inside the first line and the break falls in a different place, because
`Ｃａｐｔａｉｎ　{FC00}　ｏｆ　ｔｈｅ` is 22 columns with the insert counted as 7 and
`Ｃｏｍｍａｎｄｅｒ` would make it 24. Tag count unchanged; `９` stays full-width.

**Source** (chunk 10 — a tic under punctuation that is not its own)
```
{FC51}沼ヲオカス者、{FFFE}許サナイ、ゲロゲロ！{FFFE}
```
**Correct**
```
{FC51}Ｄｅｆｉｌｅｒｓ　ｏｆ　ｓｗａｍｐ　ａｒｅ{FFFE}ｎｏｔ　ｆｏｒｇｉｖｅｎ．　Ｒｉｂｂｉｔ！{FFFE}
```
The glossary fixes the tic as `Ｒｉｂｂｉｔ．`, but what is fixed is the **word**; the punctuation
follows the source, so `！` here. Articles are dropped throughout because that is this speaker's
registered katakana manner — the two rules compose, they do not compete.

**Source** (chunk 34 — two near-identical lines that must stay distinguishable)
```
{FC50}{FFFD}どうする、兄弟？{FC30}{FCB0}{=00080001}{FC51}{FFFD}どうしよう、兄弟？{FC30}
```
**Correct**
```
{FC50}{FFFD}Ｗｈａｔ　ｄｏ　ｗｅ　ｄｏ，　ｂｒｏｔｈｅｒ？{FC30}{FCB0}{=00080001}{FC51}{FFFD}Ｗｈａｔ　ｓｈｏｕｌｄ　ｗｅ　ｄｏ，{FFFE}ｂｒｏｔｈｅｒ？{FC30}
```
One `{FFFE}` added, because the second line is 27 columns and collapsing the two to the same
English would destroy the joke — the pair are meant to echo each other imperfectly. Adding a break
to preserve a distinction is always cheaper than flattening it.

**Wrong, and why**
```
{FC51}Search!{FFFE}They must be close by!{FC30}
```
ASCII characters (will not render), ASCII `!` (not mapped), and `{FFFE}` deleted before `{FC30}`
(changes the byte stream against the source without reason).

---

## 6. OUTPUT FORMAT

For each batch, respond with exactly:

1. **The translated lines**, in a fenced code block, one per line, in the same order as the input,
   with all non-text lines (`===`, `#`, `{PAD}`, `{HDR:}`) reproduced unchanged. State the target
   path above the block — `tl/battle/chunk_019.txt`, `tl/script/batch_002.tsv` — and emit one block
   per file so each can be saved directly with no editing. Battle chunks keep their
   `=== CHUNK n @ …` header; script batches use the `count⇥japanese⇥english` TSV form of §0.5.
2. **`GLOSSARY ADDITIONS`** — a table of new or corrected entries. Write `(none)` if empty.
3. **`FLAGS`** — a numbered list of anything the next human should look at. The first flag on a
   battle chunk is always **the byte figure**: `chunk N: 8,163 / 8,192 — 29 bytes slack`. Then:
   - lines where literal English was impossible and you deviated (§2.1 steps 5 and 6)
   - `{FFFE}` counts changed, per line, with the before → after figures
   - ambiguous referents, unclear speakers, unknown antecedents
   - katakana names with more than one defensible reading
   - lines that needed an added `{FCC0}`
   - any line still over 24 columns after your best effort
   - any tag whose meaning you had to guess in order to place text around it
   - suspected typos in the Japanese source

No commentary outside these three sections.

---

## 7. SELF-CHECK BEFORE SENDING

Run `python3 tools/assemble.py check`. Do not answer these from memory.

- [ ] **Total bytes ≤ 8,192 per battle chunk**, with the figure stated in FLAGS.
- [ ] Every tag from the source appears in the output, same count, same spelling, same order —
      except `{FFFE}`/`{FCC0}` I deliberately re-flowed, and inserts I deliberately repositioned.
- [ ] No ASCII letters, digits, or punctuation anywhere in translated text.
- [ ] No character outside the permitted set (§3.1). No `…`, no `・`, no `○`, no `'`, no `"`.
- [ ] No segment between `{FFFE}` exceeds 24 columns (name inserts counted as 7).
- [ ] No page exceeds 4 lines.
- [ ] Ellipsis dot counts match the source.
- [ ] Every proper noun matches `glossary.md` exactly.
- [ ] Identical source lines produced identical output lines — **grep the output for each repeated
      string and count the hits**, do not trust that you pasted it the same way twice. Repeats
      cross chunk boundaries: `よし、次はコーカサスだ` occurs four times across chunks 10 and 11.
- [ ] Menu options keep their leading full-width space (`　許してやる` → `　Ｓｐａｒｅ　ｈｅｒ`).
      That space is the cursor gutter, not padding.
- [ ] Any new name checked against `script_unique.txt` as well as the battle dump — a character's
      later role often fixes the reading, and several battle-script names reappear as shopkeepers.
- [ ] `{FFFF}` is still the last token on every message line.
- [ ] `{PAD n}` / `{HDR:}` / `===` lines are byte-identical to input.
- [ ] `assemble.py check` passes.
- [ ] `assemble.py build` completes and `riotbattle.py checkedit` reports only the intended chunks.

---

## APPENDIX A — the verifier

The standalone checker has been folded into `tools/assemble.py`, so there is one implementation
rather than two that can drift. `assemble.py check` performs, for every translated file:

- **byte budget** — battle chunks against the 8,192-byte slot, script banks against 0xA000;
- **tag parity** — every tag except `{FFFE}` present, same order, same spelling, and the same
  number of lines as the original chunk;
- **charset** — nothing outside §3.1 (Japanese still tolerated in the main script, which is
  translated line-by-line rather than chunk-by-chunk);
- **columns** — no run between breaks over 24, counting a `{FC00}` name insert as 7;
- **rows** — pages over four lines are reported as warnings, since the leading break after
  `{FCC0}` makes the true count ambiguous until it is checked in-game.

`merge` re-runs all of it and refuses to write on any hard error, so a broken batch cannot reach a
build by accident.
