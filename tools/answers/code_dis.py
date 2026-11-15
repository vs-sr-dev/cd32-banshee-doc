#!/usr/bin/env python3
"""Disassemble relocated bans.exe at RUNTIME addresses (Ghidra-style bases:
hunk0 @0x21f000, hunk3 @0x290f64, ...). Each line also shows hunkN+off.
Branch targets are recomputed from the encoding (as in dis68k.py).

    python code_dis.py <bans.exe> <runtime_addr> <length>      (needs capstone)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bansexe import BansExe
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN

s16 = lambda v: v - 65536 if v > 32767 else v


def branch_target(addr, b):   # same as dis68k.py (which runs main() on import)
    op = int.from_bytes(b[0:2], 'big')
    if op >> 12 == 6:
        disp = op & 0xff
        if disp == 0: return addr + 2 + s16(int.from_bytes(b[2:4], 'big'))
        if disp == 0xff: return addr + 2 + int.from_bytes(b[2:6], 'big')
        return addr + 2 + (disp - 256 if disp > 127 else disp)
    if (op & 0xf0f8) == 0x50c8: return addr + 2 + s16(int.from_bytes(b[2:4], 'big'))
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('addr')
    ap.add_argument('length')
    a = ap.parse_args()
    x = BansExe(a.exe)
    a0, ln = int(a.addr, 0), int(a.length, 0)
    hn, _ = x.to_hunk(a0)
    base = x.bases[hn]; d = x.hunk_image(hn)
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    pos, end = a0, min(a0 + ln, base + len(d))
    while pos < end:
        got = False
        for ins in md.disasm(d[pos - base:end - base], pos):
            raw = bytes(ins.bytes); ops = ins.op_str
            t = branch_target(ins.address, raw)
            if t is not None: ops = '-> %06x' % t
            print('%06x hunk%d+%05X  %-24s %-8s %s' % (ins.address, hn, ins.address - base, raw.hex(' '), ins.mnemonic, ops))
            pos = ins.address + ins.size; got = True
        if not got:
            print('%06x hunk%d+%05X  %-24s .dc.w' % (pos, hn, pos - base, d[pos - base:pos - base + 2].hex(' '))); pos += 2


if __name__ == '__main__':
    main()
