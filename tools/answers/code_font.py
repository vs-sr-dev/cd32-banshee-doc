#!/usr/bin/env python3
"""Menu/hall-of-fame font of bans.exe: decrunch the embedded RNC stream
(hunk1+0x602), read the glyph table at hunk1+0x000 (16-byte records, word +0 =
character code, terminated by a negative word), print it, and optionally render
selected glyphs to a PNG.

    python code_font.py <bans.exe> [--png out.png] [codes...]    (PNG needs Pillow)

Glyph record: +0 code, +4 long byte offset into the 640x81x3 interleaved bitmap
(row = 240 bytes), +0xa word 1 = glyph is 2 words wide, +0xc advance in pixels.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rnc
from relocs import parse


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('--png', help='output PNG path')
    ap.add_argument('codes', nargs='*', help='character codes to render (default: accented/special set)')
    a = ap.parse_args()
    d = open(a.exe, 'rb').read()
    H1 = parse(d)[0][1][2]                      # file offset of hunk 1 body
    bmp = rnc.unpack(d[H1 + 0x602:])
    assert len(bmp) == 640 * 81 * 3 // 8
    glyphs = []
    o = H1
    while True:
        code, = struct.unpack('>h', d[o:o + 2])
        if code < 0: break
        off, = struct.unpack('>I', d[o + 2:o + 6]); wide, adv = struct.unpack('>hh', d[o + 10:o + 14])
        glyphs.append((code, off, wide, adv, o - H1)); o += 16
    print('%d glyphs, table hunk1+0x000..+0x%X (file 0x%06X)' % (len(glyphs), o - H1, H1))
    for code, off, wide, adv, h in glyphs:
        y, xb = divmod(off, 240)
        print('  hunk1+0x%03X code 0x%02X  x=%3d y=%2d adv=%2d%s' % (h, code, xb * 8, y, adv, ' (2 words)' if wide else ''))
    if a.png:
        from PIL import Image
        want = [int(v, 0) for v in a.codes] or [0x22, 0x9c, 0x24, 0x2b, 0x7e, 0x3d, 0x81, 0x82, 0x84, 0x85, 0x8a, 0x8b, 0x94, 0xe1]
        pal = [(0, 0, 0), (255, 255, 255), (170, 170, 170), (85, 85, 85), (200, 200, 120), (120, 120, 200), (200, 120, 120), (120, 200, 120)]
        cell = 34; im = Image.new('RGB', (cell * len(want), 27), (40, 40, 40)); px = im.load()
        byc = {g[0]: g for g in glyphs}
        for i, c in enumerate(want):
            code, off, wide, adv, h = byc[c]
            y0, xb = divmod(off, 240)
            for yy in range(27):
                for xx in range(min(adv + 2, 32)):
                    x = xb * 8 + xx; v = 0
                    for p in range(3):
                        v |= ((bmp[(y0 + yy) * 240 + p * 80 + (x >> 3)] >> (7 - (x & 7))) & 1) << p
                    px[i * cell + xx, yy] = pal[v]
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(a.png)
        print('rendered', ' '.join('0x%02X' % c for c in want), '->', a.png)


if __name__ == '__main__':
    main()
