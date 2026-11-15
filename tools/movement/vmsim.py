#!/usr/bin/env python3
"""Simulate one enemy type's movement script (VM opcodes and the sub-ops that
move the object) and print its path: tick, x, y relative to the scroll.

    python vmsim.py --exe <bans.exe> --levels <dir> L1 1b4 [--ticks 600] [--seed 1]

Level keys: L1..L4 = level1f..level4f, LB = bossf; type in hex. The sine table
and the direction tables used by some sub-ops are read from bans.exe.
"""
import math, random, re, struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vmextract import Level

SIN_TAB = 0x23ce0e      # 1024 signed words, hunk1
RANDDIR_TAB = 0x2313c4  # 16 x (dx, dy) words, sub-op 0x30
HELI_TAB = 0x232f62     # 9 x (dx, dy) longs, sub-op 0xe0
WALK_TAB = (0x235918, 0x235930)   # 3 x (dx, dy) words per side, sub-op 0x158
SIN = RANDDIR = HELI = WALK = None


def load_tables(exe_path):
    global SIN, RANDDIR, HELI, WALK
    from bansexe import BansExe
    x = BansExe(exe_path)
    SIN = struct.unpack('>1024h', x.read(SIN_TAB, 2048))
    r = struct.unpack('>32h', x.read(RANDDIR_TAB, 64)); RANDDIR = list(zip(r[::2], r[1::2]))
    h = struct.unpack('>18i', x.read(HELI_TAB, 72)); HELI = list(zip(h[::2], h[1::2]))
    WALK = {}
    for side, a in enumerate(WALK_TAB):
        w = struct.unpack('>6h', x.read(a, 12)); WALK[side] = list(zip(w[::2], w[1::2]))


def s16(v):
    v &= 0xffff
    return v - 0x10000 if v >= 0x8000 else v


class Sim:
    def __init__(self, lv, t, x=192, y=None, player=(192, 40), seed=1, maxt=600, scroll0=1000, scroll_speed=1):
        self.L = lv
        self.t = t
        self.td = self.L.tdef(t)
        self.f = {}
        self.g = {}
        self.sc = scroll0
        self.ss = scroll_speed
        self.x, self.y = float(x), float(scroll0 + 278 if y is None else y)
        self.vx = self.vy = 0
        self.player = player
        self.rng = random.Random(seed)
        self.maxt = maxt
        self.wob = dict(ax=0, ay=0, dax=0, day=0, px=0x200, py=0, sx=0, sy=0)
        self.pc = self.td + 12
        self.timer = 0
        self.delay = 0
        self.tick = 0
        self.out = []
        self.dead = False
        self.note = set()
        self.seen_ops = []

    def P(self):
        if callable(self.player):
            return self.player(self.tick)
        return self.player[0], self.sc + self.player[1]

    def val(self, s):
        if s.startswith('#'):
            return int(s[1:])
        if s.startswith('obj.'):
            k = int(s[4:], 16)
            if k == 0x10: return int(self.x)
            if k == 0x14: return int(self.y)
            if k == 0x36: return s16(self.vx)
            if k == 0x3a: return s16(self.vy)
            if k == 0x34: return s16(self.vx >> 16)
            if k == 0x38: return s16(self.vy >> 16)
            return self.f.get(k, 0)
        if s.startswith('tgt.'):
            k = int(s[4:], 16)
            px, py = self.P()
            return {0x10: px, 0x14: int(py)}.get(k, 0)
        if s.startswith('glob.'):
            k = int(s[5:], 16)
            if k in (0x3e0, 0x3e2, 0x3e4):
                return self.rng.randrange(256) if k == 0x3e4 else self.rng.randrange(-32768, 32767)
            if k == 0x3c4:
                return self.g.get(k, 128)
            return self.g.get(k, 0)
        return 0

    def setf(self, s, v):
        if s.startswith('obj.'):
            k = int(s[4:], 16)
            if k == 0x10: self.x = float(s16(v)); return
            if k == 0x14: self.y = float(v); return
            if k in (0x34, 0x36, 0x38, 0x3a):
                cur = self.vx if k < 0x38 else self.vy
                cur &= 0xffffffff
                cur = ((v & 0xffff) << 16 | cur & 0xffff) if k in (0x34, 0x38) else (cur & 0xffff0000 | v & 0xffff)
                cur = cur - (1 << 32) if cur >= 1 << 31 else cur
                if k < 0x38: self.vx = cur
                else: self.vy = cur
                return
            self.f[k] = s16(v)
        elif s.startswith('glob.'):
            self.g[int(s[5:], 16)] = s16(v)

    def step(self):
        self.x += self.vx / 256.0
        self.y += self.vy / 256.0

    def timed(self, n, body):
        # VM semantics: first tick executes body and loads timer=n; then body each tick until timer hits 0 (incl. last)
        if self.timer == 0:
            body(); n = n
            if n == 0:
                return True
            self.timer = n
            return False
        self.timer -= 1
        body()
        if self.timer == 0:
            return True
        return False

    def emit(self):
        w = self.wob
        w['ax'] += w['dax']; w['ay'] += w['day']
        dx = dy = 0.0
        if w['ax']:
            w['px'] = (w['px'] + w['sx']) & 0x7fe
            dx = SIN[w['px'] >> 1] * w['ax'] / 65536.0
        if w['ay']:
            w['py'] = (w['py'] + w['sy']) & 0x7fe
            dy = SIN[w['py'] >> 1] * w['ay'] / 65536.0
        self.out.append((self.tick, self.x, self.y, self.x + dx, self.y + dy, self.sc))

    def run(self):
        while self.tick < self.maxt and not self.dead:
            if self.delay > 0:
                self.delay -= 1
            else:
                self.vm()
            if self.dead: break
            self.emit()
            self.tick += 1
            self.sc = self.ss(self.tick) if callable(self.ss) else self.sc + self.ss
            if self.y < self.sc - 40 or self.y > self.sc + 600 or self.x < -300 or self.x > 700:
                self.note.add('offscreen'); break
        return self.out

    def vm(self):
        guard = 0
        while True:
            guard += 1
            if guard > 400:
                self.dead = True; self.note.add('loop'); return
            txt, nxt, stop = self.L.ins(self.pc)
            a = txt.split()
            op = a[0]
            self.seen_ops.append(op)
            T = [int(m, 16) for m in re.findall(r'->([0-9a-f]+)', txt)]
            if op == 'MOVE':
                vx, vy, n = int(a[1]), int(a[2]), self.val(a[3])
                def b(): self.vx, self.vy = vx, vy; self.step()
                if self.timed(n, b) or False: self.pc = nxt
                if n == 9999: pass
                return
            if op == 'ACCELV':
                ax, ay, vx, vy, n = int(a[1]), int(a[2]), int(a[3]), int(a[4]), self.val(a[5])
                if self.timer == 0:
                    self.vx, self.vy = vx, vy
                def b(): self.step(); self.vx += ax; self.vy += ay
                if self.timed(n, b): self.pc = nxt
                return
            if op == 'ACCEL':
                ax, ay, n = int(a[1]), int(a[2]), self.val(a[3])
                def b(): self.step(); self.vx += ax; self.vy += ay
                if self.timed(n, b): self.pc = nxt
                return
            if op == 'MOVE70':
                fx, fy, n = int(a[1]), int(a[2]), self.val(a[3])
                def b(): self.step(); self.vx = int(self.vx * fx) >> 8; self.vy = int(self.vy * fy) >> 8
                if self.timed(n, b): self.pc = nxt
                return
            if op == 'WAIT':
                n = self.val(a[1])
                if self.timed(n, self.step): self.pc = nxt
                return
            if op == 'HOMING':
                ine, st, n = int(a[1]), int(a[2]), int(a[3])
                def b():
                    if self.timer & 1 or n == 0 or self.timer == 0:
                        px, py = self.P()
                        dx, dy = px - self.x, py - self.y
                        m = max(abs(dx), abs(dy)) + min(abs(dx), abs(dy)) / 2 or 1
                        self.vx = int(self.vx * ine) >> 12; self.vy = int(self.vy * ine) >> 12
                        self.vx += int(st * dx / m); self.vy += int(st * dy / m) + 16
                    self.step()
                if self.timed(n, b): self.pc = nxt
                return
            if op == 'DELAY':
                n = int(a[1]); self.pc = nxt
                if n >= 9999: self.dead = True; self.note.add('rest'); return
                self.delay = n
                return
            if op == 'END':
                self.dead = True; self.note.add('end'); return
            if op == 'GOTO':
                self.pc = T[0]; continue
            if op == 'LOOP':
                k = a[1]; c = self.val(k) - 1
                if c == 0:
                    self.setf(k, 0); self.pc = nxt
                elif c > 0:
                    self.setf(k, c); self.pc = T[0]
                else:
                    self.setf(k, self.val(a[3])); self.pc = T[0]
                continue
            if op in ('IFEQ', 'IFNE', 'IFLT', 'IFGT'):
                v, f = self.val(a[1]), self.val(a[2])
                c = {'IFEQ': v == f, 'IFNE': v != f, 'IFLT': v < f, 'IFGT': v > f}[op]
                self.pc = T[0] if c else nxt
                continue
            if op in ('SET', 'ADD', 'SUB') and len(a) == 3:
                v = self.val(a[1]); cur = self.val(a[2])
                self.setf(a[2], v if op == 'SET' else cur + v if op == 'ADD' else cur - v)
                self.pc = nxt; continue
            if op == 'SETPROG':
                if a[1] == '12':
                    self.pc = T[0]; self.timer = 0; continue
                self.pc = nxt; continue
            if op == 'WOBBLE':
                v = list(map(int, a[1:]))
                w = self.wob; w['sx'], w['sy'], w['dax'], w['day'], w['px'], w['py'], w['ax'], w['ay'] = v
                self.pc = nxt; continue
            if op == 'WOBBLE2':
                v = list(map(int, a[1:]))
                w = self.wob; w['sx'], w['sy'], w['dax'], w['day'] = v
                self.pc = nxt; continue
            if op.startswith('SUB.'):
                sub = int(op[4:].split('/')[0], 16)
                if sub == 0x1b4:
                    r = self.rng.randrange(256)
                    self.pc = T[1] if r < 0x30 else T[2] if r >= 0xd0 else T[0]; self.timer = 0
                    continue
                if sub == 0x1b8:
                    d = int(self.x) - self.P()[0]
                    self.pc = T[1] if d >= 30 else T[2] if d < -30 else T[0]; self.timer = 0
                    continue
                if sub == 0x18c:
                    self.vx = (self.vx * 266) >> 8; self.step()
                    self.vy = ((self.vy - 8) * 266) >> 8
                    return
                if sub == 0x30:
                    self.vx, self.vy = RANDDIR[int(self.y) & 15]; self.pc = nxt; continue
                if sub == 0x64:
                    c = self.f.get(0x4c, 0) - 1; self.f[0x4c] = c
                    if c == 0: self.pc = nxt; return
                    if self.rng.randrange(4096) > 0xfe0: self.f[0x50] = -self.f.get(0x50, 0)
                    ang = self.f.get(0x4e, 0) & 0x7ff
                    self.f[0x4e] = self.f.get(0x4e, 0) + self.f.get(0x50, 0)
                    self.x += SIN[((ang + 0x200) & 0x7ff) >> 1] * 32 / 65536.0
                    self.y += SIN[ang >> 1] * 32 / 65536.0
                    return
                if sub == 0x158:
                    k = self.f.get(0x4a, 0x66)
                    side = 0 if k < 0x6c else 1
                    st = self.f.get(0x99, 0); self.f[0x99] = (st + 1) % 3
                    dx, dy = WALK[side][st]; self.x += dx; self.y += dy
                    self.pc = nxt; continue
                if sub == 0xe0:
                    h = self.f.get(0x4c, 0xee)
                    if h >= 0xf3: h -= 9
                    c54 = self.f.get(0x54, 15)
                    i = max(0, min(8, h - 0xea))
                    self.vx -= self.vx >> 4; self.vy -= self.vy >> 2; self.vy += 32
                    self.vx += HELI[i][0]; self.vy += HELI[i][1]
                    self.step()
                    tog = self.f.get('tog', 0) ^ 1; self.f['tog'] = tog
                    if tog:
                        px, py = self.P()
                        d = int(round(math.atan2(-(px - self.x), -(py - self.y)) / (2 * math.pi / 16))) & 15 if self.tick >= 10 else 0
                        k = (d + 4) & 15
                        want = 0xea + (k if k < 9 else 4)
                        if want != h:
                            c54 = 7; h += 1 if want > h else -1
                        else:
                            c54 -= 1
                    else:
                        c54 -= 1
                    if c54 <= 0: c54 = 10; self.note.add('heli_fire')
                    self.f[0x4c] = h; self.f[0x54] = c54
                    return
                if sub == 0x0c:
                    self.note.add('aimvel'); self.pc = nxt; continue
                if sub in (0xc0, 0xc4, 0xf4, 0x11c):
                    self.note.add('bulletfly'); self.dead = True; return
                if 'SUB.%x' % sub in ('SUB.f0', 'SUB.134', 'SUB.140', 'SUB.144', 'SUB.164', 'SUB.174', 'SUB.178', 'SUB.184', 'SUB.1d0', 'SUB.e4', 'SUB.104', 'SUB.130', 'SUB.13c', 'SUB.168', 'SUB.1d8', 'SUB.1f0'):
                    self.note.add('special:' + op); self.dead = True; return
                self.pc = nxt
                if stop: self.dead = True; self.note.add('stop:' + op); return
                continue
            if op == 'FRAME':
                self.pc = nxt
                if stop: self.dead = True; return
                if 'delay=#' in txt and int(re.search(r'delay=#(-?\d+)', txt).group(1)) > 0:
                    return
                continue
            if nxt is None or stop:
                self.dead = True; self.note.add('stop:' + op); return
            self.pc = nxt


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--exe', required=True, help='bans.exe')
    ap.add_argument('--levels', required=True, help='directory with the unpacked level files')
    ap.add_argument('level', help='L1..L4 or LB')
    ap.add_argument('type', help='enemy type (hex)')
    ap.add_argument('--ticks', type=int, default=600)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--every', type=int, default=5, help='print every Nth tick')
    a = ap.parse_args()
    load_tables(a.exe)
    s = Sim(Level(a.level, a.levels), int(a.type, 16), seed=a.seed, maxt=a.ticks)
    o = s.run()
    for r in o[::a.every]:
        print('%4d x=%7.1f ry=%7.1f' % (r[0], r[1], r[2] - r[5]))
    print(s.note)
