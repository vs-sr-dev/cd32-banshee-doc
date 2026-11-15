#!/usr/bin/env python3
"""List every reference to the RNG state (A5+0x3e0..0x3e5) in bans.exe hunk 0,
assigned to the VM opcode / sub-op 20.xx handler it lies in.

    python rng_xref.py <bans.exe>          (needs capstone)

Hunk 0 is disassembled linearly (capstone, skipping a word where it fails), so
data inside the code hunk can produce the odd stray line.
"""
import os, re, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bansexe import BansExe
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN

SUBOP_TABLE = 0x230dea   # 127 x BRA.W
OPCODE_TABLE = 0x22f8d2  # 45 x BRA.W


def linear(x, hunk=0):
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    d = x.hunk_image(hunk); base = x.bases[hunk]
    pos = 0
    while pos < len(d):
        got = False
        for ins in md.disasm(d[pos:], base + pos):
            yield ins.address, ins.mnemonic, ins.op_str
            pos = ins.address + ins.size - base; got = True
        if not got:
            pos += 2


def table(x, base, n):
    out = []
    for k in range(n):
        op, disp = struct.unpack('>Hh', x.read(base + 4 * k, 4))
        if op == 0x6000:
            out.append((base + 4 * k + 2 + disp, 4 * k))
    return sorted(out)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    a = ap.parse_args()
    x = BansExe(a.exe)
    SUB = table(x, SUBOP_TABLE, 127); OPS = table(x, OPCODE_TABLE, 45)

    def owner(addr):
        best = best2 = None
        for t, k in SUB:
            if t <= addr: best = ('20.%x' % k, t)
        for t, k in OPS:
            if t <= addr: best2 = ('op %02x' % k, t)
        c = [v for v in (best, best2) if v]
        return max(c, key=lambda v: v[1]) if c else ('-', 0)

    pat = re.compile(r'\$3e([0-5])\((a\d)\)')
    for addr, op, ar in linear(x):
        m = pat.search(ar)
        if not m: continue
        w = ar.endswith('$3e%s(%s)' % (m.group(1), m.group(2))) and not op.startswith(('tst', 'cmp'))
        o = owner(addr)
        print('%06x hunk0+%05X  %-5s %-8s %-28s %s @%06x' % (addr, addr - x.bases[0], 'WRITE' if w else 'read', op, ar, o[0], o[1]))


if __name__ == '__main__':
    main()
