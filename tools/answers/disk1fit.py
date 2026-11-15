#!/usr/bin/env python3
"""Would the CD's banshee1: file set fit on an 880 KB FFS floppy?

Counts FFS blocks (header + data + extension blocks; dirs = 1 block) for the
retail disk-1 file set, then substitutes the CD's bans.exe / picture.exe.

    python disk1fit.py <retail disk1 .adf> <cd bans.exe> <cd picture.exe> [--exclude NAME ...]

--exclude drops entries (ADF path, e.g. foo or dir/foo) that do not belong to the
retail set.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adfdates import Adf


def blocks(size):
    n = math.ceil(size / 512)
    return 1 + n + max(0, math.ceil((n - 72) / 72))


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('adf'); ap.add_argument('bans'); ap.add_argument('picture')
    ap.add_argument('--exclude', action='append', default=[], help='ADF path to leave out (repeatable)')
    a = ap.parse_args()
    skip = {'/' + e.strip('/') for e in a.exclude}
    ents = {p: (t, s) for t, p, s, *_ in Adf(a.adf).walk() if p not in skip}
    total = 1760 - 2 - 1 - 1
    used = lambda e: sum(1 if t == 'D' else blocks(s) for t, s in e.values())
    print('retail set  : used %4d of %d' % (used(ents), total))
    for name, path in (('/bans.exe', a.bans), ('/picture.exe', a.picture)):
        e = dict(ents); e[name] = ('F', os.path.getsize(path))
        print('swap %-12s: used %4d' % (name, used(e)))
    e = dict(ents)
    e['/bans.exe'] = ('F', os.path.getsize(a.bans))
    print('CD bans.exe + floppy picture.exe : used %4d' % used(e))
    e['/picture.exe'] = ('F', os.path.getsize(a.picture))
    print('CD bans.exe + CD picture.exe     : used %4d' % used(e))


if __name__ == '__main__':
    main()
