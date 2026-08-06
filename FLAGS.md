# FLAGS.md — open issues carried forward

Everything here needs a human decision, a tool fix, or an in-game look. Nothing here is
resolved by translating more chunks. Items are grouped by what blocks them.

Session of 2026-08-06 delivered `tl/battle/chunk_007.txt` (7,793 / 8,192, 399 slack) and
parked `pending/chunk_005.txt` (8,679 / 8,192, 487 over).

Second session of 2026-08-06 delivered `tl/script/batch_002.tsv` (script lines 1234 and 8604).
**`check` reports PROBLEMS (0) and `build` writes output for the first time in the project.**
§A1, §A2 and §A3 are resolved below; §C1 is partly resolved; §D4, §D5, §C4 and §C5 are new.

Third session of 2026-08-06 delivered `tl/script/batch_003.tsv` (the 102-entry description table,
**14.6% → 41.6% of message instances**), re-flowed `batch_001`, fixed §C4 and the carried-over
`chunk_035` edit. `check` still reports **PROBLEMS (0)** and `build` still writes both dumps.
**§C4 and §E's `ほう` line are resolved; §F is new and §F2 is the most important thing here.**

---

## A. Blocking the build right now

### A1. ~~`build` refuses to write~~ — RESOLVED 2026-08-06

`python3 tools/assemble.py check` → **All checks passed** (PROBLEMS: 0).
`python3 tools/assemble.py build` → writes `build/battle_dump_merged.txt` and
`build/script_dump_merged.txt`. The patch is buildable for the first time.

`build/battle_dump_merged.txt` **was** stale, exactly as this flag said: re-merging changed it by
87 insertions / 60 deletions, i.e. it had never contained chunks 7 or 33. It is now fresh, and
verified to differ from `dumps/battle_dump.txt` in precisely the ten chunks that have a
`tl/battle/` file — no other chunk touched, no line-count drift in any chunk.

⚠️ **One step of `build` still cannot run in a fresh clone**, and this is not a defect:
`original/SCRIPT.BIN` and `original/HEXMAP.BIN` are `.gitignore`d game data, so the reinsertion
half prints `-- skipping HEXMAP.BIN (original or merged dump missing)` and produces no `.BIN`.
Whoever has the disc image should drop the two files into `original/` and re-run `build` to
confirm the binaries. See §C5 for why `checkedit` cannot stand in for that.

### A2. ~~Root cause — exactly two untranslated messages~~ — RESOLVED 2026-08-06

Both are translated in `tl/script/batch_002.tsv`. The diagnosis in this flag was correct: nothing
but these two fall-through Japanese messages was blocking the build.

| Source line | Bank | Was | Now | Note |
|---|---|---|---|---|
| `script_dump.txt:1234` | 5 | 1,182 bytes, one 39-column segment | 2,570 bytes, longest run 23 columns | see **§D4** — it is not linear dialogue |
| `script_dump.txt:8604` | 43 | 894 bytes, contains `×` | 1,870 bytes, tag stream byte-identical | `×` → `Ｃｒｏｓｓ　ｂｕｔｔｏｎ` |

Bank pressure was never a factor, as predicted. Real figures, measured through
`riotscript._emit_bytes_from_body` (which counts the 900-byte `{HDR:}` block that
`assemble.py`'s `cost()` charges as 0, so these run ~900 higher than `check` implies):

- **bank 5**: 26,523 → 30,959 / 40,960 — **10,001 bytes still free**
- **bank 43**: 19,641 → 23,665 / 40,960 — **17,295 bytes still free**
- worst bank anywhere after the merge is bank 41 at 40,607 / 40,960, i.e. its 353 free bytes
  (§3.3) are untouched — no regression there.

All 44 banks re-encode to bytes cleanly, which is the reinsertion round trip minus the binaries.

**`{FFFE}` / `{FCC0}` counts, per line, before → after:**

| Line | `{FFFE}` | `{FCC0}` | Note |
|---|---|---|---|
| 1234 | **61 → 76** | 0 → 0 | +15, every one forced by the 24-column rule, on source segments 0, 1, 9 (+2), 13 (+4), 16, 17, 33, 35, 39, 45 and 53. Segment 13 is the 39-column one and needs five rows. No `{FCC0}` added — see §D4 for why |
| 8604 | **41 → 41** | 11 → 11 | Unchanged. The English fits the source's own page structure segment for segment, so the tag stream is byte-identical to the source apart from the text itself |

### A3. ~~`×` is a button glyph, not punctuation~~ — RESOLVED 2026-08-06

**`×ボタン` → `Ｃｒｏｓｓ　ｂｕｔｔｏｎ`.** Reasoning recorded in full in `glossary.md` §16;
the entry itself is in `glossary.md` §3, alongside a prospective △ → `Ｔｒｉａｎｇｌｅ　ｂｕｔｔｏｎ`
so the fourth button cannot drift.

Two findings from `riotfont.py` worth keeping whichever way this is revisited:

1. **The font is not full.** 88 codes in `SJIS_TO_ASCII`, ~1,232 bytes of payload inside an
   8,704-byte `AUTO_WINDOW`; one more glyph costs 14 bytes. §A3 had assumed fullness might kill
   option 2 — it does not.
2. **There is nonetheless no ✗ available.** Every glyph comes from `font8x8(ch)`, a 95-entry
   ASCII bitmap indexed `ord(ch) - 0x20`. SJIS `0x817E` is absent from the map and the pipeline
   cannot express a glyph that is not an ASCII character. Adding ✗ needs a hand-drawn bitmap plus
   changes to `SJIS_TO_ASCII` / `font8_rows_msb`, then a hardware re-proof. It would not have
   round-tripped today, which is the test the session prompt set for option 2.


---

## B. Blocking tier A chunks

### B1. Chunk 5 is infeasible in 8,192 bytes

Three passes: natural 1.97x → disciplined 1.74x → maximum compression short of deleting
content **1.64x**. The budget requires **1.53x**. Final: 8,679 bytes, **487 over**.
Parked in `pending/`.

### B2. 1.64x is a floor, not slack — measured, not asserted

Achieved ratios on chunks already shipped:

| chunk | budget ratio | **achieved** ratio |
|---|---|---|
| 0 | 1.74 | **1.73** |
| 10 | 8.39 | 1.88 |
| 12 | 8.49 | 2.10 |
| 33 | 9.52 | 1.93 |

Chunk 5 at 1.64x is **tighter than anything the project has shipped** and still misses.
The remaining sanctioned lever (§2.1 step 2, merging segments to delete `{FFFE}`) was measured
exhaustively: 29 mergeable pairs, **58 bytes**, against 487 needed. Closing the rest requires
deleting sentences, which §2.1 forbids.

### B3. Tier A is probably dead as a whole — decide before spending two more sessions

Chunk 16 (budget 1.59x) and chunk 32 (budget 1.61x) both sit **below** the measured 1.64x floor.
Chunk 43 (1.23x) is already parked. If the floor holds, all four tier-A chunks need the
`pending/slot-extension.md` work rather than more translation passes. Recommend settling the
`KOUSEI.EXE` question first and confirming the floor on one of 16 or 32, not both.

---

## C. Tooling defects

### C1. `assemble.py` does not implement the row check Appendix A claims

`validate_body` (lines 88–112) does charset and columns only. There is no page/row logic
anywhere in the file, so pages exceeding 4 text rows pass silently.

`tools/rowcheck.py` (added this session) mirrors `assemble.py`'s cost, column, charset and
tag-parity semantics and adds the missing row check plus per-line `{FFFE}` before→after diffing.
Usage: `python3 tools/rowcheck.py <chunk_num> <path_to_tl_file>`. It was calibrated against the
shipped byte figures for chunks 10, 11, 12 and 33 (exact match) and falsification-tested against
four planted violations: an overlong run, ASCII characters, a dropped tag, and `…`.

**Extended 2026-08-06** with a second mode, `python3 tools/rowcheck.py script [merged_dump]`,
which does the same row check for the **main script** and additionally counts the script-side
name insert at its true width (see §C4). It diffs each translated line's pages against the
pristine dump so that source breakage is reported as `INHERITED` rather than blamed on the
translation. `ROOT` is now derived from the file's own location instead of being hard-coded.
Battle mode is unchanged and re-verified against chunks 7 and 33.

Current output: columns clean across all 1,305 translated script lines; two pages over four text
rows, **both inherited** — line 1234 (source 61 rows, English 76; see §D4) and line 8194 (source
and English both 11 rows, from `batch_001`).

`assemble.py` itself still has no row check. It is a stand-in, not clearance (§0.6) —
`assemble.py check` remains the authority.

### C2. `riotbattle.py checkedit` has a bare `argv[3]` index

Running it with one argument raises `IndexError` instead of printing usage. Correct form is
`checkedit <original> <edited>`. One-line fix in `main`.

### C4. `assemble.py`'s column check is blind to the main-script name insert

`validate_body` substitutes `{FC00}{=0000}` with 7 placeholder characters before counting
columns, then strips all remaining tags. That is right for the battle script. **The main script
does not use `{FC00}` at all** — there are zero occurrences in `script_dump.txt`. It uses
`{FFEC}{=00}{=00}`, 113 occurrences, and the contexts put it beyond doubt that it is the same
player-name insert: `９軍隊長の{FFEC}{=00}{=00}だな？`, and `さん` / `君` / `殿` suffixed forms
throughout banks 0, 1, 5, 42 and 43.

`assemble.py` strips it to **0 columns**, so a main-script line can be up to 7 columns over the
limit and pass `check` silently. `batch_002` was laid out by hand against the true cost of 7 and
verified with the new `rowcheck.py script` mode; nothing in `batch_001` or `batch_002` is over.

Fix belongs in `assemble.py`: extend the substitution to `\{FFEC\}\{=00\}\{=00\}`.
**DONE 2026-08-06 (batch 003 session).** One line added to `validate_body`, immediately after the
`{FC00}` substitution. `check` was then re-run over the whole tree as the session prompt required:
it surfaced **nothing** — PROBLEMS (0) still — so no existing line was relying on the insert
costing 0 columns, in `batch_001`, `batch_002`, `batch_003` or any fall-through Japanese line. The other `{FFEC}`
variants (`{=01}` a number, `{=03}` an item name, and `{=02}` / `{=04}` / `{=05}` / `{=06}`,
which are undocumented) have **no known width bound** and want an in-game look before anyone
gives them a number.

### C5. `riotbattle.py checkedit` takes binaries, not dumps

The session prompt's verification step 3 asked for
`checkedit dumps/battle_dump.txt build/battle_dump_merged.txt`. That cannot pass and did not:
`checkedit` reads both arguments as `HEXMAP.BIN` images, slices them into fixed `0x2A800` chunks
and proves nothing outside `+0x25000`–`+0x27000` moved. Handed two text dumps it fails at the
first line — `FAIL: size changed 247339 -> 263662` — because an English dump is simply longer
than a Japanese one. The correct call is the one `assemble.py cmd_build` already makes:
`checkedit original/HEXMAP.BIN build/HEXMAP.BIN`, and it needs the binaries (§A1).

The equivalent proof was done at dump level instead and passes: the merged battle dump differs
from the pristine dump in exactly the ten translated chunks and nowhere else, with per-chunk line
counts identical. Anyone with the disc image should still run the real `checkedit` on the `.BIN`.

### C3. Chunk 33 dumper bug — recorded in `pending/README.md`, still open

`find_script_bounds` requires `\xfc\x51`; chunk 33 uses only `{FC50}`. Already documented; noted
here so it is not lost.

---

## D. Source defects (do not "fix" silently)

### D1. Dump artifact in chunk 5 line 17

`{FC70}{=00}逓{=20000E}` where lines 14 and 16 have the clean `{FC70}{=0062}{FC20}{=000E}`.
The dumper decoded argument bytes 0x9276 as Shift-JIS text. Preserved verbatim in the
translation. **Chunk 5 could not have passed `check` even at budget**, because this trips the
charset rule. Fix belongs in the dumper, not the translation.

### D2. Source pages exceeding 4 text rows are real

14 of them, across chunks 5, 6, 7, 30, 32, 36, 37 and 42. Worst is chunk 32 line 31 at
**59 rows**. None of the nine chunks shipped before this session contained one, which is why
this has not come up.

Chunk 5 source line 10 has a 7-row and a 5-row page. Chunk 7 line 23 has 5 rows. In both cases
source structure was preserved rather than inserting `{FCC0}`, because the text looks like
auto-advancing cutscene narration where a page break would be wrong. **Needs an in-game look
to confirm.**

### D4. Script line 1234 is a scrap/variant pool, NOT linear dialogue — CONFIRMED

The session prompt's working hypothesis was right, and the evidence is stronger than
"branching variants". Line 1234 is an **earlier draft** of the war-council scene that shipped as
line **1236**, left in the bank. Six independent findings:

1. **1234, 1235 and 1236 share a byte-identical 40-byte header prefix**
   (`{FFC2}{=00}{=13}` … `{FFD2}{=00}{=14}`). They are three siblings of one event.
2. **1236 is the playable version**: 21 `{FC50}` speaker channels, 19 `{FC30}` waits,
   12 `{FCC0}` page breaks, 17 `{FCB0}` transitions.
3. **1234 has none of those.** 61 `{FFFE}` and *zero* `{FC30}`, `{FC50}`, `{FC51}`, `{FCC0}`.
   Only **two** messages in the entire 7,931-message dump have ≥8 `{FFFE}` and no `{FCC0}`, and
   the other one (8239) is visibly a pool of unrelated NPC lines too. With no `{FC30}` anywhere
   the box never waits for input, so 503 characters could not be read even if it were reached.
4. **The sentences recur in 1236 with small edits** — `これでてめえも` / `体面が保てるんだ` vs
   1236's `体面が保てるな`; `いくぞ、本当の作戦会議の開始だ` vs 1236's `いくぞ、作戦会議だ`;
   `こんな無茶な遠征を` / `計画しといて、` / `よく言うぜ。` identical in both.
5. **The 39-column segment is a symptom.** `７軍の後ろを…９軍はまだ戦力が残ってるようだな。`
   restates segment 11's `９軍はまだ`, with segments 10 and 12 (`そういえば、` / `おおかた、`)
   reading as two alternative openings for one sentence. It is an unwrapped draft line, not a
   wrapping bug in a live message.
6. **The neighbour proves the register.** Line **1235** — same header, same shape, 1,184
   characters, zero `{FC30}` — contains the literal string **`１２３４５６７８９０１２`** three
   times. That is a developer's 12-column ruler. It also carries the same sentence twice in two
   registers (`…手薄になります。` polite / `…手薄になるってことだ。` plain) and the
   奴らに悟られずに / 敵に悟られずに pair. This is a scratch pool.

**What was done.** Translated **fragment by fragment**, each `{FFFE}` segment standing alone, as
the prompt directed for the confirmed case. Longest run is 23 columns. **The tag stream is
preserved exactly and no `{FCC0}` was added**, against the prompt's general licence to add them,
because a page break without a `{FC30}` does not pause and would only clear the box mid-flow;
and because if the data is addressed as a pool, inserted bytes could shift what indexes it. This
follows the §D2 precedent of preserving source structure where the text is not a normal textbox.
The page therefore still reports 61 → 76 text rows, correctly, as `INHERITED`.

**What is still needed.** An in-game look at the war council to confirm 1236 is what plays and
1234 is unreachable. If 1234 *is* reachable, it is broken in Japanese too and the fix is a
dumper/engine question, not a translation one.

### D5. `お前らは　したらしいな。` has a hole in it — preserved, not patched

Segment 27 of line 1234. The verb `した` is present; the **object is missing**, and the source
leaves a full-width space where it should be — compare 1236's
`お前たちで要塞を落として…`. Rendered `Ｙｏｕ　ｌｏｔ　　ｄｉｄ，　ｉｔ　ｓｅｅｍｓ．`,
keeping the double space so the hole stays visible on screen and nothing is invented to fill it.
Consistent with §D4: a draft line, never finished.

### D3. Chunk 7 line 24 — the one place in shipped work that needs eyes

`{FFFE}` went 6 → 8. Both additions are forced: source segments 3 and 5 are 16 and 20 JP chars
and overflow 24 columns in any English rendering. But this pushes an already-out-of-spec page
from 6 rows to 8. Everything else in chunk 7 is within spec. Check this textbox in game before
considering chunk 7 final.

Other `{FFFE}` changes in chunk 7: lines 25 and 26, 0 → 1 each (splitting
`Ｔｈｅ　ｖｉｌｌａｇｅ　ｉｓ　ｕｎｄｅｒ　ａｔｔａｃｋ．` off the 24-column limit).

---

## E. Naming and translation decisions that could be revisited

All are entered in `glossary.md` §14 and cross-referenced from §13.

| Item | Decision | Why it might change |
|---|---|---|
| `キャビア` → Cavia | §14.1 | kana are exactly the loanword *caviar*; the pun may be deliberate (§13.14) |
| `ナコール` → Nacol | §14.1 | no in-game romanisation; alt *Nakor*, *Nacoll* (§13.15) |
| `ティータ` → Tita | §14.1 | **hapax** — one occurrence in the battle dump, zero in the script dump. Not a typo for ティミー: in ch.5 line 10 Fei is *surprised* by Timmy's arrival, so she was not calling her in line 1. Possibly Fei's beast, since Fei is a 獣使い, or a cut character (§13.16) |
| `ベルナール` → Bernard | §14.2 | alt *Bernal* |
| `オーク` → orc (lowercase) | §14.3 | class-table form still open (§10.2, §13.17) |
| `ほう` → **Ｏｈ** (was `Ｈｏｈ`) | §6, §10.6 | **Closed 2026-08-06.** `tl/battle/chunk_035.txt` now reads `Ｏｈ，`; the chunk went 557 → 555 bytes. No `Ｈｏｈ` remains anywhere in `tl/` |
| `クレス` → Cress | glossary §1 | alt *Kress*, *Cres*; no in-game romanisation |
| `ウエストバリー` → Westbury | glossary §2 | alt *Westbarry* |
| `ゼファー・クリッペン` → Zephyr Krippen | glossary §1 | name taken from the session prompt; alt *Zepher*, *Crippen*, *Klippen*. Appears **once** in either dump, so nothing corroborates the reading |
| `穀潰し` → freeloaders | glossary §2 | recurs in line 1236, so it will be re-used before it can be revisited cheaply |

### E1. Deviations from literal (§2.1 steps 5–6)

**Chunk 7:** 敵さん、大勢で → *Look at them all* (implication for the count);
傭兵あがりの若造ども → *Mercenary upstarts* (drops the youth sense);
王女の命、いただいたぞ → *Her life is mine*;
世話んなったじいさん → *the old man who raised her*;
お父様たちも → *your father* (drops the plural);
エチュード → *etude* (no `é` in charset).

**Script batch 002 (line 1234):** `わかったんだよ、` → `Ｗｅ’ｖｅ　ｆｏｕｎｄ　ｏｕｔ：` — the
source's `、` became `：` so that the three fragments after it (`薬の持ち主が。` / `薬の在処が。`
/ `黒幕が。`) read correctly whether they follow it or stand alone, which §D4 requires;
`かなり` → *very* rather than *quite*, purely for columns; `黒幕が。` → *Who is behind it.* as a
clause rather than the noun *mastermind*, because the fragment stands alone.

**Script batch 002 (line 8604):** `がんがん当てちゃおうね！！` →
`ｌｅｔ’ｓ　ｐｉｃｋ　ｐｌｅｎｔｙ　ｏｆ　ｗｉｎｎｅｒｓ！！` (implication for `がんがん`);
`ゆーことを示すの` → plain *means* — the casual spelling has no English equivalent that is not
an eye-dialect the §3.1 charset cannot carry.

**Chunk 5:** 橋の前にもオークが drops も; 王女様だけじゃなく → *not only her*;
自分たちで守る → *guarded our own*; Cavia given `ｃａｎ’ｔ` in her exhausted opening line,
against her otherwise uncontracted register (§14.6) — the one deliberate exception.

---

## F. Script batch 003 — the description table (2026-08-06)

### F1. The byte figure, measured the real way

**Bank 40: 39,189 / 40,960 used — 1,771 bytes free.** Measured through
`riotscript._emit_bytes_from_body`, i.e. counting the 900-byte `{HDR:}` block that `assemble.py`'s
`cost()` charges as 0. `check` will report this bank ~900 lighter; the figure above is the one the
inserter sees, and it is the one that decides overflow.

Every bank, before → after this session:

| Bank | before | after | free | note |
|---|---|---|---|---|
| **40** | 33,869 | **39,189** | **1,771** | the binding constraint, as predicted |
| 5 | 30,959 | 36,279 | 4,681 | |
| 2 | 26,835 | 32,155 | 8,805 | |
| 41 | 40,607 | 40,607 | 353 | **untouched** — no description line lives in bank 41 |
| the other 18 of the 21 | | | ≥ 10,000 | |

Growth is 5,320 bytes per bank: 5,130 from characters (EN 5,131 vs JP 2,530) and 190 from the
95 added `{FFFE}` breaks. One line of the block lives in bank 29 alone, not in the 21.

**Ratio hit: 2.03x.** The prompt asked for ≤ 1.8x and ~2,000 bytes of slack; I hit 2.03x and 1,771,
and here is why 1.8 is not reachable on this material rather than an excuse:

- The `Ｇｅｍ　Ｔｙｐｅ：<colour>` row is **fixed by §3 and unvarying**. It is 12–15 characters
  against the source's 8–10, i.e. **1.63x on its own**, and it is 1,371 of the 5,131 characters in
  the batch. The descriptions would have to come in at 1.72x to drag the whole to 1.8.
- `batch_001`, the same table by the same rules, shipped at **2.31x**. This batch is 12% tighter
  than the work it has to sit beside, which is as far as it can go without the entries reading
  differently from their neighbours in a list the player scans side by side.
- What is left is not fat. The ceiling is geometry, not bytes: 2 description rows × ≤23 columns
  is 46 characters, and 42 of the 101 descriptions are within 6 characters of that wall.

### F2. Bank 40 cannot hold a complete translation — and neither can 41, 5 or 2

This is the finding that matters, and it is not about this batch. I measured every bank's
**remaining untranslated Japanese** and projected it at 1.9x, a ratio no shipped work has beaten
(§B2's floor is 1.64x under maximum compression; real achieved ratios are 1.73–2.31):

| Bank | free now | untranslated JP chars | growth needed @1.9x | verdict |
|---|---|---|---|---|
| **41** | 353 | 14,607 | 26,292 | **short by 25,939** |
| **40** | 1,771 | 12,514 | 22,525 | **short by 20,754** |
| **5** | 4,681 | 9,573 | 17,231 | **short by 12,550** |
| **2** | 8,805 | 8,657 | 15,582 | **short by 6,777** |
| all other 40 banks | | | | fit, most with room to spare |

**~66,000 bytes short in total.** SCRIPT.BIN is "69% free" in aggregate (§3.3) and that aggregate
is misleading: the free space is in banks 10, 11, 21–27 and 34–39, which hold almost no text,
while the four banks that carry the bulk of it are full. Bank 41's 353 free bytes were always
known (§3.3); the other three were not.

Consequences, in order:

1. **The main script needs the same treatment as chunk 43** — repointing, or a bank-spill scheme —
   and it needs it before roughly a third of the remaining script can ship. This is the
   `pending/slot-extension.md` question again, on the `MAIN1.EXE` side. It should be settled
   before many more script sessions, for the same reason §B3 says to settle `KOUSEI.EXE` first:
   otherwise sessions are spent producing text that cannot be inserted.
2. **The "keep ~2,000 bytes of slack" instruction is moot** and I have not distorted the
   translation to satisfy it. Reserving 2,000 bytes against a 20,754-byte shortfall buys nothing;
   what buys something is writing tight, which is why this batch is at 2.03x and not at 2.31x.
3. **Nothing overflows today.** No bank exceeds 0xA000, `insert` would not raise, and `check`
   passes. The failure is in the future, not in this build.
4. Worth re-measuring with `tools/bankmeasure.py` (added this session) at the start of every
   script session. It is the only tool that reports the figure the inserter actually uses.

### F3. Scope — the block is 101 lines, not 102

The session prompt's count of "102 remaining unique lines ending `ジェムタイプ：<colour>`" includes
**`script_unique.txt` line 979**, which is not a description-table line: it is the 404-character
`『ジェム』` tutorial, and it merely *contains* the word `ジェムタイプ` in prose. Filtering on
lines that actually **end** `ジェムタイプ：<colour>`, as the prompt's own wording says, gives
**101**. Line 979 is untranslated and out of scope; it belongs with the §7 tutorial boxes.

The prompt's 2,929-character figure is inflated the same way. The block as translated is
**2,525 Japanese characters over 101 lines** (25.0 average, not 28.7), plus the `クラス７０`
placeholder at 5 — **2,530 in 102 entries**, which is the denominator of the 2.03x above.

Not a defect in the prompt's conclusion: 101 lines × 21 occurrences is still 2,121 instances and
still by far the biggest block available. `assemble.py status` now reports **41.6%** of message
instances translated, up from 14.6%.

### F4. `{FFFE}` counts, per line

Uniform, so a table of 102 rows would be noise:

| Change | Lines | Why |
|---|---|---|
| **1 → 2** | 95 | the source puts the whole description on one row (16 JP columns) and lets `ジェムタイプ` share the second; English needs two description rows plus the Gem Type row on its own |
| 1 → 1 | 6 | lines 79, 117, 119, 120, 142, 174 — the description fits one row, so the source's single break is all that is needed |
| 0 → 0 | 1 | the `クラス７０` placeholder |

**No entry exceeds three text rows**, i.e. two description rows plus `Ｇｅｍ　Ｔｙｐｅ`, per
§10.3 and the prompt's ceiling. Verified mechanically, not by eye: `rowcheck.py script` reports
columns clean across all 3,405 translated lines and no page over four text rows that the source
did not already exceed (the two inherited ones, lines 1234 and 8194, are unchanged — no third one
was introduced).

### F5. `batch_001` re-flow — 20 segments at 24 columns, now 3

Done as the prompt invited, and it **saves** 34 characters (68 bytes per bank), so it cost the
budget nothing. Sixteen entries changed; the Japanese keys are untouched and `check`/`rowcheck`
were re-run over the whole tree afterwards.

Representative changes: `Ａ　ｓｗｏｒｄ　ｗａｒｒｉｏｒ　ｏｆ　ｇｒｅａｔ` / `ｓｐｅｅｄ　ａｎｄ　ｓｋｉｌｌ．`
→ `Ａ　ｓｗｏｒｄ　ｗａｒｒｉｏｒ，　ｇｒｅａｔ` / `ｉｎ　ｓｐｅｅｄ　ａｎｄ　ｓｋｉｌｌ．`;
`ｗｈｏ　ｋｉｌｌｓ　ｗｉｔｈ　ｏｎｅ　ｂｌｏｗ．` → `ｋｉｌｌｉｎｇ　ｗｉｔｈ　ｏｎｅ　ｂｌｏｗ．`
(§4's *kills with one blow* survives intact); `ｗｈｏ　ｒｏａｍｓ　ｔｈｅ　ｗｏｏｄｌａｎｄｓ．`
→ `ｒｏａｍｉｎｇ　ｔｈｅ　ｗｏｏｄｌａｎｄｓ．`.

Three word changes worth naming, all in already-shipped text:

- 神の使いといわれる → `Ａ　ｓｗｏｒｄｓｗｏｍａｎ　ｃａｌｌｅｄ` (was *said to be*), which also
  matches how 異名を持つ / と言われる are rendered throughout `batch_003`.
- 遠隔戦闘の経験を積んだ → `ｗｅｌｌ　ｖｅｒｓｅｄ　ａｔ　ｒａｎｇｅ` (was *in ranged combat*) —
  one character short of fitting, and *ranged combat* survives in the neighbouring entry.
- 乗馬と戦闘の技術を極めた → `Ａ　ｋｎｉｇｈｔ，　ｍａｓｔｅｒ　ｏｆ` drops *both*.

**Three segments could not be brought under 24 and are unchanged**, because every arrangement
either drops a word or needs a third description row:

1. `ｓｗｏｒｄｓｍａｎ　ｉｎ　ｌｉｇｈｔ　ｇｅａｒ．` (素早さと技に優れた軽装の男剣士) — its
   partner row is fixed, at 21.
2. `Ａｎ　ａｒｍｏｕｒｅｄ　ｓｗｏｒｄｓｍａｎ　ｏｆ` and 3. `ｈｉｇｈ　ａｔｔａｃｋ　ａｎｄ　ｄｅｆｅｎｃｅ．`
   (高い攻撃力と防御力を持つ鎧剣士) — 48 characters of content against a 46-character ceiling.
   `ｏｆ　ｈｉｇｈ　ａｔｔａｃｋ　ａｎｄ　ｄｅｆｅｎｃｅ．` is 27 and `ｈｉｇｈ　ａｔｔａｃｋ　ａｎｄ　ｄｅｆｅｎｃｅ．`
   is exactly 24, so the break has nowhere to go.

### F6. `batch_001` has five entries that render four text rows

Not introduced here, but it is the one place where existing work depends on the unconfirmed §10.3
window being four rows rather than three: 高い戦闘力を持つ上級の天馬騎士, 長射程の炎・雷の単体魔法…,
モンスターを操り、氷魔法を使う…, 仲間の能力を引き出して戦うことを…, and 炎・雷・光魔法を使う最上級の….
Each is three description rows plus `Ｇｅｍ　Ｔｙｐｅ`. **Every one of the 102 entries in
`batch_003` is three rows**, so if the in-game check comes back "three rows", only these five need
re-cutting.

### F7. `Ａｔｋ＋ＮＮ`, and why the weapon stat row is not `Ａｔｔａｃｋ`

Fourteen weapon entries carry a second field: `攻撃力＋ＮＮ　ジェムタイプ：色`.
`Ａｔｔａｃｋ＋１０　Ｇｅｍ　Ｔｙｐｅ：Ｇｒｅｅｎ` is **exactly 24 columns**, and `Ｇｅｍ　Ｔｙｐｅ：`
cannot be shortened (§3, 2,964 occurrences). Rather than create the one fragile row the prompt
told me not to create, the stat label is **`Ａｔｋ＋ＮＮ`**, which holds every stat row at ≤ 21.
Prose keeps *attack power* (§4) — this is a mechanical stat field, and the source itself uses a
compressed label there.

**Swap it back to `Ａｔｔａｃｋ＋ＮＮ` the moment the description window is confirmed wider than 24**,
or if a reviewer would rather have the full word and accept 24 columns on the single Green weapon
(line 171 — the only Green one in the table, so it is exactly one row, once).

### F8. Deviations from literal (§2.1 steps 5–6)

- 古の種族、ダークエルフの血を引く → *Ａ　ｍａｇｅ　ｏｆ　ａｎｃｉｅｎｔ　ｄａｒｋ　ｅｌｆ　ｂｌｏｏｄ．*
  — 古の種族 (*an ancient race*) folded into *ancient*; both rows are within 3 of the wall.
- 鋭い爪を持ち、鋭敏な動きをする暗殺猫 → *Ａ　ｓｗｉｆｔ　ａｓｓａｓｓｉｎ　ｃａｔ　/　ｗｉｔｈ　ｓｈａｒｐ　ｃｌａｗｓ．*
  — 鋭敏な動き carried by *swift* rather than a clause.
- 帝国の量産型機械兵試作機 → *Ｔｈｅ　Ｅｍｐｉｒｅ’ｓ　ｐｒｏｔｏｔｙｐｅ　/　ｍａｃｈｉｎｅ　ｓｏｌｄｉｅｒ．*
  and クリミアの量産型機械兵２号機改良型 → *Ｃｒｉｍｅａ’ｓ　ｉｍｐｒｏｖｅｄ　…* — **量産型 is
  dropped in the derived entries only**. It is carried in full by the entry each derives from
  (`Ｍａｓｓ‐ｐｒｏｄｕｃｅｄ　ｍａｃｈｉｎｅ　ｓｏｌｄｉｅｒ　Ｕｎｉｔ　１`,
  `Ｃｒｉｍｅａ’ｓ　ｍａｓｓ‐ｐｒｏｄｕｃｅｄ　…`), which sits directly beside it in the list.
- さく裂弾を放つ長射程の無人砲台 / 火炎弾を放つ… → *Ａ　ｌｏｎｇ‐ｒａｎｇｅ　ｔｕｒｒｅｔ　…* —
  無人 (*unmanned*) dropped; *turret* carries it and 砲台 has no shorter English.
- 他のユニットを乗せて運搬できる機構車両 → *Ａ　ｖｅｈｉｃｌｅ　ａｂｌｅ　ｔｏ　ｃａｒｒｙ　/　ｏｔｈｅｒ　ｕｎｉｔｓ．*
  — 機構 (*mechanical*) dropped for width.
- 最強の攻撃能力を持つオリジナル４号機 → *…　ｏｆ　ｔｈｅ　/　ｓｔｒｏｎｇｅｓｔ　ａｔｔａｃｋ．* — 能力 dropped.
- 天をも支える怪力無双の巨人 → *Ａ　ｇｉａｎｔ　ｗｈｏｓｅ　ｍａｔｃｈｌｅｓｓ　/　ｍｉｇｈｔ　ｕｐｈｏｌｄｓ　ｔｈｅ　ｓｋｙ．*
  — reordered so the relative clause takes the break (§2.1 step 6).
- 幸運を運ぶと言われる → *ｓａｉｄ　ｔｏ　ｂｒｉｎｇ　ｌｕｃｋ．* — *good fortune* would not fit.

### F9. Readings with a defensible alternative

| Kana | Chosen | Alternative | Why it might change |
|---|---|---|---|
| ネルガリ | `Ｎｅｒｇａｌｉ` | **`Ｎｅｒｇａｌ`** | The kana are one vowel off the Babylonian death-god ネルガル, and the class is a dark elemental, so the god is very probably the source. Plain transliteration chosen because nothing in either dump corroborates it. Appears twice, both in this table |
| 水蛇 | `ｓｅａ　ｓｎａｋｅ` | *water serpent* | The literal *water serpent* is 4 columns longer and does not fit the row; *hydra* was rejected as a different creature |
| トクロフ | `Ｔｏｋｒｏｆ` | *Tokurofu*, *Tocroph* | One occurrence in either dump. A tree, apparently |
| ルシファ | `Ｌｕｃｉｆｅｒ` | *Lucifa* | Strict transliteration is *Lucifa*; the European form matches the Bauer / Carline / Helfer naming already fixed |
| 悪鬼 | `ｆｉｅｎｄ` | *demon* | §9 already glossed it *fiend*, and 豚顔 (pig-faced) is in the same sentence, so *fiend* keeps 鬼 → *ogre* free for the sibling entries |
| 魔術戦士 | `ｍａｇｅ　ｗａｒｒｉｏｒ` | *spell warrior*, *sorcerous warrior* | Must stay distinct from 魔法戦士 → *magic warrior* (§4); the chosen form uses the 魔術/魔法 split the glossary already draws |

### F10. Suspected source oddities, preserved

- **`子供のドラゴン。成長すれば・・？`** — two dots, not three, and a `？`. Reproduced exactly as
  `．．？` per §3.1's match-the-dot-count rule. It is the only entry in the table with a question
  mark, and reads like a designer's note left in.
- **`自走砲１です！` / `自走砲２です！` / `固定砲３です！`** — three entries written as sentences
  with `です！` where every other entry is a noun phrase. They are unfinished, like `ダミーぶきです`,
  and are translated the same way rather than tidied into the table's voice.
- **`量産型機械兵１号機。`** has no owner where its neighbours name the Empire, Crimea or Seneca.
  Left as it is.
