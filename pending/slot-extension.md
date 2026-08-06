# Extending chunk 43's script slot to 16,384 bytes

Traced in `KOUSEI.EXE` (1,073,152 bytes, `PS-X EXE`, `t_addr 0x80010000`, `t_size 0x105800`,
`pc0 0x800BD4AC`). File offset = `addr - 0x80010000 + 0x800`.

## 1. How a map chunk is actually loaded

`map_load(a0 = map index)` at **`0x8006365C`**. The index is turned into a sector base at
`0x80063680`–`0x8006368C`: `s2 = idx*4 + idx = idx*5`, `<<4`, added → **`s2 = idx * 85`**.
85 sectors × 2,048 = `0x2A800`, the chunk stride.

Every read goes through `read(path, sector, count)` at **`0x80064C48`**, with the destination
pointer written to the file record at `0x800F4760` (= HEXMAP record + 0x100) and the path at
`0x800F4660`. The staging buffer is **`0x801C0DDC`** (`s3`, set at `0x8006369C`).

| Call site | Sector | Count | Bytes | Chunk range | Consumer |
|---|---|---|---|---|---|
| `0x800636EC` | `s2+0x00` | 0x11 | 34,816 | `0x00000..0x08800` | TIM → VRAM |
| `0x8006375C` | `s2+0x11` | 0x11 | 34,816 | `0x08800..0x11000` | TIM → VRAM |
| `0x800637C8` | `s2+0x22` | 0x11 | 34,816 | `0x11000..0x19800` | TIM → VRAM |
| `0x80063834` | `s2+0x33` | 0x17 | 47,104 | `0x19800..0x25000` | two copies, below |
| **`0x80063914`** | **`s2+0x4A`** | **0x4** | **8,192** | **`0x25000..0x27000`** | **script** |
| `0x80063978` | `s2+0x4E` | 0x4 | 8,192 | `0x27000..0x29000` | unit / deployment |
| `0x800639CC` | `s2+0x52` | 0x3 | 6,144 | `0x29000..0x2A800` | CLUT loop → `0x80191858` |

Sectors 0..84 — **the chunk is completely full, so the slot cannot grow upward.** It has to
grow downward, into the fourth read.

### What the fourth read actually consumes

Two fixed-size copies, both taken from the staging buffer, both issued **before** the script
read:

- `0x80063854` → `0x800158B8(buf, 0x80130514, w=0x800, h=5)` — consumes `0x19808..0x1E808`.
- `0x8006389C` → `0x80015B44(buf+0x5800, 0x801D6EA8, w, h)`, a `copy(src+8, dst, w*h/2 words)`.
  Large map `w=0x68 h=0x4E` → **`0x1F008..0x22F68`**; small map `w=0x34 h=0x27` →
  `0x1F008..0x1FFE0`.

`0x22F68` is the largest offset any consumer reaches below the slot. Nothing in the image
references `buf+0x9800` (= chunk `+0x23000`), so **`0x23000` is the floor**, and it is
sector-aligned (sector 70). Chunk 43 is zero from `+0x207CD`, so `0x23000..0x25000` is free in
the only chunk that needs it.

**New slot for chunk 43: `chunk+0x23000 .. +0x27000`, sectors 70..77, 16,384 bytes.**
The `+0x27000` unit table is not touched.

## 2. The RAM buffer is the real constraint — 8,192 bytes, hard

`0x8006551C` runs immediately after the script read:

```
8006551C  a1 = 0x801C0DDC              ; staging buffer
80065528  t0 = 0x80154F40              ; destination
80065530  a3 = 0x80154F41
80065538  loop: dst[i*2]=src[1], dst[i*2+1]=src[0]   ; byte-swap to RAM order
80065560  slti v0,a2,0x1000            ; 4,096 halfwords = 8,192 bytes
80065578  sw v0, 0x801DC784            ; script base pointer
8006559C  loop: scan for 0xFFFF (skip 0xFCA6 +6), fill 0x801EC784 + i*4
80065598  a3 = 0x32                    ; 50 entry slots
800655D8  slti v0,a2,0x1000
```

`0x80154F40` is BSS. **The next code-referenced address above it is `0x80156F4C` — 12 bytes
past the end of the 8,192-byte buffer.** Reading 16 KB into it corrupts a variable with 12
references. This is the silent failure the slot change has to avoid, and it is why the disc-side
change alone is not enough.

Relocation target: **`0x80180000`**, inside the BSS region `findings.md` §16.3 already validated
as unwritten across savestates from three scenes. 32 KB clear of the relocated char buffer at
`0x80178000`, ~57 KB below the region's upper bound, inside the boot BSS clear
(`0x80115660`–`0x801FDC94`).

Staging buffer capacity is not a problem: the fourth read already writes `0x801C0DDC + 0xB800`,
and the next referenced object is `0x801D0000`, so ~62 KB is available.

## 3. The patch set

Verify every "was" word before writing. All addresses confirmed against the retail EXE.

### 3a. Injected stub — 64 bytes at `0x800F3ECC` (file `0x0E46CC`)

520-byte run, confirmed all-zero in the shipped file, `Appendix B` execution-proven.

| Addr | Word | Instruction |
|---|---|---|
| `0x800F3ECC` | `27BDFFF8` | `addiu sp,sp,-8` |
| `0x800F3ED0` | `AFBF0000` | `sw ra,0(sp)` |
| `0x800F3ED4` | `34020E47` | `ori v0,zero,0xE47`  ← 43 × 85 |
| `0x800F3ED8` | `14A20003` | `bne a1,v0,0x800F3EE8` |
| `0x800F3EDC` | `34060004` | `ori a2,zero,4` (delay) |
| `0x800F3EE0` | `24A50046` | `addiu a1,a1,0x46` |
| `0x800F3EE4` | `0803CFBC` | `j 0x800F3EF0` |
| `0x800F3EE8` | `34060008` | `ori a2,zero,8` (delay) |
| `0x800F3EEC` | `24A5004A` | `addiu a1,a1,0x4A` |
| `0x800F3EF0` | `0C019312` | `jal 0x80064C48` |
| `0x800F3EF4` | `00000000` | `nop` |
| `0x800F3EF8` | `8FBF0000` | `lw ra,0(sp)` |
| `0x800F3EFC` | `00000000` | `nop`  ← load delay slot |
| `0x800F3F00` | `27BD0008` | `addiu sp,sp,8` |
| `0x800F3F04` | `03E00008` | `jr ra` |
| `0x800F3F08` | `00000000` | `nop` |

Branch layout note: `bne` **falls through** to the chunk-43 case and branches to the normal case,
so the delay slot can carry the default `a2 = 4` for both paths. `v0` is dead at the call site
(last written `0x80063900`); `s2` is a saved register and survives.

### 3b. Call site

| Addr | File | Was | Now | Instruction |
|---|---|---|---|---|
| `0x80063910` | `0x054110` | `2645004A` | `0C03CFB3` | `jal 0x800F3ECC` |
| `0x80063914` | `0x054114` | `0C019312` | `02402821` | `addu a1,s2,zero` (delay) |
| `0x80063918` | `0x054118` | `34060004` | `00000000` | `nop` |

### 3c. RAM buffer relocation and length

| Addr | File | Was | Now | Instruction |
|---|---|---|---|---|
| `0x80065528` | `0x055D28` | `3C088015` | `3C088018` | `lui t0,0x8018` |
| `0x8006552C` | `0x055D2C` | `25084F40` | `25080000` | `addiu t0,t0,0` |
| `0x80065530` | `0x055D30` | `3C078015` | `3C078018` | `lui a3,0x8018` |
| `0x80065534` | `0x055D34` | `24E74F41` | `24E70001` | `addiu a3,a3,1` |
| `0x80065560` | `0x055D60` | `28C21000` | `28C22000` | `slti v0,a2,0x2000` |
| `0x8006556C` | `0x055D6C` | `3C028015` | `3C028018` | `lui v0,0x8018` |
| `0x80065570` | `0x055D70` | `24424F40` | `24420000` | `addiu v0,v0,0` |
| `0x800655D8` | `0x055DD8` | `28C21000` | `28C22000` | `slti v0,a2,0x2000` |

Both loop bounds are raised for **every** map, not just 43. For the other 43 maps the second
8 KB is stale staging-buffer content, which is harmless: the entry scan walks in address order,
so the real events are found first, and the table stops at 50 entries either way. Making the
bounds conditional as well is possible but buys nothing.

### 3d. Tooling

`tools/riotbattle.py` needs a per-chunk `SCRIPT_LO` — `0x23000` for chunk 43, `0x25000`
otherwise — in `find_script_bounds`, `dump`, `insert` and `checkedit`, and a per-chunk
`SCRIPT_SLOT` of 16,384 / 8,192. `checkedit`'s "all inside script slots" assertion has to widen
for 43 only, or it will report the extension as an out-of-slot write.

## 4. Verify before trusting

1. `simcheck`-style R3000 simulation of the stub, enforcing the load delay slot (`findings.md`
   §14.8 #1) — the `lw ra` / `addiu sp` pair above is exactly that hazard.
2. Boot chunk 43 and confirm the box renders; then boot **chunk 0** (8,163 / 8,192 bytes, the
   tightest translated chunk) to confirm the normal path is untouched.
3. Watch `0x80156F4C` with a write breakpoint on a stock run to confirm what it is before
   assuming the relocation was necessary — it is, but the evidence is a reference count, not a
   name.
4. `0x800F3ECC` is also `hookfont`'s preferred region. Apply the font hook first and confirm it
   did not allocate there, or reserve the 64 bytes explicitly.
