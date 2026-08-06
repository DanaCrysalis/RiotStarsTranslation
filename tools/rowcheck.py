#!/usr/bin/env python3
"""Per-chunk analyser: bytes, columns, rows, tag parity, charset.
Mirrors assemble.py exactly, and ADDS the row check assemble.py omits.

Usage:
    python3 tools/rowcheck.py <chunk_num> <path_to_tl_file>   battle chunk (as before)
    python3 tools/rowcheck.py script [merged_dump]            main script (added 2026-08-06)

The `script` mode exists because assemble.py has no row check at all (FLAGS.md C1)
and because its column check counts ONLY the battle-side {FC00}{=0000} name insert
as 7 columns. The main script uses {FFEC}{=00}{=00} for the same player name, which
assemble.py strips to 0 columns — so a script line can be 7 columns over and pass.
This mode counts it as 7. See FLAGS.md C4."""
import re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

NAME_COST, COLS, SLOT = 7, 24, 8192
SCRIPT_NAME = '{FFEC}{=00}{=00}'     # main-script player-name insert; battle side is {FC00}{=0000}
BANK = 0xA000
ALLOWED = set('\u3000\u3001\u3002\uff0c\uff0e\uff1a\uff1b\uff1f\uff01'
              '\u30fc\u2010\uff0f\u301c\u2018\u2019\u201c\u201d'
              '\uff08\uff09\uff0b\u2212\uff1d\uff05\uff06\uff0a\uff20')

def cost(s):
    n = 0
    for m in re.finditer(r'\{[^}]*\}|.', s):
        t = m.group(0)
        if t.startswith('{'):
            if t.startswith('{='):      n += (len(t) - 3) // 2
            elif t.startswith(('{PAD', '{PRE', '{HDR')): n += 0
            else:                        n += 2
        else:                            n += 2
    return n

def is_structural(line):
    s = line.strip()
    return (not s) or s.startswith('#') or s.startswith('===') \
        or re.match(r'\{(PAD|PRE) \d+\}$', s) is not None

def load_chunk(n, path=None):
    p = path or os.path.join(ROOT, 'dumps/battle_dump.txt')
    lines = open(p, encoding='utf-8').read().split('\n')
    if path:
        return lines
    st = [i for i, l in enumerate(lines) if l.startswith('=== CHUNK')] + [len(lines)]
    for a, b in zip(st, st[1:]):
        if int(lines[a].split()[2]) == n:
            return lines[a:b]

def chunk_bytes(body):
    return sum(cost(l) for l in body if not is_structural(l))

def col_problems(body, label='x'):
    bad = []
    for i, line in enumerate(body):
        if is_structural(line): continue
        for c in re.sub(r'\{[^}]*\}', '', line):
            o = ord(c)
            if 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A or 0xFF10 <= o <= 0xFF19: continue
            if c in ALLOWED: continue
            bad.append('%s line %d: illegal char %r (U+%04X)' % (label, i, c, o))
        for seg in re.split(r'\{FFFE\}', line):
            for run in re.split(r'\{(?:FCC0|FC30|FC51|FC50|FFFF)\}', seg):
                t = re.sub(r'\{FC00\}\{=0000\}', 'N' * NAME_COST, run)
                t = re.sub(r'\{[^}]*\}', '', t)
                if len(t) > COLS:
                    bad.append('%s line %d: %d cols |%s|' % (label, i, len(t), t))
    return bad

def row_problems(body, label='x'):
    """Pages: a page is bounded by {FCC0}/{FC51}/{FC50}/{FC30}/{FFFF}.
    Count text rows = non-empty segments between {FFFE} within the page."""
    bad = []
    for i, line in enumerate(body):
        if is_structural(line): continue
        for page in re.split(r'\{(?:FCC0|FC30|FC51|FC50|FFFF)\}', line):
            segs = re.split(r'\{FFFE\}', page)
            rows = 0
            for s in segs:
                t = re.sub(r'\{FC00\}\{=0000\}', 'N'*NAME_COST, s)
                t = re.sub(r'\{[^}]*\}', '', t)
                if t.strip('\u3000').strip(): rows += 1
            if rows > 4:
                bad.append('%s line %d: %d text rows > 4' % (label, i, rows))
    return bad

def tag_parity(src, tl, label='x'):
    bad = []
    if len(src) != len(tl):
        return ['%s: %d lines vs %d' % (label, len(tl), len(src))]
    for i, (a, b) in enumerate(zip(src, tl)):
        ta = [t for t in re.findall(r'\{[^}]*\}', a) if t != '{FFFE}']
        tb = [t for t in re.findall(r'\{[^}]*\}', b) if t != '{FFFE}']
        if ta != tb:
            bad.append('%s line %d: tag stream changed' % (label, i))
            for k,(x,y) in enumerate(zip(ta,tb)):
                if x!=y:
                    bad.append('    first diff @tag %d: src %s -> tl %s' % (k,x,y)); break
            if len(ta)!=len(tb): bad.append('    tag count %d -> %d' % (len(ta),len(tb)))
    return bad

def fffe_counts(body):
    return [len(re.findall(r'\{FFFE\}', l)) for l in body]

def report(n, tlpath):
    src = load_chunk(n)
    tl  = open(tlpath, encoding='utf-8').read().split('\n')
    if tl and tl[-1] == '': tl = tl[:-1]
    src2 = [l for l in src if l != ''] if src[-1]=='' else src
    b = chunk_bytes(tl)
    print('chunk %d: %d / %d bytes  slack %d' % (n, b, SLOT, SLOT-b))
    for f in (tag_parity(src2, tl, 'c%d'%n), col_problems(tl,'c%d'%n), row_problems(tl,'c%d'%n)):
        for x in f: print('  !!', x)
    sc, tc = fffe_counts(src2), fffe_counts(tl)
    ch = [(i,a,c) for i,(a,c) in enumerate(zip(sc,tc)) if a!=c]
    if ch:
        print('  {FFFE} changed:', ', '.join('line %d: %d->%d'%(i,a,c) for i,a,c in ch))
    else:
        print('  {FFFE} unchanged on every line')


# ---------------------------------------------------------------- script mode

def _script_cols(run):
    t = run.replace(SCRIPT_NAME, 'N' * NAME_COST)
    t = re.sub(r'\{FC00\}\{=0000\}', 'N' * NAME_COST, t)
    return len(re.sub(r'\{[^}]*\}', '', t))


def _script_rows(line):
    """-> list of text-row counts, one per page."""
    out = []
    for page in re.split(r'\{(?:FCC0|FC30|FC51|FC50|FFFF)\}', line):
        n = 0
        for s in re.split(r'\{FFFE\}', page):
            if re.sub(r'\{[^}]*\}', '', s.replace(SCRIPT_NAME, 'N')).strip('\u3000').strip():
                n += 1
        out.append(n)
    return out


def script_report(merged=None, pristine=None):
    """Row + column check for the main script, comparing against the pristine dump so
    inherited source breakage is not reported as if the translation caused it."""
    merged = merged or os.path.join(ROOT, 'build/script_dump_merged.txt')
    pristine = pristine or os.path.join(ROOT, 'dumps/script_dump.txt')
    M = open(merged, encoding='utf-8').read().split('\n')
    P = open(pristine, encoding='utf-8').read().split('\n')
    if len(M) != len(P):
        print('!! merged dump has %d lines, pristine has %d' % (len(M), len(P)))
        return False

    def english(s):
        return bool(re.search(r'[\uff21-\uff3a\uff41-\uff5a]', re.sub(r'\{[^}]*\}', '', s)))

    wide, rows_new, rows_inh, n_tl = [], [], [], 0
    for i, (p, m) in enumerate(zip(P, M)):
        if is_structural(m):
            continue
        if not english(m):
            continue                      # untranslated fall-through Japanese
        n_tl += 1
        for seg in re.split(r'\{FFFE\}', m):
            for run in re.split(r'\{(?:FCC0|FC30|FC51|FC50|FFFF)\}', seg):
                c = _script_cols(run)
                if c > COLS:
                    wide.append((i + 1, c, re.sub(r'\{[^}]*\}', '', run)))
        mr, pr = _script_rows(m), _script_rows(p)
        for k, r in enumerate(mr):
            if r > 4:
                src = max(pr) if len(pr) != len(mr) else pr[k]
                (rows_inh if src > 4 else rows_new).append((i + 1, k, r, src))

    print('script: %d translated lines checked (name insert %s = %d columns)'
          % (n_tl, SCRIPT_NAME, NAME_COST))
    for ln, c, t in wide:
        print('  !! line %d: %d columns > %d  |%s|' % (ln, c, COLS, t))
    for ln, k, r, src in rows_new:
        print('  !! line %d page %d: %d text rows > 4  (source page was %d — INTRODUCED)'
              % (ln, k, r, src))
    for ln, k, r, src in rows_inh:
        print('  ~  line %d page %d: %d text rows > 4  (source already %d — INHERITED)'
              % (ln, k, r, src))
    if not wide and not rows_new:
        print('  columns OK; no page over 4 text rows that the source did not already exceed')
    return not wide and not rows_new


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'script':
        sys.exit(0 if script_report(*sys.argv[2:4]) else 1)
    report(int(sys.argv[1]), sys.argv[2])
