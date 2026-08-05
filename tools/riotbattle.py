#!/usr/bin/env python3
"""
riotbattle.py -- Riot Stars (SLPS-00829) HEXMAP.BIN battle-script dumper / reinserter

HEXMAP.BIN is a container of 46 fixed-size map chunks of 0x2A800 bytes. Each chunk holds
the map's TIM graphics followed by an embedded battle event script. 43 of the 46 chunks
carry dialogue.

The battle script uses the SAME control-code language as SCRIPT.BIN (FC51 begin text,
FFFE line break, FFFF end message, FC30 wait, FCB0/FB00 with args) and is stored in
NORMAL Shift-JIS byte order, exactly like SCRIPT.BIN. (The loader byte-swaps it into
u16 LE when it reaches RAM, but the on-disc layout is standard order.)

Tokenisation and the losslessness guarantee are identical to riotscript.py:
  - runs of SJIS characters  -> readable text
  - control code (FB..FF)    -> {XXXX}
  - any other single byte    -> {=XX}
  - the graphics prefix       -> {PRE n}   (n bytes copied from the original file)
  - trailing zero padding     -> {PAD n}

Free space is TIGHT here, unlike SCRIPT.BIN: median ~1 KB per chunk, minimum 247 bytes.
The inserter hard-fails on any chunk that would overflow 0x2A800.

Usage:
    python3 riotbattle.py dump   HEXMAP.BIN  battle.txt
    python3 riotbattle.py insert HEXMAP.BIN  battle.txt  HEXMAP_new.BIN
    python3 riotbattle.py verify HEXMAP.BIN
    python3 riotbattle.py checkedit HEXMAP.BIN HEXMAP_new.BIN   # ALWAYS run before building
    python3 riotbattle.py stats  HEXMAP.BIN
"""
import sys, re

CHUNK = 0x2A800
# Each map chunk has a FIXED internal layout, verified across all 43 script-bearing chunks:
#   chunk + 0x00000  map graphics (TIM)
#   chunk + 0x25000  event script            <- sector 74, 8192-byte slot
#   chunk + 0x27000  unit / deployment data  <- sector 78, FIXED OFFSET
# The script may grow only within its slot. Anything at or after 0x27000 is read by the
# engine at a fixed offset and MUST NOT move, or the map loads garbage units (black screen).
SCRIPT_LO = 0x25000
SCRIPT_HI = 0x27000
SCRIPT_SLOT = SCRIPT_HI - SCRIPT_LO          # 8192 bytes


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def sjis_char(pair):
    try:
        s = pair.decode('shift_jis')
    except Exception:
        return None
    if len(s) != 1 or s.encode('shift_jis') != pair:
        return None
    return s


def find_script_bounds(chunk):
    """Return (start, end) of the event script inside a chunk, or None.
    start is the fixed slot base; end is the last non-zero byte WITHIN the slot."""
    if len(chunk) < SCRIPT_HI:
        return None
    slot = chunk[SCRIPT_LO:SCRIPT_HI]
    if b'\xfc\x51' not in slot:
        return None
    k = len(slot)
    while k > 0 and slot[k-1] == 0:
        k -= 1
    return (SCRIPT_LO, SCRIPT_LO + k)


def escape_text(s):
    return s.replace('{', '{{').replace('}', '}}')


def tokenise(b):
    out = []
    i = 0
    n = len(b)
    while i < n:
        c = b[i]
        if is_lead(c) and i + 1 < n:
            ch = sjis_char(b[i:i+2])
            if ch is not None:
                run = [ch]; i += 2
                while i + 1 < n and is_lead(b[i]):
                    c2 = sjis_char(b[i:i+2])
                    if c2 is None:
                        break
                    run.append(c2); i += 2
                out.append(escape_text(''.join(run)))
                continue
        if 0xfb <= c <= 0xff and i + 1 < n:
            out.append('{%02X%02X}' % (c, b[i+1])); i += 2
            continue
        # coalesce a run of raw (non-text, non-control) bytes into one tag
        j = i
        raw = bytearray()
        while j < n:
            cj = b[j]
            if 0xfb <= cj <= 0xff and j + 1 < n:
                break
            if is_lead(cj) and j + 1 < n and sjis_char(b[j:j+2]) is not None:
                break
            raw.append(cj); j += 1
        out.append('{=%s}' % raw.hex().upper())
        i = j
    return ''.join(out)


def unescape_split(s):
    i = 0; n = len(s); buf = []
    while i < n:
        if s[i] == '{':
            if i + 1 < n and s[i+1] == '{':
                buf.append('{'); i += 2; continue
            if buf:
                yield ('text', ''.join(buf)); buf = []
            j = s.index('}', i)
            yield ('tag', s[i+1:j]); i = j + 1
            continue
        if s[i] == '}':
            if i + 1 < n and s[i+1] == '}':
                buf.append('}'); i += 2; continue
        buf.append(s[i]); i += 1
    if buf:
        yield ('text', ''.join(buf))


def bytes_from_body(body, idx):
    out = bytearray()
    for kind, val in unescape_split(body):
        if kind == 'text':
            for ch in val:
                if ch == '\n':
                    continue
                out += ch.encode('shift_jis')
        else:
            if val.startswith('='):
                out += bytes.fromhex(val[1:])
            elif re.fullmatch(r'[0-9A-Fa-f]{4}', val):
                out.append(int(val[0:2], 16)); out.append(int(val[2:4], 16))
            else:
                raise ValueError('bad tag {%s} in chunk %d' % (val, idx))
    return bytes(out)


def iter_chunks(data):
    n = len(data)
    c = 0
    while c * CHUNK < n:
        s = c * CHUNK
        yield c, data[s:min(s + CHUNK, n)]
        c += 1


def dump(path, out_path):
    data = open(path, 'rb').read()
    lines = ['# Riot Stars HEXMAP.BIN battle-script dump',
             '# Edit only readable text. Leave {XXXX} {=XX} {PRE n} {PAD n} tags intact.',
             '# {PRE n} = n bytes of map graphics copied verbatim from the original HEXMAP.BIN.',
             '# WARNING: free space is tight (median ~1 KB/chunk). Half-width text strongly advised.',
             '']
    for idx, chunk in iter_chunks(data):
        b = find_script_bounds(chunk)
        if b is None:
            continue
        start, end = b
        lines.append('=== CHUNK %d @ 0x%06X  script 0x%06X..0x%06X  headroom %d'
                     % (idx, idx*CHUNK, idx*CHUNK+start, idx*CHUNK+end, SCRIPT_HI - end))
        toks = tokenise(chunk[start:end])
        toks = re.sub(r'(\{FFFF\})', r'\1\n', toks)
        for seg in toks.split('\n'):
            if seg:
                lines.append(seg)
        lines.append('{PAD %d}' % (SCRIPT_HI - end))
        lines.append('')
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    return out_path


def insert(path, dump_path, out_path):
    orig = open(path, 'rb').read()
    data = bytearray(orig)
    text = open(dump_path, 'r', encoding='utf-8').read()
    pre = {}; pad = {}; bodies = {}
    cur = None
    for line in text.split('\n'):
        if line.startswith('# '):
            continue
        m = re.match(r'=== CHUNK (\d+) @', line)
        if m:
            cur = int(m.group(1)); bodies[cur] = []
            continue
        if cur is None:
            continue
        if re.match(r'\{PRE \d+\}$', line.strip()):
            continue          # legacy tag, ignored (slot base is fixed)
        mq = re.match(r'\{PAD (\d+)\}$', line.strip())
        if mq:
            pad[cur] = int(mq.group(1)); continue
        bodies[cur].append(line)

    overflow = []
    for idx in sorted(bodies):
        body = '\n'.join(bodies[idx])
        script = bytes_from_body(body, idx)
        base = idx * CHUNK
        if len(script) > SCRIPT_SLOT:
            overflow.append((idx, len(script), len(script) - SCRIPT_SLOT))
            continue
        # write ONLY the script slot; everything before 0x25000 and at/after 0x27000 is untouched
        data[base+SCRIPT_LO:base+SCRIPT_HI] = script + b'\x00' * (SCRIPT_SLOT - len(script))

    if overflow:
        print('!! CHUNK OVERFLOW — reinsertion would corrupt the file:')
        for idx, used, over in overflow:
            print('   chunk %d: script %d bytes, %d over the %d-byte slot'
                  % (idx, used, over, SCRIPT_SLOT))
        print('   Shorten the translation in these chunks and retry.')
        raise SystemExit(2)

    open(out_path, 'wb').write(bytes(data))
    return out_path


def verify(path):
    import tempfile, os
    dtmp = tempfile.mkdtemp()
    dp = os.path.join(dtmp, 'b.txt'); op = os.path.join(dtmp, 'r.bin')
    dump(path, dp); insert(path, dp, op)
    a = open(path, 'rb').read(); b = open(op, 'rb').read()
    if a == b:
        print('ROUND TRIP OK — rebuilt file is byte-identical (%d bytes).' % len(a))
        return True
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            print('MISMATCH at 0x%X (chunk %d, +0x%X): %02X != %02X'
                  % (i, i//CHUNK, i % CHUNK, a[i], b[i]))
            break
    return False


def stats(path):
    import collections
    data = open(path, 'rb').read()
    msgs = []; frees = []
    for idx, chunk in iter_chunks(data):
        b = find_script_bounds(chunk)
        if b is None:
            continue
        start, end = b
        frees.append(SCRIPT_HI - end)
        toks = tokenise(chunk[start:end])
        for m in toks.split('{FFFF}'):
            plain = re.sub(r'\{[^}]*\}', '', m)
            if len(plain) >= 4:
                msgs.append(plain)
    c = collections.Counter(msgs)
    tot = sum(len(m) for m in msgs)
    uq = sum(len(m) for m in c)
    print('chunks with script : %d' % len(frees))
    print('messages           : %d' % len(msgs))
    print('stored characters  : %d' % tot)
    print('unique messages    : %d' % len(c))
    print('unique characters  : %d  (%.0f%% duplication)' % (uq, 100*(1-uq/tot) if tot else 0))
    print('script headroom total  : %d bytes (%.0f KB)' % (sum(frees), sum(frees)/1024))
    print('script headroom min    : %d bytes' % min(frees))
    print('script headroom median : %d bytes' % sorted(frees)[len(frees)//2])


def checkedit(orig_path, mod_path):
    """Prove a modified HEXMAP only differs inside script slots. Run this before every build."""
    a = open(orig_path, 'rb').read(); b = open(mod_path, 'rb').read()
    if len(a) != len(b):
        print('FAIL: size changed %d -> %d' % (len(a), len(b))); return False
    bad = []
    for c in range((len(a) + CHUNK - 1)//CHUNK):
        s0 = c*CHUNK; e0 = min(s0+CHUNK, len(a))
        if a[s0:s0+SCRIPT_LO] != b[s0:s0+SCRIPT_LO]:
            bad.append((c, 'graphics prefix moved'))
        if e0 > s0+SCRIPT_HI and a[s0+SCRIPT_HI:e0] != b[s0+SCRIPT_HI:e0]:
            bad.append((c, 'unit/deployment data moved'))
    if bad:
        print('FAIL — data outside the script slot changed. The map will not load:')
        for c, why in bad[:20]:
            print('   chunk %d: %s' % (c, why))
        return False
    n = sum(1 for i in range(len(a)) if a[i] != b[i])
    print('OK — %d bytes changed, all inside script slots. Safe to build.' % n)
    return True


def unique(path, out_path):
    """Export each distinct message once, for translation. Not used for reinsertion."""
    import collections
    data = open(path, 'rb').read()
    seen = collections.Counter(); order = []
    for idx, chunk in iter_chunks(data):
        bnd = find_script_bounds(chunk)
        if bnd is None:
            continue
        start, end = bnd
        toks = tokenise(chunk[start:end])
        for msg in toks.split('{FFFF}'):
            plain = re.sub(r'\{[^}]*\}', '', msg)
            if len(plain.strip()) >= 3:
                key = msg.strip()
                if key not in seen:
                    order.append(key)
                seen[key] += 1
    total = sum(seen.values())
    lines = ['# HEXMAP.BIN battle script — unique messages (translate once, propagate).',
             '# Format: <count>\t<message with tags>',
             '# %d instances, %d unique' % (total, len(order)), '']
    for m in sorted(order, key=lambda k: -seen[k]):
        lines.append('%d\t%s' % (seen[m], m.replace('\n', '')))
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    return out_path, len(order), total


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 1
    cmd = argv[1]
    if cmd == 'dump':
        print('wrote', dump(argv[2], argv[3]))
    elif cmd == 'insert':
        print('wrote', insert(argv[2], argv[3], argv[4]))
    elif cmd == 'verify':
        return 0 if verify(argv[2]) else 1
    elif cmd == 'stats':
        stats(argv[2])
    elif cmd == 'checkedit':
        return 0 if checkedit(argv[2], argv[3]) else 1
    elif cmd == 'unique':
        p, u, t = unique(argv[2], argv[3]); print('wrote %s: %d unique / %d total' % (p, u, t))
    else:
        print('unknown command', cmd); return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
