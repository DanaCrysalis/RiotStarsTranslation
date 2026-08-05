#!/usr/bin/env python3
"""
riotscript.py  --  Riot Stars (SLPS-00829) SCRIPT.BIN dumper / reinserter

SCRIPT.BIN is exactly 44 banks x 0xA000 bytes. Each bank (except bank 40) begins
with a 900-byte block of 50 x 18-byte event records; then a command stream with
inline Shift-JIS text; then zero padding out to 0xA000.

Text is standard-byte-order Shift-JIS. Control codes use lead bytes 0xFB-0xFF,
which lie outside the SJIS lead ranges (0x81-0x9F, 0xE0-0xEF), so parsing is
unambiguous. There is no pointer table; strings are inline, so lengths may be
changed freely as long as each bank still fits in 0xA000.

The dump is losslessly tokenised:
  - a run of SJIS characters is written as readable text
  - a control code (0xFB..0xFF lead) is written as a tag  {XXXX}
  - any other single byte is written as a raw tag         {=XX}
  - the header block is written once per bank as          {HDR:...hex...}
  - trailing zero padding is written as                   {PAD n}
Every token maps back to exact bytes, and each SJIS pair is accepted as text
only if it survives decode->encode identically; otherwise it is emitted as raw
{=XX} tags. This guarantees `insert(dump(x)) == x` byte-for-byte.

Usage:
    python3 riotscript.py dump   SCRIPT.BIN  script.txt
    python3 riotscript.py insert SCRIPT.BIN  script.txt  SCRIPT_new.BIN
    python3 riotscript.py verify SCRIPT.BIN                 # self-test round trip
    python3 riotscript.py unique SCRIPT.BIN  unique.txt     # dedup convenience dump
"""
import sys, re

BANK = 0xA000
NBANKS = 44
HEADERLESS = {40}          # bank 40 is a pure string pool, no 900-byte header
HDR_LEN = 0x384            # 900 bytes = 50 x 18


def is_sjis_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def sjis_char(pair):
    """Return the unicode char if `pair` is a lossless-roundtrip SJIS char, else None."""
    try:
        s = pair.decode('shift_jis')
    except Exception:
        return None
    if len(s) != 1:
        return None
    if s.encode('shift_jis') != pair:
        return None
    return s


def tokenise_stream(b):
    """Tokenise one bank's command stream (already stripped of header+pad).
    Returns a string using text + {..} tags."""
    out = []
    i = 0
    n = len(b)
    while i < n:
        c = b[i]
        if is_sjis_lead(c) and i + 1 < n:
            ch = sjis_char(b[i:i+2])
            if ch is not None:
                # accumulate a text run
                run = [ch]
                i += 2
                while i + 1 < n and is_sjis_lead(b[i]):
                    ch2 = sjis_char(b[i:i+2])
                    if ch2 is None:
                        break
                    run.append(ch2)
                    i += 2
                out.append(escape_text(''.join(run)))
                continue
        if 0xfb <= c <= 0xff and i + 1 < n:
            out.append('{%02X%02X}' % (c, b[i+1]))
            i += 2
            continue
        # any other single byte
        out.append('{=%02X}' % c)
        i += 1
    return ''.join(out)


def escape_text(s):
    # protect our tag delimiters if they ever appear literally in decoded text
    return s.replace('{', '{{').replace('}', '}}')


def unescape_split(s):
    """Yield ('text', str) or ('tag', str) tokens from a dumped line body."""
    i = 0
    n = len(s)
    buf = []
    while i < n:
        if s[i] == '{':
            if i + 1 < n and s[i+1] == '{':
                buf.append('{'); i += 2; continue
            # a real tag
            if buf:
                yield ('text', ''.join(buf)); buf = []
            j = s.index('}', i)
            # handle escaped }} inside? tags never contain }, so first } ends it
            yield ('tag', s[i+1:j])
            i = j + 1
            continue
        if s[i] == '}':
            if i + 1 < n and s[i+1] == '}':
                buf.append('}'); i += 2; continue
            buf.append('}'); i += 1; continue
        buf.append(s[i]); i += 1
    if buf:
        yield ('text', ''.join(buf))


def dump(script_path, out_path):
    data = open(script_path, 'rb').read()
    assert len(data) == BANK * NBANKS, \
        'unexpected size %d (expected %d)' % (len(data), BANK * NBANKS)
    lines = []
    lines.append('# Riot Stars SCRIPT.BIN dump')
    lines.append('# Edit only the readable text. Leave {XXXX} {=XX} {HDR:..} {PAD n} tags intact.')
    lines.append('# Split points @MSG are cosmetic; you may merge/split freely, tags are what matter.')
    lines.append('')
    for bank in range(NBANKS):
        b = data[bank*BANK:(bank+1)*BANK]
        has_hdr = bank not in HEADERLESS
        # trailing zero padding
        end = len(b)
        while end > 0 and b[end-1] == 0:
            end -= 1
        pad = len(b) - end
        body_start = HDR_LEN if has_hdr else 0
        stream = b[body_start:end]
        lines.append('=== BANK %d @ 0x%06X  hdr=%s' % (bank, bank*BANK, 'yes' if has_hdr else 'no'))
        if has_hdr:
            lines.append('{HDR:%s}' % b[:HDR_LEN].hex())
        # tokenise, then break into @MSG blocks at end-of-message {FFFF} for readability
        toks = tokenise_stream(stream)
        # insert newlines after {FFFF} and {FC30} to make it browsable
        toks = re.sub(r'(\{FFFF\})', r'\1\n', toks)
        for k, seg in enumerate(toks.split('\n')):
            if seg == '' and k == len(toks.split('\n')) - 1:
                continue
            lines.append(seg)
        lines.append('{PAD %d}' % pad)
        lines.append('')
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    return out_path


def _emit_bytes_from_body(body, bank):
    """Convert a dumped bank body (text + tags, minus HDR/PAD) back to bytes."""
    out = bytearray()
    for kind, val in unescape_split(body):
        if kind == 'text':
            for ch in val:
                if ch == '\n':
                    continue
                out += ch.encode('shift_jis')
        else:  # tag
            if val.startswith('='):
                out.append(int(val[1:], 16))
            elif re.fullmatch(r'[0-9A-Fa-f]{4}', val):
                out.append(int(val[0:2], 16))
                out.append(int(val[2:4], 16))
            else:
                raise ValueError('bad tag {%s} in bank %d' % (val, bank))
    return bytes(out)


def insert(script_path, dump_path, out_path):
    orig = open(script_path, 'rb').read()
    text = open(dump_path, 'r', encoding='utf-8').read()
    # split into banks
    banks = {}
    cur = None
    hdr = {}
    pad = {}
    bodies = {}
    for raw in text.split('\n'):
        line = raw
        if line.startswith('# '):
            continue
        m = re.match(r'=== BANK (\d+) @', line)
        if m:
            cur = int(m.group(1))
            bodies[cur] = []
            continue
        if cur is None:
            continue
        mh = re.match(r'\{HDR:([0-9a-fA-F]+)\}$', line.strip())
        if mh:
            hdr[cur] = bytes.fromhex(mh.group(1))
            continue
        mp = re.match(r'\{PAD (\d+)\}$', line.strip())
        if mp:
            pad[cur] = int(mp.group(1))
            continue
        bodies[cur].append(line)

    out = bytearray()
    overflow = []
    for bank in range(NBANKS):
        body = '\n'.join(bodies.get(bank, []))
        stream = _emit_bytes_from_body(body, bank)
        h = hdr.get(bank, b'')
        content = h + stream
        want_pad = BANK - len(content)
        if want_pad < 0:
            overflow.append((bank, len(content), len(content) - BANK))
            # still assemble (truncation would corrupt) so caller can see the failure
            bankbytes = content[:BANK]
        else:
            bankbytes = content + b'\x00' * want_pad
        assert len(bankbytes) == BANK or want_pad < 0
        out += bankbytes[:BANK]

    if overflow:
        print('!! BANK OVERFLOW — reinsertion would corrupt the file:')
        for bank, used, over in overflow:
            print('   bank %d: %d bytes used, %d over the 0x%X limit' % (bank, used, over, BANK))
        print('   Shorten the translation in these banks and retry.')
        raise SystemExit(2)

    assert len(out) == len(orig), 'size drift %d != %d' % (len(out), len(orig))
    open(out_path, 'wb').write(out)
    return out_path


def verify(script_path):
    import tempfile, os
    d = tempfile.mkdtemp()
    dp = os.path.join(d, 'dump.txt')
    op = os.path.join(d, 'rebuilt.bin')
    dump(script_path, dp)
    insert(script_path, dp, op)
    a = open(script_path, 'rb').read()
    b = open(op, 'rb').read()
    if a == b:
        print('ROUND TRIP OK — rebuilt file is byte-identical (%d bytes).' % len(a))
        return True
    # locate first diff
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            bank = i // BANK
            print('MISMATCH at 0x%X (bank %d, +0x%X): %02X != %02X'
                  % (i, bank, i % BANK, a[i], b[i]))
            break
    return False


def unique(script_path, out_path):
    """Convenience: dump each distinct FFFF-terminated message once, with a
    count of how many times it occurs. Shows the ~3x duplication and gives a
    translate-once worklist. NOT used for reinsertion."""
    data = open(script_path, 'rb').read()
    import collections
    seen = collections.Counter()
    order = []
    for bank in range(NBANKS):
        b = data[bank*BANK:(bank+1)*BANK]
        start = 0 if bank in HEADERLESS else HDR_LEN
        end = len(b)
        while end > 0 and b[end-1] == 0:
            end -= 1
        stream = b[start:end]
        toks = tokenise_stream(stream)
        for msg in toks.split('{FFFF}'):
            # keep only messages that contain readable text
            textonly = re.sub(r'\{[^}]*\}', '', msg)
            if textonly.strip():
                if msg not in seen:
                    order.append(msg)
                seen[msg] += 1
    lines = ['# Unique messages (translate once, propagate by count).',
             '# Format:  <count>\\t<message with tags>', '']
    total = sum(seen.values())
    lines.append('# %d message instances, %d unique (%.0f%% duplication)'
                 % (total, len(order), 100*(1-len(order)/total)))
    lines.append('')
    for msg in sorted(order, key=lambda m: -seen[m]):
        lines.append('%d\t%s' % (seen[msg], msg.replace('\n', '')))
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    return out_path, len(order), total


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == 'dump':
        p = dump(argv[2], argv[3]); print('wrote', p)
    elif cmd == 'insert':
        p = insert(argv[2], argv[3], argv[4]); print('wrote', p)
    elif cmd == 'verify':
        ok = verify(argv[2]); return 0 if ok else 1
    elif cmd == 'unique':
        p, u, t = unique(argv[2], argv[3]); print('wrote %s: %d unique / %d total' % (p, u, t))
    else:
        print('unknown command', cmd); return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
