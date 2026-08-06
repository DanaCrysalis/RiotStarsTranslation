# Riot Stars (SLPS-00829) — Translation Feasibility Findings

**Status:** ✅ **24-COLUMN HALF-WIDTH ENGLISH RUNNING IN-GAME** (battle, KOUSEI.EXE)
✅ **ENGLISH MENUS + LATIN NAME ENTRY PATCHED, AWAITING FIRST TEST** (boot, SLPS_008.29)
**Last updated:** 2026-08-05 (chunk-loader session — HEXMAP read map, script RAM buffer, §23)
**Analysed:** all 17 disc files, 11 savestates (RAM + VRAM), rebuild3.xml

> ⚠️ **The copy of this file in the translation repo was several sessions out of date** — it
> still said the font was unlocated. Replaced 2026-08-05 with this version. If two copies ever
> disagree again, the one carrying the highest section number wins.

> **★ MILESTONE (2026-07-31): the dialogue box is 24 columns of 8 px mixed-case English.**
> `Search! / They must be close by!` renders, correctly positioned. Sprite width and pen advance
> are 8 px, the grid is 24×6 cells, the box is pixel-identical to stock (192×64), and the battle
> script has been reflowed to the wider box. See §15–§17.
> **★ The sprite emitter is NOT in the text engine.** It is a *generic tilemap renderer* at
> `0x800C19EC`, fully parametric and shared with other clients. **Never patch it.** Sprite width
> **and** pen advance are one value: descriptor byte `+0`. See §15.
> **★ THE MENU SIDE IS THE SAME PROBLEM.** SLPS_008.29 (boot) draws the new-game menu, the
> name-entry grid and the prompt strings through the *same* `Krom2RawAdd` expander
> (`0x8001E994`). It is a hook port, not new research. See §19.
> **★ Reclaim code, not zeros.** SLPS has only 724 bytes of genuinely free zero runs, but the
> dakuten/handakuten handlers are 1,276 contiguous bytes with exactly two entry points, both of
> which die when the grid stops being kana. See §20.3.
> **★ THE FONT QUESTION IS CLOSED.** The kanji font is not on the disc — the game calls the BIOS
> routine `Krom2RawAdd` (B-table 51h) per glyph. That call is hooked in KOUSEI.EXE. See §7, §14.
> **Free space in an EXE is not "wherever the zeros are."** Three black screens came from that
> assumption. A run is usable only if a savestate shows it unwritten, **and** no code references it,
> **and** it is not part of a fixed-stride record table. Appendix B — read before injecting.
> **Runtime scratch does not belong in the image.** Static data (font tables) must live in the EXE;
> runtime buffers belong in BSS. Getting this backwards cost a debugging cycle. See §16.3.
> **Compilers share subexpressions across computations that look unrelated.** One `win*9` feeding
> both a buffer stride and a struct index cost a day. See §16.2 and Appendix D.
> **Second script store LOCATED:** battle dialogue lives in `TACTICS/HEXMAP.BIN` — note its fixed
> internal chunk layout (§5); the unit table at +0x27000 must never move.

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
│   ├── INTER.BIN       224 KB   ✅ interface gfx + tilemap + ★8×8 ASCII FONT @0x16220 (§7)
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
│   ├── BATANM.BIN    2,314 KB   ✅ animation data — NO text (§5)
│   ├── BATBG.BIN     6,068 KB   ❓ untested
│   ├── BATOBJ.BIN    6,324 KB   ❓ untested
│   ├── EFFECT.BIN      182 KB   ✅ battle effect sprites (TIM)
│   ├── HEXMAP.BIN    7,852 KB   ★ BATTLE SCRIPT + map graphics, 46 chunks (§5)
│   ├── INICHR.BIN      552 KB   ✅ unit sprites + ★8×8 ASCII FONT @0x220 (§7)
│   └── LAST_B.BIN      814 KB   ✅ graphics — NO text (§5)
├── CASINO.EXE          358 KB   ✅ casino minigame
├── KEIBA.EXE           322 KB   ✅ horse-racing minigame
├── KOUSEI.EXE        1,048 KB   ✅ battle engine
├── MAIN1.EXE           556 KB   ✅ town / overworld engine
├── SLPS_008.29         438 KB   ✅ boot executable
├── SYSTEM.CNF            1 KB
└── ZDATA.BIN        27,972 KB   ⚠️ NOT referenced by name anywhere — see §10
```

### File loading

All EXEs open data files **by CD path string** through the ISO9660 directory
(`\IMDATA\SCRIPT.BIN;1`, `cdrom:\MAIN1.EXE;1`). No hardcoded LBAs for these files, so
**an mkpsxiso rebuild is straightforward** — they can move.

| EXE | Loads |
|---|---|
| SLPS_008.29 (boot) | CASINO, KEIBA, KOUSEI, MAIN1, SOUND.EXE\*, all IMDATA, FACE.PXL |
| MAIN1.EXE | KOUSEI/CASINO/KEIBA/SLPS, all IMDATA, FACE.PXL |
| CASINO.EXE / KEIBA.EXE | all IMDATA, FACE.PXL |
| KOUSEI.EXE | **FACE.PXL + TACTICS/\*.BIN only** (no IMDATA) |

\* `cdrom:\SOUND.EXE;1` is referenced by SLPS_008.29 but **no such file exists on the disc** — dead reference.

All five EXEs load at `0x80010000` and overwrite one another. There is no resident kernel EXE.
This is why the font has to exist in *two* places — INTER.BIN for the IMDATA-side engines and
INICHR.BIN for the TACTICS-side engine (§7).

---

## 3. Text encoding — CRITICAL

All text is **plain Shift-JIS**. No compression, no DTE, no custom table, no encryption.
**But byte order differs by store:**

| Store | Layout | Example (`よ` = SJIS 0x82E6) |
|---|---|---|
| `SCRIPT.BIN` | standard SJIS byte order | `82 E6` |
| All 5 EXEs | **u16 little-endian (byte-swapped)** | `E6 82` |
| **Battle script (§5)** | **u16 little-endian (byte-swapped)** | `E6 82` |

Text is stored as C `unsigned short[]`, so MIPS little-endian order applies. Open an EXE in a
normal SJIS-aware hex editor and you get garbage like `＝モリゼ゛ゼ”` where the real text is
`メモリカード`.

**This is the single biggest trap in the project.** Anyone who misses it will conclude the
executables are encrypted. Swap every byte pair before decoding; swap back on reinsertion.

ASCII strings in the EXEs (debug printf, file paths, `TIME   :  : 0`) are stored **normally** —
they're `char[]`, not `unsigned short[]`.

### Character set
- 1,426 unique SJIS codes in SCRIPT.BIN (1,183 kanji, 155 kana, rest punctuation/symbols)
- Full-width Roman `Ａ-Ｚ` `ａ-ｚ` `０-９` already in use (`「ＲＩＯＴ　ＳＴＡＲＳ」`, `ＮＵＭＢＥＲ１`)
- **A proof-of-concept English build needs zero font work** — insert full-width Latin. Cramped, but it displays. (Verified end-to-end with the tool in §9.)

---

## 4. SCRIPT.BIN — main script

**Size:** 1,802,240 bytes = **exactly 44 banks × 0xA000 (40,960 bytes)**.
The game seeks to bank *N* at file offset `N × 0xA000` (= sector `N × 20`) and reads 40 KB.
**Keep the bank layout and total file size identical.**

### Bank layout
```
+0x0000   50 × 18-byte event records (900 bytes = 0x384)
          each record: FF FC + 8 × u16 BIG-ENDIAN
          field values are small (max ~108) → IDs/indices, not byte offsets
+0x0384   command stream with INLINE TEXT
...       zero padding to 0xA000
```
- 43 of 44 banks have exactly 50 header records.
- **Bank 40 (0x190000) has no header** — pure string pool (system/UI text).
- Banks 42–43 hold class/item/weapon/armour descriptions.

### Control codes
Lead bytes `0xFB`–`0xFF`, **outside the SJIS lead ranges** (0x81–0x9F, 0xE0–0xEF), so parsing is
unambiguous. 72 distinct 2-byte codes.

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

Argument lengths are **not fixed per code** (verified by scanning what follows each code across
the whole file), so tooling must tokenise losslessly rather than assume a table. `FC B0` and
`FB 00` reliably take 4 arg bytes; `FF xx` codes mostly take 2.

### No pointer table
**No absolute pointer table for strings exists** — not in SCRIPT.BIN, not in the EXEs. Text is
inline in the command stream; header records hold only small index-like values.
**String lengths can therefore be changed freely with zero repointing** — normally the single
largest cost in a PSX project.
⚠️ *Still unverified by disassembly of the message routine.* Cheap to confirm; expensive if wrong.

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

### Script volume (measured by the §9 tool)
| | |
|---|---|
| Total stored text | **220,240 full-width characters** |
| Message instances | **7,931** |
| Unique messages | **1,430 (82% duplication)** |
| Unique text | **~65,000 characters** |
| Rough English equivalent (unique only) | **25,000–35,000 words** |

Duplication is structural: class/item/weapon description tables are replicated verbatim across
chapter banks. `ダミーぶきです` appears 126×, `ダミーぼうぐです` 84×, class descriptions 21× each.
A dedupe-translate-propagate pipeline cuts human translation work ~3×.

### Line length limits
| | |
|---|---|
| Modal line length | 8–16 full-width chars |
| 99th percentile | **16 full-width chars** |
| Lines per box | 3–4 |

Confirmed against the live framebuffer: glyph advance measured at **~15–16 px** on a 320-px-wide
screen, three lines in the box. 16 full-width columns = 32 half-width columns.

---

## 5. ★ SECOND SCRIPT STORE — battle events (LOCATED)

**Host file: `TACTICS/HEXMAP.BIN` (7,852 KB).** Confirmed by locating the on-screen line
`探せっ！このあたりに逃げ込んだはずだ！` at **file offset 0x25022**.

`LAST_B.BIN` and `BATANM.BIN` contain **no dialogue at all** (zero `FC51`/`FC50` occurrences;
earlier marker counts were coincidental byte patterns in graphics data). BATANM is pure
animation data.

### Byte order — important correction

HEXMAP.BIN stores the battle script in **normal Shift-JIS byte order, exactly like SCRIPT.BIN.**
The byte-swapped form seen in the savestate is produced by the *loader* on the way into RAM;
the on-disc layout is standard. **No byte-swap layer is needed for this file** — the SCRIPT.BIN
tokeniser ports directly.

### Container structure — VERIFIED INTERNAL LAYOUT

HEXMAP.BIN is **46 fixed-size map chunks of 0x2A800 (174,080) bytes** (= 5 × 0x8800 texture
blocks). **44 of the 46 carry dialogue** — corrected 2026-08-05, see §23.3; the earlier 43 was a
tooling artefact. The "5 × 0x8800 texture blocks" gloss is also wrong: there are three TIMs and
then two non-TIM regions (§23.1). Every script-bearing chunk has the same fixed internal layout:

```
chunk + 0x00000   map graphics (TIM)
chunk + 0x25000   event script             <- sector 74, 8,192-byte slot
chunk + 0x27000   unit / deployment data   <- sector 78, FIXED OFFSET
```

⚠️ **The unit/deployment table at +0x27000 is read by the engine at a hardcoded offset.** The
script may grow only inside its 8,192-byte slot. If script growth pushes that table even a few
bytes, the map loads garbage units and the game hangs on a black screen (music keeps playing,
since audio is a separate task). This was hit for real during the first test build; see §9.

### Volume

| | |
|---|---|
| Chunks with script | 43 |
| Messages | 437 |
| Stored characters | **42,759** |
| Unique messages | 411 |
| Unique characters | **42,349 (only 1% duplication)** |

Unlike SCRIPT.BIN's 82% duplication, the battle script is almost entirely unique text — there is
no ~3× saving here. Budget it as ~42,000 characters of real translation work.

### Script headroom (corrected)

Measured against the real slot boundary (0x25000–0x27000), not the chunk end:

| | |
|---|---|
| Total headroom across script chunks | **228,421 bytes (223 KB)** |
| Median headroom per chunk | **5,617 bytes** |
| Minimum headroom (worst chunk) | **1,071 bytes** |

An earlier revision of this document reported 47 KB total / 1,027 bytes median. That was
measured to the wrong boundary and understated the real room by roughly 5×.

Budget: the 43 script slots hold 42,759 stored Japanese characters (85,518 bytes) with 223 KB
of headroom, so the working budget is ~309 KB. English at half-width needs roughly 77 KB, at
full-width roughly 154 KB. **Both fit** — the earlier claim that full-width English overflows
31 of 43 chunks was an artefact of the same measurement error. Half-width remains strongly
preferable for readability (§4 line limits), not for space.

---|---|
| Total trailing free across script chunks | **48,481 bytes (47 KB)** |
| Median free per chunk | **1,027 bytes** |
| Minimum free (worst chunk) | **247 bytes** |

This is the opposite of SCRIPT.BIN's 69% slack. Per-chunk budget analysis
(existing JA text bytes + free space vs. estimated English need at 1.8 chars per JA char):

| Encoding | Chunks that overflow |
|---|---|
| **Half-width English** | **0 of 43** — fits with room to spare (~77 KB needed vs 134 KB budget) |
| **Full-width English** | **31 of 43 overflow** (~154 KB needed vs 134 KB budget) |

**Conclusion: the full-width-Latin proof-of-concept shortcut works for SCRIPT.BIN but will not
fit the battle script.** Half-width rendering (§7) is a hard requirement for HEXMAP.BIN, not a
quality preference.

---

## 6. Graphics files — analysed, all clean

| File | Format | Contents | Text? |
|---|---|---|---|
| `IM.BIN` | 7 × TIM (5 × 8bpp 320×240 + 2 × 16bpp 320×240) | event CG backgrounds (e.g. chapter title on a flag: `第１章 結成！第９軍`) | **chapter titles are baked into the CG** |
| `NA.BIN` | 11 × TIM (8bpp 320×240, 256×256, 256×240) | backgrounds / title art incl. `PUSH START BUTTON`, `©HECT 1997` | some baked Latin |
| `INICHR.BIN` | 14 × TIM (4bpp 256×256, 16 CLUTs each) + 78 KB offset/length table at 0x77000 | unit sprite sheets — **and the 8×8 font (§7)** | font only |
| `FACE.PXL` | raw 8bpp, no header — 10,320 rows × 256-byte stride, content 240 px wide, cols 240–255 are `0xDF` padding, ~80-row vertical period | character portraits | none |
| `INTER.BIN` | header `22 03 00 00 00 08 20 40`, 8-byte tile descriptors `(u8 x, u8 y, u16 tpage, u16 0000, u16 clut)` stepping 8 px, then 4bpp graphics in 0x8800-stride blocks | menu/window frames, HUD tilemap — **and the 8×8 font (§7)** | font only |
| `EFFECT.BIN` | 3 × TIM (4bpp 256×256) at 0x0/0x8800/0x11000, then 81,920-byte animation descriptor region from 0x19800 (`aa 03 00 40 …`) | battle effect / particle sprites | none |

Chapter-title CGs in `IM.BIN` and the title art in `NA.BIN` will need image editing.

---

## 7. ★ THE FONT — RESOLVED

### The half-width font exists, in two copies

A complete **8×8, 4bpp, ASCII-ordered font** is embedded as the first TIM of two files:

| File | Font sheet offset | Loaded by |
|---|---|---|
| `IMDATA/INTER.BIN` | **0x16220** | SLPS_008.29, MAIN1, CASINO, KEIBA |
| `TACTICS/INICHR.BIN` | **0x220** | KOUSEI (battle) |

Byte-identical glyph data in both — the duplication exists precisely because the EXEs overwrite
each other and each side of the game needs its own copy. **Between them, every engine has it.**

Layout: 4bpp, sheet 256 px wide (128-byte rows), glyph cells 8×8, laid out 32 per row in
**straight ASCII order starting at 0x20**:

```
band 0 (rows  0- 7) = 0x20–0x3F   space ! " # $ % & ' ( ) * + , - . / 0-9 : ; < = > ?
band 1 (rows  8-15) = 0x40–0x5F   @ A B C D E F G H I J K L M N O P Q R S T U V W X Y Z [ \ ] ^ _
band 2 (rows 16-23) = 0x60–0x7F   ` a b c d e f g h i j k l m n o p q r s t u v w x y z { | } ~
band 3+            = half-width katakana
```

Verified by decoding cells directly: cell 0 of band 1 renders `@`, cell 1 `A`, cell 2 `B` … cell 23 `W`.
Confirmed resident in VRAM during battle at halfword **(960, 0)**, matching INICHR's TIM header.

### The half-width renderer exists and is in use

`KOUSEI.EXE @ 0x8002FF88` is a **single-byte string draw routine**:

```
0x8002FFF4  lui   $s7, 0x8016
0x8002FFF8  addiu $s7, $s7, 0x50FC      ; s7 = 0x801650FC  → text tilemap buffer
0x80030000  jal   0x800BD880            ; strlen(str)
0x80030014  lbu   $v0, ($a0)            ; c = str[i]
0x8003001C  addiu $v0, $v0, 0x22
0x80030024  sltiu $v0, $v0, 2           ; special-case c == 0xDE / 0xDF
                                        ;   (half-width dakuten / handakuten)
0x8003006C  ori   $v0, $zero, 0x20
0x80030070  beq   $v1, $v0, ...         ; special-case space
0x80030090  addu  $v0, $v0, $s5         ; tile index = char code + base
0x800300A4  sh    $v0, ($v1)            ; store u16 tile index into the tilemap
```

Index into the tilemap is `row * width + col`, width read from `0xF30($gp)`.
**Each character is one tile, addressed directly by its byte value.** That is a complete
half-width text pipeline: single-byte in, 8×8 glyph out.

It is demonstrably live: `KOUSEI.EXE @ 0x800229A0` calls it with the ASCII string
`"TIME   :  : 0"` (stored at `0x800100B4`) to draw the battle timer. English UI strings
(`Battle Results`, `Player`, `Enemy`, `Reward`, `Bonus`, `Coins`, `Wait:`) are visible in VRAM.

### The engine also converts full-width → half-width

`KOUSEI.EXE @ 0x8003174C` maps full-width codepoints to single bytes:
`0x8140 → 0x20` (space), `0x815B → 0xB0` (half-width ー), `0x817B → 0x2B` (+), `0x817C → 0x2D` (−).
The engine natively round-trips between the two width domains.

### ★★ THE KANJI FONT IS IN THE PLAYSTATION BIOS — not on the disc

Traced end to end from the savestate. The chain:

**1. Text is drawn one character at a time as a textured sprite.** GPU primitive at RAM `0x801B06C4`:

```
E1 draw-mode 0x000215  -> texture page X=320 halfwords, Y=256, 4bpp
sprite cmd   0x64      -> textured rectangle, variable size
             (112,152) -> screen pos, u=0x00 v=0x80, 16x16, CLUT 0x7C03
```

**2. The source is a 256-slot on-demand glyph cache** at VRAM **(320, 256)** — a 256×256 4bpp
page, only colour indices 0 and 15 used. Rendering it reproduces on-screen 探 pixel-for-pixel.
Proven dynamic across three savestates:

| State | Slots occupied |
|---|---|
| dialogue, message 1 | **19** / 256 |
| dialogue, message 2 | **26** / 256 (7 new glyphs) |
| in-battle status screen | **91** / 256 (different set) |

**3. Glyphs are expanded through a staging buffer.** One of the 7 newly-uploaded glyphs was found
in RAM at **`0x80164DC8`** in 4bpp-expanded form (128 bytes) — the game expands one glyph at a
time, then `LoadImage`s a 4-halfword × 16-row rect into the cache slot (`KOUSEI.EXE @ 0x8001C174`).

**4. The glyph bitmaps come from `Krom2RawAdd`.** The expander at `KOUSEI.EXE 0x80015CF0` does:

```
jal   0x800BD688          ; a0 = Shift-JIS code
move  $v1, $v0            ; v1 = returned POINTER to glyph data
lhu   $v0, ($v1)          ; read 16 halfwords = 32 bytes = 16x16 1bpp
```

And `0x800BD688` is a **PlayStation BIOS call stub**:

```
addiu $t2, $zero, 0xB0    ; B-table
jr    $t2
addiu $t1, $zero, 0x51    ; function 51h
```

**`B(51h)` is `Krom2RawAdd(shiftjis_code)` — the BIOS routine that returns a pointer to the
16×16 kanji glyph in the console's built-in kanji ROM.**

Present in **all five executables**:

| EXE | Stub | Called from |
|---|---|---|
| KOUSEI.EXE | 0x800BD688 | 0x80015DA0, 0x80015F40 |
| MAIN1.EXE | 0x8004587C | 0x8003A578 |
| SLPS_008.29 | 0x8002CD08 | 0x8001E9F0 |
| CASINO.EXE | 0x8002C468 | 0x8002381C |
| KEIBA.EXE | 0x8002B51C | 0x80023ABC |

### → Implementation: see §14

The analysis below identified the BIOS call. §14 records the **working hook** built on top of it:
the injected routine, the empirically confirmed glyph format, the half-width patch, and the
renderer map (including a correction — there are *two* independent grids, not one).

### Why every earlier search failed — and why this is good news

There is no kanji font on the disc because **the game never shipped one**. It borrows the
Japanese PS1 BIOS kanji ROM at runtime. This retrospectively explains every negative result:
no font in any of the 17 files, none in RAM, none in VRAM beyond the small live cache, and **no
SJIS→glyph lookup table anywhere** — the BIOS does the lookup.

It also **eliminates ZDATA.BIN as the font suspect entirely.**

**The consequence for translation is excellent.** `Krom2RawAdd` is a single, well-defined call
returning a pointer to 32 bytes of 1bpp bitmap. To render English you do not touch the BIOS —
you replace that call with your own routine returning a pointer into a custom font table placed
in free space in the EXE. Five call sites, all listed above. The renderer downstream is
completely agnostic about what the glyph looks like.

Half-width then falls out of the same work: the sprite primitive already carries explicit width
(`w=16`) and per-character screen X, so narrowing is a matter of emitting `w=8` and advancing the
pen by 8 — no new renderer, no VWF engine written from scratch.

Note the second KOUSEI call site (`0x80015F40`) is a separate expander with a different colour
setup — likely the shadowed/outlined variant. Both need the same patch.

### Independent half-width asset already present

The 8×8 ASCII font in INTER.BIN (0x16220) and INICHR.BIN (0x220) remains available for
tilemap UI text (§7 above), and `KOUSEI.EXE 0x8002FF88` already renders single-byte strings
through it. Two independent half-width routes now exist.

---|---|
| dialogue, message 1 | **19** / 256 |
| dialogue, message 2 (58 bytes later) | **26** / 256 (7 new glyphs appear) |
| in-battle status screen | **91** / 256 (a completely different set) |

Everything else in VRAM is byte-identical across all three states — only the framebuffers and
this one texture page ever change. Text is drawn as one 16×16 textured sprite per character.

**This explains every earlier negative result.** There is no font atlas in any file because
nothing ever holds the whole font; glyphs are fetched per character as needed. It also explains
the absence of any SJIS→glyph lookup table — with on-demand fetch, the code computes a source
address arithmetically instead.

### Source of the glyph data — the one remaining unknown

The 19 cached glyph bitmaps were packed to 1bpp (32 bytes each, both bit orders) and searched
across **all 15 available files and the full 2 MB of main RAM. Zero matches.** So the data is
neither resident in RAM at draw time nor in any file examined so far.

KOUSEI.EXE (the engine resident during battle) opens exactly:

```
\IMDATA\FACE.PXL          ✅ checked      \TACTICS\EFFECT.BIN   ✅ checked
\MUSIC\BATTLE0[1-5].SEQ   (audio)        \TACTICS\HEXMAP.BIN   ✅ checked
\TACTICS\BATANM.BIN       ✅ checked      \TACTICS\INICHR.BIN   ✅ checked
\TACTICS\BATBG.BIN        ❌ NOT CHECKED  \TACTICS\LAST_B.BIN   ✅ checked
\TACTICS\BATOBJ.BIN       ❌ NOT CHECKED
```

By elimination the battle-side font is in **`BATBG.BIN` or `BATOBJ.BIN`** — or in **`ZDATA.BIN`
by raw LBA**, which is the only file no EXE names.

A numerical coincidence worth noting for ZDATA.BIN: 27,972 KB = **13,986 sectors of 2048 bytes**.
JIS Level 1+2 is 6,879 glyphs; at two font sizes that is 13,758 glyphs — within 1.7% of the
sector count. One glyph per sector would make LBA addressing pure arithmetic and require no
lookup table, matching the observed absence of one. Storing 32 bytes in a 2048-byte sector is
wasteful, but on a disc with room to spare it buys a single-read glyph fetch. **Hypothesis, not
yet confirmed.**

### Precedent for duplication

MAIN1.EXE (town) cannot read `TACTICS/`, so it needs its own access to the font. The 8×8 ASCII
font is duplicated exactly this way (INTER.BIN for IMDATA-side, INICHR.BIN for TACTICS-side), so
expect either a second copy in an IMDATA file (`MATI.BIN`, `MISE.BIN`, `MAP*.BIN`, `SLOT.BIN`,
`TRUMP.BIN`, `KEIBA.BIN`) or a shared LBA-addressed source — which would favour the ZDATA
hypothesis, since one LBA-addressed font serves every engine without duplication.

### Why this is good news for the project

A 256-slot cache addressed by a per-character sprite draw is *easier* to retarget than a
fixed-width tilemap. The renderer already issues one textured sprite per character with
independent screen X, width, and UV. Narrowing a glyph to half-width is a matter of changing the
sprite's width and the pen advance — the primitive format already supports it.

---

## 8. Executable text

All five EXEs, byte-swapped u16 SJIS:

| File | Strings | Full-width chars |
|---|---|---|
| SLPS_008.29 | 1,335 | 11,719 |
| MAIN1.EXE | 1,995 | 13,417 |
| KOUSEI.EXE | 1,755 | 13,019 |
| CASINO.EXE | 1,543 | 11,883 |
| KEIBA.EXE | 1,505 | 12,010 |
| **Union (deduped)** | **2,176** | **17,383** |

Massive cross-EXE duplication — save/load prompts, unit names, class names, monster tables are
copy-pasted into all five. **Translate once, script the propagation into all five binaries.**
KOUSEI-exclusive: 517 strings / 4,171 chars (skill descriptions, terrain/ambush strings, victory
conditions like `０２：３０：００以内にクリア`).

### Fixed-width string tables
Space-padded with `0x8140` (full-width space):

| Table | Stride | Capacity |
|---|---|---|
| Unit names (KOUSEI 0xEF8D0…) | 0x10 | 8 full-width chars |
| Monster names (KEIBA 0x385FC…, CASINO 0x457C4…) | 0x14 | 10 full-width chars |
| Class names (MAIN1 0x6153C…) | 0x14 | 10 full-width chars |

**Hard caps** unless the tables are widened and every consumer's stride is patched — *but* if the
field is switched to half-width these become 16 and 20 characters, which is workable.

### Other landmarks
- `SLPS_008.29 @ 0x5266E` — naming-screen kana grid (gojūon layout, u16 LE). Needs a Latin grid.
- All EXEs share save-file header strings (`「ＲＩＯＴ　ＳＴＡＲＳ」`, `序章クリア`, `ファイル１`).

---

## 9. Tooling — built and verified

### `riotscript.py` — SCRIPT.BIN (main script)
Commands: `dump`, `insert`, `verify`, `unique`.

Design notes:
- **Lossless by construction.** A SJIS pair is accepted as text only if it survives a
  decode→encode round trip byte-for-byte; anything else becomes a raw `{=XX}` tag.
  `verify` confirms `insert(dump(x)) == x` — **byte-identical, 1,802,240 bytes**.
- **Overflow guard.** Reinsertion recomputes each bank against 0xA000 and hard-fails with a
  per-bank report rather than writing a corrupt file. Tested by overstuffing bank 41.
- Header block preserved per bank as `{HDR:…}`, padding as `{PAD n}`, control codes as `{FFFE}` etc.
- Verified: an edit changes only its own bank and preserves total file size.

**Known behaviour:** full-width Latin round-trips as readable text; half-width ASCII inserts
correctly but re-displays as `{=54}{=68}…` raw tags on a second dump (single bytes aren't SJIS
pairs). Bytes are correct either way.

Outputs: `script_dump.txt` (976 KB, all 44 banks, editable) and `script_unique.txt`
(377 KB, 1,430 unique messages by frequency — the translate-once worklist).

### ✅ Proof-of-concept build (2026-07-30)

First English text confirmed on screen. `探せっ！/ このあたりに / 逃げ込んだはずだ！` replaced with
full-width Latin `ＳＥＡＲＣＨ！/ ＴＨＥＹ　ＭＵＳＴ　ＢＥ / ＣＬＯＳＥ　ＢＹ！`, rebuilt via
mkpsxiso, renders correctly in the first battle with the portrait and box intact.

**No executable patching was needed** — the PS1 BIOS kanji ROM already contains full-width Latin,
so English displays through the untouched `Krom2RawAdd` path. This validates: script tokenising,
length-changing reinsertion, dedupe propagation (the edit hit 2 sites across 2 chunks), file-size
preservation, and the ISO rebuild.

It also confirms the readability problem first-hand: full-width Latin is ~16 characters per line
and `ＴＨＥＹ　ＭＵＳＴ　ＢＥ` alone consumes 12 of them. Usable as proof, not as a release.

**Bug found and fixed during this build.** The first attempt black-screened. Cause: the tool
treated "script" as everything up to the last non-zero byte in the chunk, which swallowed the
unit/deployment table at +0x27000; an 18-byte text expansion shifted that table and the map
failed to load. `verify` did not catch it because it only tests that an *unchanged* dump
round-trips — it never exercised a length change, and the overflow guard was checking the chunk
boundary rather than the script slot. Both are fixed, and `checkedit` now exists specifically to
catch this class of error:

```
python3 riotbattle.py checkedit HEXMAP.BIN HEXMAP_new.BIN
→ OK — 9200 bytes changed, all inside script slots. Safe to build.
```

**Run `checkedit` before every build.** It fails loudly if anything outside a script slot moves.

### `riotbattle.py` — HEXMAP.BIN (battle script)
Commands: `dump`, `insert`, `verify`, `checkedit`, `stats`, `unique`.

Same losslessness guarantee — `verify` confirms a **byte-identical 8,040,448-byte** round trip.
Chunk-aware (0x2A800), with a hard-fail overflow guard tested by overstuffing chunk 0.
Each chunk's map graphics are referenced as `{PRE n}` (n bytes copied from the original file)
rather than embedded, and runs of raw command bytes are coalesced into single `{=hex}` tags,
which keeps the dump to 1.8 MB instead of 17 MB.

Outputs: `battle_dump.txt` (1.8 MB, 43 chunks, editable) and `battle_unique.txt`
(225 KB, 429 unique messages).

### `riotfont.py` — font hook, free-space analysis, script case conversion

Built this session. Commands:

| Command | Purpose |
|---|---|
| `info EXE` | locate the `Krom2RawAdd` stub and every `jal` call site |
| `findspace EXE [MIN]` | list zero runs (candidates only — **not** proof of free space) |
| `liveness EXE SAV...` | compare those runs against main RAM in DuckStation savestates |
| `xref EXE [ADDR...]` | find every address code can construct (lui+imm pairs, pointer constants) |
| `hook EXE OUT --addr A` | inject a single fixed test glyph (region probe) |
| `hookfont EXE OUT --sav S` | **production** font hook; auto placement requires savestate evidence |
| `halfwidth EXE OUT [--glyph-only] [--revert]` | narrow the glyph and its VRAM cell |
| `fullwidth FILE [OUT]` / `-t "text"` | ASCII → full-width SJIS (leaves `{tags}` and `#` lines alone) |
| `sentencecase FILE` | full-width ALL-CAPS → sentence case, Japanese untouched |
| `replace FILE "old" "new"` | substitute text, converting both sides to full-width |
| `findtext FILE "text"` | search any binary for text in full-width SJIS, several capitalisations |

`findtext` is the fastest way to localise a "*I changed it and nothing happened*" failure: run it on
the extracted file, then the rebuilt ISO. (First use of it caught a wrong-ISO copy in seconds.)

Session-3 commands for the boot EXE (`slpsmap`, `namegrid`, `menutext`, `prompttext`, `gridsim`,
`deadcode`) are documented in §22.

All injected MIPS is verified before it ships by an in-tool R3000 simulator that **enforces the load
delay slot**. This is not optional rigour — see §14's bug log.

---

## 10. Reinsertion strategy

1. **SCRIPT.BIN** — via `riotscript.py`. Preserve all `FB`/`FC`/`FF` codes, keep each bank ≤ 0xA000
   and the file at exactly 1,802,240 bytes.
2. **Battle script (§5)** — identify the host TACTICS file, then reuse the tokeniser with a
   byte-swap layer.
3. **EXEs** — byte-swap, patch strings in place, byte-swap back. Respect stride caps (§8).
4. **Font (dialogue)** — via `riotfont.py hookfont` against a **pristine** KOUSEI.EXE. Never hook an
   already-hooked EXE: the payload occupies free-space runs, so a second pass would stack a copy
   (the tool detects this and refuses). Always keep the patched output under a different filename.
4b. **Font (8×8 sheet, UI/menus)** — 4bpp at a known offset in INTER.BIN (0x16220) and INICHR.BIN
   (0x220); both copies must be patched identically if glyphs are redrawn. This is a *separate*
   path from the dialogue font — the bottom-of-screen HUD does not go through `Krom2RawAdd`.
5. **ISO** — rebuild with mkpsxiso using `rebuild3.xml`. Files load by path so positions can move.
   `ZDATA.BIN` is listed **last**, followed by `<dummy sectors="150"/>`; since both tools rebuild
   SCRIPT.BIN and HEXMAP.BIN at byte-identical sizes, everything before ZDATA keeps its length and
   ZDATA's LBA is preserved automatically. **Rule: never change any file's size.** Note the XML
   carries no LBA attributes, so it records order, not addresses.

---

## 11. Open questions / risks

| # | Item | Risk |
|---|---|---|
| 1 | ~~Retarget the dialogue renderer to half-width~~ **PARTLY RESOLVED** — glyphs are now 8 px wide (§14). What remains is the **on-screen pen advance and column count**: the box is still 12 columns with a 16 px step, so half-width buys shape, not line length yet. | **MEDIUM** |
| 1a | **Widen the dialogue box 12 → 24 columns.** Requires ~14 coupled constants (inventory in §14) *plus* the sprite width / pen advance in the generic drawing module, which is **not** in the text engine and is still unlocated. | **MEDIUM** |
| 1b | ~~Glyph-data source unidentified~~ **RESOLVED** — BIOS `Krom2RawAdd`, five call sites located (§7), hook implemented (§14). | CLOSED |
| 1c | **Half-width breaks BIOS fallthrough glyphs.** With the expander patched, any code falling through to `Krom2RawAdd` (kanji, kana) renders **left half only**. Keep a full-width build (`halfwidth --revert`) for reading untranslated sections during the project. | LOW — cosmetic, dev-time only |
| 2 | ~~Battle script host unidentified~~ **RESOLVED** — `HEXMAP.BIN`, 42,349 unique chars, tooling built (§5, §9). Residual risk is the tight per-chunk free space. | LOW |
| 3 | **ZDATA.BIN (27,972 KB) not referenced by name in any EXE.** **No longer a font suspect** (§7) — most likely disc padding. **Mitigated for the rebuild:** both tools preserve exact file sizes, and `rebuild3.xml` places ZDATA.BIN last, so its LBA is unchanged as long as nothing before it is resized. | LOW |
| 4 | "No pointer table" assumption unverified by disassembly | MEDIUM — cheap to confirm |
| 4b | **Font payload placement rests on one savestate** for 0x80105448. It is xref-clean and unwritten in that state, but only 0x800F3ECC is *execution*-proven. Cheap upgrade: pass more savestates to `liveness` (different scenes, no extra play needed). | LOW–MEDIUM |
| 5 | Baked-in Japanese in chapter-title CGs (`IM.BIN`) and title art (`NA.BIN`) | LOW–MEDIUM — image editing |
| 6 | Untested files: `MATI.BIN`, `MISE.BIN`, `MAP*.BIN`, `SLOT.BIN`, `TRUMP.BIN`, `KEIBA.BIN`, `BATBG/BATOBJ.BIN` | LOW–MEDIUM |
| 7 | Semantics of the 50 × 18-byte bank header records | LOW — event metadata, probably untouched |
| 8 | ~60 rarer control codes | LOW — preserve verbatim |
| 9 | ~~Name-entry screen kana grid~~ **RESOLVED** — 10×6×2 data-driven grid at `0x80061E6C` with a parallel attribute table; Latin layout shipped (§20, `riotfont.py namegrid`) | CLOSED |
| 10 | **Name field is capped at 7 full-width characters** (8 × u16 with a `0xFFFE` sentinel, §20.1). Short for English names; widening means auditing every consumer of the 16-byte record across all five EXEs. | MEDIUM |
| 11 | **SLPS half-width not started.** Space is secured (§20.3) and `0x8001EAF8` is the `LoadImage` width, but the expander's right-half-byte skip (KOUSEI `0x80015E78`) is not yet located in SLPS. | MEDIUM |
| 12 | **Name-prompt fragment rectangle unconfirmed** — assumed 10 chars; the emitter was not located (§21). Visible immediately in the first test build. | LOW |
| 13 | `simcheck` / `renderer` / `windiag` **not re-run** after the shared-`R3000` extension (KOUSEI.EXE unavailable this session). Re-run once before trusting the merged tool on the battle side. | LOW–MEDIUM |

---

## 12. Overall assessment

| Area | Difficulty | Notes |
|---|---|---|
| Script extraction / reinsertion | **Easy — done** | Tool built and round-trip verified. |
| Translation volume | **Moderate** | ~65k unique chars main script + 42k unique chars battle script + 17k chars EXE = **~124,000 unique Japanese characters ≈ 50,000–60,000 English words**. |
| Half-width font (UI) | **Solved** | Already in the game, ASCII-ordered, in files every engine loads. |
| Dialogue font (custom glyphs) | **Solved — running** | `Krom2RawAdd` hooked; 88 glyphs incl. lowercase in 1,064 bytes (§14). |
| Dialogue line length | **Moderate — open** | Glyphs are 8 px but the pen still steps 16 px and the box is 12 columns (§14). |
| Menus / fixed-width tables | Moderate | 8–10 full-width caps → 16–20 half-width if converted. |
| Graphics | Low–Moderate | Chapter-title CGs and title art need editing; sprite/effect files are clean. |
| ISO rebuild | Easy | Path-based loading; watch ZDATA.BIN. |

**Verdict: a favourable target, materially better than it looked at the start.** No compression, no
encryption, no pointer tables, 69% free space, 82% text duplication, a verified lossless script
tool, and — the decisive finding — a complete half-width ASCII font *plus* a working single-byte
renderer already shipping in the game. The nightmare scenario for this kind of project (write a VWF
from scratch against an unknown font) is off the table. What remains is ordinary romhacking work.

**Update after the font session:** the dialogue font is no longer a question at all — custom glyphs,
including lowercase, render in-game from an injected routine, with graceful fallthrough to the BIOS
for untranslated Japanese. The one substantive engine task left is widening the message box, which
is bounded, enumerable work (§14) rather than research.

---

## 13. Immediate next steps

1. ~~Trace the dialogue box renderer~~ **DONE** (§7). ~~`Krom2RawAdd` replacement~~ **DONE — shipping** (§14).
2. ~~Locate the sprite emitter; sprite width + pen advance 16 → 8~~ **DONE** (§15).
3. ~~Widen the box 12 → 24 columns~~ **DONE — shipping** (§16).
4. ~~Reflow the script for the wider box~~ **DONE** (§17, `riotfont.py rewrap`).
4b. ~~Menu / name-entry text path~~ **DONE** (§19–§21). **Test the boot build** —
   `namegrid` → `menutext` → `prompttext`, then `gridsim` must print `RESULT: PASS`.
   Confirm: the prompt is not truncated, row 5 cols 6–7 insert `,`/space instead of applying
   dakuten, and settle the End marker (`＊` is a placeholder).
4c. **Port the font hook to SLPS_008.29** into the 1,276-byte dakuten block (§20.3), then the
   half-width patch, then widen the menu 12 → 24 columns (12×16 = 24×8, so the box is unchanged).
5. **Redraw the font.** 8 bytes/glyph, sorted-SJIS order, at the reported `font @` address. Still the
   8×8 face drawn at rows 4–11 of a 15-row cell — worth improving now the layout is settled.
6. **Propagate translations** — unique-worklist → all duplicate sites, both dumps.
7. Reflow and reinsert the SCRIPT.BIN side (`riotscript.py`), same method as §17.
8. Confirm the no-pointer-table assumption by disassembling the message routine.
9. Spot-check `MATI.BIN` / `MISE.BIN` / `ZDATA.BIN` for baked-in Japanese.
10. Untranslated Japanese renders **left-half-only** under `halfwidth --glyph-only`. Acceptable while
    translating; revisit if any Japanese must ship.

---

## 14. ★ Custom font hook — IMPLEMENTED (2026-07-30)

Mixed-case English renders in the battle dialogue box from a custom glyph table injected into
KOUSEI.EXE. Untranslated Japanese is unaffected.

### 14.1 The hook

| | |
|---|---|
| BIOS stub (`B(51h) Krom2RawAdd`) | `0x800BD688` (file 0xADE88) |
| Call sites patched | `0x80015DA0` (file 0x65A0), `0x80015F40` (file 0x6740) |
| Signature | `expand(a0 = SJIS code, a1 = dest, a2 = fg, a3 = bg)` at `0x80015CF0` |

Both `jal`s are retargeted to an injected routine. The routine linearly scans a list of mapped SJIS
codes; on a hit it returns a pointer to glyph data, and **on a miss it tail-jumps to
`0x800BD688`** — the original BIOS entry. That fallthrough is what makes partial translation
practical: a half-translated script displays English and Japanese correctly in the same box, with
no flag day.

Mapped set (88 codes): `0x824F–0x8258` digits, `0x8260–0x8279` A–Z, `0x8281–0x829A` a–z, plus 25
punctuation codes (`0x8140` ideographic space, `0x8141/2/3/4`, `0x8146–0x8149`, `0x815B/D/E`,
`0x8160`, `0x8165–0x816A`, `0x817B/C`, `0x8181`, `0x8193/5/6/7`).

### 14.2 Glyph format — confirmed empirically, then by disassembly

The first test injected one asymmetric glyph (an `F` with a corner dot) for *every* character, so
its on-screen orientation proved the format outright:

- **16 rows, 2 bytes per row.** Byte 0 = left 8 px, byte 1 = right 8 px, **MSB = leftmost pixel.**
- The caller (`0x80015DB4`) copies **only 15 halfwords** and writes zero to the 16th itself, so a
  glyph needs just **30 bytes** and the blank last row (line spacing) is free.
- The copy uses `lhu` → **glyph pointers must be 2-byte aligned** (this rules out interleaving two
  glyphs at even/odd offsets, which otherwise looks like an easy 2× saving).
- Only **one glyph is live at a time** — it is copied to the stack immediately on return. This is
  what makes compressed storage with a single shared scratch buffer safe.

### 14.3 Compact storage (current design)

Glyphs are stored as the **8×8 source, 8 bytes each**, and expanded at call time into a 32-byte
scratch buffer, drawn at rows 4–11 of the 15-row cell.

| Component | Bytes |
|---|---|
| Routine (38 instructions) | 152 |
| SJIS code list (88 × 2) | 176 |
| Font table (88 × 8) | 704 |
| Scratch buffer | 32 |
| **Total** | **1,064** |

That replaced a 3,428-byte expanded layout that did **not** fit the safe regions. Everything now
lives in the single run at `0x80105448` (1,176 bytes), so the footprint is one region rather than
four, and ~2.3 KB remains there for a taller font later.

### 14.4 Half-width patch (2 words)

| Address | Was | Now | Effect |
|---|---|---|---|
| `0x80015E78` | `lhu v0,(a2)` `94C20000` | `j 0x80015EEC` `080057BB` | expander skips the right-half byte → 8 px/row |
| `0x8001C174` | `ori v0,zero,4` `34020004` | `ori v0,zero,2` `34020002` | `LoadImage` rect width 4 → 2 halfwords |

`riotfont.py halfwidth --glyph-only` applies exactly these two and nothing else; `--revert` undoes
them. **Consequence:** anything falling through to the BIOS renders left-half-only, so keep a
full-width build for reading untranslated text.

### 14.5 Renderer map — there are TWO grids (important correction)

An earlier model assumed one character counter drove both storage and layout. It does not, and
patching the wrong one produced correct 8 px glyphs in a scrambled layout.

**Grid A — VRAM glyph cache** (storage):
- 256-slot 4bpp page at VRAM **(320, 256)**; per-window base set via `0x8001BC18` (window 1 = 320,384).
- Slot counter `0x801162E0[win]`, limit **48** (`sltiu 0x31` @ `0x8001B908`), incremented at `0x8001B7D4`.
- Upload position: `x = base_x + (slot*4) % 64`, `y = base_y + (slot & ~15)` → **16 slots per cache row**.
- Staging buffer `0x80164DC8` (128 bytes, 16×16 4bpp); `LoadImage` at `0x8001C174`.

**Grid B — on-screen text buffer** (layout):
- **12 columns × 6 rows = 72 cells**; char buffer `0x80130230 + win*144`, blank code `0xC9`.
- Position counter `0x801162FC[win]`, limit **72** (`sltiu 0x48`).
- Line wrap: `pos % 12` (magic divide `0x8001B814–0x8001B828`) compared against the per-window width
  at `0x80115ABC`, sourced from `0x80115804` (written at `0x8001C21C`).
- Descriptor at `0x8011B21C + win*16` — **full layout corrected 2026-07-31, see §15.1**:
  `+0` u8 **cell width px** = 0x10 (`0x8001C384`), `+1` u8 **cell height px** = 0x10,
  `+2` u16 cols = 12 (`0x8001C3B8`), `+4` u16 rows = 6 (`0x8001C3C8`),
  `+8` → UV/CLUT/TPAGE table, `+12` → char buffer (tilemap).
  The `+0`/`+1` bytes were missed originally; they are the sprite size **and** the pen advance.
- Window geometry **hardcoded** at `0x8001BAE4` and `0x8001BB00`: `a2 = 0xC` columns, `a3 = 4` visible rows.
  (Not script data — an earlier note in this file said otherwise and was wrong.)

The two grids hold the same 48 characters by coincidence of capacity, which is exactly why the
single-counter model survived scrutiny longer than it should have.

### 14.6 Widening to 24 columns — constant inventory (SUPERSEDED — use §16)

> WARNING: **wrong in both directions.** Built from an immediate-value scan: two false positives,
> three missed entries, and blind to the shared-subexpression trap (§16.2). Kept for the record.

Do these as one verified set:

| Address | Current | Purpose |
|---|---|---|
| `0x8001B814`, `0x8001B81C`, `0x8001B828` | ÷12 magic + ×12 | line-wrap modulo |
| `0x8001B848` | `addiu v0, a3, 0xd` | round up to next line (12+1) |
| `0x8001B8DC`, `0x8001BEFC`, `0x8001BFAC`, `0x8001C1EC` | `sltiu 0x48` | 72-cell buffer limit |
| `0x80018F44`, `0x80018FA8`, `0x80019A18` | `addiu v0, v0, 0xc` | line-clear span |
| `0x8001806C`, `0x8001B6C8` | `ori 0xc` | column count |
| `0x8001C3B8` | `ori 0xc` | descriptor columns |
| `0x8001BAE4`, `0x8001BB00` | `ori a2, zero, 0xc` | window setup columns |
| `0x8001B908` | `sltiu 0x31` | cache slot limit — 24×4 = 96 needs **0x61** |
| *unlocated* | — | **sprite width + pen advance** in the generic drawing module |

Cache capacity is sufficient: 96 slots = 6 cache rows × 16 lines = 96 lines, inside the 128-line
per-window band.

### 14.7 Script-side encoding

`riotbattle.py bytes_from_body` calls `ch.encode('shift_jis')` literally. Plain ASCII therefore
emits a **single byte** (e.g. `a` → `0x61`), which is not a valid SJIS lead byte and desyncs the
tokeniser for the rest of the message. Always author English as **full-width** — use
`riotfont.py fullwidth` / `sentencecase` / `replace`, then `riotbattle.py checkedit`.

### 14.8 Bug log — mistakes worth not repeating

1. **R3000 load delay slot.** `lhu v0,(t1)` immediately followed by `beq v0,a0` is illegal on the
   PS1 CPU (no interlock); the branch compares a stale register. A naive sequential simulator
   reported a pass. Every load in injected code now has an explicit `nop` after it, and the
   verifier enforces the delay.
2. **Little-endian byte order.** Storing the glyph row as `byte << 8` puts it at the **odd** offset —
   precisely the byte the half-width patch skips. It would have booted to a blank text box. The
   ASCII previews *looked* correct because the preview read halfwords rather than the bytes the
   expander reads. Verify against the exact load the target performs, not a convenient rendering.
3. **Free space by eyeball.** Three black screens — see Appendix B.
4. **Hooking an already-hooked EXE.** Always build from a pristine copy; the tool now detects a
   prior hook and says so.

---

## 15. ★ The sprite emitter — LOCATED (`0x800C19EC`)

It is **not** in the text engine. `0x80018000–0x8001D000` contains no sprite setup code because
there is none to find: the text engine only fills a descriptor and hands a pointer to a **generic
tilemap renderer** that is shared with other clients. **Never patch the renderer.**

```
text engine ──writes──▶ descriptor 0x8011B21C + win*16
                            │
           0x8001C4BC  sw   ▼
           per-window record 0x80160EF0 + win*36, field +0x14
                            │
                      ──▶ 0x800C19EC   (loads it at 0x800C1A30)
```

Callers of the renderer loop over both windows: `0x8002A1B4`, `0x8002A724`, `0x8002B3D0`.

### 15.1 Descriptor layout (16 bytes/window), built at `0x8001C378`–`0x8001C418`

| Off | Size | Stock | Meaning |
|---|---|---|---|
| **+0** | u8 | 0x10 | **cell width px — sprite width AND pen advance** (`0x8001C384`) |
| **+1** | u8 | 0x10 | **cell height px** |
| +2 | u16 | 12 | columns (`0x8001C3B8`) |
| +4 | u16 | 6 | rows (`0x8001C3C8`) |
| +8 | u32 | `0x80190040 + win*0x800` | UV/CLUT/TPAGE attribute table |
| +12 | u32 | `0x80130230 + win*144` | tilemap / char buffer, `cols*rows` u16 |

`+0` and `+1` are both written from one `ori $v1,$zero,0x10` at `0x8001C384`. That is why no
"sprite width constant" was ever found in the text engine — it is a descriptor *byte*, not an
immediate in a drawing path.

### 15.2 What the renderer does

- `0x800C1A38` `lbu` → cellW, `0x800C1A50` `lbu` → cellH (both default to 0x100 if zero).
- `cellW*cols` and `cellH*rows` give the texture extent, used for the scroll modulo.
- Tilemap lookup `0x800C202C`: `tile = map[(col + row*cols) * 2]`; **`0xFFFF` = skip**. The blank
  code `0xC9` is *not* skipped — every cell emits a primitive.
- Attribute lookup `0x800C1DC4`: `attr = uvtable + tile*8`.
- Emits a 6-word primitive: `+0` tag(len 5), `+4` `0xE1000200|tpage` (DR_TPAGE), `+8`
  `0x64......|colour` (SPRT, variable size), `+0xC` xy, `+0x10` u,v,clut, **`+0x14` w | h<<16**.
- Per-tile advance `0x800C1FE8` `addu $t3,$t3,$v0`, where `$v0` is that same width.

**So sprite width and pen advance are one value: `desc[0]`.** A second path emits a `POLY_FT4`
(`0x2C`) when the scroll X is odd; it takes its size from the same two bytes.

### 15.3 The UV table is not a primitive buffer

`0x80190040 + win*0x800` is a **256-entry × 8-byte attribute table**, built by the loop at
`0x8001C4F0`: `u=(i%16)*16`, `v=(i/16)*16` (−0x80 for window 1), clut `0x7C03`, tpage `0x0015`.
Tpage 0x15 decodes to VRAM page (320, 256) 4bpp — confirming Grid A of §14.5. Verified
byte-for-byte against a savestate. **It is rewritten on every window init**, so it is not free space.

### 15.4 Window geometry (`0x8001C1B0`–`0x8001C370`)

| Field (record `0x80160EF0 + win*36`) | Source |
|---|---|
| `+8` px width | `cols << 4` at **`0x8001C250`** |
| `+0x0A` px height | `visible_rows << 4` at `0x8001C268` |
| `+0x18` half_w | `px_w / 2` at `0x8001C2A4` |
| `+0x1A` half_h | `px_h / 2` at `0x8001C2D4` |
| `+4` x | `half_w − 0xA0 + winx` at `0x8001C308` |
| `+6` y | `half_h − 0x78 + winy` at `0x8001C33C` |

The renderer then computes `screen_x = x − half_w + Gx` (`Gx` at `0x80191408` = 160,
`Gy` at `0x8019140C`). The `half_w` terms cancel **only if both are consistent** — see §16.2.

`half_w`/`half_h` have exactly **two writers** (`0x8001C2A4`, `0x8001C2D4`) and **four readers**
(`0x8001C2E0`, `0x8001C314`, `0x800C1B3C`, `0x800C1B58`) in the whole image.

---

## 16. ★ 24-column widening — IMPLEMENTED (2026-07-31)

`riotfont.py renderer` — **39 words, size preserved**. 24 columns × 6 rows, 8×16 px cells.
Because 24×8 = 12×16, the box is **pixel-identical to stock**: 192×64 at (−48,−64) / (112,152).
Capacity 48 → 96 visible characters.

### 16.1 The applied set

| Address | → | Purpose |
|---|---|---|
| `0x8001C384` | `ori v1,0,8` | desc[0] cell width 16 → 8 (**sprite width + pen advance**) |
| `0x8001C398` | `ori v1,0,0x10` | desc[1] height stays 16 — placed in the `lhu` **load-delay slot** |
| `0x8001C3B8` | `ori v0,0,0x18` | desc[2] columns 24 |
| `0x8001BAE4`, `0x8001BB00` | `ori a2,0,0x18` | window setup columns 24 |
| `0x8001C250` | `sll v0,v0,3` | cols→pixels ×16 → ×8, so the box stays 192 px |
| `0x8001B8DC`, `0x8001BEFC`, `0x8001BFAC`, `0x8001C1EC` | `sltiu 0x90` | cell limit 72 → 144 |
| `0x800198B8`, `0x800199F0`, `0x8001B81C` | `srl 3 → 4` | ÷12 → ÷24 (**three** sites) |
| `0x800198C4`, `0x800199FC`, `0x8001B828` | `sll 2 → 3` | ×12 → ×24 |
| `0x80018F44`, `0x80018FA8`, `0x80019A18` | `addiu 0x18` | line-clear span / next-row |
| `0x8001B848` | `addiu 0x19` | wrap round-up 13 → 25 (dead path, see below) |
| `0x8001B908` | `sltiu 0x61` | VRAM cache slots 48 → 96 |
| 6 sites × 3 words | base + final shift | char buffer, §16.3 |

Notes:
- The magic constant `0xAAAAAAAB` is identical for ÷12 and ÷24; **only the shifts move**.
  `0x8001B814` needs no change.
- `0x8001B848` is dead in stock configuration: the wrap test compares `pos % stride` against the
  active line width (`0x80115ABC`), and when both equal the grid width, `pos % 24 ∈ [0,23]` can
  never reach 24. Updated for correctness only.
- §14.6 false positives, confirmed by disassembly, **must not be patched**:
  `0x8001806C` is the *height* argument to the blit at `0x80015BD4` (`copy(src,dst,w,h)`, 26×12);
  `0x8001B6C8` sits in a branch delay slot and feeds `sb $v0,0xd50($gp)`, a script-state id
  dispatched through a 0x65-entry jump table at `0x800101B0`.
- Cache budget: 96 slots × 16 px = 6 rows × 16 lines = 96 lines. Window 0 y 256–352 (< 384),
  window 1 y 384–480 (< 512). No overlap.
- Must sit on top of `halfwidth --glyph-only`, **not** full `halfwidth`: the full form repacks the
  VRAM cache to 8 px cells (`0x8001C108/0x8001C158/0x8001C168`), contradicting the UV table's
  16 px stride. `0x8001B908` is shared and takes the same value either way.

### 16.2 ★★ The shared-subexpression trap — the expensive lesson

The first attempt put the box 96 px right and 32 px down. Root cause:

```
8001C3F4  sll  $v0, $a0, 3      ; v0 = win*8
8001C3F8  addu $v0, $v0, $a0    ; v0 = win*9    <-- SHARED
8001C3FC  sll  $v1, $v0, 4      ; v1 = win*144  (char buffer offset)
...
8001C418  sll  $v0, $v0, 2      ; v0 = win*36   (WINDOW RECORD index!)
8001C424  sw   $zero, 0xef0($at)
```

The compiler shares `win*9` between the char-buffer stride (`<<4`) and the window-record index
(`<<2`). Rewriting it to `win*15` for a 240-byte stride silently made the record index `win*60`, so
for window 1 the store landed on `0x80160EF0 + 60` = `0x80160F2C` = `half_w`/`half_h`, zeroing both
with one word. `screen_x = x − half_w + 160` then shifted the box by exactly `half_w` = 96 px.
The stray `sb $a0,0xf00($at)` likewise landed at `0x80160F3C` (= `0x00000080`).

**Window 0 was immune** because `0*60 == 0*36`, which is why the first savestate (window 0 active)
looked healthy and hid the fault for a full cycle.

**The tell, visible in the disassembly all along:** site 6 writes `sll $v1, $v0, 4` — *distinct
destination*, preserving `$v0`. The other five write `sll $vX, $vX, 4` in place, scratch dead after.

**Rule: change only the final shift.** Stride is then `9 << k`, which locks `cols*rows` to 72 (k=4)
or 144 (k=5). At 24 columns that means rows = 3 or 6; 3 is below the `visible+1` floor, so
**rows = 6** — which is what stock ships (visible+2 slack).

### 16.3 Char buffer placement — scratch belongs in BSS

`0x80130230` is **outside the loaded image** (image ends `0x80115800`), i.e. BSS. Appendix B's
file-based method does not apply to it. In place is fatal: the stock buffer ends exactly at
`0x80130350`, and `0x8013035C`–`0x8013039A` is densely code-referenced from `0x80078xxx`–`0x8008Dxxx`.

The first attempt relocated it into the scarce execution-proven **in-image** run at `0x800F3ECC`.
That was a **category error**: the font table is static file data and *must* be in the image; the
char buffer is runtime scratch, fully rewritten before use. 704 + 576 never fits the 1176-byte run.

Now at **`0x80178000`** (576 B = 288 B/window), inside a 138,259-byte BSS region with zero code
references and zero non-zero bytes across **all savestates from three scenes**. Margins 45 KB below,
92 KB above. It falls inside the boot BSS clear (`0x80115660`–`0x801FDC94`, loop at `0x800BD4BC`,
entry point `0x800BD4AC` = header `pc0`), so it starts zeroed; the engine fills it with `0xC9` on
window open regardless.

### 16.4 Ring-scroll floor

The tilemap is a scroll ring; `0x80018FB8` advances it 4 px/frame, 4 frames per 16 px row. Covering
a 4-row (64 px) window from a partial offset needs 5 row slots, so **rows ≥ visible + 1**. Stock
ships visible + 2, giving one fully off-screen row for write-ahead — which is what rows = 6 restores.

---

## 17. Line breaks are authored, not computed

`{FFFE}` is a **hard line break** and the engine has **no word wrap**. The check at `0x8001B844`
compares `pos % stride` against the active line width (`0x80115ABC`); when both equal the grid width
the path is unreachable. Stock is the same (12 vs 12).

**Widening does not reflow existing text.** Every break was authored for a 12-cell box.

The engine *can* wrap if the configured line width is set below the grid stride —
`0x8001BAE4`/`0x8001BB00` feed `0x80115804` → `0x80115ABC`, independent of the descriptor's `cols`
at `0x8001C3B8` — but it is a hard **character** wrap that breaks words mid-way. Not usable for
English. Reflowing the script is the correct fix.

### `riotfont.py rewrap IN OUT [--cols 24] [--rows 4] [--all]`

Merges a line into the previous one **only** when the previous line does not end in terminal
punctuation (i.e. it was split mid-sentence to fit the old box) and the result still fits. This
preserves deliberate breaks: `Search!` keeps its own line; `They must be` + `close by!` join.
Groups that are not predominantly Latin pass through byte-identical, so untranslated Japanese is
untouched (`--all` overrides). Warns when a page exceeds the visible rows so a `{FCC0}` page break
can be added.

**Size-neutral by construction:** each merge deletes one `{FFFE}` (2 bytes) and inserts one
full-width space (2 bytes in SJIS). This matters — HEXMAP.BIN chunk headroom is tight (median ~1 KB,
minimum 247 bytes) and the inserter hard-fails on overflow.

Reinsertion: `riotbattle.py insert HEXMAP.BIN battle_24.txt HEXMAP_new.BIN`, then
`riotbattle.py checkedit HEXMAP.BIN HEXMAP_new.BIN` (never optional), then rebuild the disc.

---

## 18. Tooling added — renderer session (`riotfont.py`)

| Command | Purpose |
|---|---|
| `renderer IN OUT [--cols N --rows N --cellw N --charbuf 0x…] [--revert] [--dry]` | the §16 set, applied atomically |
| `simcheck EXE` | R3000 simulation of the descriptor build + window geometry, **enforcing the load delay slot**, plus the §16.2 regression test |
| `windiag EXE SAV` | diffs live savestate state against what the EXE should produce; flags any window where `half ≠ px/2` |
| `rewrap IN OUT` | §17 script reflow |

All patches verify **every** original opcode before writing anything, preserve file size, are
idempotent, and `--revert` round-trips byte-identical.

`charbuf_reservation()` / `drop_reserved()` stop `hookfont` from allocating into the relocated char
buffer — the renderer only *points* at it, so those bytes stay zero in the file and `all_runs()`
would otherwise offer them. **Run `hookfont` before `renderer`.**

### Build order

```
riotfont.py hookfont  KOUSEI.EXE s1.EXE --addr auto --sav X.sav --style half
riotfont.py halfwidth s1.EXE s2.EXE --glyph-only
riotfont.py renderer  s2.EXE  KOUSEI_new.EXE
riotfont.py simcheck  KOUSEI_new.EXE          # must print RESULT: PASS
```

---

## 19. ★ Menus and name entry — SLPS_008.29 (2026-07-31, session 3)

**The boot executable owns both target screens.** Confirmed, not assumed: both savestates
calibrate against `SLPS_008.29` with **29/29 anchors** and against `MAIN1.EXE` with 3/26 (noise).
MAIN1 is the town/overworld engine and is not resident on the title or name-entry screens.

`gp = 0x8007C998` (from the entry prologue at `pc0 = 0x8002CB3C`).
Boot BSS clear range **`0x8007CAA4`–`0x801EFCF4`**.
Note the clear range *starts inside the image* (image ends `0x8007D000`), so the last 0x55C bytes
of the file are zeroed at boot and cannot hold static data.

### 19.1 The text path — it is `Krom2RawAdd`, so this is a hook PORT

SLPS has the same pipeline as KOUSEI. Expander at **`0x8001E994`**, signature
`expand(a0 = SJIS, a1 = colour, a2 = vram_x, a3 = vram_y)`:

```
8001E9F0  jal   0x8002CD08        ; Krom2RawAdd, the single call site
8001EA18  lhu   $v1, ($a0)        ; 15-halfword copy out of the returned pointer
8001EA50  lhu   $a0, 8($v0)       ; nibble expansion 1bpp -> 4bpp, 128-byte stage
8001EAF8  ori   $v0, $zero, 4     ; LoadImage rect width (halfwords)
8001EB0C  jal   0x8002F664        ; LoadImage(rect, data), w=4 h=16
```

**Both target screens go through it**, verified by disassembly *and* against VRAM:

| Screen | Renderer | VRAM atlas |
|---|---|---|
| Name-entry kana grid | `0x80027890` | `(832 + col*6 (+6 if col≥5), 48 + row*24)` hiragana; `+256` katakana |
| Prompt / confirm text | `0x800271D8` | `(832 + col*4, line*16)`, 2 lines × 15 chars |
| Entered name | main loop, `0x80025F48` | `(832 + i*4, 32)`, **7 slots** |
| Main menu | `0x80027B80` | `(768 + col*4, 128 + row*16)`, 12 × 4 |

Ground truth: dumping the predicted cells out of `riotstars_nameentry.sav` reproduces あ, い, う
and ア as bitmaps at exactly the computed addresses. **The INTER.BIN 8×8 font is not involved on
these screens** — no single-byte renderer appears in either path.

> Rendering trap: the expander is called with `a1 = 1`, so glyphs land in the atlas as colour
> index **1**. Rendering a 4bpp VRAM page with brightness = nibble×17 makes them near-black and
> the atlas looks empty. Threshold any non-zero nibble instead.

### 19.2 The menu is NOT the generic tilemap renderer

Unlike KOUSEI's dialogue box (§15), the menu does **not** fill a descriptor for `0x800C19EC`.
It renders 12×4 characters into a scratch VRAM atlas and blits **one 192×64 sprite**
(`w=0xC0, h=0x40`, built at `0x800FF560`). Different mechanism, and a cheaper one to widen —
12 × 16 px = 192 = 24 × 8 px, the same identity that made §16 pixel-neutral.

---

## 20. Name entry — structure

### 20.1 Storage, and the real cap

Field at **`0x800F16CE`**: 8 × u16, initialised to `0x8140` (full-width space) by the loop at
`0x80025C94`, then slot 7 overwritten with **`0xFFFE`** as a sentinel (`0x80025CD8`). Commit
refuses at `len == 7` (`0x8002645C`). The draw loop iterates `i < 7` (`0x80025F80`).

**Hard cap is 7 full-width characters**, not 8 — this is the 0x10 stride of §8 with the final
slot reserved for the terminator. Backspace at `0x80025EB4` decrements and rewrites `0x8140`.

State (all `$gp`-relative): name length `0x8007CC94` (`gp+0x2FC`), bank `0x8007CBC0`
(`gp+0x228`), cursor column `0x8007CCA4` (`gp+0x30C`), cursor row `0x8007CCAC` (`gp+0x314`),
pad state `0x8007CD10` (`gp+0x378`).

The name is read from `0x800F16CE` in ~12 places across the EXE, including a dialogue
substitution helper at `0x8001E88C` (`a1 == 0` → `name[a2]`, else a string table at
`0x80055970`), a default-name writer at `0x8002B530`, and a byte-swap-to-standard-SJIS copy at
`0x80024930` (for the memory-card header, via the swap routine at `0x80015FD8`).

### 20.2 The grid is almost entirely data-driven

**10 columns × 6 rows × 2 banks**, index `bank*60 + row*10 + col`.

| Table | Address | Contents |
|---|---|---|
| glyph codes | `0x80061E6C` | 120 × u16 SJIS |
| **cell attributes** | `0x80061F5C` | 120 × s16 |
| column X (on screen) | `0x80010304` | 10 × s16 `[-136,-112,-88,-64,-40, 8,32,56,80,104]` |
| row Y (on screen) | `0x80010318` | 6 × s16 `[-56,-32,-8,16,40,64]` |
| name slot X | `0x800102F4` | 8 × s16, 16 px pitch |

Attribute values: **0** = normal, **1** = not valid as the *first* character (small kana, ー, ゛,
゜, ん — a linguistic rule), **−1** = dead cell, **2** = the End command (`終`).

**The same attribute table is read through three windows**, which is the neat part:

| Base | Read from | Meaning |
|---|---|---|
| `0x80061F5C` (+0) | `0x800263CC` | this cell — commit rejects attr 1 when `len == 0` |
| `0x80061F5E` (+1 entry) | `0x80026BD4` | the cell to the RIGHT — −1 blocks movement |
| `0x80061F70` (+10 entries) | `0x80026B1C` | the cell BELOW — −1 blocks movement |

Only four things live in code rather than data: the grid dimensions; the dakuten / handakuten
cells (`row==5 && col==6/7`); End (`row==5 && col==9`, **not** bank-checked); and one LEFT
special case (`bank==1 && col==9 && row==5 → col=7`) that skips the blank before `終`.

Cursor movement is `0x80026A00(a0)` with a0 = 0 up / 1 down / 2 left / 3 right. Up at row 0 and
down at row 5 wrap between banks. R1 (`0x0800`) jumps straight to the End cell.

### 20.3 ★ The dakuten block is 1,276 reclaimable bytes

SLPS free space is **far tighter than KOUSEI**: the Appendix B three-filter method yields
**15 usable runs totalling 724 bytes, largest 76** — nowhere near the 1,064 the compact hook
needs, and nothing contiguous.

But the dakuten and handakuten handlers are contiguous inline code,
**`0x80026504`–`0x80026A00` = 1,276 bytes**, and a full entry scan (jal/j, branches, pointer
constants, lui+imm data refs) finds **exactly two ways in**: `jal 0x80026504` at `0x8002641C`
and `jal 0x800268A4` at `0x8002644C`. Both are the kana-only special-case cells.

`riotfont.py namegrid` makes the row test unsatisfiable and nops both jal sites; after it,
`riotfont.py deadcode SLPS_new.29 80026504 80026A00` reports **no entries from outside**.

**This is the space for the font hook** — reclaimed by enumerating consumers, not by assuming
zeros are free. It is the inverse of the Appendix B failures: the bytes are not zero at all, they
are provably unreachable once the grid stops being kana.

---

## 21. Prompt and confirm strings — one block, addressed by span

`0x8001038C` is **one block of 2 lines × 15 full-width chars** (60 bytes), uploaded to the atlas
at `(832, 0)` and `(832, 16)`. UI fragments are blitted as sub-rectangles of it. Recovered by
simulating `0x800271D8` and reading back the primitives it builds at `0x800FF3D4 + n*36`
(layout `+4 x, +6 y, +8 w, +10 h, +12 clut, +14 u, +15 v`):

| Fragment | Span | Rect | Screen |
|---|---|---|---|
| name prompt | line 0, chars 0–9 | — | top box |
| No (`いいえ`) | line 0, chars 11–13 | 48×16, u=176 v=0 | (48, 8) |
| question (`これで　よろしいですか？`) | line 1, chars 0–11 | 192×16, u=0 v=16 | (−128, −32) |
| Yes (`はい`) | line 1, chars 12–13 | 32×16, u=192 v=16 | (−32, 8) |

**Because fragments are addressed by character span, the exact rectangle widths never need to be
known** — English is safe as long as it occupies the same span and is space padded. The one
exception is the 2-char Yes button; `0x80027464 ori $v0,$zero,0x20 → 0x30` grows it to 3 chars
and consumes the trailing spacer, which is a space in stock.

⚠️ **Do not "centre" the widened Yes button.** Its X comes from `addiu $v1,$zero,-32` at
`0x8002745C`, which is **shared with rec3's Y**. This is the §16.2 trap in miniature; the button
renders 16 px right of centre and that is the correct trade.

The emitter for the name-prompt fragment itself was **not** located — the routine reached from
`0x80026F54` depends on state not established at that entry point, and simulating it in isolation
writes through a null pointer. It was not needed, and forcing it would have violated the method.
If `YOUR NAME:` renders truncated in the test build, that fragment is narrower than 10 chars and
the string should shrink to `NAME:`.

---

## 22. Tooling added — menu session (`riotfont.py`)

| Command | Purpose |
|---|---|
| `slpsmap EXE` | verified address map; live grid / menu / prompt dump; name cap |
| `namegrid IN OUT [--dry]` | kana grid → Latin A–Z/a–z (data + 5 guard words) |
| `menutext IN OUT [--dry]` | main menu → English (4 × 12 full-width) |
| `prompttext IN OUT [--dry] [--narrow-yes]` | prompt/confirm strings + Yes-button width |
| `gridsim EXE SAV...` | simulate the grid renderer, check every cell against savestate VRAM |
| `deadcode EXE LO HI` | enumerate every entry into a code region |

Build order for the boot EXE:

```
riotfont.py namegrid   SLPS_008.29 s1.29
riotfont.py menutext   s1.29       s2.29
riotfont.py prompttext s2.29       SLPS_new.29
riotfont.py gridsim    SLPS_new.29 nameentry.sav      # must print RESULT: PASS
```

324 bytes change; size preserved; all patches verify every original opcode through `_apply_set`
before writing, and are idempotent. **`--revert` is deliberately not offered** for these three:
they rewrite data rather than apply a reversible delta, so rebuild from a pristine EXE.

### 22.1 The simulator is now shared

`R3000` (built in §18 for `simcheck`) was extended **additively** rather than duplicated:

- `lwl` / `lwr` / `swl` / `swr`, implemented byte-wise for the general unaligned case. The SLPS
  string-block copies use them and previously hit `SystemExit`.
- An `intercept` set: `jal`s to those targets are recorded with their arguments and skipped, so a
  caller can be observed without simulating the callee.

With `intercept` empty and no unaligned ops in range, behaviour is unchanged, so `simcheck`,
`renderer` and `windiag` are unaffected. **They were not re-run this session — KOUSEI.EXE was not
available — so re-run `simcheck KOUSEI_new.EXE` once before trusting the merged tool on the
battle side.**

`gridsim` was validated on the **pristine** EXE before being trusted on a patched one
(Appendix D #1): 120/120 cells agree with `riotstars_nameentry.sav`, 0 hazards. Two guards were
added after they fired for real:

- **Wrong scene.** `riotstars_mainmenu.sav` has an empty kana atlas — it is not on that screen.
  Reported as "no evidence", not a failure (Appendix D #2).
- **Wrong build.** A patched EXE checked against a pristine savestate produced 5 "mismatches"
  that were simply the cells that had changed. `gridsim` now compares the grid table in the image
  against the same address in savestate RAM and skips the VRAM oracle when they differ
  (Appendix D #8).

### 22.2 Still open on these screens

- **7 characters is short for English names.** Widening the record means finding every consumer
  of the 16-byte name field across all five EXEs; not attempted.
- **`＊` is a placeholder for End.** One cell cannot hold "End". Settle it against a screenshot.
- **Half-width is unblocked but not done.** The space exists (§20.3), the menu's 12×16 = 24×8
  identity holds (§19.2), and `0x8001EAF8` is the SLPS `LoadImage` width. The expander's
  right-half-byte skip (KOUSEI's `0x80015E78`) has **not** been located in SLPS yet.

---

---

## 23. ★ HEXMAP chunk loader — TRACED (2026-08-05)

Traced in `KOUSEI.EXE` against the retail `TACTICS/HEXMAP.BIN` (8,040,448 bytes = 46 × 0x2A800
plus a 0x8000 tail that is zero but for one stray `0xFF` at file `0x7AAA20`).

### 23.1 What a chunk actually contains

`map_load(a0 = map index)` at **`0x8006365C`**. The index becomes a sector base at
`0x80063680`–`0x8006368C`: `v0 = idx*5`, `v1 = v0<<4`, `s2 = v0+v1` → **`s2 = idx * 85`**.
85 × 2,048 = `0x2A800`. Reads go through `read(path, sector, count)` at **`0x80064C48`**; the
destination pointer is written to the file record at `0x800F4760` (HEXMAP record + 0x100), the
path lives at `0x800F4660`, and the staging buffer is **`0x801C0DDC`** (`s3` @ `0x8006369C`).

| Call site | Sector | Count | Chunk range | Consumer |
|---|---|---|---|---|
| `0x800636EC` | `s2+0x00` | 0x11 | `0x00000..0x08800` | TIM → VRAM |
| `0x8006375C` | `s2+0x11` | 0x11 | `0x08800..0x11000` | TIM → VRAM |
| `0x800637C8` | `s2+0x22` | 0x11 | `0x11000..0x19800` | TIM → VRAM |
| `0x80063834` | `s2+0x33` | 0x17 | `0x19800..0x25000` | two copies, below |
| `0x80063914` | `s2+0x4A` | 0x4 | `0x25000..0x27000` | **script** |
| `0x80063978` | `s2+0x4E` | 0x4 | `0x27000..0x29000` | unit / deployment |
| `0x800639CC` | `s2+0x52` | 0x3 | `0x29000..0x2A800` | CLUT loop → `0x80191858` |

Sectors 0..84 — **the chunk is completely full. The script slot cannot grow upward.** §5's
statement that the unit table is the binding constraint is true but incomplete: the table cannot
move because there is nothing above it to move into.

Only three TIM headers per chunk, at `+0`, `+0x8800`, `+0x11000` (verified across all 46; chunks
44 and 45 have none and are not map chunks at all). The fourth read's consumers are two
fixed-size copies, both issued **before** the script read:

- `0x80063854` → `0x800158B8(buf, 0x80130514, w=0x800, h=5)` — spans `0x19808..0x1E808`.
- `0x8006389C` → `0x80015B44(buf+0x5800, 0x801D6EA8, w, h)`, a `copy(src+8, dst, w*h/2 words)`.
  Large map `w=0x68 h=0x4E` → **`0x1F008..0x22F68`**; small map `w=0x34 h=0x27` → `0x1F008..0x1FFE0`.

**`0x22F68` is the deepest offset any consumer reaches below the slot**, so `0x23000` (sector 70)
is the floor for extending a slot downward. Nothing in the image references `buf+0x9800`.

### 23.2 The script's RAM buffer is 8,192 bytes with 12 bytes of clearance

`0x8006551C`, called immediately after the script read, byte-swaps the slot from the staging
buffer into **`0x80154F40`** (`slti v0,a2,0x1000` @ `0x80065560` = 4,096 halfwords), stores the
base pointer at `0x801DC784`, then scans for `0xFFFF` markers (skipping `0xFCA6` +6) to fill a
50-entry table at `0x801EC784` (`slti` @ `0x800655D8`, cap `a3 = 0x32` @ `0x80065598`).

**The next code-referenced address above `0x80154F40` is `0x80156F4C`** — twelve bytes past the
end of the buffer, with twelve references. Reading a larger slot into it corrupts that variable
silently: nothing fails at map load. Any slot extension must relocate this buffer as well;
`0x80180000` is the recommended target, inside the BSS region §16.3 already validated.

Full patch spec — eleven words, all opcodes verified — in `pending/slot-extension.md`.

### 23.3 Chunk 33 was missing from the dump

`riotbattle.py::find_script_bounds` returned `None` unless `\xfc\x51` appeared in the slot.
**Chunk 33 opens every message with `{FC50}` and never uses `{FC51}`**, so it was silently
dropped: the dump held 43 chunks (0–32, 34–43) against 44 script-bearing chunks in the file.

Fixed by accepting either marker. Re-dumping adds exactly one section and changes nothing else —
chunks are keyed by absolute index, `dumps/` is pristine, and translations live in `tl/battle/`.
Chunk 33 is 1,413 bytes: the sanctuary sorceress, the 『知識の書』, and the 魔術師 → ウィザード
class-change trial. Round trip re-verified byte-identical at 8,040,448 bytes.

**Lesson, and it generalises:** the detector encoded an assumption ("text always opens `{FC51}`")
that held for 43 of 44 samples, and the 44th was invisible rather than wrong. A tool that skips
input silently should say what it skipped. `find_script_bounds` should log every chunk it rejects.

---

## Appendix A — Savestate forensics (reproducible method)

DuckStation `.sav` for this game:
- Header `DUCCT`, game serial `SLPS-00829` at 0x148.
- **Two zstd streams**: `0x116` (→ 3,950,181 bytes) and `0xD0D0` (→ 3,819,109 bytes). Decompress with
  `zstandard.ZstdDecompressor().stream_reader()`.
- In the first blob: section tags `CPU` @0x2002B, `Bus` @0x21A1F, `GPU` @0x35BBA, `SPU` @0x3698A,
  `InterruptController` @0x221B01, **`GPU-VRAM` @0x221DD0**.
- **VRAM payload begins at 0x221DD8** (tag + 8), 0x100000 bytes, 1024×512 × 16bpp BGR555.
- **Main RAM base = blob 0x21A62 ↔ PSX 0x80000000.** Calibrated by locating `\TACTICS\`
  (KOUSEI.EXE file 0xE48D4 → PSX 0x800F40D4) at blob 0x115B36.
- Framebuffer is double-buffered at VRAM (0,0) and (0,256), 320×240.
- When rendering VRAM as 4bpp, **a row is 4096 nibbles** (1024 halfwords × 4 px), not 2048 —
  getting this wrong interleaves every image and makes fonts unreadable.

---

## Appendix B — Free space in an EXE (method, and three failures)

**The rule that cost three black screens:** zeros in a shipped binary are not free space. They are
usually *structure* — reserved fields, string-record padding, or memory the game zero-initialises
and then writes at runtime.

### The three-filter method

A run of zeros inside the loaded image is usable only if **all three** hold:

1. **Unwritten at runtime** — compare against main RAM in DuckStation savestates
   (`riotfont.py liveness EXE SAV...`). Calibration per Appendix A. A run written in *any* state is
   out. Note this proves *not-written*, not *not-read*.
2. **Not referenced by code** — `riotfont.py xref` reconstructs every address reachable via
   `lui`+immediate pairs and every 32-bit pointer constant in the image. References landing exactly
   at `run_end` are fine (they belong to the next object); references landing *inside* are fatal.
   This filter needs no savestate and no play-through, and it catches code paths a play-through
   would never reach.
3. **Not part of a fixed-stride table** — if run start addresses form an arithmetic progression,
   the whole cluster is a record table and its zeros are fields. Detected automatically by
   `detect_tables()` (≥3 runs, constant stride ±8).

### Results for KOUSEI.EXE

68 candidate runs → 23 rejected as record table, 21 rejected as code-referenced, **24 usable
(3,356 bytes)**.

| Region | Verdict | Evidence |
|---|---|---|
| `0x800F3ECC` (520 B) | ✅ **safe, execution-proven** | trailing padding before the path table; ran injected code successfully |
| `0x80105448` (1,176 B) | ✅ safe | xref-clean; nearest reference is `0x801058E0` = exactly run end |
| `0x800F40EC–0x800F594C` | ❌ **fatal** | 23-run table, stride `0x11C`; 21-byte CD path + 263 zero bytes per record; `\TACTICS\` at `0x800F40D4`. Every record touched so far was written at runtime |
| `0x80113920` (4,208 B) | ❌ **fatal** | tail region; savestate shows 261 bytes written — live zero-init loader state |
| `0x8010EA40` (656 B) | ❌ **fatal** | unwritten in savestate but referenced by code at `0x800C808C–0x800C8150` |
| `0x8010D574` (180 B) | ❌ unsafe | 15 references, 12-byte stride — another record table |

### Failure sequence (for the record)

1. **`0x80113920`** — chosen because it was the largest zero run. Black screen at map load.
2. **`0x800F4xxx` cluster** — chosen because a 48-byte probe at `0x800F3ECC` had worked; the payload
   then spilled into 23 further runs of the *same table*. Black screen at map load.
3. **`0x8010EA40`** — passed the savestate filter, failed only under xref. Caught statically before
   it could fail in play.

The general lesson: prefer **static evidence over runtime sampling**. A savestate shows one moment;
an xref scan covers every code path in the binary. Filter 2 should be run first — it is instant and
requires nothing from the user.


---

## Appendix C — Verified address maps (KOUSEI.EXE and SLPS_008.29)

| Address | What |
|---|---|
| `0x800BD688` | BIOS `Krom2RawAdd` (B 51h) dispatch stub |
| `0x80015CF0` | `expand(sjis, dest, fg, bg)` → 16×16 4bpp buffer |
| `0x80015DA0`, `0x80015F40` | the two `jal` sites into the BIOS stub |
| `0x80015DB4` | 15-halfword copy loop out of the returned glyph pointer (`lhu`) |
| `0x80015E00` | pixel expansion, left byte (`lbu`, MSB = leftmost) |
| `0x80015E78` | pixel expansion, right byte — **patched to `j` for half-width** |
| `0x80164DC8` | 128-byte glyph staging buffer |
| `0x8001C174` | `LoadImage` rect width (4 halfwords → 2 for half-width) |
| `0x801162E0[win]` | VRAM cache slot counter (limit 48 @ `0x8001B908`) |
| `0x801162FC[win]` | on-screen cell counter (limit 72 @ `0x8001B8DC`) |
| `0x80115FE8`, `0x80115FFC` | cache base x / base y per window |
| `0x80115804`, `0x80115ABC` | configured / active line width per window |
| `0x8011B21C + win*16` | draw descriptor: cols, rows, prim buffer, char buffer |
| `0x80130230 + win*144` | 72-cell character buffer (blank = `0xC9`) |
| `0x80190040 + win*0x800` | per-window primitive buffer |
| `0x8001BAE4`, `0x8001BB00` | window geometry setup (`a2` = 12 cols, `a3` = 4 rows) |
| `0x8001BC18` | set cache base x/y | 
| `0x8001BC40` | set window position + cols/rows |
| `0x800F3ECC`, `0x80105448` | verified-safe injection regions (Appendix B) |


### Added 2026-07-31 (renderer session)

| Address | What |
|---|---|
| `0x800BD4AC` | EXE entry point (= header `pc0`); BSS clear loop at `0x800BD4BC`, range `0x80115660`–`0x801FDC94` |
| `0x800C19EC` | **generic tilemap renderer** — reads descriptor, emits SPRT/POLY_FT4. DO NOT PATCH |
| `0x800C1A38` / `0x800C1A50` | renderer reads cellW / cellH |
| `0x800C1B3C` / `0x800C1B58` | renderer reads `half_w` / `half_h` |
| `0x800C1DC4` | attribute lookup `uvtable + tile*8` |
| `0x800C1FE8` | per-tile pen advance (`addu $t3,$t3,$v0`) |
| `0x800C202C` | tilemap lookup `map[(col + row*cols)*2]`; `0xFFFF` = skip |
| `0x8002A1B4`, `0x8002A724`, `0x8002B3D0` | renderer call sites (loop over 2 windows) |
| `0x8011B21C + win*16` | window descriptor (§15.1) |
| `0x80160EF0 + win*36` | window record; `+0x14` = descriptor pointer, written at `0x8001C4BC` |
| `0x80190040 + win*0x800` | 256×8 UV/CLUT/TPAGE table, built by `0x8001C4F0` — **rewritten on init, not free** |
| `0x80191408` / `0x8019140C` | screen-centre Gx / Gy (160 / 120) |
| `0x8001C1B0`–`0x8001C370` | window open: clears tilemap, computes px size, half extents, position |
| `0x8001C378`–`0x8001C418` | descriptor build |
| `0x8001C3F4`/`F8` → `0x8001C418` | **shared `win*9`** — buffer stride AND record index (§16.2) |
| `0x8001B844` | line-wrap test — unreachable when line width == grid stride |
| `0x80015BD4` | `copy(src,dst,w,h)` blit — *not* a text routine (§14.6 false positive) |
| `0x800101B0` | 0x65-entry script-state jump table, index at `0xd50($gp)` (§14.6 false positive) |
| `0x80178000` | relocated char buffer (BSS, 576 B, §16.3) |

### Added 2026-08-05 (chunk loader session) — KOUSEI.EXE

| Address | What |
|---|---|
| `0x8006365C` | `map_load(a0 = map index)`; `s2 = idx * 85` at `0x80063680`–`0x8006368C` |
| `0x80064C48` | `read(path, sector, count)` — every HEXMAP read goes through it |
| `0x801C0DDC` | staging buffer (~62 KB before the next object at `0x801D0000`) |
| `0x800F4660` / `0x800F4760` | HEXMAP path string / record +0x100 destination pointer |
| `0x80063914` | **script read** — `s2+0x4A`, 4 sectors (§23.1) |
| `0x80063978` / `0x800639CC` | unit-table read (`s2+0x4E`) / CLUT read (`s2+0x52`) |
| `0x800158B8` / `0x80015B44` | the two map copies out of the staging buffer; deepest reach `+0x22F68` |
| `0x8006551C` | byte-swap slot → `0x80154F40`, then build the 50-entry table at `0x801EC784` |
| `0x80154F40` | **script RAM buffer, 8,192 bytes — next reference `0x80156F4C`, 12 bytes above** |
| `0x801DC784` | script base pointer, written at `0x80065578` |
| `0x80065560` / `0x800655D8` | the two `slti 0x1000` loop bounds (halfwords) |

### Added 2026-07-31 (menu session) — **SLPS_008.29**, not KOUSEI

| Address | What |
|---|---|
| `0x8002CB3C` | entry point; `gp = 0x8007C998`; BSS clear `0x8007CAA4`–`0x801EFCF4` |
| `0x8002CD08` | BIOS `Krom2RawAdd` stub; single call site `0x8001E9F0` |
| `0x8001E994` | `expand(sjis, colour, vram_x, vram_y)` — 20 callers |
| `0x8001EAF8` | `LoadImage` rect width (`ori $v0,$zero,4`) — half-width target |
| `0x8001E88C` | name/variable substitution: `a1==0` → `name[a2]`, else table `0x80055970` |
| `0x80015FD8` | u16 byte-swap (SJIS LE ↔ standard) |
| `0x80025B84` | name-entry main loop (input dispatch, backspace, done flag) |
| `0x8002637C` | commit selected character |
| `0x80026504`–`0x80026A00` | dakuten + handakuten — **1,276 reclaimable bytes** (§20.3) |
| `0x80026A00` | cursor move, `a0` = 0 up / 1 down / 2 left / 3 right |
| `0x80026B7C` | LEFT special case: bank1 col9 row5 → col 7 |
| `0x800271D8` | prompt / confirm draw; primitives at `0x800FF3D4 + n*36` |
| `0x80027464` | Yes-button sprite width (`ori $v0,$zero,0x20`) |
| `0x8002745C` | `-32` — **shared** between rec3.y and rec4.x. Do not touch |
| `0x80027890` | kana grid renderer (10×6×2 → VRAM atlas) |
| `0x80027B80` | main menu draw (12×4 → atlas → one 192×64 sprite) |
| `0x8001038C` | prompt block, 2 × 15 full-width |
| `0x800102F4` / `0x80010304` / `0x80010318` | name-slot X / grid column X / grid row Y |
| `0x800103C8` | main menu strings, 4 × 12 full-width |
| `0x80061E6C` | kana grid codes, 2 banks × 60 u16 |
| `0x80061F5C` | grid attribute table, 2 banks × 60 s16 (also read at +2 and +0x14) |
| `0x800F16CE` | name field, 8 × u16, slot 7 = `0xFFFE` → **cap 7 chars** |
| `0x8007CBC0` / `0x8007CCA4` / `0x8007CCAC` / `0x8007CC94` | bank / col / row / length |

---

## Appendix D — Debugging a layout fault (the method that worked)

Four techniques, in the order they paid off. Together they took a fault from "somewhere in 46 words"
to a single instruction in about six iterations.

**1. Simulate against ground truth first.** `simcheck` was validated on the **pristine** EXE before
being trusted on a patched one: it reproduces a savestate exactly (descriptor `10 10 0C 00 06 00`,
UV `0x80190040`/`0x80190840`, record `px 0xC0/0x40`, half `0x60/0x20`, pos `0xFFD0/0xFFC0`). A
simulator that has not reproduced known-good state proves nothing.

**2. A/B savestates from the *same* moment.** The first comparison used a stock save with window 0
active and a patched save with window 1 active — different scenes, different windows, no conclusion
possible. Rebuilding hook-only and capturing the identical scene made the difference obvious in one
line of `windiag`. **Never compare savestates from different game states.**

**3. Emulator write breakpoints for what static analysis cannot see.**
`half_w`/`half_h` had two writers and four readers in the whole image, all correct in isolation, yet
the value was wrong — the classic signature of a write through a *computed pointer*, which no
displacement scan can find. A DuckStation write breakpoint on `0x80160F2C` named the instruction.

Practicalities: the first hit is always the **boot BSS clear** (`0x800BD4BC`, entry `0x800BD4AC`
= header `pc0`, range `0x80115660`–`0x801FDC94`) — continue past it. Breakpoints fire on the
instruction *after* the store. CPU breakpoints do **not** catch DMA. And **check which EXE is
running**: one whole cycle was spent on data from the wrong build. `windiag` now reports this by
reading the live code out of the savestate.

**4. Savestates at the breakpoint beat asking for register values.** A save captured while paused
lets the whole machine state be inspected offline and re-inspected as hypotheses change.

### Turn every fixed bug into a simulator assertion

`simcheck` now pre-seeds `half_w`/`half_h` to 96/32, runs `0x8001C378`–`0x8001C460` for both windows,
and asserts they survive and that `record[win]+0` is actually written. It **reproduces the §16.2 bug**
(win1 → 0/0, record write misdirected) and passes on the fix. Regression tests that cannot reproduce
the original failure are not regression tests.

### Bug log additions (extends §14.8)

5. **Shared compiler subexpression.** `win*9` fed both a buffer stride and a struct index 36 bytes
   apart in the source. Rewriting the stride silently corrupted an unrelated structure. **Before
   changing a strength-reduced multiply, find every consumer of the intermediate** — the tell is a
   shift writing to a *different* destination register than its source.
6. **Category error in free space.** Runtime scratch was placed in scarce execution-proven in-image
   space, which is reserved for static data that must ship in the file. Ask what the bytes *are*
   before asking where they fit.
7. **Incomparable evidence.** Two savestates from different scenes were treated as an A/B. They were
   not, and the mismatch was rationalised for two rounds.
8. **Testing the wrong binary.** A full breakpoint session ran against the A/B build handed over for
   a different purpose. Always verify the running build from the savestate itself.
9. **Immediate-value scans miss strength-reduced arithmetic.** `sll 4` as a ×16 multiplier
   (`0x8001C250`) and the `srl 3`/`sll 2` halves of a ÷12 magic divide carry no `0xC` operand, so an
   inventory built by scanning for the literal missed three genuine sites while inventing two.

### Bug log additions 2026-07-31 (menu session)

10. **Intercepting a `jal` must still execute its delay slot.** The delay slot runs *before* the
    callee, so it is part of the argument setup — this game puts `addiu $a3,$a3,48` there.
    Skipping it reported every name-entry glyph at y=0 instead of y=48. The simulator was wrong;
    the game was not. Fixed in `R3000.run`, and `gridsim` asserts the geometry so it cannot
    regress silently.
11. **An adjacent `lwl`/`lwr` pair is not a load-delay hazard.** Adding `rt` to `_reads` for the
    unaligned loads made the hazard detector fire on *pristine* game code at `0x800278BC`. The
    pair is the architecturally sanctioned idiom. Only `swl`/`swr` genuinely read `rt`. A
    detector that flags stock code is worse than none — it trains you to ignore it.
12. **BSS-clear bounds must come from the clear loop, not from any two `lui` constants near the
    entry point.** Taking the widest pair gave `0x80000000`–`0x801EFCF4`, which swallowed the
    whole image and rejected all 84 candidate free-space runs. Anchor on
    `sw $zero,0($ptr)` / `sltu $at,$ptr,$end` and resolve those two registers.
13. **Reimplementing an existing tool re-introduces solved bugs.** A throwaway xref written this
    session dropped the `lui` high half on `addu $at,$at,$idx`, so the kana table looked
    completely unreferenced. `riotfont.py`'s own `code_xrefs` handles that indexed-array pattern
    correctly (verified against `0x80061E6C`, `0x80061F5C`, `0x800103C8`). **Use the tool in the
    repo; do not rewrite it for a quick check.**
