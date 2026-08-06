# FLAGS.md — open issues carried forward

Everything here needs a human decision, a tool fix, or an in-game look. Nothing here is
resolved by translating more chunks. Items are grouped by what blocks them.

Session of 2026-08-06 delivered `tl/battle/chunk_007.txt` (7,793 / 8,192, 399 slack) and
parked `pending/chunk_005.txt` (8,679 / 8,192, 487 over).

Second session of 2026-08-06 delivered `tl/script/batch_002.tsv` (script lines 1234 and 8604).
**`check` reports PROBLEMS (0) and `build` writes output for the first time in the project.**
§A1, §A2 and §A3 are resolved below; §C1 is partly resolved; §D4, §D5, §C4 and §C5 are new.

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

Fix belongs in `assemble.py`: extend the substitution to `\{FFEC\}\{=00\}\{=00\}`. Not done
here — this session deliberately changed no tool that `check` depends on. The other `{FFEC}`
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
| `ほう` → **Ｏｈ** (was `Ｈｏｈ`) | §6, §10.6 | **Resolved, not open** — chunk 0 line 14 already had `Ｏｈ．．．．` and §10.6 said chunk 0 wins. ⚠️ `tl/battle/chunk_035.txt` line 13 still reads `Ｈｏｈ，` and must become `Ｏｈ，`. Same width, no re-flow. Not done here: this session was script-only |
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
