#!/usr/bin/env python3
"""Pure-Python model of the Banshee (CD32) random number generators.

    python banshee_rng.py          run the self-test
    from banshee_rng import BansheeRNG, PodRNG

Main RNG state: A = glob.3e0, B = glob.3e2, C = byte glob.3e5 (byte glob.3e4 = H
is never written -> 0 from BSS, so the word glob.3e4 equals C).
Stepped once per logic tick (0x22f1b4 = hunk0+0x101B4); inputs: P1.x (A5+0x216)
and P2.y (A5+0x2ac; not P2.x).
"""
M16 = 0xffff


def ror16(v, n): v &= M16; return ((v >> n) | (v << (16 - n))) & M16
def ror8(v, n): v &= 0xff; return ((v >> n) | (v << (8 - n))) & 0xff


class BansheeRNG:
    def __init__(self, a=0, b=0, c=0, h=0):
        self.a, self.b, self.c, self.h = a & M16, b & M16, c & 0xff, h & 0xff

    @classmethod
    def from_words(cls, w3e0, w3e2, w3e4):
        return cls(w3e0, w3e2, w3e4 & 0xff, w3e4 >> 8)

    def words(self):
        return self.a, self.b, (self.h << 8) | self.c

    # --- main step, once per tick (0x22f1ce..0x22f1e4) ---
    def tick(self, p1x, p2y):
        self.b = (self.b + 0x19a3) & M16
        d = (self.b + p1x + p2y) & M16
        self.a = (self.a + d) & M16
        self.c = (self.c - d) & 0xff

    # --- level init (0x22e87a..0x22e88a); w6 = word at levelNf+6 after relocation (bytes 6-7 = high word of a pointer) ---
    def level_init(self, w6):
        self.a = ror16(self.a - w6, 2)
        self.b = (self.b - self.a) & M16

    # --- consumers that modify the state ---
    def spawn_target_2p(self):            # 0x22edc4: spawn with 2 players; sign of A after doubling picks the target
        self.a = (self.a * 2) & M16
        return 'P2' if self.a & 0x8000 else 'P1'

    def sub10(self):                      # 0x23130e (20.10, bullet spread): C += 0x2a, returns word 3e4 - 0x80
        self.c = (self.c + 0x2a) & 0xff
        return ((self.h << 8) | self.c) - 0x80

    def sub_a8(self):                     # 0x232506..0x23252a: returns old B, B = ror5(B)
        old = self.b; self.b = ror16(old, 5); return old

    def mix_1f(self):                     # 0x23289c / 0x23552a (20.1f8, 20.1f4): A = ror5(word@3e1 - 0x4f17)
        w = ((self.a & 0xff) << 8) | (self.b >> 8)
        self.a = ror16(w - 0x4f17, 5); return self.a

    def sub58(self):                      # 0x2350c4 / 0x235296 (20.58, 20.5c): C = ror3(C ^ 0x48)
        self.c = ror8(self.c ^ 0x48, 3); return self.c

    def sub1a0(self):                     # 0x235630: C ^= 0xa7 (H ^= 0)
        self.c ^= 0xa7; return (self.h << 8) | self.c

    def sub1b4(self):                     # 0x23641c: C = ror1(C); <0x30 -> T1, >=0xd0 -> T2, else T0
        self.c = ror8(self.c, 1); v = (self.h << 8) | self.c
        return 1 if v < 0x30 else (2 if v >= 0xd0 else 0)

    APPLY = {0x22edc8: 'spawn_target_2p', 0x23130e: 'sub10', 0x23252a: 'sub_a8', 0x2328a6: 'mix_1f',
             0x235534: 'mix_1f', 0x2350d6: 'sub58', 0x2352a0: 'sub58', 0x235630: 'sub1a0', 0x236422: 'sub1b4'}

    def vm_add(self, field, v):           # 0x22fe92: VM op 18 ADD V glob.3e0 (only case: L1, ADD #4291 glob.3e0)
        if field == 0x3e0: self.a = (self.a + v) & M16

    # --- common reads (no modification) ---
    def coin(self):                       # scripts: IFLT #0 glob.3e2 -> 50%
        return bool(self.b & 0x8000)

    def byte(self):                       # scripts: IFLT/IFGT #n glob.3e4, 20.68, boss directors
        return (self.h << 8) | self.c


class PodRNG:
    """Second generator: pod drift (0x230d3e = hunk0+0x11D3E). State P,Q are words
    inside the CODE hunk at 0x230daa/0x230dac (hunk0+0x11DAA); initial values from
    the file are 0xa743/0x71ae; they are NOT reset at level or game start."""
    def __init__(self, p=0xa743, q=0x71ae):
        self.p, self.q = p & M16, q & M16

    def pod(self, p1x, p2x, x):
        """One pod: returns the (vx, vy) impulse. x = pod screen position (d0)."""
        self.p = (self.p + 0x1376) & M16
        self.q = (self.q + self.p) & M16
        r = lambda v: (((v << 3) | (v >> 13)) & M16)
        vx = (r((self.p + p1x) & M16) & 0x1f) - 0x10
        vy = (r((self.q + p2x) & M16) & 0x1f) + 0x10
        if vx >= 0:
            if x >= 0x120: vx = -vx
        else:
            if x <= 0x60: vx = -vx
        return vx, vy


def weyl_b(n):
    """B after n ticks from level start, when sub-op 20.a8 (ror5 B) does not run: a pure Weyl sequence."""
    return (n * 0x19a3) & M16


if __name__ == '__main__':
    # reference values observed in an emulator run (boot -> start of L1): state at level start = (0,0,0)
    r = BansheeRNG()
    exp = [((144, 66), (6773, 6563, 139)), ((144, 67), (20110, 13126, 114)), ((144, 68), (40011, 19689, 181))]
    for (x, y), w in exp:
        r.tick(x, y); assert r.words() == w, (r.words(), w)
    assert weyl_b(400) == 3760       # B after 400 ticks of L1, identical in 1P/2P/drop-in runs
    print('OK', r.words())
