#!/usr/bin/env python3
"""riotfont.py — Krom2RawAdd hook prototype for Riot Stars (SLPS-00829).

The game fetches every 16x16 kanji glyph from the PS1 BIOS kanji ROM via
B(51h) Krom2RawAdd (see findings.md §7). This tool redirects that call to a
routine injected into free space in the EXE, which returns a pointer to a
custom 32-byte (16 halfword) 1bpp glyph.

Prototype behaviour: the injected routine IGNORES the requested SJIS code and
always returns one fixed test glyph (an asymmetric 'F' with a dot in the
bottom-right corner). If the hook works, every character in the dialogue box
renders as that glyph — and its orientation tells you the real bit/byte order
of the bitmap the expander expects.

Commands
  info EXE                    locate the BIOS stub and all jal call sites
  findspace EXE [MIN]         list zero runs inside the loaded image (candidates
                              for injection; default MIN=64 bytes)
  liveness EXE SAV [SAV...]   compare those zero runs against main RAM in one or
                              more DuckStation savestates. Runs the game writes
                              to at runtime are LIVE and must never be used.
                              This is the only trustworthy free-space evidence.
  hook EXE OUT --addr 0xADDR  [--site N | --site all] [--flip-bits] [--swap-bytes]
                              inject the fixed F test glyph (space-probing tool)
  hookfont EXE OUT --addr auto [--style wide|narrow] [--site N | --site all]
                              PRODUCTION hook: ASCII font table for full-width
                              Latin/digit/punct SJIS codes; anything unmapped
                              falls through to the BIOS (kanji keeps working).
                              'auto' scatters the ~3 KB payload across the
                              execution-proven path-table padding cluster
                              (0x800F3E00-0x800F6000) using per-glyph pointers.
                              --addr also accepts a comma list of PSX addresses.
                              In-place patch, size preserved. AVOID the zero
                              runs above 0x80100000: they are live
                              zero-initialised battle-loader state (confirmed
                              by black screen after name entry, 2026-07-30).

SLPS_008.29 -- menus and name entry (session 3, findings §19-§22)
  slpsmap EXE                 verified address map, live grid/menu/prompt dump
  namegrid IN OUT [--dry]     kana grid -> Latin A-Z/a-z (data + 5 guard words)
  menutext IN OUT [--dry]     main menu -> English (4 x 12 full-width)
  prompttext IN OUT [--dry]   prompt/confirm strings (+ Yes-button width;
                              --narrow-yes keeps the stock 2-char button)
  gridsim EXE SAV [SAV...]    simulate the name-entry grid renderer and check
                              every cell against savestate VRAM. PASSES on the
                              pristine EXE (120/120) -- that is what makes it
                              trustworthy on a patched one.
  deadcode EXE LO HI          enumerate every entry into a code region; this
                              is how 0x80026504-0x80026A00 (1276 bytes) was
                              proved reclaimable.

  Build order for the boot EXE:
    namegrid SLPS_008.29 s1.29 ; menutext s1.29 s2.29 ; prompttext s2.29 OUT
    gridsim OUT nameentry.sav        # must print RESULT: PASS

Notes
  * --addr is a PSX address (0x80xxxxxx) inside the EXE's loaded image.
  * CAUTION on free space: a zero run inside the file may be genuinely-used
    zero-initialised data, not padding. If the game misbehaves in ways
    unrelated to text, try a different run. Runs snuggled between code/data
    sections at 4-byte-odd sizes are usually alignment padding and safest.
  * Default glyph packing: one row per halfword pair, byte0 = left 8 pixels,
    MSB = leftmost pixel. If the on-screen glyph is mirrored use --flip-bits;
    if the left/right byte halves are swapped use --swap-bytes. Re-run hook
    with the flag and rebuild.
"""
import re
import struct, sys

HDR = 0x800

# BIOS B(51h) dispatch stub: addiu t2,zero,0xB0 ; jr t2 ; addiu t1,zero,0x51
STUB_PATTERN = struct.pack('<III', 0x240A00B0, 0x01400008, 0x24090051)

# Test glyph: bold 'F' + 2x2 dot bottom-right. bit15 = leftmost pixel.
GLYPH_ROWS = [
    0b0000000000000000,
    0b0111111111111100,
    0b0111111111111100,
    0b0110000000000000,
    0b0110000000000000,
    0b0110000000000000,
    0b0111111111100000,
    0b0111111111100000,
    0b0110000000000000,
    0b0110000000000000,
    0b0110000000000000,
    0b0110000000000000,
    0b0110000000000000,
    0b0110000000000000,
    0b0000000000000011,
    0b0000000000000011,
]


def load_exe(path):
    data = bytearray(open(path, 'rb').read())
    if data[:8] != b'PS-X EXE':
        raise SystemExit('not a PS-X EXE: %s' % path)
    t_addr = struct.unpack_from('<I', data, 0x18)[0]
    t_size = struct.unpack_from('<I', data, 0x1C)[0]
    pc0 = struct.unpack_from('<I', data, 0x10)[0]
    return data, t_addr, t_size, pc0


def psx_to_file(psx, t_addr):
    return psx - t_addr + HDR


def file_to_psx(off, t_addr):
    return off - HDR + t_addr


def find_stub(data, t_addr):
    hits = []
    i = HDR
    while True:
        j = data.find(STUB_PATTERN, i)
        if j < 0:
            break
        hits.append(file_to_psx(j, t_addr))
        i = j + 4
    return hits


def jal_encoding(target):
    return 0x0C000000 | ((target & 0x0FFFFFFF) >> 2)


def find_call_sites(data, t_addr, stub_psx):
    enc = struct.pack('<I', jal_encoding(stub_psx))
    sites = []
    for off in range(HDR, len(data) - 3, 4):
        if data[off:off+4] == enc:
            sites.append(file_to_psx(off, t_addr))
    return sites


def cmd_info(path):
    data, t_addr, t_size, pc0 = load_exe(path)
    print('%s: t_addr=0x%08X t_size=0x%X (file %d bytes) pc0=0x%08X'
          % (path, t_addr, t_size, len(data), pc0))
    stubs = find_stub(data, t_addr)
    if not stubs:
        print('NO Krom2RawAdd (B 51h) stub found.')
        return
    for s in stubs:
        print('B(51h) Krom2RawAdd stub at 0x%08X (file 0x%X)' % (s, psx_to_file(s, t_addr)))
        sites = find_call_sites(data, t_addr, s)
        if not sites:
            print('  no jal call sites found (indirect call? check disassembly)')
        for k, c in enumerate(sites):
            print('  call site %d: jal @ 0x%08X (file 0x%X)' % (k, c, psx_to_file(c, t_addr)))


def cmd_findspace(path, minlen):
    data, t_addr, t_size, _ = load_exe(path)
    end = min(len(data), HDR + t_size)
    runs = []
    i = HDR
    while i < end:
        if data[i] == 0:
            j = i
            while j < end and data[j] == 0:
                j += 1
            if j - i >= minlen:
                runs.append((i, j - i))
            i = j
        else:
            i += 1
    if not runs:
        print('no zero runs >= %d bytes' % minlen)
        return
    print('zero runs inside loaded image (>=%d bytes):' % minlen)
    for off, n in sorted(runs, key=lambda r: -r[1])[:30]:
        print('  PSX 0x%08X  file 0x%06X  %6d bytes' % (file_to_psx(off, t_addr), off, n))
    print('pick a 4-byte-aligned address with >= 48 bytes; pass it to hook --addr')


def build_glyph(flip_bits, swap_bytes):
    out = bytearray()
    for r in GLYPH_ROWS:
        if flip_bits:
            r = int('{:016b}'.format(r)[::-1], 2)
        hi, lo = (r >> 8) & 0xFF, r & 0xFF          # hi = left 8 px by default
        pair = bytes([lo, hi]) if swap_bytes else bytes([hi, lo])
        out += pair
    assert len(out) == 32
    return bytes(out)


def cmd_hook(path, out_path, addr, site_sel, flip_bits, swap_bytes):
    data, t_addr, t_size, _ = load_exe(path)
    orig = bytes(data)
    stubs = find_stub(data, t_addr)
    if len(stubs) != 1:
        raise SystemExit('expected exactly 1 stub, found %d — aborting' % len(stubs))
    stub = stubs[0]
    sites = find_call_sites(data, t_addr, stub)
    if not sites:
        raise SystemExit('no jal call sites found — aborting')

    if site_sel == 'all':
        chosen = sites
    else:
        n = int(site_sel)
        if n < 0 or n >= len(sites):
            raise SystemExit('site %d out of range (0..%d)' % (n, len(sites) - 1))
        chosen = [sites[n]]

    if addr & 3:
        raise SystemExit('--addr must be 4-byte aligned')
    routine_off = psx_to_file(addr, t_addr)
    glyph_psx = addr + 16
    glyph_off = routine_off + 16
    total = 16 + 32
    if routine_off < HDR or glyph_off + 32 > min(len(data), HDR + t_size):
        raise SystemExit('--addr 0x%08X (+%d bytes) is outside the loaded image' % (addr, total))
    if any(data[routine_off:routine_off + total]):
        raise SystemExit('target region at 0x%08X is not all zero — refusing to overwrite' % addr)

    hi = ((glyph_psx + 0x8000) >> 16) & 0xFFFF
    lo = glyph_psx & 0xFFFF
    routine = struct.pack('<IIII',
                          0x3C020000 | hi,      # lui   v0, hi(glyph)
                          0x03E00008,           # jr    ra
                          0x24420000 | lo,      # addiu v0, v0, lo(glyph)  (delay slot)
                          0x00000000)           # pad
    data[routine_off:routine_off + 16] = routine
    data[glyph_off:glyph_off + 32] = build_glyph(flip_bits, swap_bytes)

    enc = struct.pack('<I', jal_encoding(addr))
    for c in chosen:
        off = psx_to_file(c, t_addr)
        data[off:off + 4] = enc

    if len(data) != len(orig):
        raise SystemExit('internal error: size changed')
    changed = sum(1 for a, b in zip(orig, data) if a != b)
    open(out_path, 'wb').write(bytes(data))
    print('routine  @ 0x%08X (file 0x%X)' % (addr, routine_off))
    print('glyph    @ 0x%08X (file 0x%X)  flip_bits=%s swap_bytes=%s'
          % (glyph_psx, glyph_off, flip_bits, swap_bytes))
    for c in chosen:
        print('patched  jal @ 0x%08X  -> 0x%08X (was -> 0x%08X)' % (c, addr, stub))
    skipped = [c for c in sites if c not in chosen]
    for c in skipped:
        print('UNTOUCHED call site @ 0x%08X (still BIOS)' % c)
    print('OK — %d bytes changed, size preserved (%d bytes). Rebuild the ISO and boot.'
          % (changed, len(data)))




# ============================ v2: production font hook ============================

# Public-domain 8x8 font (dhepper/font8x8, IBM VGA lineage), chars 0x20..0x7E,
# 8 bytes per char, one byte per row, LSB = LEFTMOST pixel (reversed on emit).
FONT8X8_HEX = (
    '0000000000000000183C3C1818001800363600000000000036367F367F3636000C3E031E301F'
    '0C00006333180C6663001C361C6E3B336E000606030000000000180C0606060C1800060C1818'
    '180C060000663CFF3C660000000C0C3F0C0C000000000000000C0C060000003F000000000000'
    '0000000C0C006030180C060301003E63737B6F673E000C0E0C0C0C0C3F001E33301C06333F00'
    '1E33301C30331E00383C36337F3078003F031F3030331E001C06031F33331E003F3330180C0C'
    '0C001E33331E33331E001E33333E30180E00000C0C00000C0C00000C0C00000C0C06180C0603'
    '060C180000003F00003F0000060C1830180C06001E3330180C000C003E637B7B7B031E000C1E'
    '33333F3333003F66663E66663F003C66030303663C001F36666666361F007F46161E16467F00'
    '7F46161E16060F003C66030373667C003333333F333333001E0C0C0C0C0C1E00783030303333'
    '1E006766361E366667000F06060646667F0063777F7F6B63630063676F7B736363001C366363'
    '63361C003F66663E06060F001E3333333B1E38003F66663E366667001E33070E38331E003F2D'
    '0C0C0C0C1E003333333333333F0033333333331E0C006363636B7F7763006363361C1C366300'
    '3333331E0C0C1E007F6331184C667F001E06060606061E0003060C18306040001E1818181818'
    '1E00081C36630000000000000000000000FF0C0C18000000000000001E303E336E000706063E'
    '66663B0000001E3303331E003830303E33336E0000001E333F031E001C36060F06060F000000'
    '6E33333E301F0706366E666667000C000E0C0C0C1E00300030303033331E070666361E366700'
    '0E0C0C0C0C0C1E000000337F7F6B630000001F333333330000001E3333331E0000003B66663E'
    '060F00006E33333E307800003B6E66060F0000003E031E301F00080C3E0C0C2C180000003333'
    '33336E0000003333331E0C000000636B7F7F3600000063361C36630000003333333E301F0000'
    '3F190C263F00380C0C070C0C38001818180018181800070C0C380C0C07006E3B000000000000'
)

# SJIS full-width code -> ASCII char covered by the custom font.
SJIS_TO_ASCII = {}
for i in range(10):
    SJIS_TO_ASCII[0x824F + i] = chr(ord('0') + i)      # fullwidth digits
for i in range(26):
    SJIS_TO_ASCII[0x8260 + i] = chr(ord('A') + i)      # fullwidth uppercase
    SJIS_TO_ASCII[0x8281 + i] = chr(ord('a') + i)      # fullwidth lowercase
SJIS_TO_ASCII.update({
    0x8140: ' ',   # ideographic space
    0x8141: ',',   0x8142: '.',    # 、 。
    0x8143: ',',   0x8144: '.',    # ， ．
    0x8146: ':',   0x8147: ';',
    0x8148: '?',   0x8149: '!',
    0x815B: '-',   0x815D: '-',    # ー ‐
    0x815E: '/',   0x8160: '~',
    0x8165: "'",   0x8166: "'",
    0x8167: '"',   0x8168: '"',
    0x8169: '(',   0x816A: ')',
    0x817B: '+',   0x817C: '-',
    0x8181: '=',
    0x8193: '%',   0x8195: '&',   0x8196: '*',   0x8197: '@',
})


def font8x8(ch):
    i = ord(ch) - 0x20
    h = FONT8X8_HEX
    return bytes.fromhex(h[i*16:(i+1)*16])


def make_glyph(ch, style):
    """Build a 32-byte 16x16 1bpp glyph in the CONFIRMED on-target order:
    16 rows top-to-bottom, [left byte, right byte], MSB = leftmost pixel."""
    rows8 = font8x8(ch)
    if style == 'half':
        out = bytearray(b'\x00' * 8)          # 4 blank rows (2 bytes each)
        for r in rows8:
            w = 0
            for b in range(8):
                if r & (1 << b):
                    w |= 1 << (15 - b)
            out += bytes([(w >> 8) & 0xFF, w & 0xFF])
        out += b'\x00' * (32 - len(out))
        assert len(out) == 32
        return bytes(out)
    out = bytearray()
    for r in rows8:
        # font8x8: LSB = leftmost. Build a 16-bit row with bit15 = leftmost.
        if style == 'wide':
            w = 0
            for b in range(8):
                if r & (1 << b):
                    w |= 0b11 << (14 - 2*b)          # double each pixel
        elif style == 'half':
            # 8 px in the LEFT byte only; the renderer patch emits byte0 alone
            w = 0
            for b in range(8):
                if r & (1 << b):
                    w |= 1 << (15 - b)
        else:  # narrow: 8px glyph centered in columns 4..11
            w = 0
            for b in range(8):
                if r & (1 << b):
                    w |= 1 << (11 - b)
        pair = bytes([(w >> 8) & 0xFF, w & 0xFF])
        out += pair                                   # vertical double:
        out += pair                                   # each row emitted twice
    assert len(out) == 32
    return bytes(out)


# ---- minimal two-pass MIPS assembler (just what the routine needs) ----
ZERO, V0, V1, A0, T0, T1, T2, RA = 0, 2, 3, 4, 8, 9, 10, 31
T3, T4, T5, T6 = 11, 12, 13, 14


def assemble(prog, base):
    """prog: list of ('op', args...) or ('label', name). Returns bytes."""
    # pass 1: addresses
    labels = {}
    pc = base
    for ins in prog:
        if ins[0] == 'label':
            labels[ins[1]] = pc
        else:
            pc += 4
    # pass 2: encode
    out = bytearray()
    pc = base
    for ins in prog:
        op = ins[0]
        if op == 'label':
            continue
        if op == 'lui':
            w = 0x3C000000 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op == 'ori':
            w = 0x34000000 | ins[2] << 21 | ins[1] << 16 | (ins[3] & 0xFFFF)
        elif op == 'addiu':
            w = 0x24000000 | ins[2] << 21 | ins[1] << 16 | (ins[3] & 0xFFFF)
        elif op == 'addu':
            w = 0x00000021 | ins[2] << 21 | ins[3] << 16 | ins[1] << 11
        elif op == 'sll':
            w = 0x00000000 | ins[2] << 16 | ins[1] << 11 | ins[3] << 6
        elif op == 'lhu':
            w = 0x94000000 | ins[3] << 21 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op == 'lw':
            w = 0x8C000000 | ins[3] << 21 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op == 'lbu':
            w = 0x90000000 | ins[3] << 21 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op == 'sh':
            w = 0xA4000000 | ins[3] << 21 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op == 'sw':
            w = 0xAC000000 | ins[3] << 21 | ins[1] << 16 | (ins[2] & 0xFFFF)
        elif op in ('beq', 'bne'):
            off = (labels[ins[3]] - (pc + 4)) >> 2
            w = (0x10000000 if op == 'beq' else 0x14000000) \
                | ins[1] << 21 | ins[2] << 16 | (off & 0xFFFF)
        elif op == 'jr':
            w = ins[1] << 21 | 0x08
        elif op == 'j':
            w = 0x08000000 | ((ins[1] & 0x0FFFFFFF) >> 2)
        elif op == 'nop':
            w = 0
        else:
            raise ValueError(op)
        out += struct.pack('<I', w)
        pc += 4
    return bytes(out), labels


AUTO_WINDOW = (0x800F3E00, 0x800F6000)   # path-table padding cluster, execution-proven
ROUTINE_LEN = 21 * 4                      # instructions in the v3 routine


def zero_runs(data, t_addr, lo_psx, hi_psx, minlen=64):
    """Zero runs inside [lo_psx, hi_psx), 4-aligned start, as (psx, usable_len)."""
    lo = psx_to_file(lo_psx, t_addr); hi = psx_to_file(hi_psx, t_addr)
    lo = max(lo, HDR); hi = min(hi, len(data))
    runs = []
    i = lo
    while i < hi:
        if data[i] == 0:
            j = i
            while j < hi and data[j] == 0:
                j += 1
            a = (i + 3) & ~3
            if j - a >= minlen:
                runs.append((file_to_psx(a, t_addr), (j - a) & ~3))
            i = j
        else:
            i += 1
    return runs


def run_extent(data, t_addr, psx):
    """Usable zero extent starting at a user-supplied address."""
    off = psx_to_file(psx, t_addr)
    j = off
    while j < len(data) and data[j] == 0:
        j += 1
    return (j - off) & ~3


class Alloc:
    def __init__(self, runs):
        # runs: list of [psx, remaining]
        self.runs = [list(r) for r in sorted(runs, key=lambda r: -r[1])]

    def take(self, size, align=4):
        size = (size + align - 1) // align * align
        for r in self.runs:
            base, rem = r
            pad = (-base) % align
            if rem - pad >= size:
                addr = base + pad
                r[0] = addr + size
                r[1] = rem - pad - size
                return addr
        return None


def build_routine(entry, codes_psx, ptrs_psx, n, stub_psx):
    hi = lambda x: ((x + 0x8000) >> 16) & 0xFFFF
    lo = lambda x: x & 0xFFFF
    prog = [
        ('lui',   T1, hi(codes_psx)),
        ('addiu', T1, T1, lo(codes_psx)),
        ('ori',   T2, ZERO, n),
        ('addu',  T0, ZERO, ZERO),
        ('label', 'loop'),
        ('lhu',   V0, 0, T1),
        ('nop',),                       # R3000 load delay slot — MANDATORY
        ('beq',   V0, A0, 'hit'),
        ('addiu', T1, T1, 2),           # delay slot (harmless on hit)
        ('addiu', T0, T0, 1),
        ('bne',   T0, T2, 'loop'),
        ('nop',),
        ('j',     stub_psx),            # miss -> original BIOS Krom2RawAdd
        ('nop',),
        ('label', 'hit'),
        ('sll',   T0, T0, 2),           # index * 4
        ('lui',   V0, hi(ptrs_psx)),
        ('addiu', V0, V0, lo(ptrs_psx)),
        ('addu',  V0, V0, T0),
        ('lw',    V0, 0, V0),           # v0 = glyph pointer
        ('nop',),                       # load delay slot
        ('jr',    RA),
        ('nop',),                       # delay slot; load完成 before caller reads v0
    ]
    code, _ = assemble(prog, entry)
    if len(code) != ROUTINE_LEN:
        raise SystemExit('internal: routine is %d bytes, expected %d' % (len(code), ROUTINE_LEN))
    return code



# ---- evidence-based placement (v5) ----

def all_runs(data, t_addr, t_size, minlen=32):
    end_img = min(len(data), HDR + t_size)
    runs = []
    i = HDR
    while i < end_img:
        if data[i] == 0:
            j = i
            while j < end_img and data[j] == 0:
                j += 1
            a = (i + 3) & ~3
            if j - a >= minlen:
                runs.append((file_to_psx(a, t_addr), (j - a) & ~3))
            i = j
        else:
            i += 1
    return runs


def detect_tables(runs, tol=8, minrun=3):
    """Mark runs that sit in an arithmetic progression = fixed-stride record
    table. Those zeros are structure, not padding, even when never written."""
    addrs = sorted(r[0] for r in runs)
    flagged = set()
    n = len(addrs)
    i = 0
    while i < n - 2:
        d = addrs[i + 1] - addrs[i]
        if not (0x40 <= d <= 0x600):
            i += 1
            continue
        j = i + 1
        while j < n - 1 and abs((addrs[j + 1] - addrs[j]) - d) <= tol:
            j += 1
        if j - i + 1 >= minrun:
            for k in range(i, j + 1):
                flagged.add(addrs[k])
            i = j
        else:
            i += 1
    return flagged


def live_runs(runs, data, t_addr, t_size, sav_paths):
    live = {}
    used = 0
    for sp in sav_paths:
        blob = load_savestate(sp)
        base, conf = calibrate(blob, data, t_addr, t_size)
        if base is None:
            print('  %s: could not calibrate — SKIPPED' % sp)
            continue
        used += 1
        for psx, n in runs:
            off = base + (psx - 0x80000000)
            if 0 <= off and off + n <= len(blob) and any(blob[off:off + n]):
                live[psx] = max(live.get(psx, 0), sum(1 for b in blob[off:off + n] if b))
    return live, used


SET_UPPER = 'upper'
SET_FULL = 'full'


def code_subset(which):
    codes = sorted(SJIS_TO_ASCII)
    if which == SET_FULL:
        return codes
    keep = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ .,!?\'-:;')
    return [c for c in codes if SJIS_TO_ASCII[c] in keep]



def detect_hooked(data, t_addr, t_size, stub_psx):
    """Our injected routine falls through with `j stub`. Its presence means the
    EXE has already been hooked (so no jal to the BIOS stub remains)."""
    want = 0x08000000 | ((stub_psx & 0x0FFFFFFF) >> 2)
    end = min(len(data), HDR + t_size)
    for off in range(HDR, end - 3, 4):
        if struct.unpack_from('<I', data, off)[0] == want:
            return file_to_psx(off, t_addr)
    return None



# ---- compact half-width font: 8 bytes/glyph, expanded at call time (v7) ----
# Safe because the caller (KOUSEI.EXE 0x80015DB4) copies all 15 halfwords out of
# our pointer immediately, so only one glyph is ever live. Storage drops from
# 30 bytes/glyph to 8, which is what makes the lowercase set fit.

GLYPH_TOP = 4          # first pixel row of the 8x8 cell within the 15-row cell


def font8_rows_msb(ch):
    """8 bytes, one per row, MSB = leftmost (font8x8 stores LSB = leftmost)."""
    out = bytearray()
    for r in font8x8(ch):
        v = 0
        for b in range(8):
            if r & (1 << b):
                v |= 1 << (7 - b)
        out.append(v)
    return bytes(out)


def build_compact_routine(entry, codes_psx, font_psx, buf_psx, n, stub_psx):
    hi = lambda x: ((x + 0x8000) >> 16) & 0xFFFF
    lo = lambda x: x & 0xFFFF
    top = GLYPH_TOP * 2                       # byte offset of first drawn row
    prog = [
        ('lui',   T1, hi(codes_psx)),
        ('addiu', T1, T1, lo(codes_psx)),
        ('ori',   T2, ZERO, n),
        ('addu',  T0, ZERO, ZERO),
        ('label', 'loop'),
        ('lhu',   V0, 0, T1),
        ('nop',),                              # load delay
        ('beq',   V0, A0, 'hit'),
        ('addiu', T1, T1, 2),
        ('addiu', T0, T0, 1),
        ('bne',   T0, T2, 'loop'),
        ('nop',),
        ('j',     stub_psx),                   # unmapped -> BIOS kanji ROM
        ('nop',),
        ('label', 'hit'),
        ('sll',   T0, T0, 3),                  # idx * 8
        ('lui',   T1, hi(font_psx)),
        ('addiu', T1, T1, lo(font_psx)),
        ('addu',  T1, T1, T0),                 # t1 = &font[idx]
        ('lui',   V0, hi(buf_psx)),
        ('addiu', V0, V0, lo(buf_psx)),
        ('sw',    ZERO, 0, V0),                # blank rows above
        ('sw',    ZERO, 4, V0),
        ('sw',    ZERO, 24, V0),               # blank rows below
        ('sh',    ZERO, 28, V0),
        ('addu',  T2, ZERO, ZERO),
        ('ori',   T6, ZERO, 8),
        ('label', 'row'),
        ('addu',  T3, T1, T2),
        ('lbu',   T4, 0, T3),
        ('sll',   T5, T2, 1),
        ('nop',),                              # (byte goes in the LOW half:
                                               #  even offset = left 8 px, which
                                               #  is what the expander lbu's)
        ('addu',  T5, T5, V0),
        ('sh',    T4, top, T5),
        ('addiu', T2, T2, 1),
        ('bne',   T2, T6, 'row'),
        ('nop',),
        ('jr',    RA),
        ('nop',),
    ]
    return assemble(prog, entry)[0]


def cmd_hookfont_compact(data, t_addr, t_size, runs, stub, codes):
    """Allocate + emit the compact layout. Returns (rout_psx, writes, need)."""
    n = len(codes)
    al = Alloc(runs)
    font_psx = al.take(8 * n)                  # one contiguous block
    codes_psx = al.take(2 * n)
    buf_psx = al.take(32, align=2)
    rout_psx = al.take(4 * 38)
    if None in (font_psx, codes_psx, buf_psx, rout_psx):
        return None
    writes = [
        (rout_psx, build_compact_routine(rout_psx, codes_psx, font_psx,
                                         buf_psx, n, stub)),
        (codes_psx, b''.join(struct.pack('<H', c) for c in codes)),
        (font_psx, b''.join(font8_rows_msb(SJIS_TO_ASCII[c]) for c in codes)),
    ]
    need = 8 * n + 2 * n + 32 + 4 * 38
    return rout_psx, writes, need, font_psx, buf_psx



def charbuf_reservation(data, t_addr):
    """If the `renderer` patch has relocated the tilemap/char buffer out of
    BSS into an in-image free run, those bytes are still ZERO in the file --
    the game only writes them at runtime. all_runs() would therefore happily
    hand them to the font hook. Decode the relocated base/size and reserve it.
    Returns (base_psx, n_bytes) or None."""
    try:
        wl = struct.unpack_from('<I', data, psx_to_file(0x8001C400, t_addr))[0]
        wa = struct.unpack_from('<I', data, psx_to_file(0x8001C404, t_addr))[0]
        wc = struct.unpack_from('<I', data, psx_to_file(0x8001C3B8, t_addr))[0]
        wr = struct.unpack_from('<I', data, psx_to_file(0x8001C3C8, t_addr))[0]
    except Exception:
        return None
    if (wl >> 26) != 0x0F or (wa >> 26) != 0x09:
        return None
    lo = wa & 0xFFFF
    base = ((wl & 0xFFFF) << 16) + (lo - 0x10000 if lo & 0x8000 else lo)
    if base == 0x80130230:
        return None                      # stock BSS location, nothing to reserve
    cols, rows = wc & 0xFFFF, wr & 0xFFFF
    return (base, cols * rows * 2 * 2)


def drop_reserved(runs, res):
    """Remove any run overlapping the reserved char-buffer range."""
    if not res:
        return runs, []
    base, n = res
    keep, hit = [], []
    for psx, ln in runs:
        if psx < base + n and base < psx + ln:
            hit.append((psx, ln))
        else:
            keep.append((psx, ln))
    return keep, hit


def cmd_hookfont(path, out_path, addr_spec, site_sel, style, sav_paths, which, force):
    data, t_addr, t_size, _ = load_exe(path)
    orig = bytes(data)
    stubs = find_stub(data, t_addr)
    if len(stubs) != 1:
        raise SystemExit('expected exactly 1 stub, found %d' % len(stubs))
    stub = stubs[0]
    sites = find_call_sites(data, t_addr, stub)
    if not sites:
        hooked_at = detect_hooked(data, t_addr, t_size, stub)
        if hooked_at is not None:
            raise SystemExit(
                'This EXE is ALREADY HOOKED (font routine at 0x%08X).\n'
                'Its payload still occupies free-space runs, so re-hooking would\n'
                'stack a second copy. Start from a pristine KOUSEI.EXE:\n'
                '  1. restore the original (re-extract the ISO or keep a backup)\n'
                '  2. python riotfont.py halfwidth KOUSEI.EXE KOUSEI_hw.EXE\n'
                '  3. python riotfont.py hookfont KOUSEI_hw.EXE KOUSEI_font.EXE ...\n'
                'Tip: `info` on a clean EXE shows 2 call sites pointing at the BIOS stub.'
                % hooked_at)
        raise SystemExit('no jal call sites found, and no prior hook detected — '
                         'is this the right EXE?')
    chosen = sites if site_sel == 'all' else [sites[int(site_sel)]]

    codes = code_subset(which)
    n = len(codes)
    need = ROUTINE_LEN + 2 * n + 4 * n + 30 * n

    if addr_spec not in (None, 'auto'):
        runs = []
        for a in addr_spec.split(','):
            psx = int(a, 16)
            psx = (psx + 3) & ~3
            m = run_extent(data, t_addr, psx)
            if m < 32:
                raise SystemExit('address 0x%08X has <32 zero bytes' % psx)
            runs.append((psx, m))
        print('using %d caller-specified run(s)' % len(runs))
    else:
        cand = all_runs(data, t_addr, t_size)
        _res = charbuf_reservation(data, t_addr)
        cand, _hit = drop_reserved(cand, _res)
        if _hit:
            print('RESERVED: 0x%08X (%d B) is the relocated dialogue char buffer '
                  '(renderer patch);' % _res)
            print('          excluded %d run(s) from font-hook placement.' % len(_hit))
        tables = detect_tables(cand)
        if not sav_paths and not force:
            raise SystemExit(
                'auto placement now REQUIRES savestate evidence.\n'
                '  python riotfont.py hookfont EXE OUT --sav state.sav [--sav state2.sav]\n'
                "  (use --force to place without evidence — this black-screened twice)")
        live, used = live_runs(cand, data, t_addr, t_size, sav_paths) if sav_paths else ({}, 0)
        refs = code_xrefs(data, t_addr, t_size)
        runs = []
        rej_live = rej_tab = rej_ref = 0
        for psx, m in cand:
            if psx in live:
                rej_live += 1
                continue
            if psx in tables:
                rej_tab += 1
                continue
            if xref_hits(refs, psx, m):
                rej_ref += 1
                continue
            runs.append((psx, m))
        print('candidate runs: %d total | %d LIVE (%d savestate(s)) | %d record-table | '
              '%d code-referenced | %d usable (%d bytes)'
              % (len(cand), rej_live, used, rej_tab, rej_ref, len(runs),
                 sum(r[1] for r in runs)))
        if not runs:
            raise SystemExit('no usable runs')

    total = sum(r[1] for r in runs)
    if total < need:
        raise SystemExit('need %d bytes, only %d usable — try --set upper' % (need, total))

    if style == 'half':
        res = cmd_hookfont_compact(data, t_addr, t_size, runs, stub, codes)
        if res is None:
            raise SystemExit('compact allocation failed — try --set upper')
        rout_psx, writes, need, font_psx, buf_psx = res
        for psx, blob in writes:
            off = psx_to_file(psx, t_addr)
            if any(data[off:off + len(blob)]):
                raise SystemExit('internal: region 0x%08X not zero' % psx)
            data[off:off + len(blob)] = blob
        enc = struct.pack('<I', jal_encoding(rout_psx))
        for c in chosen:
            data[psx_to_file(c, t_addr):psx_to_file(c, t_addr) + 4] = enc
        changed = sum(1 for a, b in zip(orig, data) if a != b)
        open(out_path, 'wb').write(bytes(data))
        print('compact half-width font: %d glyphs, %d bytes total' % (n, need))
        print('  routine @ 0x%08X  codes @ 0x%08X  font @ 0x%08X  scratch @ 0x%08X'
              % (rout_psx, writes[1][0], font_psx, buf_psx))
        print('  font table is 8 bytes/glyph, sorted by SJIS code — redraw there.')
        for c in chosen:
            print('  patched jal @ 0x%08X -> 0x%08X' % (c, rout_psx))
        print('OK — %d bytes changed, size preserved (%d bytes).' % (changed, len(data)))
        return

    al = Alloc(runs)
    ptrs_psx = al.take(4 * n)
    codes_psx = al.take(2 * n)
    rout_psx = al.take(ROUTINE_LEN)
    GLYPH_BYTES = 30      # 15 rows x 2; row 16 is forced blank by the caller
    glyph_psx = [al.take(GLYPH_BYTES, align=2) for _ in range(n)]
    if None in glyph_psx or None in (ptrs_psx, codes_psx, rout_psx):
        raise SystemExit('allocation failed (fragmentation) — try --set upper')

    def write(psx, blob):
        off = psx_to_file(psx, t_addr)
        if any(data[off:off + len(blob)]):
            raise SystemExit('internal: region 0x%08X not zero' % psx)
        data[off:off + len(blob)] = blob

    write(rout_psx, build_routine(rout_psx, codes_psx, ptrs_psx, n, stub))
    write(codes_psx, b''.join(struct.pack('<H', c) for c in codes))
    write(ptrs_psx, b''.join(struct.pack('<I', g) for g in glyph_psx))
    for c, g in zip(codes, glyph_psx):
        write(g, make_glyph(SJIS_TO_ASCII[c], style)[:30])

    enc = struct.pack('<I', jal_encoding(rout_psx))
    for c in chosen:
        data[psx_to_file(c, t_addr):psx_to_file(c, t_addr) + 4] = enc

    touched = sorted({r[0] for r in runs if any(
        r[0] <= x < r[0] + r[1] for x in [rout_psx, codes_psx, ptrs_psx] + glyph_psx)})
    changed = sum(1 for a, b in zip(orig, data) if a != b)
    open(out_path, 'wb').write(bytes(data))
    print('font hook: %d glyphs (%s, set=%s), %d bytes in %d run(s)'
          % (n, style, which, need, len(touched)))
    print('  routine @ 0x%08X   codes @ 0x%08X   ptr table @ 0x%08X'
          % (rout_psx, codes_psx, ptrs_psx))
    print('  runs used: %s' % ', '.join('0x%08X' % a for a in touched))
    for c in chosen:
        print('  patched jal @ 0x%08X -> 0x%08X (was -> 0x%08X)' % (c, rout_psx, stub))
    print('  unmapped SJIS codes fall through to the BIOS: kanji/kana still render.')
    print('OK — %d bytes changed, size preserved (%d bytes).' % (changed, len(data)))


# ======================= savestate liveness analysis =======================

def load_savestate(path):
    try:
        import zstandard as zstd
    except ImportError:
        raise SystemExit('pip install zstandard')
    raw = open(path, 'rb').read()
    best = None
    i = 0
    while True:
        j = raw.find(bytes.fromhex('28b52ffd'), i)
        if j < 0:
            break
        try:
            out = zstd.ZstdDecompressor().stream_reader(memoryview(raw)[j:]).read()
            if best is None or len(out) > len(best):
                best = out
        except Exception:
            pass
        i = j + 1
    if best is None:
        raise SystemExit('no zstd stream found in %s' % path)
    return best


def calibrate(blob, data, t_addr, t_size):
    """Find blob offset corresponding to PSX 0x80000000, using unique EXE slices."""
    end = min(len(data), HDR + t_size)
    cands = {}
    tried = 0
    for frac in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9):
        off = HDR + int((end - HDR) * frac) & ~3
        chunk = bytes(data[off:off + 48])
        if len(chunk) < 48 or chunk.count(0) > 24:
            continue
        if data.count(chunk) != 1:
            continue
        tried += 1
        j = blob.find(chunk)
        if j < 0:
            continue
        base = j - (file_to_psx(off, t_addr) - 0x80000000)
        cands[base] = cands.get(base, 0) + 1
    if not cands:
        return None, tried
    base = max(cands, key=lambda b: cands[b])
    return (base, cands[base]) if cands[base] >= 2 else (None, tried)


def cmd_liveness(exe_path, sav_paths):
    data, t_addr, t_size, _ = load_exe(exe_path)
    end_img = min(len(data), HDR + t_size)

    # all candidate zero runs in the loaded image
    runs = []
    i = HDR
    while i < end_img:
        if data[i] == 0:
            j = i
            while j < end_img and data[j] == 0:
                j += 1
            a = (i + 3) & ~3
            if j - a >= 32:
                runs.append((file_to_psx(a, t_addr), (j - a) & ~3))
            i = j
        else:
            i += 1

    status = {r[0]: 'clean' for r in runs}
    checked = 0
    for sp in sav_paths:
        blob = load_savestate(sp)
        base, conf = calibrate(blob, data, t_addr, t_size)
        if base is None:
            print('%s: could not calibrate (is %s the resident EXE in this state?) — SKIPPED'
                  % (sp, exe_path))
            continue
        checked += 1
        print('%s: RAM base at blob 0x%X (%d anchors agree)' % (sp, base, conf))
        for psx, n in runs:
            off = base + (psx - 0x80000000)
            if off < 0 or off + n > len(blob):
                status[psx] = 'oob'
                continue
            if any(blob[off:off + n]):
                dirty = sum(1 for b in blob[off:off + n] if b)
                if status[psx] != 'dirty':
                    status[psx] = 'dirty'
                    globals().setdefault('_dirtyinfo', {})[psx] = (dirty, n)
    if not checked:
        raise SystemExit('no usable savestates — cannot judge liveness')

    print()
    print('run            size   verdict')
    clean_total = 0
    for psx, n in sorted(runs, key=lambda r: -r[1]):
        st = status[psx]
        if st == 'dirty':
            d, tot = globals().get('_dirtyinfo', {}).get(psx, (0, n))
            print('0x%08X %6d   LIVE — game wrote %d/%d bytes at runtime' % (psx, n, d, tot))
        elif st == 'oob':
            print('0x%08X %6d   ? outside captured RAM' % (psx, n))
        else:
            print('0x%08X %6d   still zero in %d state(s)' % (psx, n, checked))
            clean_total += n
    print()
    print('total still-zero capacity: %d bytes across %d state(s)' % (clean_total, checked))
    print('NOTE: "still zero" means not-written; a run can still be READ as structure')
    print('      (that is how the 0x800F3Exx path-record table black-screened the map).')
    print('      Prefer runs far from any nearby ASCII strings or record stride.')




# ---- static cross-reference scan (v6) ----

def code_xrefs(data, t_addr, t_size):
    """Every address code can construct via lui+imm, plus stored 32-bit pointers.
    Returns a sorted list of referenced addresses."""
    end = min(len(data), HDR + t_size)
    refs = set()
    luis = {}
    for off in range(HDR, end - 3, 4):
        w = struct.unpack_from('<I', data, off)[0]
        op = w >> 26
        if op == 0x0F:
            luis[(w >> 16) & 31] = ((w & 0xFFFF) << 16, off)
            continue
        rs = (w >> 21) & 31
        if rs in luis and op in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24,
                                 0x25, 0x28, 0x29, 0x2B, 0x30, 0x38):
            hi, lo_off = luis[rs]
            if off - lo_off <= 64:
                imm = w & 0xFFFF
                simm = imm - 0x10000 if (imm & 0x8000) and op != 0x0D else imm
                refs.add((hi + simm) & 0xFFFFFFFF)
        if op in (0x02, 0x03) or (op == 0 and (w & 0x3F) in (8, 9)):
            luis.clear()
    for off in range(HDR, end - 3, 4):
        v = struct.unpack_from('<I', data, off)[0]
        if t_addr <= v < t_addr + t_size:
            refs.add(v)
    return refs


def xref_hits(refs, psx, n):
    """References landing strictly INSIDE [psx, psx+n). Addresses exactly at
    psx+n belong to the next object, so a run that is pure trailing padding
    shows zero hits."""
    return sorted(r for r in refs if psx <= r < psx + n)


def cmd_xref(path, args):
    data, t_addr, t_size, _ = load_exe(path)
    refs = code_xrefs(data, t_addr, t_size)
    print('%d distinct addresses referenced by code or pointer constants' % len(refs))
    if args:
        for a in args:
            psx = int(a, 16)
            n = run_extent(data, t_addr, psx) or 32
            h = xref_hits(refs, psx, n)
            print('0x%08X (%d zero bytes): %s' % (psx, n,
                  'CLEAN — no references inside' if not h else
                  '%d REFERENCE(S): %s' % (len(h), ', '.join('0x%08X' % x for x in h[:8]))))
    else:
        for psx, n in all_runs(data, t_addr, t_size):
            h = xref_hits(refs, psx, n)
            if h:
                print('0x%08X %6d  REFERENCED (%d) e.g. 0x%08X' % (psx, n, len(h), h[0]))


# ---- half-width renderer patch (v6) ----
# Verified by disassembly of KOUSEI.EXE:
#   80015CF0 expand(sjis, dst, fg, bg) -> 16x16 4bpp buffer (2 bytes/row in,
#            4 halfwords/row out; byte0 = left 8 px, MSB = leftmost)
#   8001C060 draw: x = base_x + (charpos*4) % 64 ; y = base_y + (charpos & ~15)
#            LoadImage(rect{w=4,h=16}, 0x80164DC8)
#   8001B7D4 charpos++ ; 8001B908 wrap when charpos >= 0x31 (48 = 3 lines x 16)
HALFWIDTH_PATCHES = [
    (0x80015E78, 0x94C20000, 0x080057BB, 'expand: skip right-half byte (j 80015EEC)'),
    (0x8001C174, 0x34020004, 0x34020002, 'LoadImage rect.w 4 -> 2 halfwords'),
    (0x8001C108, 0x00021080, 0x00021040, 'x advance: charpos*4 -> charpos*2'),
    (0x8001C158, 0x3063FFF0, 0x3063FFE0, 'row mask: 16/line -> 32/line'),
    (0x8001C168, 0x00000000, 0x00031842, 'row: srl v1,v1,1 (was nop/load slot)'),
    (0x8001B908, 0x2C420031, 0x2C420061, 'window wrap 48 -> 96 chars'),
]


def cmd_halfwidth(path, out_path, revert, glyph_only=False):
    data, t_addr, t_size, _ = load_exe(path)
    n = 0
    plist = HALFWIDTH_PATCHES[:2] if glyph_only else HALFWIDTH_PATCHES
    if glyph_only:
        print('GLYPH-ONLY: narrowing the glyph + its VRAM cell, leaving all')
        print('layout/positioning math untouched.')
    for psx, orig, new, why in plist:
        if revert:
            orig, new = new, orig
        off = psx_to_file(psx, t_addr)
        cur = struct.unpack_from('<I', data, off)[0]
        if cur == new:
            print('  already patched @ 0x%08X (%s)' % (psx, why))
            continue
        if cur != orig:
            raise SystemExit('UNEXPECTED word at 0x%08X: found %08X, expected %08X.\n'
                             'This EXE is not the build these offsets were derived from.'
                             % (psx, cur, orig))
        struct.pack_into('<I', data, off, new)
        print('  0x%08X  %08X -> %08X  %s' % (psx, orig, new, why))
        n += 1
    open(out_path, 'wb').write(bytes(data))
    print('%s: %d word(s) changed, size preserved (%d bytes).'
          % ('reverted' if revert else 'half-width', n, len(data)))
    if not revert:
        print('NOTE: glyphs must be built with --style half, and any character that')
        print('      falls through to the BIOS (kanji/kana) will render LEFT HALF ONLY.')



def cmd_fullwidth(args):
    """Convert ASCII in a script edit file to the full-width SJIS forms the
    engine expects (and that the font hook maps). Leaves existing full-width
    text, {tags}, and comment lines untouched."""
    import io
    if not args:
        raise SystemExit('usage: fullwidth IN.txt [OUT.txt]   (or: fullwidth -t "text")')
    if args[0] == '-t':
        print(to_fullwidth(' '.join(args[1:])))
        return
    inp = args[0]
    out = args[1] if len(args) > 1 else inp
    lines = io.open(inp, encoding='utf-8').read().split('\n')
    res = []
    for ln in lines:
        if ln.startswith('#'):
            res.append(ln); continue
        buf = ''
        i = 0
        while i < len(ln):
            if ln[i] == '{':                      # preserve {tags} verbatim
                j = ln.find('}', i)
                if j < 0:
                    buf += to_fullwidth(ln[i:]); break
                buf += ln[i:j + 1]; i = j + 1; continue
            buf += to_fullwidth(ln[i])
            i += 1
        res.append(buf)
    io.open(out, 'w', encoding='utf-8').write('\n'.join(res))
    print('converted %s -> %s' % (inp, out))


def to_fullwidth(s):
    o = []
    for ch in s:
        c = ord(ch)
        if c == 0x20:
            o.append('\u3000')                    # ideographic space -> 0x8140
        elif 0x21 <= c <= 0x7E:
            o.append(chr(c + 0xFEE0))             # ASCII -> U+FF01..U+FF5E
        else:
            o.append(ch)
    return ''.join(o)



FW_UPPER = {chr(0xFF21 + i): chr(0xFF41 + i) for i in range(26)}
FW_LOWER = {v: k for k, v in FW_UPPER.items()}
FW_TERM = '\uFF01\uFF1F\uFF0E\u3002'          # fullwidth ! ? . and 。


def _sentence_case_line(ln):
    out = []
    i = 0
    start = True
    while i < len(ln):
        ch = ln[i]
        if ch == '{':                              # copy {tags} verbatim
            j = ln.find('}', i)
            if j < 0:
                out.append(ln[i:]); break
            out.append(ln[i:j + 1]); i = j + 1; continue
        if ch in FW_UPPER or ch in FW_LOWER:
            up = ch if ch in FW_UPPER else FW_LOWER[ch]
            low = FW_UPPER[up]
            out.append(up if start else low)
            start = False
        else:
            if ch in FW_TERM:
                start = True
            out.append(ch)
        i += 1
    return ''.join(out)


def cmd_sentencecase(args):
    """Rewrite full-width Latin ALL-CAPS as sentence case, in place.
    Only touches U+FF21..U+FF3A / U+FF41..U+FF5A, so Japanese text, control
    {tags} and # comment lines are left exactly as they were."""
    import io
    if not args:
        raise SystemExit('usage: sentencecase FILE [OUT]')
    inp = args[0]
    out = args[1] if len(args) > 1 else inp
    lines = io.open(inp, encoding='utf-8').read().split('\n')
    res, changed = [], 0
    for ln in lines:
        if ln.startswith('#'):
            res.append(ln); continue
        new = _sentence_case_line(ln)
        if new != ln:
            changed += 1
        res.append(new)
    io.open(out, 'w', encoding='utf-8').write('\n'.join(res))
    print('sentence-cased %d line(s): %s -> %s' % (changed, inp, out))


def cmd_replace(args):
    """replace FILE "old" "new"  — both sides converted to full-width first,
    so you type plain ASCII and the file keeps engine-legal encoding."""
    import io
    if len(args) < 3:
        raise SystemExit('usage: replace FILE "old text" "new text"')
    path, old, new = args[0], to_fullwidth(args[1]), to_fullwidth(args[2])
    txt = io.open(path, encoding='utf-8').read()
    n = txt.count(old)
    if n == 0:
        raise SystemExit('not found: %s' % old)
    io.open(path, 'w', encoding='utf-8').write(txt.replace(old, new))
    print('replaced %d occurrence(s)' % n)



def cmd_findtext(args):
    """findtext FILE "text"  — search a binary for that text encoded as
    full-width Shift-JIS, trying several capitalisations. Tells you what is
    actually in the file, independent of what any dump/edit step reported."""
    if len(args) < 2:
        raise SystemExit('usage: findtext FILE "some text"')
    path, text = args[0], args[1]
    data = open(path, 'rb').read()
    variants = []
    seen = set()
    for label, t in (('as given', text), ('UPPER', text.upper()),
                     ('lower', text.lower()), ('Sentence', text.capitalize())):
        fw = to_fullwidth(t)
        try:
            enc = fw.encode('shift_jis')
        except UnicodeEncodeError:
            continue
        if enc in seen:
            continue
        seen.add(enc)
        variants.append((label, t, enc))
    print('%s (%d bytes)' % (path, len(data)))
    any_hit = False
    for label, t, enc in variants:
        hits = []
        i = 0
        while True:
            j = data.find(enc, i)
            if j < 0:
                break
            hits.append(j)
            i = j + 1
        head = ' '.join('%02X' % b for b in enc[:10])
        if hits:
            any_hit = True
            print('  FOUND %-8s "%s"' % (label, t))
            print('        bytes %s ...  at %s'
                  % (head, ', '.join('0x%X' % h for h in hits[:6])))
        else:
            print('  absent %-8s "%s"  (%s ...)' % (label, t, head))
    if not any_hit:
        print('  -> none of those capitalisations are present; the text in the')
        print('     file differs from what you searched for.')



# ============================================================================
# Renderer geometry patches (v7, 2026-07-31)
#
# Two coupled changes, applied as ONE set:
#   (a) sprite width + pen advance 16 -> 8 px
#   (b) dialogue box 12 -> 24 columns
#
# Model (disassembled + validated against a DuckStation savestate):
#
#   The text engine at 0x80018000-0x8001D000 emits NO sprites. It fills a
#   descriptor at 0x8011B21C + win*16 and hands a pointer to it (via the
#   per-window record at 0x80160EF0 + win*36, field +0x14) to a GENERIC
#   TILEMAP RENDERER at 0x800C19EC.
#
#   descriptor layout (16 bytes/window), written at 0x8001C378..0x8001C418:
#     +0  u8   cell width  in px   = 0x10   <- sprite width AND pen advance
#     +1  u8   cell height in px   = 0x10
#     +2  u16  columns             = 12
#     +4  u16  rows                = 6
#     +8  u32  -> UV/CLUT/TPAGE table  0x80190040 + win*0x800 (256 x 8 bytes)
#     +12 u32  -> tilemap (char buffer) 0x80130230 + win*144 (cols*rows u16)
#
#   The renderer reads desc[0]/desc[1] at 0x800C1A38/0x800C1A50, multiplies by
#   cols/rows for the texture extent, and emits a 6-word primitive:
#     +0 tag(len=5) +4 0xE1..tpage  +8 0x64..colour  +0xC xy
#     +0x10 u,v,clut  +0x14 w|h<<16     <- w comes straight from desc[0]
#   Per-tile advance is `addu $t3,$t3,$v0` @0x800C1FE8 with $v0 = that same w.
#   So sprite width and pen advance are ONE value: desc[0]. No renderer patch
#   is needed or wanted (it is shared with other clients).
#
# Why cols*8 and not cols*16: the pixel width of the window is computed
# separately at 0x8001C250 as `cols << 4`. Changing it to `cols << 3` makes
# 24 columns x 8 px = 192 px -- byte-identical to today's 12 x 16 px. The
# window position (-48,-64) and size (192x64) are therefore UNCHANGED, which
# keeps the box art aligned and removes a whole class of risk.
#
# Why rows 6 -> 5: the tilemap is a scroll ring. Covering a 4-row window from
# a partial scroll offset needs 5 row slots, so rows >= visible+1 = 5 is the
# correctness floor; stock ships 6 (one row of write-ahead slack). At 24 cols
# the buffer is cols*rows*2 bytes per window:
#     rows=6 -> 288 B/win -> 576 B total  (NO proven region is that large)
#     rows=5 -> 240 B/win -> 480 B total  (fits 0x800F3ECC, 520 B, execution-proven)
# 0x800F3ECC is the only region in the Appendix B usable set big enough, and
# it is the one region that has already run injected code successfully.
# ============================================================================

CHARBUF_DEFAULT = 0x80178000          # BSS: see 15.4b. The char buffer is
                                      # runtime scratch, NOT file data -- it does
                                      # not belong in the scarce in-image space.
COLS_NEW = 24
ROWS_NEW = 6
CELLW_NEW = 8
CELLH_KEEP = 16


def _enc_lui(rt, imm):
    return (0x0F << 26) | (rt << 16) | (imm & 0xFFFF)


def _enc_addiu(rt, rs, imm):
    return (0x09 << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)


def _enc_sll(rd, rt, sa):
    return (rt << 16) | (rd << 11) | ((sa & 31) << 6)


def _enc_subu(rd, rs, rt):
    return (rs << 21) | (rt << 16) | (rd << 11) | 0x23


def _dec(w):
    return (w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31,
            (w >> 6) & 31, w & 0x3F, w & 0xFFFF)


# --- word patches that are independent of the buffer address -----------------
# (address, expected_original, new, description)
def geometry_patches(cols=COLS_NEW, rows=ROWS_NEW, cellw=CELLW_NEW):
    cells = cols * rows
    if cells > 0xFFFF:
        raise SystemExit('cell count out of range')
    ori = lambda rt, imm: (0x0D << 26) | (rt << 16) | (imm & 0xFFFF)
    sltiu = lambda rt, rs, imm: (0x0B << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
    addiu = lambda rt, rs, imm: (0x09 << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
    V0, V1, A2, A3 = 2, 3, 6, 7
    p = [
        # --- (a) sprite width + pen advance -----------------------------------
        (0x8001C384, 0x34030010, ori(V1, cellw),
         'desc[0] cell width %d -> %d px (sprite width AND pen advance)' % (16, cellw)),
        (0x8001C398, 0x00000000, ori(V1, CELLH_KEEP),
         'desc[1] cell height stays 16 px: re-set $v1 in the lhu load-delay slot'),
        # --- (b) column count --------------------------------------------------
        (0x8001C3B8, 0x3402000C, ori(V0, cols),      'desc[2] columns 12 -> %d' % cols),
        (0x8001C3C8, 0x34020006, ori(V0, rows),      'desc[4] rows 6 -> %d' % rows),
        (0x8001BAE4, 0x3406000C, ori(A2, cols),      'window 0 setup: columns 12 -> %d' % cols),
        (0x8001BB00, 0x3406000C, ori(A2, cols),      'window 1 setup: columns 12 -> %d' % cols),
        (0x8001C250, 0x00021100, _enc_sll(V0, V0, 3),
         'cols->pixels: <<4 -> <<3, so %d x %d = %d px (unchanged)' % (cols, cellw, cols * cellw)),
        # --- cell-count limits (cols*rows) -------------------------------------
        (0x8001B8DC, 0x2C420048, sltiu(V0, V0, cells), 'cell counter wrap 72 -> %d' % cells),
        (0x8001BEFC, 0x2C420048, sltiu(V0, V0, cells), 'clear loop bound 72 -> %d' % cells),
        (0x8001BFAC, 0x2C420048, sltiu(V0, V0, cells), 'clear loop bound 72 -> %d' % cells),
        (0x8001C1EC, 0x2C420048, sltiu(V0, V0, cells), 'clear loop bound 72 -> %d' % cells),
        # --- modulo-12 -> modulo-24 (THREE sites; magic 0xAAAAAAAB is unchanged)
        (0x800198B8, 0x000318C2, (V1 << 16) | (V1 << 11) | (4 << 6) | 2,
         'mod site 1: srl 3 -> 4  (/12 -> /24)'),
        (0x800198C4, 0x00021080, _enc_sll(V0, V0, 3),
         'mod site 1: sll 2 -> 3  (*12 -> *24)'),
        (0x800199F0, 0x000318C2, (V1 << 16) | (V1 << 11) | (4 << 6) | 2,
         'mod site 2: srl 3 -> 4'),
        (0x800199FC, 0x00021080, _enc_sll(V0, V0, 3),
         'mod site 2: sll 2 -> 3'),
        (0x8001B81C, 0x000318C2, (V1 << 16) | (V1 << 11) | (4 << 6) | 2,
         'mod site 3: srl 3 -> 4'),
        (0x8001B828, 0x00021080, _enc_sll(V0, V0, 3),
         'mod site 3: sll 2 -> 3'),
        # --- row span ----------------------------------------------------------
        (0x80018F44, 0x2442000C, addiu(V0, V0, cols), 'line-clear span 12 -> %d' % cols),
        (0x80018FA8, 0x2442000C, addiu(V0, V0, cols), 'line-clear span 12 -> %d' % cols),
        (0x80019A18, 0x2442000C, addiu(V0, V0, cols), 'next-row advance 12 -> %d' % cols),
        (0x8001B848, 0x24E2000D, addiu(V0, A3, cols + 1),
         'wrap round-up 13 -> %d' % (cols + 1)),
        # --- VRAM glyph cache --------------------------------------------------
        (0x8001B908, 0x2C420031, sltiu(V0, V0, cols * 4 + 1),
         'VRAM cache slot limit 48 -> %d (24 cols x 4 visible rows)' % (cols * 4)),
    ]
    return p


# --- char buffer: base + stride ---------------------------------------------
# Six genuine base+stride computations. Each is
#     lui  rB, 0x8013 ; addiu rB, rB, 0x230      (base 0x80130230)
#     sll  rS, rW, 3  ; addu  rS, rS, rW ; sll rS, rS, 4      (rW * 144)
# New stride cols*rows*2; for 24x5 that is 240 = ((w<<4) - w) << 4, so the
# shift becomes 4 and the addu becomes subu. Same registers, same slots.
CHARBUF_SITES = [
    # (lui, addiu, final_shift)
    #
    # ** 2026-07-31: DO NOT touch the `sll rX,win,3 / addu rX,rX,win` pair. **
    # The compiler shares that `win*9` subexpression. At site 6 it feeds BOTH
    # the char-buffer offset (<<4 -> 144) AND the window-record index
    # (<<2 -> 36, at 0x8001C418). Rewriting it to win*15 made the record index
    # win*60, so `sw $zero,0xef0($at)` at 0x8001C424 landed on 0x80160EF0+60 =
    # 0x80160F2C -- window 1's half_w/half_h -- zeroing both with one word and
    # shifting the dialogue box 96 px right / 32 px down. Confirmed on hardware
    # via a write breakpoint: 96 before 0x8001C424, 0 after.
    #
    # So: change ONLY the final shift. stride = (win*9) << k, i.e. 9*2^k, which
    # locks cols*rows to 72 (k=4) or 144 (k=5). With 24 columns that means
    # rows = 3 or 6; 3 is below the visible+1 floor, so rows = 6 -- which is
    # also what stock ships (visible+2 slack). k=5 -> stride 288.
    (0x80018F58, 0x80018F5C, 0x80018F68),
    (0x8001BEC8, 0x8001BECC, 0x8001BED8),
    (0x8001BF78, 0x8001BF7C, 0x8001BF88),
    (0x8001C06C, 0x8001C070, 0x8001C07C),
    (0x8001C1B8, 0x8001C1BC, 0x8001C1C8),
    (0x8001C400, 0x8001C404, 0x8001C3FC),   # <- the shared-subexpression site
]


def charbuf_patches(data, t_addr, newbase, cols=COLS_NEW, rows=ROWS_NEW):
    """Base + stride for the tilemap/char buffer. Stride must be 9*2^k."""
    stride = cols * rows * 2
    k = None
    for cand in range(0, 12):
        if 9 << cand == stride:
            k = cand
    if k is None:
        raise SystemExit(
            'stride %d (= %d cols x %d rows x 2) is not 9*2^k.\n'
            'The window-record index at 0x8001C418 shares the win*9 term, so\n'
            'only strides of 144 (k=4) or 288 (k=5) are reachable. With %d\n'
            'columns that means rows must be %s.'
            % (stride, cols, rows, cols,
               ' or '.join(str(s // (cols * 2)) for s in (144, 288)
                           if s % (cols * 2) == 0) or '(none)'))
    hi = ((newbase + 0x8000) >> 16) & 0xFFFF
    lo = newbase & 0xFFFF
    out = []
    for lui_a, addiu_a, shift_a in CHARBUF_SITES:
        wl = struct.unpack_from('<I', data, psx_to_file(lui_a, t_addr))[0]
        wa = struct.unpack_from('<I', data, psx_to_file(addiu_a, t_addr))[0]
        ws = struct.unpack_from('<I', data, psx_to_file(shift_a, t_addr))[0]
        op, rs, rt, rd, sa, fn, imm = _dec(wl)
        if op != 0x0F or imm not in (0x8013, hi):
            raise SystemExit('0x%08X is not `lui r,0x8013`/`lui r,0x%04X` (found %08X)'
                             % (lui_a, hi, wl))
        rB = rt
        op2, rs2, rt2, _, _, _, imm2 = _dec(wa)
        if op2 != 0x09 or rs2 != rB or rt2 != rB or imm2 not in (0x230, lo):
            raise SystemExit('0x%08X is not `addiu r,r,0x230`/`addiu r,r,0x%04X` (found %08X)'
                             % (addiu_a, lo, wa))
        op3, _, rtS, rdS, saS, fnS, _ = _dec(ws)
        if op3 != 0 or fnS != 0 or saS not in (4, k):
            raise SystemExit('0x%08X is not `sll r,r,4` (found %08X)' % (shift_a, ws))
        out.append((lui_a, _enc_lui(rB, 0x8013), _enc_lui(rB, hi),
                    'char buffer base hi -> 0x%04X' % hi))
        out.append((addiu_a, _enc_addiu(rB, rB, 0x230), _enc_addiu(rB, rB, lo),
                    'char buffer base lo -> 0x%04X' % lo))
        out.append((shift_a, _enc_sll(rdS, rtS, 4), _enc_sll(rdS, rtS, k),
                    'stride: sll 4 -> %d  (win*%d); win*9 term LEFT INTACT' % (k, stride)))
    return out


# ============================================================================
# R3000 simulator -- enforces the load delay slot (findings.md 14.8 bug 1)
# ============================================================================

class Hazard(Exception):
    pass


class R3000:
    """Minimal R3000A interpreter. The register written by a load is NOT
    visible to the immediately following instruction; reading it there is
    recorded as a load-delay hazard rather than silently returning the new
    value (which is what the naive simulator did in the 2026-07-30 bug)."""

    LOADS = {0x20, 0x21, 0x23, 0x24, 0x25}          # lb lh lw lbu lhu
    UNALIGNED = {0x22, 0x26, 0x2A, 0x2E}             # lwl lwr swl swr

    def __init__(self, data, t_addr, t_size):
        self.data = data
        self.t_addr = t_addr
        self.t_size = t_size
        self.mem = {}
        self.reset()

    def reset(self):
        self.r = [0] * 32
        self.hi = self.lo = 0
        self.pending = None
        self.hazards = []
        self.writes = []
        self.intercept = set()     # jal targets to record and skip
        self.calls = []            # (target, a0, a1, a2, a3)

    # ---- memory -----------------------------------------------------------
    def _rb(self, a):
        a &= 0xFFFFFFFF
        if a in self.mem:
            return self.mem[a]
        off = a - self.t_addr + HDR
        if HDR <= off < HDR + self.t_size and off < len(self.data):
            return self.data[off]
        return 0

    def rw(self, a):
        return (self._rb(a) | (self._rb(a + 1) << 8) |
                (self._rb(a + 2) << 16) | (self._rb(a + 3) << 24))

    def rh(self, a):
        return self._rb(a) | (self._rb(a + 1) << 8)

    def wb(self, a, v):
        self.mem[a & 0xFFFFFFFF] = v & 0xFF

    def store(self, a, v, n):
        for i in range(n):
            self.wb(a + i, (v >> (8 * i)) & 0xFF)
        self.writes.append((a, v, n))

    # ---- decode helpers ---------------------------------------------------
    @staticmethod
    def _reads(w):
        op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
        if op == 0:
            fn = w & 0x3F
            if fn in (0x00, 0x02, 0x03):            # sll srl sra  -> rt only
                return {rt}
            if fn in (0x10, 0x12):                  # mfhi mflo
                return set()
            if fn == 0x08:                          # jr
                return {rs}
            return {rs, rt}
        if op in (0x0F,):                           # lui
            return set()
        if op in (0x02, 0x03):                      # j jal
            return set()
        if op in (0x04, 0x05):                      # beq bne
            return {rs, rt}
        if op in (0x01, 0x06, 0x07):                # bltz/bgez blez bgtz
            return {rs}
        if op in (0x28, 0x29, 0x2B):                # sb sh sw
            return {rs, rt}
        if op in (0x2A, 0x2E):                      # swl swr genuinely read rt
            return {rs, rt}
        # lwl/lwr (0x22/0x26) also touch rt, but an adjacent lwl+lwr pair to
        # the SAME register is the architecturally sanctioned idiom and is not
        # a load-delay hazard. Reporting it flagged pristine game code at
        # 0x800278BC, so they fall through to the {rs}-only default below.
        return {rs}

    def step(self, pc):
        w = self.rw(pc)
        op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
        rd, sa, fn = (w >> 11) & 31, (w >> 6) & 31, w & 0x3F
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        R = self.r

        if self.pending and self.pending[0] in self._reads(w) and self.pending[0] != 0:
            self.hazards.append((pc, w, self.pending[0]))

        nxt, target = pc + 4, None
        wreg = wval = None
        u = lambda x: x & 0xFFFFFFFF
        s = lambda x: x - 0x100000000 if x & 0x80000000 else x

        if op == 0:
            if fn == 0x00:   wreg, wval = rd, u(R[rt] << sa)
            elif fn == 0x02: wreg, wval = rd, u(R[rt] >> sa)
            elif fn == 0x03: wreg, wval = rd, u(s(R[rt]) >> sa)
            elif fn == 0x04: wreg, wval = rd, u(R[rt] << (R[rs] & 31))
            elif fn == 0x06: wreg, wval = rd, u(R[rt] >> (R[rs] & 31))
            elif fn == 0x08: target = R[rs]
            elif fn == 0x09: target, wreg, wval = R[rs], rd, pc + 8
            elif fn == 0x10: wreg, wval = rd, self.hi
            elif fn == 0x12: wreg, wval = rd, self.lo
            elif fn == 0x18:
                p = s(R[rs]) * s(R[rt]); self.lo, self.hi = u(p), u(p >> 32)
            elif fn == 0x19:
                p = R[rs] * R[rt]; self.lo, self.hi = u(p), u(p >> 32)
            elif fn == 0x1A:
                if R[rt]:
                    a, b = s(R[rs]), s(R[rt])
                    q = abs(a) // abs(b); q = -q if (a < 0) != (b < 0) else q
                    self.lo, self.hi = u(q), u(a - b * q)
            elif fn == 0x1B:
                if R[rt]: self.lo, self.hi = u(R[rs] // R[rt]), u(R[rs] % R[rt])
            elif fn in (0x20, 0x21): wreg, wval = rd, u(R[rs] + R[rt])
            elif fn in (0x22, 0x23): wreg, wval = rd, u(R[rs] - R[rt])
            elif fn == 0x24: wreg, wval = rd, R[rs] & R[rt]
            elif fn == 0x25: wreg, wval = rd, R[rs] | R[rt]
            elif fn == 0x26: wreg, wval = rd, R[rs] ^ R[rt]
            elif fn == 0x27: wreg, wval = rd, u(~(R[rs] | R[rt]))
            elif fn == 0x2A: wreg, wval = rd, int(s(R[rs]) < s(R[rt]))
            elif fn == 0x2B: wreg, wval = rd, int(R[rs] < R[rt])
            elif fn == 0x0D: pass                                   # break
            else: raise SystemExit('sim: SPECIAL fn 0x%02X @%08X' % (fn, pc))
        elif op == 0x01:
            take = (s(R[rs]) < 0) if rt == 0 else (s(R[rs]) >= 0)
            if take: target = pc + 4 + simm * 4
        elif op == 0x02: target = (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        elif op == 0x03:
            target = (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2); wreg, wval = 31, pc + 8
        elif op == 0x04:
            if R[rs] == R[rt]: target = pc + 4 + simm * 4
        elif op == 0x05:
            if R[rs] != R[rt]: target = pc + 4 + simm * 4
        elif op == 0x06:
            if s(R[rs]) <= 0: target = pc + 4 + simm * 4
        elif op == 0x07:
            if s(R[rs]) > 0: target = pc + 4 + simm * 4
        elif op in (0x08, 0x09): wreg, wval = rt, u(R[rs] + simm)
        elif op == 0x0A: wreg, wval = rt, int(s(R[rs]) < simm)
        elif op == 0x0B: wreg, wval = rt, int(R[rs] < u(simm))
        elif op == 0x0C: wreg, wval = rt, R[rs] & imm
        elif op == 0x0D: wreg, wval = rt, R[rs] | imm
        elif op == 0x0E: wreg, wval = rt, R[rs] ^ imm
        elif op == 0x0F: wreg, wval = rt, u(imm << 16)
        elif op in self.LOADS:
            a = u(R[rs] + simm)
            if op == 0x20:   v = self._rb(a); v = v - 256 if v & 0x80 else v
            elif op == 0x24: v = self._rb(a)
            elif op == 0x21: v = self.rh(a); v = v - 0x10000 if v & 0x8000 else v
            elif op == 0x25: v = self.rh(a)
            else:            v = self.rw(a)
            # commit the PREVIOUS load, then queue this one
            if self.pending:
                self.r[self.pending[0]] = self.pending[1]; self.pending = None
            self.pending = (rt, u(v))
            self.r[0] = 0
            return target if target is not None else nxt, target is not None
        elif op in self.UNALIGNED:
            # Byte-wise little-endian lwl/lwr/swl/swr. The SLPS string-block
            # copies use these in aligned pairs, but implementing the general
            # case costs nothing and removes a lurking wrong answer.
            a = u(R[rs] + simm)
            base_a, b = a & ~3, a & 3
            if op in (0x22, 0x26):                  # lwl / lwr
                if self.pending:
                    self.r[self.pending[0]] = self.pending[1]; self.pending = None
                cur = R[rt]
                by = [(cur >> (8 * i)) & 0xFF for i in range(4)]
                if op == 0x22:
                    for i in range(b + 1):
                        by[3 - b + i] = self._rb(base_a + i)
                else:
                    for i in range(b, 4):
                        by[i - b] = self._rb(base_a + i)
                self.pending = (rt, u(sum(by[i] << (8 * i) for i in range(4))))
                self.r[0] = 0
                return target if target is not None else nxt, target is not None
            by = [(R[rt] >> (8 * i)) & 0xFF for i in range(4)]
            if op == 0x2A:
                for i in range(b + 1):
                    self.wb(base_a + i, by[3 - b + i])
            else:
                for i in range(b, 4):
                    self.wb(base_a + i, by[i - b])
        elif op == 0x28: self.store(u(R[rs] + simm), R[rt], 1)
        elif op == 0x29: self.store(u(R[rs] + simm), R[rt], 2)
        elif op == 0x2B: self.store(u(R[rs] + simm), R[rt], 4)
        else: raise SystemExit('sim: op 0x%02X @%08X' % (op, pc))

        if self.pending:
            self.r[self.pending[0]] = self.pending[1]; self.pending = None
        if wreg is not None and wreg != 0:
            self.r[wreg] = u(wval)
        self.r[0] = 0
        return (target if target is not None else nxt), (target is not None)

    def run(self, start, stop, max_steps=20000):
        stops = stop if isinstance(stop, (set, frozenset, tuple, list)) else {stop}
        pc, steps = start, 0
        while pc not in stops and steps < max_steps:
            w = self.rw(pc)
            hooked = None
            if (w >> 26) == 3 and self.intercept:      # jal
                tgt = (pc & 0xF0000000) | ((w & 0x03FFFFFF) << 2)
                if tgt in self.intercept:
                    hooked = tgt
            nxt, branched = self.step(pc)
            if branched:
                self.step(pc + 4)          # delay slot
                if hooked is not None:
                    # The delay slot runs BEFORE the callee, so it is part of
                    # the argument setup (this game puts 'addiu $a3,$a3,48'
                    # there). Record args only after it has executed.
                    self.calls.append((hooked, self.r[4], self.r[5],
                                       self.r[6], self.r[7]))
                    pc = pc + 8
                else:
                    pc = nxt
            else:
                pc = nxt
            steps += 1
        if steps >= max_steps:
            raise SystemExit('sim: step limit at %08X' % pc)
        return steps


def _apply_set(data, t_addr, patches, revert=False, label='patch'):
    """Atomic: verify EVERY original opcode first, then write. Nothing is
    written unless the whole set verifies."""
    plan, already = [], 0
    for psx, orig, new, why in patches:
        a, b = (new, orig) if revert else (orig, new)
        off = psx_to_file(psx, t_addr)
        cur = struct.unpack_from('<I', data, off)[0]
        if cur == b:
            already += 1
            continue
        if cur != a:
            raise SystemExit(
                'ABORT: 0x%08X holds %08X, expected %08X (%s).\n'
                'Nothing has been written. This EXE is not the build these\n'
                'offsets were derived from, or a conflicting patch is applied.'
                % (psx, cur, a, why))
        plan.append((off, psx, a, b, why))
    for off, psx, a, b, why in plan:
        struct.pack_into('<I', data, off, b)
    return plan, already


def cmd_renderer(path, out_path, revert=False, cols=COLS_NEW, rows=ROWS_NEW,
                 cellw=CELLW_NEW, charbuf=CHARBUF_DEFAULT, dry=False):
    data, t_addr, t_size, _ = load_exe(path)
    n0 = len(data)
    patches = geometry_patches(cols, rows, cellw) + \
              charbuf_patches(data, t_addr, charbuf, cols, rows)

    # buffer must fit a region the three-filter method calls usable
    need = cols * rows * 2 * 2
    in_image = t_addr <= charbuf < t_addr + t_size
    extent = run_extent(data, t_addr, charbuf) if (in_image and not revert) else need
    if in_image and not revert and extent < need:
        raise SystemExit('ABORT: char buffer needs %d bytes at 0x%08X but the '
                         'zero run there is only %d.' % (need, charbuf, extent))
    print('%s: %d columns x %d rows, %dx%d px cells, box %d x %d px'
          % ('REVERT' if revert else 'renderer', cols, rows, cellw, CELLH_KEEP,
             cols * cellw, 4 * CELLH_KEEP))
    print('  char buffer 0x%08X, %d B/window, %d B total (run has %d B)'
          % (charbuf, cols * rows * 2, need, extent))
    if not in_image:
        print('  (BSS placement: verified unreferenced by code and zero across '
              'all available savestates)')
    plan, already = _apply_set(data, t_addr, patches, revert)
    for off, psx, a, b, why in plan:
        print('  0x%08X  %08X -> %08X  %s' % (psx, a, b, why))
    if already:
        print('  (%d word(s) already at the target value)' % already)
    if dry:
        print('DRY RUN: nothing written.')
        return
    if len(data) != n0:
        raise SystemExit('internal: size changed')
    open(out_path, 'wb').write(bytes(data))
    print('%d word(s) changed; size preserved (%d bytes).' % (len(plan), len(data)))


def _sim(path, cols, rows, cellw, charbuf):
    data, t_addr, t_size, _ = load_exe(path)
    GP = 0x80180000
    out = {}
    for win in (0, 1):
        m = R3000(data, t_addr, t_size)
        m.r[28] = GP
        m.store(GP + 0xAE8, win, 2)
        m.writes.clear()
        m.run(0x8001C378, 0x8001C444)
        d = 0x8011B21C + win * 16
        out['desc%d' % win] = dict(
            cellw=m._rb(d), cellh=m._rb(d + 1), cols=m.rh(d + 2), rows=m.rh(d + 4),
            uv=m.rw(d + 8), charbuf=m.rw(d + 12))
        out['hz%d' % win] = list(m.hazards)
    # window-open: cols/rows -> pixel geometry in the 0x80160EF0 record
    m = R3000(data, t_addr, t_size)
    m.r[28] = GP
    m.store(GP + 0xAE8, 0, 2)
    m.store(0x80115804, cols, 2)
    m.store(0x80115788, 4, 2)
    m.store(0x8011625C, 0x10, 2)
    m.store(0x80116264, 0x18, 2)
    m.writes.clear()
    m.run(0x8001C1F8, 0x8001C370)
    out['rec'] = dict(px_w=m.rh(0x80160EF8), px_h=m.rh(0x80160EFA),
                      half_w=m.rh(0x80160F08), half_h=m.rh(0x80160F0A),
                      x=m.rh(0x80160EF4), y=m.rh(0x80160EF6))
    out['hzrec'] = list(m.hazards)
    return out


def cmd_simcheck(path, cols=COLS_NEW, rows=ROWS_NEW, cellw=CELLW_NEW,
                 charbuf=CHARBUF_DEFAULT):
    r = _sim(path, cols, rows, cellw, charbuf)
    ok = True
    print('R3000 simulation (load-delay slot enforced)')
    for win in (0, 1):
        d = r['desc%d' % win]
        want = dict(cellw=cellw, cellh=CELLH_KEEP, cols=cols, rows=rows,
                    uv=0x80190040 + win * 0x800,
                    charbuf=charbuf + win * cols * rows * 2)
        print('  descriptor win%d @0x%08X' % (win, 0x8011B21C + win * 16))
        for k in ('cellw', 'cellh', 'cols', 'rows', 'uv', 'charbuf'):
            good = d[k] == want[k]
            ok &= good
            print('    %-8s %-10s expected %-10s %s'
                  % (k, hex(d[k]), hex(want[k]), 'OK' if good else '** MISMATCH **'))
        for pc, w, reg in r['hz%d' % win]:
            ok = False
            print('    ** LOAD DELAY HAZARD @0x%08X (%08X) reads r%d **' % (pc, w, reg))
    rec = r['rec']
    print('  window record @0x80160EF0')
    wantrec = dict(px_w=cols * cellw, px_h=4 * CELLH_KEEP,
                   half_w=cols * cellw // 2, half_h=32,
                   x=(cols * cellw // 2 - 0xA0 + 0x10) & 0xFFFF,
                   y=(32 - 0x78 + 0x18) & 0xFFFF)
    for k in ('px_w', 'px_h', 'half_w', 'half_h', 'x', 'y'):
        good = rec[k] == wantrec[k]
        ok &= good
        print('    %-8s %-10s expected %-10s %s'
              % (k, hex(rec[k]), hex(wantrec[k]), 'OK' if good else '** MISMATCH **'))
    for pc, w, reg in r['hzrec']:
        ok = False
        print('    ** LOAD DELAY HAZARD @0x%08X (%08X) reads r%d **' % (pc, w, reg))
    # --- regression: the shared win*9 term at 0x8001C418 --------------------
    # Rewriting `sll/addu` at 0x8001C3F4/F8 also rescales the WINDOW RECORD
    # index, sending `sw $zero,0xef0($at)` onto record[1]+0x18 (half_w/half_h).
    # Caught on hardware 2026-07-31; this check exists so it never returns.
    data, t_addr, t_size, _ = load_exe(path)
    for win in (0, 1):
        m = R3000(data, t_addr, t_size)
        m.r[28] = 0x80180000
        m.store(0x80180000 + 0xAE8, win, 2)
        m.store(0x80160EF0 + win * 36 + 0x18, 96, 2)
        m.store(0x80160EF0 + win * 36 + 0x1A, 32, 2)
        m.writes.clear()
        m.run(0x8001C378, 0x8001C460)
        hw = m.rh(0x80160EF0 + win * 36 + 0x18)
        hh = m.rh(0x80160EF0 + win * 36 + 0x1A)
        hit = any(a == 0x80160EF0 + win * 36 for a, v, n in m.writes)
        good = (hw, hh) == (96, 32) and hit
        ok &= good
        print('  record index win%d: half_w/half_h survive descriptor build = %d/%d, '
              'record[%d]+0 written = %s  %s'
              % (win, hw, hh, win, hit, 'OK' if good else '** CLOBBERED **'))
    print('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1




def _sav_blob(path):
    """Robust: locate the RAM zstd stream by magic rather than fixed offset
    (DuckStation moves it between versions -- 0x116 and 0x10C both seen)."""
    import zstandard, io
    d = open(path, 'rb').read()
    i = 0
    while True:
        j = d.find(b'\x28\xb5\x2f\xfd', i)
        if j < 0:
            raise SystemExit('no zstd stream in %s' % path)
        try:
            b = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(d[j:])).read()
        except Exception:
            i = j + 4
            continue
        k = b.find(b'\\TACTICS\\')
        if k >= 0:
            return b, k - 0x800F40D4 + 0x80000000
        i = j + 4


def cmd_windiag(exe_path, sav_path):
    """Diff the LIVE dialogue-window state in a savestate against what the
    EXE's own code should produce. Localises a layout fault to one field."""
    blob, base = _sav_blob(sav_path)
    data, t_addr, t_size, _ = load_exe(exe_path)

    def rb(p):
        return blob[base + (p - 0x80000000)]

    def rh(p):
        o = base + (p - 0x80000000)
        return blob[o] | (blob[o + 1] << 8)

    def rw(p):
        o = base + (p - 0x80000000)
        return struct.unpack_from('<I', blob, o)[0]

    def sh(p):
        v = rh(p)
        return v - 0x10000 if v & 0x8000 else v

    gx, gy = sh(0x80191408), sh(0x8019140C)
    print('savestate RAM base 0x%X   global centre (%d,%d)' % (base, gx, gy))
    bad = []
    for win in (0, 1):
        d = 0x8011B21C + win * 16
        r = 0x80160EF0 + win * 36
        cellw, cellh = rb(d), rb(d + 1)
        cols, rows = rh(d + 2), rh(d + 4)
        px_w, px_h = rh(r + 8), rh(r + 0x0A)
        hw, hh = sh(r + 0x18), sh(r + 0x1A)
        x, y = sh(r + 4), sh(r + 6)
        print('--- window %d ---' % win)
        print('  descriptor : cell %dx%d  grid %dx%d  uv 0x%08X  map 0x%08X'
              % (cellw, cellh, cols, rows, rw(d + 8), rw(d + 12)))
        print('  record     : px %dx%d  half %d/%d  pos (%d,%d)  scroll (%d,%d)'
              % (px_w, px_h, hw, hh, x, y, sh(r + 0x0C), sh(r + 0x0E)))
        print('  counters   : cell %d  cache %d  line %d  linewidth %d  rows %d'
              % (rh(0x801162FC + win * 2), rh(0x801162E0 + win * 2),
                 rh(0x80116244 + win * 2), rh(0x80115ABC + win * 2),
                 rh(0x80115A34 + win * 2)))
        print('  SCREEN     : (%d,%d)  size %dx%d' % (x - hw + gx, y - hh + gy,
                                                      cols * cellw, rh(0x80115A34 + win * 2) * cellh))
        if px_w and hw * 2 != px_w:
            bad.append('window %d: half_w=%d but px_w=%d (expected %d) -> window drawn '
                       '%d px too far RIGHT' % (win, hw, px_w, px_w // 2, px_w // 2 - hw))
        if px_h and hh * 2 != px_h:
            bad.append('window %d: half_h=%d but px_h=%d (expected %d) -> window drawn '
                       '%d px too far DOWN' % (win, hh, px_h, px_h // 2, px_h // 2 - hh))
        if cols and cellw:
            cb = rw(d + 12)
            n = cols * rows
            cells = [rh(cb + i * 2) for i in range(n)]
            used = [i for i, c in enumerate(cells) if c != 0xC9]
            if used:
                print('  tilemap    : %d non-blank cells, rows touched %s'
                      % (len(used), sorted({i // cols for i in used})))
                for rw_ in sorted({i // cols for i in used}):
                    run = [c for i, c in enumerate(cells) if i // cols == rw_ and c != 0xC9]
                    print('      row %d: %d chars, slots %s'
                          % (rw_, len(run), '%X..%X' % (run[0], run[-1]) if run else '-'))
    print()
    if bad:
        print('FAULTS:')
        for b in bad:
            print('  ** %s' % b)
    else:
        print('geometry self-consistent (half == px/2 for every open window)')
    return 1 if bad else 0




# ---------------------------------------------------------------------------
# rewrap: re-flow script line breaks for a wider box
#
# {FFFE} is a HARD line break. The engine has no word wrap: the check at
# 0x8001B844 compares pos%stride against the active line width, and when both
# are the grid width that path is unreachable. So every break is authored.
# Widening 12 -> 24 columns therefore does NOT reflow existing text.
#
# Blind re-flow would destroy intent ("Search!" is deliberately its own line).
# So this only merges a line into the previous one when the previous line does
# NOT end in terminal punctuation -- i.e. it was split mid-sentence to fit the
# old box -- and the result still fits.
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r'\{[^}]*\}')
_TERM = '。．！？…!?.:;、，,'


def _half(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF01 <= o <= 0xFF5E:
            out.append(chr(o - 0xFEE0))
        elif o == 0x3000:
            out.append(' ')
        else:
            out.append(ch)
    return ''.join(out)


def _is_latin(s):
    t = _half(s).strip()
    if not t:
        return True
    lat = sum(1 for c in t if c.isascii())
    return lat >= max(1, int(len(t) * 0.9))


def _tokenise(line):
    out, i = [], 0
    for m in _TOKEN.finditer(line):
        if m.start() > i:
            out.append(('t', line[i:m.start()]))
        out.append(('c', m.group()))
        i = m.end()
    if i < len(line):
        out.append(('t', line[i:]))
    return out


def _reflow(lines, cols):
    """Merge continuation lines; then hard-wrap anything still too long."""
    merged = []
    for ln in lines:
        if merged:
            prev = merged[-1]
            ph = _half(prev).rstrip()
            if ph and ph[-1] not in _TERM and ln.strip():
                cand = prev + '\u3000' + ln
                if len(cand) <= cols:
                    merged[-1] = cand
                    continue
        merged.append(ln)
    out = []
    for ln in merged:
        while len(ln) > cols:
            cut = ln.rfind('\u3000', 0, cols + 1)
            if cut <= 0:
                cut = cols
                out.append(ln[:cut]); ln = ln[cut:]
            else:
                out.append(ln[:cut]); ln = ln[cut + 1:]
        out.append(ln)
    return out


def cmd_rewrap(args):
    """rewrap INFILE OUTFILE [--cols 24] [--rows 4] [--all]"""
    import io
    if len(args) < 2:
        raise SystemExit('usage: rewrap INFILE OUTFILE [--cols 24] [--rows 4] [--all]')
    inf, outf = args[0], args[1]
    cols, rows, do_all = 24, 4, '--all' in args
    for i, a in enumerate(args):
        if a == '--cols':
            cols = int(args[i + 1])
        if a == '--rows':
            rows = int(args[i + 1])
    src = io.open(inf, encoding='utf-8').read().split('\n')
    out_lines, changed, skipped, overflow = [], 0, 0, []
    for lineno, line in enumerate(src, 1):
        toks = _tokenise(line)
        res, group, page, dirty = [], [], 0, False
        def flush():
            nonlocal group, dirty
            if not group:
                return
            lines = []
            cur = ''
            for kind, v in group:
                if kind == 'c':
                    lines.append(cur); cur = ''
                else:
                    cur += v
            lines.append(cur)
            if do_all or all(_is_latin(x) for x in lines):
                new = _reflow(lines, cols)
                if new != lines:
                    dirty = True
                lines = new
            for j, x in enumerate(lines):
                if j:
                    res.append('{FFFE}')
                res.append(x)
            group = []
        for kind, v in toks:
            if kind == 't' or v == '{FFFE}':
                group.append((kind, v))
            else:
                flush()
                res.append(v)
        flush()
        new_line = ''.join(res)
        if new_line != line:
            changed += 1
        else:
            skipped += 1
        # warn if any page now exceeds the visible rows
        for chunk in new_line.split('{FCC0}'):
            n = chunk.count('{FFFE}') + 1
            if n > rows:
                overflow.append((lineno, n))
        out_lines.append(new_line)
    io.open(outf, 'w', encoding='utf-8').write('\n'.join(out_lines))
    print('rewrap -> %s  (%d columns, %d visible rows)' % (outf, cols, rows))
    print('  %d line(s) changed, %d unchanged' % (changed, skipped))
    if overflow:
        print('  WARNING: %d message(s) exceed %d visible rows (first 5): %s'
              % (len(overflow), rows, ', '.join('line %d=%d rows' % o for o in overflow[:5])))
        print('           insert a {FCC0} page break in those.')




# =====================================================================
# ===  SESSION 3 (2026-07-31): SLPS_008.29 menus + name entry       ===
# ===  findings.md §19-§22                                          ===
# =====================================================================
#
# The BOOT executable SLPS_008.29 is resident on both the new-game menu
# and the name-entry screen (both supplied savestates calibrate against
# it 29/29; MAIN1 gets 3/26). Their text goes through the SAME BIOS
# Krom2RawAdd path as the battle dialogue, so this is a hook PORT.

SLPS_GP = 0x8007C998          # from the entry-point prologue at pc0
SLPS_SP = 0x801FFF00          # any sane stack; the routines only use locals

SLPS = dict(
    stub          = 0x8002CD08,   # BIOS B(51h) Krom2RawAdd dispatch stub
    expander      = 0x8001E994,   # expand(sjis, colour, vram_x, vram_y)
    expander_jal  = 0x8001E9F0,   # the single jal into the stub
    li_width      = 0x8001EAF8,   # ori $v0,$zero,4 -> LoadImage rect width
    grid_draw     = 0x80027890,   # renders both kana banks into the VRAM atlas
    grid_end      = 0x80027A2C,
    grid_kana     = 0x80061E6C,   # 2 banks x 60 u16 SJIS codes
    grid_attr     = 0x80061F5C,   # 2 banks x 60 s16 cell attributes
    grid_colx     = 0x80010304,   # 10 x s16 on-screen column X
    grid_rowy     = 0x80010318,   # 6  x s16 on-screen row Y
    name_slotx    = 0x800102F4,   # 8  x s16 on-screen name slot X
    commit        = 0x8002637C,   # insert the selected character
    dakuten       = 0x80026504,   # dakuten + handakuten, contiguous...
    handakuten    = 0x800268A4,
    dead_end      = 0x80026A00,   # ...to here: 1276 reclaimable bytes
    cursor_move   = 0x80026A00,   # a0 = 0 up / 1 down / 2 left / 3 right
    name_buf      = 0x800F16CE,   # 8 x u16, slot 7 = 0xFFFE sentinel
    name_len      = 0x8007CC94,   # gp+0x2FC
    cur_bank      = 0x8007CBC0,   # gp+0x228
    cur_col       = 0x8007CCA4,   # gp+0x30C
    cur_row       = 0x8007CCAC,   # gp+0x314
    pad           = 0x8007CD10,   # gp+0x378
    menu_str      = 0x800103C8,   # 4 entries x 12 full-width chars
    menu_draw     = 0x80027B80,
    prompt_str    = 0x8001038C,   # 2 lines x 15 full-width chars
    prompt_draw   = 0x800271D8,
)

GRID_COLS, GRID_ROWS, GRID_BANKS = 10, 6, 2
GRID_CELLS = GRID_COLS * GRID_ROWS


def _rdw(data, t_addr, psx):
    return struct.unpack_from('<I', data, psx_to_file(psx, t_addr))[0]


def _wrw(data, t_addr, psx, val):
    struct.pack_into('<I', data, psx_to_file(psx, t_addr), val & 0xFFFFFFFF)


def _rdh(data, t_addr, psx):
    return struct.unpack_from('<H', data, psx_to_file(psx, t_addr))[0]


def _wrh(data, t_addr, psx, val):
    struct.pack_into('<H', data, psx_to_file(psx, t_addr), val & 0xFFFF)


def sjis_ch(code):
    if code == 0:
        return '.'
    try:
        return bytes(((code >> 8) & 0xFF, code & 0xFF)).decode('shift_jis')
    except Exception:
        return '?'


def to_fw_code(ch):
    """ASCII -> full-width SJIS code (the codes the BIOS kanji ROM renders,
    and the same set the KOUSEI hook maps in §14.1)."""
    if ch == ' ':
        return 0x8140
    o = ord(ch)
    if 'A' <= ch <= 'Z':
        return 0x8260 + (o - 65)
    if 'a' <= ch <= 'z':
        return 0x8281 + (o - 97)
    if '0' <= ch <= '9':
        return 0x824F + (o - 48)
    table = {'-': 0x817C, '.': 0x8144, ',': 0x8143, ':': 0x8146, "'": 0x8166,
             '!': 0x8149, '?': 0x8148, '(': 0x8169, ')': 0x816A, '/': 0x815E,
             '&': 0x8195, '*': 0x8196, '+': 0x817B, '=': 0x8181}
    if ch in table:
        return table[ch]
    raise SystemExit('no full-width SJIS mapping for %r' % ch)


# ---------------------------------------------------------------------
# The Latin grid  (§20)
# ---------------------------------------------------------------------
# 10 cols x 6 rows x 2 banks. Both banks carry identical content, so every
# navigation edge case behaves exactly as stock (the bank switch just
# redraws the same layout).
#
#   rows 0-4 : A-Z then a-x          (50 cells)
#   row  5   : y z _ - ' . , _ _ *   (* = End, at col 9)
#
# Row 5 cols 6 and 7 are the stock dakuten / handakuten cells, hardcoded by
# (row==5 && col==6/7) in the commit routine; the guard patches below make
# them ordinary insertable cells.

def latin_grid():
    codes = [0x8260 + i for i in range(26)]        # A-Z
    codes += [0x8281 + i for i in range(24)]       # a-x
    codes += [0x8281 + 24, 0x8281 + 25]            # y z
    codes += [0x8140, 0x817C, 0x8166, 0x8144, 0x8143, 0x8140, 0x8140, 0x8196]
    assert len(codes) == GRID_CELLS, len(codes)
    # 0 = usable anywhere, 1 = not valid as the FIRST character,
    # 2 = the End command, -1 = dead cell. No -1 here, so the -1
    # navigation paths simply never trigger.
    attrs = [0] * 52 + [1] * 7 + [2]
    assert len(attrs) == GRID_CELLS, len(attrs)
    return codes, attrs


GRID_GUARDS = [
    (0x80026410, 0x34020005, 0x34027FFF, 'commit: dakuten row test 5 -> 0x7FFF'),
    (0x80026438, 0x34020005, 0x34027FFF, 'commit: handakuten row test 5 -> 0x7FFF'),
    (0x80026B7C, 0x34020007, 0x34020008, 'cursor LEFT from End: col 7 -> 8'),
    # with the guards in place these two jal sites are unreachable; nop them
    # so nothing can enter 0x80026504-0x80026A00 (1276 bytes, now reclaimable)
    (0x8002641C, 0x0C009941, 0x00000000, 'orphan jal dakuten -> nop'),
    (0x8002644C, 0x0C009A29, 0x00000000, 'orphan jal handakuten -> nop'),
]


def cmd_namegrid(path, out_path, revert=False, dry=False):
    data, t_addr, t_size, _ = load_exe(path)
    kana, attr = SLPS['grid_kana'], SLPS['grid_attr']
    if revert:
        raise SystemExit('namegrid rewrites data rather than applying a reversible '
                         'delta -- rebuild from a pristine EXE instead')
    cur = _rdh(data, t_addr, kana)
    if cur == 0x8260:
        print('already a Latin grid -- nothing to do (idempotent)')
        if not dry:
            open(out_path, 'wb').write(data)
        return
    if cur != 0x82A0:                       # あ
        raise SystemExit('unexpected grid data at 0x%08X: 0x%04X (expected 0x82A0)'
                         % (kana, cur))

    codes, attrs = latin_grid()
    plan, already = _apply_set(data, t_addr, GRID_GUARDS, revert=False,
                               label='grid guard')

    print('name-entry grid -> Latin')
    for _, psx, a, b, why in plan:
        print('  0x%08X  %08X -> %08X  %s' % (psx, a, b, why))
    if already:
        print('  %d guard word(s) already applied' % already)
    for bank in range(GRID_BANKS):
        for i in range(GRID_CELLS):
            if not dry:
                _wrh(data, t_addr, kana + (bank * GRID_CELLS + i) * 2, codes[i])
                _wrh(data, t_addr, attr + (bank * GRID_CELLS + i) * 2, attrs[i] & 0xFFFF)
    for r in range(GRID_ROWS):
        print('  row%d  %s' % (r, ''.join(sjis_ch(codes[r * GRID_COLS + c])
                                          for c in range(GRID_COLS))))
    if dry:
        print('(dry run, nothing written)')
        return
    open(out_path, 'wb').write(data)
    print('wrote %s (%d bytes, size preserved)' % (out_path, len(data)))


# ---------------------------------------------------------------------
# Menu strings  (§19.2)
# ---------------------------------------------------------------------
# 4 entries x 12 full-width chars. The draw loop at 0x80027B80 is hardcoded
# to 12 (slti 12) and 4 (slti 4) and blits one 192x64 sprite, so 12 is a
# hard cap until the half-width work lands.

MENU_EN = ['RESUME SAVE', 'CHAPTER SAVE', 'NEW GAME', 'TITLE SCREEN']
MENU_WIDTH = 12


def cmd_menutext(path, out_path, revert=False, dry=False, entries=None):
    data, t_addr, t_size, _ = load_exe(path)
    base = SLPS['menu_str']
    entries = entries or MENU_EN
    if revert:
        raise SystemExit('menutext rewrites data -- rebuild from a pristine EXE')
    cur = _rdh(data, t_addr, base)
    if cur != 0x9286 and cur != to_fw_code(entries[0][0]):     # 中
        raise SystemExit('unexpected menu data at 0x%08X: 0x%04X' % (base, cur))

    print('main menu -> English (%d entries x %d chars)' % (len(entries), MENU_WIDTH))
    for i, s in enumerate(entries):
        if len(s) > MENU_WIDTH:
            raise SystemExit('entry %d %r is %d chars, cap is %d'
                             % (i, s, len(s), MENU_WIDTH))
        for j, ch in enumerate(s.ljust(MENU_WIDTH)):
            if not dry:
                _wrh(data, t_addr, base + (i * MENU_WIDTH + j) * 2, to_fw_code(ch))
        print('  [%d] %s' % (i, s.ljust(MENU_WIDTH)))
    if dry:
        print('(dry run, nothing written)')
        return
    open(out_path, 'wb').write(data)
    print('wrote %s (%d bytes, size preserved)' % (out_path, len(data)))


# ---------------------------------------------------------------------
# Prompt / confirm strings  (§21)
# ---------------------------------------------------------------------
# 0x8001038C is ONE block of 2 lines x 15 full-width chars, uploaded to the
# atlas at (832,0)/(832,16). UI fragments are sub-rectangles of it:
#
#   line 0  chars  0..9   name prompt
#   line 0  chars 11..13  No button     (rec5, 48x16, u=176 v=0)
#   line 1  chars  0..11  question      (rec3, 192x16, u=0 v=16)
#   line 1  chars 12..13  Yes button    (rec4, 32x16, u=192 v=16)
#
# Fragments are addressed by CHARACTER SPAN, so English is safe as long as
# it occupies the same span and is space padded -- the exact rectangle
# widths never need to be known.

PROMPT_LINES, PROMPT_COLS = 2, 15
PROMPT_SPANS = [
    ('prompt',   0,  0, 10, 'YOUR NAME:'),
    ('no',       0, 11,  3, 'NO'),
    ('question', 1,  0, 12, 'IS THIS OK?'),
    ('yes',      1, 12,  2, 'OK'),
]
YES_WIDE = ('yes', 1, 12, 3, 'YES')

# rec4 width 32 -> 48 px so "YES" fits into the trailing spacer (a space in
# stock). $v0 feeds exactly one sh here.
# WARNING: rec4's X comes from 'addiu $v1,$zero,-32' at 0x8002745C, which is
# SHARED with rec3's Y -- the §16.2 trap in miniature. Do NOT re-centre it.
YES_WIDTH_PATCH = [(0x80027464, 0x34020020, 0x34020030, 'Yes button 32px -> 48px')]


def cmd_prompttext(path, out_path, dry=False, wide_yes=True, spans=None):
    data, t_addr, t_size, _ = load_exe(path)
    base = SLPS['prompt_str']
    spans = list(spans or PROMPT_SPANS)
    if wide_yes:
        spans = [s for s in spans if s[0] != 'yes'] + [YES_WIDE]

    cur = _rdh(data, t_addr, base)
    if cur not in (0x96BC, to_fw_code(spans[0][4][0])):        # 名
        raise SystemExit('unexpected prompt data at 0x%08X: 0x%04X' % (base, cur))
    if wide_yes:
        # verify against a copy first so --dry still catches a wrong build
        plan, already = _apply_set(data if not dry else bytearray(data), t_addr,
                                   YES_WIDTH_PATCH, revert=False, label='yes width')
        for _, psx, a, b, why in plan:
            print('  0x%08X  %08X -> %08X  %s' % (psx, a, b, why))
        if already:
            print('  yes-width patch already applied')

    grid = [[0x8140] * PROMPT_COLS for _ in range(PROMPT_LINES)]
    print('prompt / confirm strings -> English')
    for name, line, col, width, text in spans:
        if len(text) > width:
            raise SystemExit('%s: %r is %d chars, span is %d'
                             % (name, text, len(text), width))
        for i, ch in enumerate(text.ljust(width)):
            grid[line][col + i] = to_fw_code(ch)
        print('  %-9s line %d chars %2d..%-2d  %r'
              % (name, line, col, col + width - 1, text))
    if not dry:
        for l in range(PROMPT_LINES):
            for c in range(PROMPT_COLS):
                _wrh(data, t_addr, base + (l * PROMPT_COLS + c) * 2, grid[l][c])
    for l in range(PROMPT_LINES):
        print('  line%d "%s"' % (l, ''.join(sjis_ch(x) for x in grid[l])))
    if dry:
        print('(dry run, nothing written)')
        return
    open(out_path, 'wb').write(data)
    print('wrote %s (%d bytes, size preserved)' % (out_path, len(data)))


# ---------------------------------------------------------------------
# gridsim -- simulate the grid renderer, check against savestate VRAM
# ---------------------------------------------------------------------

def sav_vram(blob):
    i = blob.find(b'GPU-VRAM')
    if i < 0:
        raise SystemExit('no GPU-VRAM section in savestate')
    return blob[i + 8:i + 8 + 0x100000]


def cmd_gridsim(path, sav_paths):
    """Regression test for the name-entry grid renderer.

    Validated on the PRISTINE EXE before being trusted on a patched one
    (Appendix D #1): 120/120 cells agree with riotstars_nameentry.sav.
    """
    data, t_addr, t_size, _ = load_exe(path)
    cpu = R3000(data, t_addr, t_size)
    cpu.r[28], cpu.r[29] = SLPS_GP, SLPS_SP
    cpu.intercept = {SLPS['expander'], 0x8002F5D0}
    cpu.run(SLPS['grid_draw'], SLPS['grid_end'], max_steps=200000)
    cells = [c for c in cpu.calls if c[0] == SLPS['expander']]

    fails = []
    if len(cells) != GRID_CELLS * GRID_BANKS:
        fails.append('expected %d expander calls, got %d'
                     % (GRID_CELLS * GRID_BANKS, len(cells)))
    for h_pc, h_w, h_r in cpu.hazards:
        fails.append('load-delay hazard at 0x%08X ($%d)' % (h_pc, h_r))

    # geometry assertions: these encode the model, so a patch that moves the
    # grid fails here rather than on hardware
    for i, (_, sjis, colour, x, y) in enumerate(cells):
        bank, n = i % 2, i // 2
        row, col = n // GRID_COLS, n % GRID_COLS
        exp_x = 832 + col * 6 + (0 if col < 5 else 6)
        exp_y = (48 if bank == 0 else 256) + row * 24
        if (x, y) != (exp_x, exp_y):
            fails.append('bank%d r%d c%d: expected (%d,%d) got (%d,%d)'
                         % (bank, row, col, exp_x, exp_y, x, y))
        if colour != 1:
            fails.append('bank%d r%d c%d: colour %d != 1' % (bank, row, col, colour))

    print('%s: %d cells simulated, %d hazards' % (path, len(cells), len(cpu.hazards)))
    for sp in sav_paths:
        blob = load_savestate(sp)
        base, conf = calibrate(blob, data, t_addr, t_size)
        if base is None:
            print('  %s: not the resident EXE -- SKIPPED' % sp)
            continue

        # Appendix D #8: check WHICH BUILD the state came from before using its
        # VRAM as an oracle. The grid table is in the image, so compare it
        # against RAM; if they differ this state says nothing about this EXE.
        n = GRID_CELLS * GRID_BANKS * 2
        off = base + (SLPS['grid_kana'] - 0x80000000)
        here = bytes(data[psx_to_file(SLPS['grid_kana'], t_addr):][:n])
        if blob[off:off + n] != here:
            print('  %s: savestate is from a DIFFERENT BUILD (grid table differs)'
                  ' -- VRAM oracle skipped' % sp)
            continue

        vram = sav_vram(blob)

        def ink(x, y):
            t = 0
            for yy in range(y, y + 16):
                o = (yy * 1024 + x) * 2
                t += sum(1 for k in range(8) if vram[o + k])
            return t

        # Appendix D #2: an empty atlas means this state is not on the
        # name-entry screen. That is no evidence, not a failure.
        if not any(ink(x, y) for _, s, _, x, y in cells if s != 0x8140):
            print('  %s: kana atlas empty -- not on the name-entry screen, '
                  'SKIPPED (no evidence)' % sp)
            continue

        agree = 0
        for _, sjis, colour, x, y in cells:
            if (ink(x, y) == 0) == (sjis == 0x8140):
                agree += 1
            else:
                fails.append('VRAM mismatch: 0x%04X at (%d,%d)' % (sjis, x, y))
        print('  %s: %d/%d cells agree with VRAM' % (sp, agree, len(cells)))

    if fails:
        print()
        for f in fails[:20]:
            print('  FAIL %s' % f)
        if len(fails) > 20:
            print('  ... %d more' % (len(fails) - 20))
        print('RESULT: FAIL (%d)' % len(fails))
        return 1
    print('RESULT: PASS')
    return 0


# ---------------------------------------------------------------------
# deadcode -- is a code region reclaimable?  (§20.3)
# ---------------------------------------------------------------------

def cmd_deadcode(path, lo, hi):
    """Enumerate EVERY way into a code region. Reclaiming code is only safe
    if all entries are known and removed -- this is how the 1276-byte
    dakuten block was proved dead, as opposed to Appendix B's 'the zeros
    look free' failures."""
    data, t_addr, t_size, _ = load_exe(path)
    end = min(len(data), HDR + t_size)
    hits = []
    for off in range(HDR, end - 3, 4):
        w = struct.unpack_from('<I', data, off)[0]
        pc = file_to_psx(off, t_addr)
        inside = lo <= pc < hi
        op = w >> 26
        tgt = kind = None
        if op in (2, 3):
            tgt = (pc & 0xF0000000) | ((w & 0x03FFFFFF) << 2)
            kind = 'jal' if op == 3 else 'j'
        elif op in (1, 4, 5, 6, 7):
            imm = w & 0xFFFF
            tgt = pc + 4 + ((imm - 0x10000 if imm & 0x8000 else imm) << 2)
            kind = 'branch'
        if tgt is not None and lo <= tgt < hi and not inside:
            hits.append((pc, tgt, kind))
    for r in code_xrefs(data, t_addr, t_size):
        if lo <= r < hi:
            hits.append((0, r, 'data/pointer reference'))

    print('region 0x%08X - 0x%08X (%d bytes)' % (lo, hi, hi - lo))
    if not hits:
        print('NO entries from outside -- reclaimable as-is.')
        return 0
    for pc, tgt, kind in sorted(set(hits)):
        if pc:
            print('  from 0x%08X -> 0x%08X  %s' % (pc, tgt, kind))
        else:
            print('  address 0x%08X is %s' % (tgt, kind))
    print('%d entry point(s): reclaimable only once ALL of these are removed.'
          % len(set(hits)))
    return 0


def cmd_slpsmap(path):
    data, t_addr, t_size, pc0 = load_exe(path)
    print('%s  image 0x%08X-0x%08X  pc0 0x%08X  gp 0x%08X'
          % (path, t_addr, t_addr + t_size, pc0, SLPS_GP))
    for s in find_stub(data, t_addr):
        print('Krom2RawAdd stub 0x%08X  called from %s'
              % (s, ', '.join('0x%08X' % x for x in find_call_sites(data, t_addr, s))))
    print()
    print('verified address map:')
    for k in sorted(SLPS):
        print('  %-14s 0x%08X' % (k, SLPS[k]))
    print()
    kana, attr = SLPS['grid_kana'], SLPS['grid_attr']
    print('name-entry grid (%d x %d x %d banks):' % (GRID_COLS, GRID_ROWS, GRID_BANKS))
    for bank in range(GRID_BANKS):
        print('  bank %d:' % bank)
        for r in range(GRID_ROWS):
            cs, at = [], []
            for c in range(GRID_COLS):
                i = bank * GRID_CELLS + r * GRID_COLS + c
                cs.append(sjis_ch(_rdh(data, t_addr, kana + i * 2)))
                a = _rdh(data, t_addr, attr + i * 2)
                at.append(a - 0x10000 if a & 0x8000 else a)
            print('    r%d  %s   attr %s' % (r, ''.join(cs), ' '.join('%2d' % a for a in at)))
    print()
    print('menu entries at 0x%08X (4 x %d full-width):' % (SLPS['menu_str'], MENU_WIDTH))
    for i in range(4):
        print('  [%d] %s' % (i, ''.join(
            sjis_ch(_rdh(data, t_addr, SLPS['menu_str'] + (i * MENU_WIDTH + j) * 2))
            for j in range(MENU_WIDTH))))
    print()
    print('prompt block at 0x%08X (%d lines x %d full-width):'
          % (SLPS['prompt_str'], PROMPT_LINES, PROMPT_COLS))
    for l in range(PROMPT_LINES):
        print('  line%d "%s"' % (l, ''.join(
            sjis_ch(_rdh(data, t_addr, SLPS['prompt_str'] + (l * PROMPT_COLS + c) * 2))
            for c in range(PROMPT_COLS))))
    print()
    print('name field 0x%08X: 8 x u16, slot 7 = 0xFFFE sentinel -> HARD CAP 7 chars'
          % SLPS['name_buf'])
    print('reclaimable: 0x%08X-0x%08X (%d bytes) once namegrid is applied'
          % (SLPS['dakuten'], SLPS['dead_end'], SLPS['dead_end'] - SLPS['dakuten']))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == 'fullwidth':
        cmd_fullwidth(argv[2:]); return 0
    if cmd == 'sentencecase':
        cmd_sentencecase(argv[2:]); return 0
    if cmd == 'replace':
        cmd_replace(argv[2:]); return 0
    if cmd == 'rewrap':
        cmd_rewrap(argv[2:]); return 0
    if cmd == 'findtext':
        cmd_findtext(argv[2:]); return 0
    if cmd == 'slpsmap':
        cmd_slpsmap(argv[2]); return 0
    if cmd == 'gridsim':
        return cmd_gridsim(argv[2], argv[3:])
    if cmd == 'deadcode':
        if len(argv) < 5:
            raise SystemExit('deadcode EXE LO HI   (PSX addresses, hex)')
        return cmd_deadcode(argv[2], int(argv[3], 16), int(argv[4], 16))
    if cmd in ('namegrid', 'menutext', 'prompttext'):
        out = argv[3] if len(argv) > 3 and not argv[3].startswith('--') else None
        dry = '--dry' in argv
        if out is None and not dry:
            raise SystemExit('%s IN OUT [--dry]' % cmd)
        if cmd == 'namegrid':
            cmd_namegrid(argv[2], out, revert='--revert' in argv, dry=dry)
        elif cmd == 'menutext':
            cmd_menutext(argv[2], out, revert='--revert' in argv, dry=dry)
        else:
            cmd_prompttext(argv[2], out, dry=dry,
                           wide_yes='--narrow-yes' not in argv)
        return 0
    path = argv[2]
    if cmd == 'info':
        cmd_info(path)
    elif cmd == 'fullwidth':
        cmd_fullwidth(argv[2:])
    elif cmd == 'xref':
        cmd_xref(path, argv[3:])
    elif cmd == 'halfwidth':
        cmd_halfwidth(path, argv[3], '--revert' in argv, '--glyph-only' in argv)
    elif cmd == 'renderer':
        out = argv[3] if len(argv) > 3 and not argv[3].startswith('--') else path
        kw = {}
        i = 3
        while i < len(argv):
            a = argv[i]
            if a == '--cols':    kw['cols'] = int(argv[i+1], 0); i += 2
            elif a == '--rows':  kw['rows'] = int(argv[i+1], 0); i += 2
            elif a == '--cellw': kw['cellw'] = int(argv[i+1], 0); i += 2
            elif a == '--charbuf': kw['charbuf'] = int(argv[i+1], 16); i += 2
            elif a == '--revert': kw['revert'] = True; i += 1
            elif a == '--dry':   kw['dry'] = True; i += 1
            else: i += 1
        cmd_renderer(path, out, **kw)
    elif cmd == 'simcheck':
        kw = {}
        i = 3
        while i < len(argv):
            a = argv[i]
            if a == '--cols':    kw['cols'] = int(argv[i+1], 0); i += 2
            elif a == '--rows':  kw['rows'] = int(argv[i+1], 0); i += 2
            elif a == '--cellw': kw['cellw'] = int(argv[i+1], 0); i += 2
            elif a == '--charbuf': kw['charbuf'] = int(argv[i+1], 16); i += 2
            else: i += 1
        return cmd_simcheck(path, **kw)
    elif cmd == 'windiag':
        return cmd_windiag(path, argv[3])
    elif cmd == 'liveness':
        cmd_liveness(path, argv[3:])
    elif cmd == 'findspace':
        cmd_findspace(path, int(argv[3]) if len(argv) > 3 else 64)
    elif cmd in ('hook', 'hookfont'):
        out = argv[3]
        addr = None
        site = 'all'
        flip = swap = False
        style = 'wide'
        savs = []
        which = 'full'
        force = False
        i = 4
        while i < len(argv):
            a = argv[i]
            if a == '--addr':
                addr = argv[i + 1]; i += 2
            elif a == '--site':
                site = argv[i + 1]; i += 2
            elif a == '--flip-bits':
                flip = True; i += 1
            elif a == '--swap-bytes':
                swap = True; i += 1
            elif a == '--style':
                style = argv[i + 1]; i += 2
            elif a == '--sav':
                savs.append(argv[i + 1]); i += 2
            elif a == '--set':
                which = argv[i + 1]; i += 2
            elif a == '--force':
                force = True; i += 1
            else:
                raise SystemExit('unknown option %s' % a)
        if cmd == 'hookfont':
            if addr is None:
                addr = 'auto'
            if addr != 'auto':
                for a in addr.split(','):
                    if not a.strip().lower().startswith('0x'):
                        raise SystemExit("--addr must be 'auto' or hex address(es) like 0x800F3ECC")
                    if 0x80100000 <= int(a, 16) < 0x80116000:
                        print('WARNING: 0x%08X is in the tail region that black-screened the '
                              'game on 2026-07-30 (live zero-init loader state, NOT free space).'
                              % int(a, 16))
                        print("         Use --addr auto unless you are deliberately re-probing it.")
            cmd_hookfont(path, out, addr, site, style, savs, which, force)
        else:
            if addr is None:
                raise SystemExit('hook requires --addr 0x8XXXXXXX (use findspace to pick one)')
            cmd_hook(path, out, int(addr, 16), site, flip, swap)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
