#!/usr/bin/env python3
"""
assemble.py -- Riot Stars fan translation build tool

Merges whatever has been translated so far into complete, buildable dumps, so the
patch can be tested at ANY point in the project, not only when everything is done.

Untranslated chunks and lines fall through to the original Japanese, so the game is
always playable. Nothing is ever half-written.

Layout it expects (paths relative to the project root, i.e. the parent of tools/):

    original/   SCRIPT.BIN  HEXMAP.BIN            pristine, never modified
    dumps/      script_dump.txt  battle_dump.txt  pristine dumps, regenerate with `refresh`
                script_unique.txt  battle_unique.txt
    tl/battle/  chunk_000.txt ... chunk_043.txt   one file per translated battle chunk
    tl/script/  batch_*.tsv                       JP<TAB>EN pairs for the main script
    build/                                        everything this tool writes

Usage:
    python3 tools/assemble.py status              progress + byte headroom report
    python3 tools/assemble.py check               validate translated files, build nothing
    python3 tools/assemble.py merge               write build/*_dump_merged.txt
    python3 tools/assemble.py build               merge, then reinsert into build/*.BIN
    python3 tools/assemble.py refresh             re-dump from original/ into dumps/
    python3 tools/assemble.py all                 check + build + checkedit

Exit code is non-zero if anything failed, so this is safe to wire into a script.
"""
import sys, os, re, subprocess

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS  = os.path.join(ROOT, 'tools')
ORIG   = os.path.join(ROOT, 'original')
DUMPS  = os.path.join(ROOT, 'dumps')
TLB    = os.path.join(ROOT, 'tl', 'battle')
TLS    = os.path.join(ROOT, 'tl', 'script')
BUILD  = os.path.join(ROOT, 'build')

SCRIPT_SLOT = 8192          # battle chunk script slot, 0x25000..0x27000
BANK        = 0xA000        # SCRIPT.BIN bank size
NAME_COST   = 7             # {FC00}{=0000} occupies 7 columns on screen
COLS        = 24

ALLOWED = set('\u3000\u3001\u3002\uff0c\uff0e\uff1a\uff1b\uff1f\uff01'
              '\u30fc\u2010\uff0f\u301c\u2018\u2019\u201c\u201d'
              '\uff08\uff09\uff0b\u2212\uff1d\uff05\uff06\uff0a\uff20')


# ---------------------------------------------------------------- primitives

def cost(s):
    """Byte cost of a tokenised body, matching riotbattle/riotscript semantics."""
    n = 0
    for m in re.finditer(r'\{[^}]*\}|.', s):
        t = m.group(0)
        if t.startswith('{'):
            if t.startswith('{='):
                n += (len(t) - 3) // 2
            elif t.startswith(('{PAD', '{PRE', '{HDR')):
                n += 0
            else:
                n += 2
        else:
            n += 2
    return n


def is_structural(line):
    s = line.strip()
    return (not s) or s.startswith('#') or s.startswith('===') \
        or re.match(r'\{(PAD|PRE) \d+\}$', s) is not None


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------------------------------------------------------------- validation

def validate_body(lines, label, jp_ok=False):
    """Charset / column / row checks. Returns list of problem strings."""
    bad = []
    for i, line in enumerate(lines):
        if is_structural(line):
            continue
        # charset
        for c in re.sub(r'\{[^}]*\}', '', line):
            o = ord(c)
            if 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A or 0xFF10 <= o <= 0xFF19:
                continue
            if c in ALLOWED:
                continue
            if jp_ok and o > 0x2000:
                continue            # untranslated Japanese, tolerated
            bad.append('%s line %d: illegal char %r (U+%04X)' % (label, i, c, o))
        # columns
        for seg in re.split(r'\{FFFE\}', line):
            for run in re.split(r'\{(?:FCC0|FC30|FC51|FC50|FFFF)\}', seg):
                t = re.sub(r'\{FC00\}\{=0000\}', 'N' * NAME_COST, run)
                t = re.sub(r'\{[^}]*\}', '', t)
                if len(t) > COLS:
                    bad.append('%s line %d: %d columns > %d  |%s|'
                               % (label, i, len(t), COLS, t))
    return bad


def tag_parity(src_lines, tl_lines, label):
    """Every tag except {FFFE} must survive, in order. Line counts must match."""
    bad = []
    if len(src_lines) != len(tl_lines):
        bad.append('%s: %d lines vs %d in the original dump — line counts must match'
                   % (label, len(tl_lines), len(src_lines)))
        return bad
    for i, (a, b) in enumerate(zip(src_lines, tl_lines)):
        ta = [t for t in re.findall(r'\{[^}]*\}', a) if t != '{FFFE}']
        tb = [t for t in re.findall(r'\{[^}]*\}', b) if t != '{FFFE}']
        if ta != tb:
            bad.append('%s line %d: tag stream changed' % (label, i))
    return bad


# ---------------------------------------------------------------- battle side

def split_battle(text):
    """-> (preamble_lines, {chunk_idx: (header_line, body_lines)}) in file order."""
    pre, chunks, order, cur = [], {}, [], None
    for line in text.split('\n'):
        m = re.match(r'=== CHUNK (\d+) @', line)
        if m:
            cur = int(m.group(1))
            chunks[cur] = [line, []]
            order.append(cur)
            continue
        if cur is None:
            pre.append(line)
        else:
            chunks[cur][1].append(line)
    return pre, chunks, order


def load_battle_tl():
    """-> {idx: body_lines} for every tl/battle/chunk_NNN.txt present."""
    out = {}
    if not os.path.isdir(TLB):
        return out
    for fn in sorted(os.listdir(TLB)):
        m = re.match(r'chunk_(\d+)\.txt$', fn)
        if not m:
            continue
        idx = int(m.group(1))
        lines = read(os.path.join(TLB, fn)).split('\n')
        # tolerate the === CHUNK header being present or absent
        if lines and lines[0].startswith('=== CHUNK'):
            hm = re.match(r'=== CHUNK (\d+) @', lines[0])
            if hm and int(hm.group(1)) != idx:
                print('  !! %s declares CHUNK %s but is named %03d' % (fn, hm.group(1), idx))
            lines = lines[1:]
        out[idx] = lines
    return out


def merge_battle(verbose=True):
    src_path = os.path.join(DUMPS, 'battle_dump.txt')
    if not os.path.exists(src_path):
        return None, ['dumps/battle_dump.txt missing — run `refresh` first']
    pre, chunks, order = split_battle(read(src_path))
    tl = load_battle_tl()
    problems, report = [], []

    for idx in order:
        header, body = chunks[idx]
        if idx not in tl:
            continue
        new = tl[idx]
        # drop a trailing blank the dump keeps between chunks, then restore it
        while new and not new[-1].strip():
            new.pop()
        old = [l for l in body]
        while old and not old[-1].strip():
            old.pop()
        problems += tag_parity(old, new, 'chunk %d' % idx)
        problems += validate_body(new, 'chunk %d' % idx)
        used = cost(''.join(l for l in new if not is_structural(l)))
        report.append((idx, used, SCRIPT_SLOT - used))
        if used > SCRIPT_SLOT:
            problems.append('chunk %d: %d bytes, %d OVER the %d-byte slot'
                            % (idx, used, used - SCRIPT_SLOT, SCRIPT_SLOT))
        chunks[idx][1] = new + ['']

    out = list(pre)
    for idx in order:
        out.append(chunks[idx][0])
        out += chunks[idx][1]
    merged = '\n'.join(out)
    if not merged.endswith('\n'):
        merged += '\n'

    if verbose and report:
        print('  battle chunks translated: %d / %d' % (len(report), len(order)))
        for idx, used, slack in sorted(report):
            mark = '!!' if slack < 0 else ('~ ' if slack < 50 else '  ')
            print('   %s chunk %2d  %5d / %d bytes   slack %5d' % (mark, idx, used, SCRIPT_SLOT, slack))
    return merged, problems


# ---------------------------------------------------------------- script side

def load_script_tl():
    """tl/script/*.tsv -> {japanese: english}.  Format: JP<TAB>EN, # comments ignored."""
    pairs, dupes = {}, []
    if not os.path.isdir(TLS):
        return pairs, dupes
    for fn in sorted(os.listdir(TLS)):
        if not fn.endswith('.tsv'):
            continue
        for n, line in enumerate(read(os.path.join(TLS, fn)).split('\n'), 1):
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('\t')
            if parts and re.fullmatch(r'\d+', parts[0]):
                parts = parts[1:]          # tolerate the count column from script_unique.txt
            if len(parts) < 2:
                dupes.append('%s:%d: no tab separator' % (fn, n))
                continue
            jp, en = parts[0], parts[1]
            if jp in pairs and pairs[jp] != en:
                dupes.append('%s:%d: conflicting translation for the same source line' % (fn, n))
            pairs[jp] = en
    return pairs, dupes


def merge_script(verbose=True):
    src_path = os.path.join(DUMPS, 'script_dump.txt')
    if not os.path.exists(src_path):
        return None, ['dumps/script_dump.txt missing — run `refresh` first']
    pairs, problems = load_script_tl()
    if not pairs:
        return read(src_path), problems

    text = read(src_path)
    out, hits = [], 0
    for line in text.split('\n'):
        if is_structural(line):
            out.append(line)
            continue
        if line in pairs:
            out.append(pairs[line]); hits += 1
        elif line.endswith('{FFFF}') and line[:-6] in pairs:
            # script_unique.txt keys omit the {FFFF} terminator the dump line carries
            en = pairs[line[:-6]]
            out.append(en if en.endswith('{FFFF}') else en + '{FFFF}')
            hits += 1
        else:
            out.append(line)
    merged = '\n'.join(out)

    # bank budget check
    banks = {}
    cur = None
    for line in merged.split('\n'):
        m = re.match(r'=== BANK (\d+)', line)
        if m:
            cur = int(m.group(1)); banks[cur] = 0; continue
        if cur is not None and not is_structural(line):
            banks[cur] += cost(line)
    for b, used in sorted(banks.items()):
        if used > BANK:
            problems.append('bank %d: %d bytes, %d over the 0x%X limit' % (b, used, used - BANK, BANK))

    problems += validate_body([l for l in merged.split('\n')], 'script', jp_ok=True)
    if verbose:
        print('  script lines replaced: %d  (unique forms: %d)' % (hits, len(pairs)))
        unused = [jp for jp in pairs if jp not in text and jp + '{FFFF}' not in text]
        if unused:
            print('  !! %d translated source lines never matched the dump:' % len(unused))
            for jp in unused[:5]:
                print('     %s' % jp[:60])
    return merged, problems


# ---------------------------------------------------------------- commands

def run(cmd):
    print('  $ ' + ' '.join(os.path.basename(c) if c.endswith('.py') else c for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    for stream in (r.stdout, r.stderr):
        for line in stream.rstrip().split('\n'):
            if line.strip():
                print('    ' + line)
    return r.returncode == 0


def cmd_refresh():
    ok = True
    for binary, tool, out in (('SCRIPT.BIN', 'riotscript.py', 'script_dump.txt'),
                              ('HEXMAP.BIN', 'riotbattle.py', 'battle_dump.txt')):
        src = os.path.join(ORIG, binary)
        if not os.path.exists(src):
            print('  -- original/%s not present, skipping' % binary); continue
        ok &= run([sys.executable, os.path.join(TOOLS, tool), 'dump', src,
                   os.path.join(DUMPS, out)])
    return ok


def cmd_check():
    print('BATTLE')
    _, pb = merge_battle()
    print('SCRIPT')
    _, ps = merge_script()
    problems = pb + ps
    if problems:
        print('\nPROBLEMS (%d):' % len(problems))
        for p in problems:
            print('  !! ' + p)
        return False
    print('\nAll checks passed.')
    return True


def cmd_merge():
    print('BATTLE')
    mb, pb = merge_battle()
    print('SCRIPT')
    ms, ps = merge_script()
    problems = [p for p in pb + ps if 'missing' not in p]
    hard = [p for p in problems if 'OVER' in p or 'over the' in p or 'illegal' in p or 'tag stream' in p]
    for p in problems:
        print('  !! ' + p)
    if hard:
        print('\nRefusing to write: fix the errors above first.')
        return False
    if mb:
        write(os.path.join(BUILD, 'battle_dump_merged.txt'), mb)
        print('  -> build/battle_dump_merged.txt')
    if ms:
        write(os.path.join(BUILD, 'script_dump_merged.txt'), ms)
        print('  -> build/script_dump_merged.txt')
    return True


def cmd_build():
    if not cmd_merge():
        return False
    ok = True
    jobs = (('HEXMAP.BIN', 'riotbattle.py', 'battle_dump_merged.txt'),
            ('SCRIPT.BIN', 'riotscript.py', 'script_dump_merged.txt'))
    for binary, tool, merged in jobs:
        src = os.path.join(ORIG, binary)
        dump = os.path.join(BUILD, merged)
        if not (os.path.exists(src) and os.path.exists(dump)):
            print('  -- skipping %s (original or merged dump missing)' % binary)
            continue
        out = os.path.join(BUILD, binary)
        ok &= run([sys.executable, os.path.join(TOOLS, tool), 'insert', src, dump, out])
    if os.path.exists(os.path.join(BUILD, 'HEXMAP.BIN')):
        ok &= run([sys.executable, os.path.join(TOOLS, 'riotbattle.py'), 'checkedit',
                   os.path.join(ORIG, 'HEXMAP.BIN'), os.path.join(BUILD, 'HEXMAP.BIN')])
    return ok


def cmd_status():
    src = os.path.join(DUMPS, 'battle_dump.txt')
    if os.path.exists(src):
        _, chunks, order = split_battle(read(src))
        tl = load_battle_tl()
        done_j = tot_j = 0
        print('BATTLE — %d / %d chunks' % (len(tl), len(order)))
        for idx in order:
            body = ''.join(l for l in chunks[idx][1] if not is_structural(l))
            ja = len(re.sub(r'\{[^}]*\}', '', body))
            tot_j += ja
            if idx in tl:
                done_j += ja
                used = cost(''.join(l for l in tl[idx] if not is_structural(l)))
                print('   [x] chunk %2d  %5d JP chars  ->  %5d / %d bytes, slack %d'
                      % (idx, ja, used, SCRIPT_SLOT, SCRIPT_SLOT - used))
        print('   %d / %d Japanese characters translated (%.1f%%)'
              % (done_j, tot_j, 100.0 * done_j / tot_j if tot_j else 0))
    uni = os.path.join(DUMPS, 'script_unique.txt')
    if os.path.exists(uni):
        pairs, _ = load_script_tl()
        rows = [l for l in read(uni).split('\n') if l.strip() and not l.startswith('#')]
        total = weighted = done = wdone = 0
        for r in rows:
            p = r.split('\t')
            if len(p) < 2:
                continue
            c = int(p[0]); total += 1; weighted += c
            if p[1] in pairs:
                done += 1; wdone += c
        print('SCRIPT — %d / %d unique lines (%d / %d message instances, %.1f%%)'
              % (done, total, wdone, weighted, 100.0 * wdone / weighted if weighted else 0))
    return True


def main(argv):
    cmds = {'status': cmd_status, 'check': cmd_check, 'merge': cmd_merge,
            'build': cmd_build, 'refresh': cmd_refresh}
    if len(argv) < 2 or argv[1] not in cmds and argv[1] != 'all':
        print(__doc__)
        return 2
    if argv[1] == 'all':
        return 0 if (cmd_check() and cmd_build()) else 1
    return 0 if cmds[argv[1]]() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
