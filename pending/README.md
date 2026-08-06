# pending/ — translated chunks that do not fit their slot

Files here are finished, format-clean translations that `assemble.py` **must not** pick up,
because they exceed the 8,192-byte script slot. The directory name deliberately does not match
`tl/battle/chunk_NNN.txt`, so `check`, `merge` and `build` ignore it and the patch stays
buildable with those chapters falling through to Japanese (prompt §0.5).

Move a file into `tl/battle/` only once the slot constraint for that chunk has been lifted.

| File | Bytes | Slot | Notes |
|---|---|---|---|
| `chunk_043.txt` | 11,181 | 8,192 | faithful translation, 1.86x. Needs a ~12 KB slot. **Ship this one.** |
| `chunk_043_abridged.txt` | 8,941 | 8,192 | evidence only, 1.41x, 13 sentences already deleted — still 749 over. Do not ship. |

Both pass every other `assemble.py check` rule: tag parity, charset, 24 columns, 4 rows,
line count and `{PAD}` identity. The byte budget is the only failure.

---

## HEXMAP.BIN inspection (2026-08-05) — the space exists, in chunk 43 only

Measured directly on the retail `TACTICS/HEXMAP.BIN` (8,040,448 bytes, 46 × 0x2A800 chunks
plus a 0x8000 tail).

**Chunk 43 has 18,483 contiguous zero bytes immediately below its script slot:**
`chunk+0x207CD .. chunk+0x25000`, i.e. file `0x743FCD..0x748800`. Nothing sits between that
run and the script. The unit/deployment table at `+0x27000` is not involved — the slot would
grow *downward*, away from it.

Recommended new geometry for chunk 43: **start `chunk+0x23000` (sector 70), length 0x4000 =
16,384 bytes**, ending at the existing `+0x27000` boundary. Sector-aligned, entirely inside the
verified zero run, 5,203 bytes of slack over the 11,181-byte translation.

**This cannot be done globally.** Across the 44 script-bearing chunks the byte immediately
below the slot is free in only three of them (24, 28, 43); the other 41 carry a variable-length
structure that runs as late as `+0x24F15`, and every one of the 41 has a lone `0xFF` sentinel at
exactly `+0x24F18`. A uniform "script starts earlier" change buys **3 bytes** and corrupts 41
maps. The loader change must be conditional on the map index.

Rejected alternatives, for the record:

- **Chunks 44 and 45 are not map chunks** and cannot be borrowed. They have no TIM at any
  0x8800 boundary (all real map chunks have three, at +0, +0x8800, +0x11000) and their
  `+0x25000` regions hold non-script data — chunk 44's is 3,799 non-zero bytes.
- **The 32,768-byte file tail** (`0x7A3000..0x7AB000`) is zero but for one stray `0xFF`.
  Usable as a relocation target only if the loader can be given an arbitrary LBA, which is a
  larger change than the conditional offset above and buys nothing extra for this chunk.

Blocked on `KOUSEI.EXE` to locate the `0x25000` / sector-74 constant and, more importantly, to
size the destination RAM buffer — a 16 KB read into an 8 KB buffer is the one way this fix
fails silently.

## Separate finding: chunk 33 is missing from the dump

`tools/riotbattle.py::find_script_bounds` returns `None` unless `\xfc\x51` appears in the slot.
**Chunk 33 opens every message with `{FC50}` and never uses `{FC51}`**, so it is silently
dropped: `dumps/battle_dump.txt` holds 43 chunks (0–32, 34–43) but the file has **44**
script-bearing chunks.

Chunk 33 is 1,413 bytes of real dialogue — the sorceress guarding the 聖堂, the
`『知識の書』` (Book of Knowledge), the 魔術師 → ウィザード class-change trial, plus the
deployment restriction notice (`このマップでは、魔術師がリーダーのユニット以外は配置することは
できません。`). Headroom 6,779 bytes, so it is an easy chunk once it is dumped.

Fix: relax the detector to `\xfc\x51` **or** `\xfc\x50`, re-dump, and add chunk 33 to the queue.
