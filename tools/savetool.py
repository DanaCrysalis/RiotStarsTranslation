#!/usr/bin/env python3
"""Extract main RAM and VRAM from a DuckStation savestate for Riot Stars."""
import zstandard as zstd, sys, struct

def find_zstd(d):
    offs=[]; i=0
    while True:
        j=d.find(bytes.fromhex('28b52ffd'), i)
        if j<0: break
        offs.append(j); i=j+1
    return offs

def load(path):
    raw=open(path,'rb').read()
    best=None
    for off in find_zstd(raw):
        try:
            out=zstd.ZstdDecompressor().stream_reader(memoryview(raw)[off:]).read()
            if best is None or len(out)>len(best[1]):
                best=(off,out)
        except Exception:
            pass
    if best is None:
        raise RuntimeError('no zstd stream')
    return best[1]

def vram_of(blob):
    i=blob.find(b'GPU-VRAM')
    if i<0: raise RuntimeError('no GPU-VRAM tag')
    return blob[i+8:i+8+0x100000]

def ram_base(blob):
    """Calibrate PSX 0x80000000 -> blob offset using a known EXE string."""
    for probe, fileoff in ((b'\\TACTICS\\', 0xe48d4), (b'\\IMDATA\\SCRIPT.BIN;1', None)):
        j=blob.find(probe)
        if j<0: continue
        if fileoff is not None:
            psx=0x80010000+(fileoff-0x800)
            return j-(psx-0x80000000)
    return None

if __name__=='__main__':
    b=load(sys.argv[1])
    print('blob', len(b))
    print('ram_base', hex(ram_base(b) or 0))
    print('vram ok', len(vram_of(b)))
