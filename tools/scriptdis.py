#!/usr/bin/env python3
"""Disassembler for the enemy-script VM stored in RNC-unpacked level files
(level1f..level4f, bossf).

    python scriptdis.py <levelf> [<levelf> ...]     disassemble every spawned type
    python scriptdis.py --reach [--exe bans.exe] <levelf> [<levelf> ...]
                                                    reachability of types, opcodes
                                                    and sub-ops across level files

Level header: +0x0e type table, +0x12 scripts base, +0x1c spawn list (12-byte
records, type word at +6). Script addresses printed are level-file offsets.
--reach walks from the spawn-list roots following jump targets, SPAWN/SPAWNREL
children and sub-op operand types; with --exe the types spawned directly by
sub-op handlers in the 68k code are found by scanning bans.exe (needs capstone).
"""
import os, sys, re, struct, collections

NAMES = {
    0x00: 'FRAME', 0x04: 'MOVE', 0x08: 'ACCELV', 0x0c: 'ACCEL', 0x10: 'SOUNDR', 0x14: 'SET', 0x18: 'ADD', 0x1c: 'SUB',
    0x20: 'SUB', 0x24: 'SOUND', 0x28: 'IFEQ', 0x2c: 'IFNE', 0x30: 'IFLT', 0x34: 'IFGT', 0x38: 'SPAWN', 0x3c: 'SPAWNREL',
    0x40: 'GOTO', 0x44: 'SNDMOD', 0x48: 'EFFECT', 0x4c: 'LOOP', 0x50: 'END', 0x54: 'DELAY', 0x58: 'COND58', 0x5c: 'COND5C',
    0x60: 'ANIMDELAY', 0x64: 'ANIMCYC', 0x68: 'ANIM68', 0x6c: 'ANIM6C', 0x70: 'MOVE70', 0x74: 'POD', 0x78: 'SCORE',
    0x7c: 'WOBBLE', 0x80: 'WOBBLE2', 0x84: 'HOME84', 0x88: 'HOME88', 0x8c: 'EFFECTV', 0x90: 'SETPROG', 0x94: 'HOMING',
    0x98: 'SWITCHRATING', 0x9c: 'OP9C', 0xa0: 'OPA0', 0xa4: 'OPA4', 0xa8: 'OPA8', 0xac: 'TARGET', 0xb0: 'WAIT',
}
# w=word, V=value operand (1 or 2 words), A=address word, T=target (relative to scripts base)
SPEC = {
    0x04: 'wwV', 0x08: 'wwwwV', 0x0c: 'wwV', 0x10: 'www', 0x14: 'VA', 0x18: 'VA', 0x1c: 'VA', 0x24: 'www',
    0x28: 'VAT', 0x2c: 'VAT', 0x30: 'VAT', 0x34: 'VAT', 0x38: 'ww', 0x40: 'T', 0x44: 'wwww', 0x4c: 'ATV',
    0x50: '', 0x54: 'w', 0x58: 'VA', 0x5c: 'VA', 0x60: 'w', 0x64: 'wwAw', 0x68: 'wwAw', 0x6c: 'wwAw', 0x70: 'wwV', 0x84: 'wwwAV', 0x88: 'wwwAV', 0x3c: 'VVwwww', 0x94: 'www', 0x9c: 'www', 0xa4: 'Vww',
    0x74: 'wwwww', 0x78: 'www', 0x7c: 'wwwwwwww', 0x80: 'wwww', 0x8c: 'wwwVV', 0x90: 'wT', 0xa8: '', 0xac: '', 0xa0: 'w',
    0xb0: 'V',
}
SUBSPEC = {0x30: '', 0x34: '', 0x68: 'VVV', 0x20: '', 0x24: '', 0x28: '', 0x2c: '', 0x40: 'VV', 0x44: '', 0x48: '', 0x50: 'T', 0x84: '', 0x88: '', 0x94: '', 0xa4: '', 0xa8: '', 0xb0: '', 0xbc: '', 0xf8: '', 0x12c: 'ww', 0x18: '', 0x4c: '', 0xac: '',
           0x00: 'V', 0x08: 'VV', 0x14: 'T', 0x38: 'VV', 0x60: 'T', 0xe8: 'T', 0xec: 'V', 0x110: 'T', 0x15c: 'V', 0x160: 'V', 0x198: 'T', 0x1a0: 'T', 0x1ac: 'T', 0x1b4: 'TTT', 0x1b8: 'TTT', 0x1e0: 'V', 0x1f4: 'VV',
           **{k: '' for k in (0x04, 0x0c, 0x10, 0x1c, 0xb4, 0x13c, 0x168, 0x18c, 0x1f8, 0x3c, 0x54, 0x58, 0x5c, 0x64, 0x6c, 0x70, 0x74, 0x78, 0x7c, 0x80, 0x8c, 0x90, 0x98, 0x9c, 0xa0,
                              0xb8, 0xc0, 0xc4, 0xc8, 0xcc, 0xd0, 0xd4, 0xd8, 0xdc, 0xe0, 0xe4, 0xf0, 0xf4, 0xfc, 0x100, 0x104, 0x108, 0x10c,
                              0x114, 0x118, 0x11c, 0x120, 0x124, 0x128, 0x130, 0x134, 0x138, 0x140, 0x144, 0x148, 0x14c, 0x150, 0x154, 0x158,
                              0x164, 0x16c, 0x170, 0x174, 0x178, 0x17c, 0x180, 0x184, 0x188, 0x190, 0x194, 0x19c, 0x1a4, 0x1a8, 0x1b0, 0x1bc, 0x1c0,
                              0x1c4, 0x1c8, 0x1cc, 0x1d0, 0x1d4, 0x1d8, 0x1dc, 0x1e4, 0x1e8, 0x1ec, 0x1f0)}}
SUBNAME = {0x00: 'DEBUGCOL', 0x0c: 'AIMVEL', 0x10: 'SPREAD', 0x3c: 'TOSS', 0xd4: 'TURRET16', 0xd8: 'ANGLEFRAME', 0xe0: 'HELI_A',
           0xe4: 'HELI_B', 0xf0: 'MINELAYER', 0xfc: 'SHOT8', 0x104: 'DIRECTOR', 0x124: 'FAN4B', 0x128: 'FAN3C', 0x12c: 'BOSSBOUND',
           0x130: 'BURST', 0x134: 'DRIFT', 0x138: 'BOSSPTR', 0x150: 'DROPPER', 0x04: 'REVDIR', 0x30: 'RANDDIR', 0x34: 'FAN3', 0x58: 'SHARDS12', 0x60: 'COREHP', 0x64: 'CIRCLE',
           0x68: 'SHOOT', 0x70: 'MIRRORDIR', 0x74: 'SHOTDIR', 0x78: 'TURRET8', 0x7c: 'TURRET4', 0x84: 'SPRBLK3_L1', 0x88: 'LEVEL_END',
           0x8c: 'SPRBLK3', 0x90: 'COPPER', 0x98: 'FAN3B', 0x9c: 'SIDESHOT', 0xb8: 'ANIMALS', 0xc0: 'BULLETFLY', 0xc8: 'DOWN3',
           0xcc: 'ARMBODY', 0xd0: 'ARMSEG', 0xf8: 'SETLOOP', 0x100: 'SPRBLK4', 0x14c: 'ARMMID', 0x154: 'LEVEL_END2', 0x158: 'WALKER',
           0x15c: 'BARREL', 0x160: 'BARRELSHOT', 0x164: 'UPDOWNFIRE', 0x16c: 'FRAMES_M3', 0x170: 'FRAMES_P3', 0x174: 'TRACK',
           0x178: 'LOCO', 0x17c: 'LOCO_L', 0x180: 'LOCO_R', 0x184: 'WAGON', 0x188: 'WAGONSHOT', 0x190: 'GNDMARK', 0x194: 'FORTSTART',
           0x198: 'SLOTTAKE', 0x19c: 'SLOTKILL', 0x1a0: 'SLOTRAND', 0x1a4: 'GUN5', 0x1bc: 'COUNTDOWN', 0x1c0: 'FAN4',
           0x1c4: 'BOSS_DIRECTOR_A', 0x1c8: 'BOSS_DIRECTOR_B', 0x1cc: 'RING6', 0x1d0: 'JITTER', 0x1d4: 'COPPER_ON',
           0x1d8: 'FINALBOSS_AI', 0x1dc: 'SCROLLSTOP', 0x1e0: 'TURRETSHOT', 0x1e4: 'AIMFRAME', 0x1e8: 'MIDBOSS_SPR', 0x1f0: 'STICK_BOSS',
           0x1f4: 'DEBRIS'}
END = {0x40, 0x50}
SUBNORET = {0x78, 0x7c, 0x94, 0xbc, 0xc0, 0xcc, 0xe0, 0xe4, 0xf0, 0x104, 0x130, 0x134, 0x13c, 0x140, 0x148, 0x150, 0x178, 0x190, 0x194, 0x1e4, 0x1ec, 0x1f0}


class Dis:
    def __init__(self, data, scripts_base):
        self.d = data
        self.base = scripts_base
        self.unknown = collections.Counter()
        self.multi = False

    def w(self, o):
        return struct.unpack('>H', self.d[o:o + 2])[0]

    def s(self, o):
        return struct.unpack('>h', self.d[o:o + 2])[0]

    def val(self, o):
        v = self.w(o)
        if v == 0:
            return '#%d' % self.s(o + 2), o + 4
        sv = self.s(o)
        if sv < 0:
            a = sv + 0x4000
            return ('obj.%x' % a if a >= 0 else 'glob.%x' % (a + 0x4000 + 0x10000 - 0x10000 & 0xffff)), o + 2
        return 'tgt.%x' % ((v - 0x4000) & 0xffff), o + 2

    def addr(self, o):
        sv = self.s(o) + 0x4000
        sv = sv - 0x10000 if sv >= 0x8000 else sv
        return ('obj.%x' % sv if sv >= 0 else 'glob.%x' % ((sv + 0x4000) & 0xffff)), o + 2

    def one(self, o):
        op = self.w(o)
        p = o + 2
        args = []
        if op == 0x00:
            a, p = self.val(p)
            n = self.s(p)
            bobs = [self.w(p + 2 + 2 * i) for i in range(max(n + 1, 0))]
            p = p + 2 + 2 * max(n + 1, 0) if n >= 0 else p + 2
            fr = ['%x' % b if b < 0x8000 else 'obj.%x' % (b & 0x7fff) for b in bobs]
            return 'FRAME delay=%s bobs=[%s]' % (a, ','.join(fr) if n >= 0 else 'none'), p, a == '#9999'
        if op == 0x20:
            sub = self.w(p); p += 2
            spec = SUBSPEC.get(sub)
            if spec is None:
                self.unknown['20.%02x' % sub] += 1
                return 'SUB.%02x ???' % sub, None, True
            for c in spec:
                if c == 'V':
                    a, p = self.val(p); args.append(a)
                elif c == 'w':
                    args.append('%d' % self.s(p)); p += 2
                elif c == 'T':
                    args.append('->%x' % (self.base + self.w(p))); p += 2
            nm = 'SUB.%02x' % sub + ('/' + SUBNAME[sub] if sub in SUBNAME else '')
            return '%s %s' % (nm, ' '.join(args)), p, sub == 0x50 or sub in SUBNORET
        if op == 0x48:
            t = self.s(p); a1 = self.w(p + 2)
            if a1 == 0x8000:
                return 'EFFECT typ=%d dx=obj.%x dy=obj.%x' % (t, self.w(p + 4), self.w(p + 6)), p + 8, False
            return 'EFFECT typ=%d dx=%d dy=%d' % (t, self.s(p + 2), self.s(p + 4)), p + 6, False
        if op == 0x90:
            f = self.s(p); t = self.base + self.w(p + 2)
            return 'SETPROG %d ->%x' % (f, t + 2 if f == 0x2c else t), p + 4, False
        if op == 0x98:
            return 'SWITCHRATING base=%x off=%d div=%d' % (self.base + self.w(p), self.s(p + 2), self.s(p + 4)), None, True
        spec = SPEC.get(op)
        if spec is None:
            self.unknown['%02x' % op] += 1
            return 'OP.%02x ???' % op, None, True
        for c in spec:
            if c == 'w':
                args.append('%d' % self.s(p)); p += 2
            elif c == 'V':
                a, p = self.val(p); args.append(a)
            elif c == 'A':
                a, p = self.addr(p); args.append(a)
            elif c == 'T':
                args.append('->%x' % (self.base + self.w(p))); p += 2
        if op == 0x14 and args[1] == 'obj.7e' and args[0].startswith('#') and int(args[0][1:]) >= 0x100:
            self.multi = True
        stop = op == 0x54 and self.multi
        return '%s %s' % (NAMES.get(op, 'OP%02x' % op), ' '.join(args)), p, stop or op in END or (op in (0x54, 0x60) and args == ['9999']) or (op in (4, 8, 0xc, 0x70, 0x84, 0x88, 0xb0) and args[-1:] == ['#9999'])

    def run(self, start, limit=80):
        out = []
        o = start
        self.multi = False
        for _ in range(limit):
            txt, p, stop = self.one(o)
            out.append('%05x  %s' % (o, txt))
            if p is None or stop:
                break
            o = p
        return out


def level(path):
    d = open(path, 'rb').read()
    L = lambda o: struct.unpack('>I', d[o:o + 4])[0]
    return d, L(0xe), L(0x12), L(0x1c)


def disasm_level(path):
    d, TT, SC, SP = level(path)
    dis = Dis(d, SC)
    S = lambda o: struct.unpack('>h', d[o:o + 2])[0]
    o = SP; used = collections.Counter()
    while S(o) >= 0:
        used[S(o + 6)] += 1; o += 12
    for t in sorted(used):
        td = struct.unpack('>I', d[TT + t:TT + t + 4])[0]
        print('=== type %x (spawns %d) def@%x' % (t, used[t], td))
        print('  -- movement'); print('\n'.join('    ' + l for l in dis.run(td + 12)))
        print('  -- animation'); print('\n'.join('    ' + l for l in dis.run(SC + S(td), 20)))
        if S(td + 10):
            print('  -- death'); print('\n'.join('    ' + l for l in dis.run(SC + S(td + 10) + 2, 30)))
    print('UNKNOWN:', dis.unknown.most_common())


# ---- reachability -------------------------------------------------------

SPAWN_FN = 0x22ecd0       # runtime address of the spawn routine (type in D2)
SUBOP_TABLE = 0x230dea    # runtime address of the sub-op jump table (127 x BRA.W)
MANUAL_SUBTYPES = {0x18: {0x1ac}, 0xcc: {0x194}}   # calls >0x400 past handler start
OPERAND_TYPE = {0x08: (1, 1), 0x38: (0, 4), 0x40: (0, 4), 0x68: (1, 1)}   # sub-op: (operand index, multiplier)


def code_spawns(exe_path, verbose=False):
    """sub-op -> set of types spawned by its 68k handler with an immediate D2."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bansexe import BansExe
    from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN
    x = BansExe(exe_path)
    B = x.bases[0]
    d = x.hunk_image(0)
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    sub = {}
    for i in range(127):
        a = SUBOP_TABLE + 4 * i
        op, disp = struct.unpack('>Hh', d[a - B:a - B + 4])
        if op == 0x6000:
            sub[a + 2 + disp] = 4 * i
    starts = sorted(sub)
    callers = []
    for o in range(0, len(d) - 4, 2):
        op = struct.unpack('>H', d[o:o + 2])[0]
        if op == 0x6100:
            if o + B + 2 + struct.unpack('>h', d[o + 2:o + 4])[0] == SPAWN_FN:
                callers.append(o + B)
        elif op >> 8 == 0x61 and op & 0xff not in (0, 0xff):
            disp = op & 0xff; disp = disp - 256 if disp > 127 else disp
            if o + B + 2 + disp == SPAWN_FN:
                callers.append(o + B)

    def back_ins(a, n):
        for s in range(a - n, a, 2):
            ins = list(md.disasm(d[s - B:a - B], s))
            if ins and ins[-1].address + ins[-1].size == a:
                return ins
        return []

    res = collections.defaultdict(set)
    for c in callers:
        owner = None
        for s in starts:
            if s <= c: owner = s
        typ = None
        for i in reversed(back_ins(c, 48)):
            m = re.match(r'#\$([0-9a-f]+), d2$', i.op_str)
            if i.mnemonic in ('move.w', 'moveq', 'move.l') and m:
                typ = int(m.group(1), 16); break
            if re.search(r', d2$', i.op_str): break
        so = sub.get(owner) if owner and c - owner < 0x400 else None
        if verbose:
            h, off = x.to_hunk(c)
            print('  call %06x hunk%d+0x%05x  type=%s sub-op=%s' % (c, h, off,
                  '%x' % typ if typ is not None else '?', '%x' % so if so is not None else '-'))
        if typ is not None and so is not None:
            res[so].add(typ)
    return res


def analyse(path, subtypes):
    d = open(path, 'rb').read()
    L = lambda o: struct.unpack('>I', d[o:o + 4])[0]
    S = lambda o: struct.unpack('>h', d[o:o + 2])[0]
    TT, SC, SP = L(0xe), L(0x12), L(0x1c)
    types = {4 * i: L(TT + 4 * i) for i in range((SC - TT) // 4)}
    dis = Dis(d, SC)
    o = SP; spawned = collections.Counter()
    while S(o) >= 0:
        spawned[S(o + 6)] += 1; o += 12
    sub_where = collections.defaultdict(set); op_where = collections.defaultdict(set)
    todo = sorted(spawned); done = set()

    def walk(start, owner, seen):
        stack = [start]
        while stack:
            p = stack.pop()
            for _ in range(400):
                if p is None or p in seen or p < SC or p >= len(d) - 2:
                    break
                txt, nxt, stop = dis.one(p)
                seen.add(p)
                opw = struct.unpack('>H', d[p:p + 2])[0]
                op_where[opw].add(owner)
                if opw == 0x20:
                    sub = struct.unpack('>H', d[p + 2:p + 4])[0]
                    sub_where[sub].add(owner)
                    todo.extend(subtypes.get(sub, ()))
                    if sub in OPERAND_TYPE:
                        a = txt.split()[1:]; k, mul = OPERAND_TYPE[sub]
                        if len(a) > k and a[k].startswith('#'):
                            todo.append(int(a[k][1:]) * mul)
                for t in re.findall(r'->([0-9a-f]+)', txt):
                    stack.append(int(t, 16))
                if txt.startswith('SPAWNREL'):
                    a = txt.split()[1:]
                    try: todo.append(int(a[4]))
                    except (IndexError, ValueError): pass
                elif txt.startswith('SPAWN '):
                    todo.append(int(txt.split()[1]))
                if nxt is None or stop:
                    break
                p = nxt

    while todo:
        t = todo.pop()
        if t in done: continue
        done.add(t)
        if t not in types: continue
        td = types[t]
        seen = set(); dis.multi = False          # each type walked on its own: owners are complete
        walk(td + 12, t, seen)
        if S(td): walk(SC + S(td), t, seen)
        if S(td + 10): walk(SC + S(td + 10) + 2, t, seen)
    unreached = sorted(set(types) - done)
    return types, unreached, op_where, sub_where


def hexset(s): return ','.join('%x' % v for v in sorted(s))


def reach(paths, exe, verbose=False):
    subtypes = collections.defaultdict(set)
    if exe:
        subtypes.update(code_spawns(exe, verbose))
    else:
        print('(no --exe: only the built-in sub-op spawn additions are used)')
    for k, v in MANUAL_SUBTYPES.items():
        subtypes[k] |= v
    allops = set(); allsub = set()
    for p in paths:
        types, unreached, op_where, sub_where = analyse(p, subtypes)
        allops |= set(op_where); allsub |= set(sub_where)
        print('== %s: types %d, reached %d, unreached %d' % (os.path.basename(p), len(types), len(types) - len(unreached), len(unreached)))
        if unreached:
            print('   unreached types:', hexset(unreached))
        print('   opcodes used (owner types):')
        for op in sorted(op_where):
            print('     %02x %-12s %s' % (op, NAMES.get(op, '?'), hexset(op_where[op])))
        print('   sub-ops used (owner types):')
        for s in sorted(sub_where):
            print('     %02x %-16s %s' % (s, SUBNAME.get(s, ''), hexset(sub_where[s])))
    print('== sub-ops unused in all given files:', ' '.join('%x' % s for s in range(0, 0x1fc, 4) if s not in allsub))
    print('== opcodes unused in all given files:', ' '.join('%x' % s for s in range(0, 0xb4, 4) if s not in allops))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('levels', nargs='+', help='unpacked level file(s)')
    ap.add_argument('--reach', action='store_true', help='reachability report instead of disassembly')
    ap.add_argument('--exe', help='bans.exe, to derive sub-op -> code-spawned types (with --reach)')
    ap.add_argument('-v', '--verbose', action='store_true', help='list the spawn calls found in the code')
    a = ap.parse_args()
    if a.reach:
        reach(a.levels, a.exe, a.verbose)
    else:
        for p in a.levels:
            disasm_level(p)
