# Riot Stars (SLPS-00829) — Translation Feasibility Findings

**Status:** research / pre-production
**Last updated:** 2026-07-24
**Files analysed so far:** SCRIPT.BIN, SLPS_008.29, MAIN1.EXE, KOUSEI.EXE, CASINO.EXE, KEIBA.EXE, IM.BIN, NA.BIN, INICHR.BIN, FACE.PXL, INTER.BIN, EFFECT.BIN

---

## 1. Game identification

| | |
|---|---|
| Title | Riot Stars (ライアット・スターズ) |
| Serial | SLPS-00829 |
| Platform | Sony PlayStation (NTSC-J) |
| Developer / Publisher | Hect |
| Release | 1997-05-02 |
| Genre | Tactical RPG (SRPG) with casino / horse-racing minigames |
| Existing translation | **None found.** No known patch, no known project. |

---

## 2. Disc layout

```
ROOT
├── IMDATA/
│   ├── FACE.PXL      2,580 KB   ✅ portraits, raw 8bpp headerless (§6)
│   ├── IM.BIN          684 KB   ✅ event CG backgrounds (TIM)
│   ├── INTER.BIN       224 KB   ✅ interface graphics + 8×8 tilemaps (§6)
│   ├── KEIBA.BIN       232 KB   ❓ untested
│   ├── MAP1.BIN        266 KB   ❓ untested
│   ├── MAP2.BIN        266 KB   ❓ untested
│   ├── MAP4.BIN        266 KB   ❓ untested
│   ├── MATI.BIN      1,368 KB   ❓ untested — town graphics (町)
│   ├── MISE.BIN        880 KB   ❓ untested — shop graphics (店)
│   ├── NA.BIN          836 KB   ✅ backgrounds / illustrations (TIM)
│   ├── SCRIPT.BIN    1,760 KB   ✅ MAIN SCRIPT (§4)
│   ├── SLOT.BIN        176 KB   ❓ untested
│   └── TRUMP.BIN       222 KB   ❓ untested
├── MUSIC/                       ❓ untested
├── TACTICS/
│   ├── BATANM.BIN    2,314 KB   ❓ untested
│   ├── BATBG.BIN     6,068 KB   ❓ untested
│   ├── BATOBJ.BIN    6,324 KB   ❓ untested
│   ├── EFFECT.BIN      182 KB   ✅ battle effect sprites (TIM) (§6)
│   ├── HEXMAP.BIN    7,852 KB   ❓ untested
│   ├── INICHR.BIN      552 KB   ✅ unit sprite sheets (TIM)
│   └── LAST_B.BIN      814 KB   ❓ untested
├── CASINO.EXE          358 KB   ✅ casino minigame
├── KEIBA.EXE           322 KB   ✅ horse-racing minigame
├── KOUSEI.EXE        1,048 KB   ✅ battle engine
├── MAIN1.EXE           556 KB   ✅ town / overworld engine
├── SLPS_008.29         438 KB   ✅ boot executable
├── SYSTEM.CNF            1 KB
└── ZDATA.BIN        27,972 KB   ⚠️ NOT referenced by name anywhere — see §9
```

### File loading

All EXEs open data files **by CD path string** through the ISO9660 directory, e.g.
`\IMDATA\SCRIPT.BIN;1`, `cdrom:\MAIN1.EXE;1`. No hardcoded LBAs observed for these files.
**An mkpsxiso rebuild is therefore straightforward** — these files can move.

| EXE | Loads |
|---|---|
| SLPS_008.29 (boot) | CASINO, KEIBA, KOUSEI, MAIN1, SOUND.EXE\*, all IMDATA, FACE.PXL |
| MAIN1.EXE | KOUSEI/CASINO/KEIBA/SLPS, all IMDATA, FACE.PXL |
| CASINO.EXE / KEIBA.EXE | all IMDATA, FACE.PXL |
| KOUSEI.EXE | **FACE.PXL + TACTICS/\*.BIN only** (no IMDATA) |

\* `cdrom:\SOUND.EXE;1` is referenced by SLPS_008.29 but **no such file exists on the disc** — dead reference.

All five EXEs load at `0x80010000`, so they overwrite one another. There is **no resident kernel/library EXE**; each is a standalone program that must contain or load everything it needs. This is an important constraint on the font search (§7).

---

## 3. Text encoding — CRITICAL

Both text stores are **plain Shift-JIS**. No compression, no DTE, no custom character table, no encryption.

**But the byte order differs between the two stores:**

| Store | Layout | Example (`よ` = SJIS 0x82E6) |
|---|---|---|
| `SCRIPT.BIN` | standard SJIS byte order | `82 E6` |
| All 5 EXEs | **u16 little-endian (byte-swapped)** | `E6 82` |

The EXEs store dialogue as C `unsigned short[]` arrays, so MIPS little-endian byte order applies. Open an EXE in a normal SJIS-aware hex editor and you get garbage like `＝モリゼ゛ゼ”` where the real text is `メモリカード`.

**This is the single biggest trap in the project.** Anyone who doesn't spot it will conclude the executables are encrypted. Swap every byte pair before decoding EXE text; swap back on reinsertion.

ASCII strings in the EXEs (debug printf, file paths) are stored **normally**, not swapped — they're `char[]`, not `unsigned short[]`.

### Character set

- 1,426 unique SJIS codes in SCRIPT.BIN (1,183 kanji, 155 kana, rest punctuation/symbols)
- Full-width Roman `Ａ-Ｚ` `ａ-ｚ` `０-９` are already in use (`「ＲＩＯＴ　ＳＴＡＲＳ」`, `ＮＵＭＢＥＲ１`)
- **A proof-of-concept English build needs zero font work** — just insert full-width Latin. Ugly and cramped, but it will display.

---

## 4. SCRIPT.BIN — main script

**Size:** 1,802,240 bytes = **exactly 44 banks × 0xA000 (40,960 bytes)**

The game almost certainly seeks to bank *N* at file offset `N × 0xA000` (= sector `N × 20`) and reads 40 KB. **Keep the bank layout and total file size identical.**

### Bank layout

```
+0x0000   50 × 18-byte event records (900 bytes = 0x384)
          each record: FF FC + 8 × u16 BIG-ENDIAN
          field values are small (max ~108) → IDs/indices, not byte offsets
+0x0384   command stream with INLINE TEXT
...       zero padding to 0xA000
```

- 43 of 44 banks have exactly 50 header records.
- **Bank 40 (0x190000) has no header** — pure string pool (system/UI text: save/load prompts, menu labels, option descriptions).
- Banks 42–43 (0x1A4000, 0x1AE000) hold class descriptions, item descriptions, weapon/armour text.

### Control codes

All control codes use lead bytes `0xFB`–`0xFF`, **outside the SJIS lead-byte ranges** (0x81–0x9F, 0xE0–0xEF). Parsing is unambiguous. 72 distinct 2-byte codes observed. Most common:

| Code | Count | Meaning (inferred) |
|---|---|---|
| `FF FE` | 12,930 | line break |
| `FF FF` | 8,736 | end of message |
| `FC 30` | 1,367 | end text / wait for input |
| `FB 01` | 1,316 | ? (very common, precedes text) |
| `FC C0` | 950 | clear window / page break |
| `FC 51` | 920 | begin text |
| `FC B0` | 768 | takes 4 bytes of args |
| `FF F8` | 598 | ? |
| `FB 00` | 533 | set speaker/portrait — `FB 00 <u16 id> <u16 flag>` |
| `FC 50` | 422 | ? |

`FB 00` observed with repeating ids (0x165, 0x178) — actor/portrait ids, **not** lengths or offsets (deltas to the next marker don't match).

### No pointer table

**No absolute pointer table for strings was found anywhere** — not in SCRIPT.BIN, not in the EXEs. Text is embedded inline in the command stream. The header records hold only small index-like values.

**If this holds, string lengths can be changed freely with zero repointing** — normally the single largest cost in a PSX project.

⚠️ *Not yet verified by disassembly.* Confirm the message routine in MAIN1.EXE before building tooling on this assumption.

### Free space

| | |
|---|---|
| Total trailing padding | **1,219 KB (69% of the file)** |
| Banks with >50% free | 31 of 44 |
| Tightest bank | **bank 41 (0x19A000): 353 bytes free (0.9%)** |
| Second tightest | bank 40 (0x190000): 10,139 bytes free (24.8%) |

Every other bank has 14 KB–40 KB of slack. Only bank 41 needs care.

<details>
<summary>Full per-bank free space table</summary>

| Bank | Offset | Used | Free | % free |
|---|---|---|---|---|
| 0 | 0x0 | 5,763 | 35,197 | 85.9 |
| 1 | 0xA000 | 8,785 | 32,175 | 78.6 |
| 2 | 0x14000 | 23,787 | 17,173 | 41.9 |
| 3 | 0x1E000 | 20,701 | 20,259 | 49.5 |
| 4 | 0x28000 | 19,487 | 21,473 | 52.4 |
| 5 | 0x32000 | 26,523 | 14,437 | 35.2 |
| 6 | 0x3C000 | 17,781 | 23,179 | 56.6 |
| 7 | 0x46000 | 17,719 | 23,241 | 56.7 |
| 8 | 0x50000 | 19,003 | 21,957 | 53.6 |
| 9 | 0x5A000 | 18,139 | 22,821 | 55.7 |
| 10 | 0x64000 | 4,317 | 36,643 | 89.5 |
| 11 | 0x6E000 | 1,283 | 39,677 | 96.9 |
| 12 | 0x78000 | 20,971 | 19,989 | 48.8 |
| 13 | 0x82000 | 17,843 | 23,117 | 56.4 |
| 14 | 0x8C000 | 17,799 | 23,161 | 56.5 |
| 15 | 0x96000 | 17,859 | 23,101 | 56.4 |
| 16 | 0xA0000 | 18,837 | 22,123 | 54.0 |
| 17 | 0xAA000 | 17,473 | 23,487 | 57.3 |
| 18 | 0xB4000 | 20,273 | 20,687 | 50.5 |
| 19 | 0xBE000 | 20,369 | 20,591 | 50.3 |
| 20 | 0xC8000 | 11,471 | 29,489 | 72.0 |
| 21 | 0xD2000 | 4,141 | 36,819 | 89.9 |
| 22 | 0xDC000 | 2,187 | 38,773 | 94.7 |
| 23 | 0xE6000 | 7,575 | 33,385 | 81.5 |
| 24 | 0xF0000 | 1,261 | 39,699 | 96.9 |
| 25 | 0xFA000 | 18,377 | 22,583 | 55.1 |
| 26 | 0x104000 | 1,071 | 39,889 | 97.4 |
| 27 | 0x10E000 | 1,041 | 39,919 | 97.5 |
| 28 | 0x118000 | 6,119 | 34,841 | 85.1 |
| 29 | 0x122000 | 13,637 | 27,323 | 66.7 |
| 30 | 0x12C000 | 4,289 | 36,671 | 89.5 |
| 31 | 0x136000 | 5,379 | 35,581 | 86.9 |
| 32 | 0x140000 | 2,677 | 38,283 | 93.5 |
| 33 | 0x14A000 | 21,977 | 18,983 | 46.3 |
| 34 | 0x154000 | 1,307 | 39,653 | 96.8 |
| 35 | 0x15E000 | 1,019 | 39,941 | 97.5 |
| 36 | 0x168000 | 2,185 | 38,775 | 94.7 |
| 37 | 0x172000 | 1,043 | 39,917 | 97.5 |
| 38 | 0x17C000 | 1,173 | 39,787 | 97.1 |
| 39 | 0x186000 | 997 | 39,963 | 97.6 |
| 40 | 0x190000 | 30,821 | 10,139 | 24.8 |
| 41 | 0x19A000 | 40,607 | **353** | **0.9** |
| 42 | 0x1A4000 | 19,311 | 21,649 | 52.9 |
| 43 | 0x1AE000 | 19,641 | 21,319 | 52.0 |

</details>

### Script volume

| | |
|---|---|
| Total stored text | **~220,000 full-width characters** |
| Unique text | **~65,000 characters** (~70% is duplicated) |
| Messages | ~7,900 total, ~1,300 unique |
| Rough English equivalent (unique only) | **25,000–35,000 words** |

Duplication is structural: class/item/weapon description tables are replicated verbatim in many chapter banks (some strings appear 21×; `ダミーぶきです` appears 126×). A dedupe-translate-propagate pipeline cuts human translation work by roughly 3×.

### Line length limits

| | |
|---|---|
| Modal line length | 8–16 full-width chars |
| 99th percentile | **16 full-width chars** |
| Lines per box | 3–4 |

16 full-width columns = 32 half-width columns. **In full-width Latin that's 16 English characters per line — unusable for real prose.** Half-width glyphs or a VWF are required for a quality release.

---

## 5. Executable text

All five EXEs, byte-swapped u16 SJIS:

| File | Strings | Full-width chars |
|---|---|---|
| SLPS_008.29 | 1,335 | 11,719 |
| MAIN1.EXE | 1,995 | 13,417 |
| KOUSEI.EXE | 1,755 | 13,019 |
| CASINO.EXE | 1,543 | 11,883 |
| KEIBA.EXE | 1,505 | 12,010 |
| **Union (deduped)** | **2,176** | **17,383** |

Massive cross-EXE duplication — save/load prompts, unit names, class names, monster tables are copy-pasted into all five. **Translate once, script the propagation into all five binaries.**

KOUSEI-exclusive text: 517 strings / 4,171 chars — skill descriptions, terrain/ambush strings, victory conditions (`０２：３０：００以内にクリア`), mission objectives.

### Fixed-width string tables

Name/class tables use fixed strides, space-padded with `0x8140` (full-width space):

| Table | Stride | Capacity |
|---|---|---|
| Unit names (KOUSEI 0xEF8D0…) | 0x10 | 8 full-width chars |
| Monster names (KEIBA 0x385FC…, CASINO 0x457C4…) | 0x14 | 10 full-width chars |
| Class names (MAIN1 0x6153C…) | 0x14 | 10 full-width chars |

**Hard caps** unless the tables are widened and every consumer's stride is patched. 8–10 characters is very tight for English unit/class names.

### Other EXE landmarks

- `SLPS_008.29 @ 0x5266E` — naming-screen character grid (gojūon kana layout, u16 LE). Needs replacing with a Latin grid.
- All EXEs share the save-file header strings (`「ＲＩＯＴ　ＳＴＡＲＳ」`, `序章クリア`, `ファイル１`).

---

## 6. Graphics files — all analysed, all clean

| File | Format | Contents | Text? |
|---|---|---|---|
| `IM.BIN` | 7 × TIM (5 × 8bpp 320×240 + 2 × 16bpp 320×240) | event CG backgrounds | none |
| `NA.BIN` | 11 × TIM (8bpp 320×240, 256×256, 256×240) | backgrounds / illustrations | none |
| `INICHR.BIN` | 14 × TIM (4bpp 256×256, 16 CLUTs each) + 78 KB offset/length table at 0x77000 | unit sprite sheets | none |
| `FACE.PXL` | raw 8bpp, **no header** — 10,320 rows × 256-byte stride, content 240 px wide, cols 240–255 are `0xDF` padding, ~80-row vertical period | character portraits; one large 2-colour logo/ornament graphic around 0x78000 | none |
| `INTER.BIN` | header `22 03 00 00 00 08 20 40`, then 8-byte tile descriptors `(u8 x, u8 y, u16 tpage, u16 0000, u16 clut)` with x/y stepping 8 px, x∈[0,248], y∈[0,240]; graphics from ~0xD221 in 0x8800-stride 4bpp 256×256 blocks | menu/window frames, icons, HUD; the descriptor table is a **screen-composition tilemap** built from 8×8 tiles | none |
| `EFFECT.BIN` | 3 × TIM (4bpp 256×256, 16 CLUTs) at 0x0/0x8800/0x11000, then an 81,920-byte descriptor/animation region from 0x19800 (header `aa 03 00 40 …`) | battle effect / particle sprites | none |

**None of these contain a font or any translatable text.** They require no work.

---

## 7. THE FONT — still not located ❗

This remains the open question that determines project scope. **All 12 available files have been checked.**

### Ruled out — with method

| Candidate | How it was ruled out |
|---|---|
| All 5 EXEs | Glyph-stride periodicity scan (18/24/32/36/48/72/128-byte strides), every candidate hit rendered manually — all structured tables, no glyphs. Cross-diff MAIN1 ↔ KOUSEI: largest shared block 17.5 KB, ~65 KB shared total — far too small for a kanji font. |
| `IM.BIN`, `NA.BIN`, `INICHR.BIN` | Parsed as TIM; all artwork. |
| `FACE.PXL` | Every 64-row block scanned for low-colour / hard-edged regions. The only 2-colour region (≈0x78000, values {0,14,15}) is a large decorative logo graphic, not a glyph grid. |
| `INTER.BIN` | Rendered at 1bpp 16×16 and 12×12 across all data regions — no glyphs. Structure is tilemap + 4bpp interface sprites. |
| `EFFECT.BIN` | 3 effect sprite sheets + sparse particle descriptors. Rendered at 1bpp — no glyphs. |
| **Any subset font anywhere** | **No SJIS→glyph lookup table exists in any file** — no sorted SJIS list, no sparse monotone index table. Also no `×188` / `×94` SJIS-index arithmetic and no 0x81/0x9F/0xE0 lead-byte range check in any EXE's instruction stream. |

### What this implies

Since each EXE overwrites the others at `0x80010000`, every EXE must independently obtain the font. The only data file loaded by *both* MAIN1 (town) and KOUSEI (battle) is `FACE.PXL` — and that's portraits. So either:

1. **`ZDATA.BIN` (27,972 KB) holds the font and is read by raw LBA** — it is the only file on the disc not referenced by any path string, which is exactly what LBA-addressed access looks like. On-demand glyph streaming from CD into a small VRAM font cache is a standard 1997 PSX technique and would explain the absence of both a resident font and a lookup table. **Leading hypothesis.**
2. The font is duplicated per-context in files not yet examined (`MATI.BIN`/`MISE.BIN`/`MAP*.BIN` for town, `BATOBJ.BIN`/`BATBG.BIN`/`LAST_B.BIN` for battle).

### Recommended next step: dump VRAM instead of guessing

Static analysis has hit diminishing returns. The decisive experiment is cheap:

1. Run the game in an emulator with a VRAM viewer — **no$psx**, **DuckStation debugger**, or **PCSX-Redux**.
2. Open a dialogue box so kanji are on screen. The font texture will be visible in VRAM.
3. Dump VRAM to a file, crop a few known glyphs, and **byte-search the raw disc files for that bitmap pattern**.

That pins the font's file *and* offset exactly, in about 20 minutes. It also immediately answers the question that actually matters:

> **Does the glyph renderer handle single-byte / half-width codes?**
>
> - **Yes** → insert half-width ASCII, 32 columns per line, the project is mostly done.
> - **No** → a VWF must be written into the text renderer in MIPS. Doable, but it becomes the main engineering task.

Watching whether the font region of VRAM is fully populated or refilled between screens will also settle hypothesis 1 (streamed glyph cache) vs 2 (resident font upload).

---

## 8. Reinsertion strategy

1. **SCRIPT.BIN** — dump per bank, translate, reinsert. Preserve all `FB`/`FC`/`FF` control codes. Keep every bank ≤ 0xA000 and the file at exactly 1,802,240 bytes. Tool must hard-fail on bank overflow (bank 41 has only 353 bytes of headroom).
2. **EXEs** — byte-swap, patch strings in place, byte-swap back. Respect fixed-stride table caps (§5).
3. **ISO** — rebuild with mkpsxiso. Files are opened by path, so positions can move — **except possibly ZDATA.BIN (§9)**.

---

## 9. Open questions / risks

| # | Item | Risk |
|---|---|---|
| 1 | **Font location & half-width support** | **HIGH** — determines whether this is a text-swap job or a renderer rewrite. Resolve via VRAM dump (§7). |
| 2 | **ZDATA.BIN (27,972 KB) is not referenced by name in any EXE.** Every other file is opened via a `\PATH\FILE.EXT;1` string. This one isn't. | **MEDIUM–HIGH** — likely raw-LBA access. If so, the ISO rebuild must preserve its exact sector position, or the base LBA must be patched. Also the leading font suspect. |
| 3 | "No pointer table" assumption unverified by disassembly | MEDIUM — cheap to confirm, expensive if wrong. |
| 4 | Semantics of the 50 × 18-byte bank header records | LOW — appear to be event/trigger metadata with index fields; probably untouched by translation. |
| 5 | Meaning of ~60 rarer control codes | LOW — preserve verbatim; only need to know which take inline arguments. |
| 6 | Untested files: `MATI.BIN`, `MISE.BIN`, `MAP*.BIN`, `SLOT.BIN`, `TRUMP.BIN`, `KEIBA.BIN`, `BATANM/BATBG/BATOBJ/HEXMAP/LAST_B.BIN`, `ZDATA.BIN` | LOW–MEDIUM — likely graphics, but may contain baked-in Japanese (shop signage, title screen, UI labels) and possibly the font. |
| 7 | Name-entry screen (`SLPS_008.29 @ 0x5266E`) is a kana grid | LOW — needs replacing with a Latin grid. |

---

## 10. Overall assessment

| Area | Difficulty | Notes |
|---|---|---|
| Script extraction / reinsertion | **Easy** | Uncompressed SJIS, no pointers, 69% free space, clean bank structure. A Python dumper/inserter is a weekend of work. |
| Translation volume | **Moderate** | ~30k English words of unique script + ~17k chars of UI/EXE text. |
| Font / VWF | **Unknown — likely the bulk of the engineering** | Blocked on locating the font. |
| Menus / fixed-width tables | Moderate | 8–10 char caps on names will need table widening. |
| Graphics | Low–Moderate | All six analysed asset files are clean. Remaining risk is title screen and any baked-in UI text in untested files. |
| ISO rebuild | Easy | Path-based loading; watch ZDATA.BIN. |

**Verdict: a favourable target.** Structurally this is one of the easier PSX SRPGs — no compression, no encryption, no pointer tables, enormous free space, and heavy text duplication that cuts translation workload by ~3×. Six graphics files have been cleared with zero work required. Difficulty is concentrated almost entirely in one unresolved question: where the font lives and whether it can render half-width characters.

---

## 11. Immediate next steps

1. **Dump VRAM in an emulator with a dialogue box on screen; byte-search the disc files for the glyph bitmaps.** This resolves risk #1 and probably #2 at the same time.
2. Determine half-width support in the glyph renderer.
3. Build the SCRIPT.BIN bank dumper/reinserter (control-code-aware, overflow-checked).
4. Disassemble the MAIN1.EXE message routine to confirm the no-pointer-table assumption.
5. Spot-check `MATI.BIN` / `MISE.BIN` / `ZDATA.BIN` / the remaining TACTICS set for baked-in Japanese.
