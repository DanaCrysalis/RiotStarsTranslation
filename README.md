# Riot Stars — English fan translation

Riot Stars (Hect, PS1, SLPS-00829, 1997). Text is extracted, translated in batches, and reassembled
into the original binaries by `tools/assemble.py`.

**The point of this layout:** anything translated so far can be built and played at any moment.
Untranslated chunks and lines fall through to the original Japanese.

## First-time setup

Put the two untouched files from the disc image in `original/`:

```
original/SCRIPT.BIN     44 banks × 0xA000   main script
original/HEXMAP.BIN     46 chunks × 0x2A800 battle maps + battle script
```

Then generate the pristine dumps:

```
python3 tools/assemble.py refresh
```

That writes `dumps/script_dump.txt` and `dumps/battle_dump.txt`. Do not edit either by hand — they
are the reference the merge diffs against, and `refresh` will overwrite them.

## Everyday commands

```
python3 tools/assemble.py status     what is done, and how much slack each finished chunk has
python3 tools/assemble.py check      validate translated files; builds nothing
python3 tools/assemble.py merge      splice finished work into build/*_dump_merged.txt
python3 tools/assemble.py build      merge, then reinsert into build/SCRIPT.BIN and build/HEXMAP.BIN
python3 tools/assemble.py all        check + build + riotbattle checkedit
```

Then rebuild the disc image with the two files in `build/` and run it.

## Where translations go

**Battle script — one file per chunk:** `tl/battle/chunk_000.txt` … `chunk_043.txt`.
Each is that chunk copied out of `battle_dump.txt` — the `=== CHUNK n @ …` header, every body line
in the same order and the same count, then `{PAD n}` — with only the readable text changed.

**Main script — batches of unique lines:** `tl/script/batch_001.tsv` … Tab-separated:

```
<count>	<japanese source message>	<english replacement>
```

The Japanese column is the lookup key and must be copied byte-for-byte out of
`script_unique.txt`, tags included. The count column is optional and ignored. `#` starts a comment.
One translated line replaces every occurrence — the script is 82% duplicated, so 47 lines already
cover 14.6% of all message instances.

## Constraints that will bite

- Battle chunks have a hard **8,192-byte slot** each. The inserter fails rather than overflow;
  anything at or after `+0x27000` is read at a fixed offset and must not move.
- Text must be **full-width Latin only** — the font hook maps those codepoints, ASCII is not mapped
  and renders as nothing.
- The battle box is **24 columns × 4 rows**. The main-script box has not been widened yet.
- **Chunk 43 does not fit** at any reasonable translation density (1.23 English characters allowed
  per Japanese character). It needs a repoint, borrowed space, or an abridged script. Decide before
  investing twenty sessions.

See `translation_prompt.md` §0 for the session schedule and §3 for the full format rules, and
`glossary.md` for every fixed term.

## Status

| | Done | Total |
|---|---|---|
| Battle chunks | 1 (chunk 0) | 43 |
| Battle Japanese characters | 1,914 | 42,763 (4.5%) |
| Script unique lines | 47 | 1,430 |
| Script message instances | 1,155 | 7,931 (14.6%) |

`assemble.py status` prints the current figures.
