#!/usr/bin/env python3
"""bankmeasure.py — real per-bank byte usage for SCRIPT.BIN, via riotscript's own emitter.

`assemble.py check` charges the {HDR:} blob 0 bytes; the inserter does not. This measures
the way the inserter does, so the figures are the ones that decide whether a bank overflows.

Usage:
    python3 tools/bankmeasure.py [merged_dump]      default build/script_dump_merged.txt
    python3 tools/bankmeasure.py --banks 40,5,2     restrict the report
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import riotscript

BANK = 0xA000


def measure(path):
    text = open(path, encoding='utf-8').read()
    banks, hdr, cur = {}, {}, None
    for raw in text.split('\n'):
        if raw.startswith('# '):
            continue
        m = re.match(r'=== BANK (\d+) @', raw)
        if m:
            cur = int(m.group(1))
            banks[cur] = []
            continue
        if cur is None:
            continue
        mh = re.match(r'\{HDR:([0-9a-fA-F]+)\}$', raw.strip())
        if mh:
            hdr[cur] = bytes.fromhex(mh.group(1))
            continue
        if re.match(r'\{PAD \d+\}$', raw.strip()):
            continue
        banks[cur].append(raw)
    out = {}
    for b, body in sorted(banks.items()):
        stream = riotscript._emit_bytes_from_body('\n'.join(body), b)
        out[b] = len(hdr.get(b, b'')) + len(stream)
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    only = None
    if args and args[0] == '--banks':
        only = {int(x) for x in args[1].split(',')}
        args = args[2:]
    path = args[0] if args else os.path.join(ROOT, 'build', 'script_dump_merged.txt')
    used = measure(path)
    worst = None
    for b, n in sorted(used.items()):
        if only and b not in only:
            continue
        free = BANK - n
        mark = '!!' if free < 0 else ('~ ' if free < 2000 else '  ')
        print('%s bank %2d  %6d / %d used   free %6d' % (mark, b, n, BANK, free))
    tight = sorted(used.items(), key=lambda kv: -kv[1])[:3]
    print('tightest: ' + ', '.join('bank %d %d free' % (b, BANK - n) for b, n in tight))
