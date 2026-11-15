#!/usr/bin/env python3
"""Extract the movement program graph of every enemy type from the unpacked
level files into one JSON file (per level: type -> definition offset, flags,
spawn count, reachable VM instructions, children spawned, spawned_by).

    python vmextract.py --levels <dir with level1f..level4f,bossf> <out.json>

Level keys: L1..L4 = level1f..level4f, LB = bossf.
"""
import struct, sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scriptdis import Dis

LEVELS = {'L1': 'level1f', 'L2': 'level2f', 'L3': 'level3f', 'L4': 'level4f', 'LB': 'bossf'}


def load(lv, levels_dir):
    d = open(os.path.join(levels_dir, LEVELS[lv]), 'rb').read()
    L = lambda o: struct.unpack('>I', d[o:o + 4])[0]
    return d, L(0xe), L(0x12), L(0x1c)


class Level:
    def __init__(self, lv, levels_dir):
        self.lv = lv
        self.d, self.TT, self.SC, self.SP = load(lv, levels_dir)
        self.dis = Dis(self.d, self.SC)
        self.cache = {}

    def S(self, o):
        return struct.unpack('>h', self.d[o:o + 2])[0]

    def I(self, o):
        return struct.unpack('>I', self.d[o:o + 4])[0]

    def tdef(self, t):
        return self.I(self.TT + t)

    def spawns(self):
        o = self.SP; r = []
        while self.S(o) >= 0:
            r.append(dict(trig=self.S(o), x=self.S(o + 2), y=self.S(o + 4), t=self.S(o + 6), hp=self.S(o + 8), drop=self.S(o + 10)))
            o += 12
        return r

    def ins(self, o):
        if o not in self.cache:
            self.dis.multi = False
            try:
                txt, p, stop = self.dis.one(o)
            except Exception as ex:
                txt, p, stop = 'ERR %s' % ex, None, True
            self.cache[o] = (txt, p, stop)
        return self.cache[o]

    def graph(self, start, maxn=3000):
        seen = {}; todo = [start]; self.ends = set()
        while todo and len(seen) < maxn:
            o = todo.pop()
            while o is not None and o not in seen and 0 <= o < len(self.d) - 2:
                txt, p, stop = self.ins(o)
                seen[o] = txt
                if p is not None: self.ends.add(p)
                for m in re.finditer(r'->([0-9a-f]+)', txt):
                    t = int(m.group(1), 16)
                    if txt.startswith('SETPROG') and not txt.startswith('SETPROG 12 '):
                        continue
                    todo.append(t)
                if p is None or stop:
                    break
                o = p
        return dict(sorted(seen.items()))

    def children(self, g):
        ch = set()
        for txt in g.values():
            m = re.match(r'SPAWN (-?\d+) ', txt)
            if m: ch.add(int(m.group(1)))
            m = re.match(r'SPAWNREL \S+ \S+ -?\d+ -?\d+ (-?\d+) ', txt)
            if m: ch.add(int(m.group(1)))
        return {c for c in ch if 0 <= c < 0x1000 and c % 4 == 0}

    def types(self):
        sp = self.spawns()
        cnt = collections.Counter(s['t'] for s in sp)
        allt = []; t = 0
        while self.TT + t + 4 <= self.SC and t < 0x1000:
            td = self.I(self.TT + t)
            if 0 < td < len(self.d) and self.SC <= td: allt.append(t)
            t += 4
        out = {}; todo = list(cnt) + allt; spawned_by = collections.defaultdict(set)
        while todo:
            t = todo.pop()
            if t in out: continue
            try:
                td = self.tdef(t)
            except struct.error:
                continue
            if not (0 < td < len(self.d)): continue
            g = self.graph(td + 12); ends = sorted(self.ends)
            ch = self.children(g)
            out[t] = dict(t=t, td=td, flags=self.S(td + 2) & 0xffff, w7e=self.S(td + 8), n_spawn=cnt.get(t, 0), prog=g, ends=ends, children=sorted(ch))
            for c in ch:
                spawned_by[c].add(t)
                if c not in out: todo.append(c)
        for t in out: out[t]['spawned_by'] = sorted(spawned_by.get(t, ()))
        return out, sp


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--levels', required=True, help='directory with the unpacked level files')
    ap.add_argument('out', help='output JSON path')
    a = ap.parse_args()
    res = {}
    stats = collections.Counter()
    for lv in LEVELS:
        L = Level(lv, a.levels)
        ty, sp = L.types()
        res[lv] = {'%x' % t: dict(v, prog={'%05x' % k: s for k, s in v['prog'].items()}) for t, v in ty.items()}
        for v in ty.values():
            for s in v['prog'].values():
                stats[s.split()[0]] += 1
        print(lv, 'types', len(ty), 'spawns', len(sp))
    json.dump(res, open(a.out, 'w'), indent=0)
    print(stats.most_common())
