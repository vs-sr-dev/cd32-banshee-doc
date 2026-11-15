# The enemy and object scripting VM

Every enemy, bullet, debris shower, boss part and pick-up pod in Banshee is
driven by a small bytecode interpreter in `bans.exe`. This chapter documents
the object definition in `levelNf`/`bossf`, the instruction encoding, all 45
opcodes, the 127 entries of the `0x20` sub-op table, death scripts, the time
and distance units, and how to disassemble the scripts. It replaces the
"scripts" paragraph of [13-level-formats-and-floppy.md](13-level-formats-and-floppy.md),
which stopped at opcode `0` and called the death-script field a "path".

**Addresses.** Code and data in `bans.exe` are given as hunk offsets
(`hunk0+0x…`), per the [address convention](00-overview.md#address-convention).
Our working notes and the first version of chapter 13 used runtime addresses
with the six hunks loaded back to back from `0x21f000`; for hunk 0, runtime = `0x21f000 + N` and
file offset = `N + 0x34`. Example: the opcode jump table is `hunk0+0x108D2`
(runtime `0x22f8d2`, file `0x10906`). Offsets inside a level file are file
offsets into that (unpacked) file. Field names `obj.X` are byte offsets into the
live object record; `glob.X` are offsets from the game's base register `A5`
(`hunk5+0x723DC`).

## Evidence and confidence

| Claim | Evidence | Confidence |
|---|---|---|
| Opcode set, operand counts | handler code for all 45 table entries; recursive disassembly of every type in all five level files with **0 unknown opcodes and 0 operand desynchronisations** outside the 6 cases listed under *Anomalies* | high |
| Opcode semantics | handler code; tick-by-tick comparison of a VM simulator against emulation (see [15-enemy-movement.md](15-enemy-movement.md)) | high for movement, control flow, arithmetic, animation; medium for effects/sound side effects |
| Sub-op operand counts | handler code for all 127 entries | high |
| Sub-op meanings | handler code + emulation; 22 entries not characterised | mixed, stated per row |
| 25 Hz tick | measured in emulation (logic runs every second PAL frame) | high |

Recursive pass (movement, animation and death programs of every type, following
every jump, `SETPROG` and spawn):

| File | Instructions reached | Types extracted |
|---|---:|---:|
| `level1f` | 2,478 | 145 |
| `level2f` | 3,446 | 174 |
| `level3f` | 1,747 | 107 |
| `level4f` | 1,964 | 104 |
| `bossf` | 545 | 23 |

"Types extracted" is every entry of the level's type table (all definitions
are disassembled). Of these, 138 / 156 / 94 / 98 / 23 are statically reachable
from spawn records, from other scripts and from native code; the rest are
listed in [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §5
(`tools/scriptdis.py --reach`).

## Type definitions

`levelNf + 0x0e` is the type table: a longword per type, indexed by
`type×4` (the value stored in spawn records), giving the file offset of a
**type definition**. Script offsets inside the definition are relative to the
script base, the longword at `levelNf + 0x12`.

| Offset | Size | Contents | Copied to |
|---:|---|---|---|
| `+0` | word | animation program, offset from script base | `obj.28` |
| `+2` | word | object flags | `obj.3e` |
| `+4` | 2 words | x/y clip offsets — sprite clipping window, used when the spawn record has bit 15 set (objects emerging from a tunnel or hangar) | |
| `+8` | word | multi-part selector; `≥ 0x100` = multi-part object (below) | `obj.7e` |
| `+10` | word | **death program**, offset from script base; 0 = none | `obj.2c` |
| `+12` | … | **movement program, inline** | `obj.0c` |

Example (`level1f`, type `0x1b4`, the first wave of level 1):

```
098c 0000 0000 0000 0018 0a70 | ...
anim  flags clip x/y 7e  death | script: SOUND, SET #0x1b5 obj.4a, MOVE 0 -512 #9, ...
```

There are **no path tables**. The field chapter 13 calls the "path offset" is
the death program; the whole trajectory lives in the movement program and is
built from the movement instructions below.

### Object flags (`obj.3e`)

| Bits | Meaning |
|---|---|
| 0–2 | not hittable when set (`b8 ANIMALS` sets them for civilians/animals unless the cheat flag is on) |
| 10 (`0x400`) | damage taken is added to the boss energy bar (`glob.8f6`) |
| 15 | being hit (flash, when bit 2 is clear) |
| `0xd0` | lethal obstacle — kills the player even through the shield |

### Object record fields used by scripts

| Field | Meaning |
|---|---|
| `obj.08` | pointer to the targeted player (set by `ac TARGET`) |
| `obj.0c`, `obj.28`, `obj.2c` | movement, animation, death program counters |
| `obj.10`, `obj.14` | x, y, 16.16 fixed point, world coordinates (y grows up the map) |
| `obj.34`, `obj.38` | vx, vy, longwords in 1/256 px per tick (`pos += v << 8`) |
| `obj.4a`, `obj.4c`, `obj.4e`, `obj.50`… | general registers: current bob, direction index, counters |
| `obj.5e`, `obj.62` | vector/parameter handed down by the parent at spawn |
| `obj.66`/`68`, `obj.6e`/`70` | sine overlay amplitude and phase (`7c WOBBLE`) |
| `obj.76` | hit points |
| `obj.78` | animation delay; the animation program runs once every `obj.78` ticks |
| `obj.7c` | `DELAY` counter |
| `obj.7e` | multi-part selector |
| `obj.82` | power-up drop (spawn-record field 6) |
| `obj.84` | which player scored the hit |
| `obj.86`, `obj.8a` | sound voice handle (one voice per object) |

Each object therefore runs **three programs**: movement (every tick),
animation (every `obj.78` ticks), and death (replaces movement when HP reaches
zero).

## Instruction encoding

Big-endian words. The first word of an instruction is the opcode, a **byte
offset into a 45-entry table of `bra.w`** at `hunk0+0x108D2`, so opcodes run
`0x00`–`0xB0` in steps of 4. Operands follow inline; there are four kinds:

| Kind | Encoding |
|---|---|
| `w` | signed literal word |
| `V` (value) | `0000 nnnn` → literal `nnnn` (two words); `0xC000+X` → `obj.X`; `0x8000+X` → `glob.X`; `0x4000+X` → field `X` of the **targeted player** (`obj.08`), e.g. `tgt.10` = player x |
| `A` (address) | one word, same field mapping as `V` minus the literal case: `0xC000+X` → `obj.X`, `0x8000+X` → `glob.X` |
| `T` (target) | one word, byte offset from the script base |

Handlers return in `D0`: `0` = continue with the next instruction this tick;
`1` = end the tick (handlers that wait back `A3` up by 4 first, so the same
instruction runs again next tick); `−1` = delete the object.

A program ends at `50 END`, an unconditional `40 GOTO`, `20 50`, a timed
instruction with time `#9999` (`04 08 0c 70 84 88 b0`, `54`/`60` with 9999), a
sub-op that never returns (listed below), or `SET #≥0x100 obj.7e` followed by a
`DELAY` (multi-part object: the VM stops and the part handler takes over).

### Timed instructions

The time operand `t` is a `V`; the instruction runs **t+1 ticks** (`#0` = one
tick), `#9999` = forever.

## Opcodes

Operand letters as above. Handler addresses are hunk-0 offsets. Names are the
mnemonics printed by the disassembler; where the original tool name is a
placeholder the semantics column is authoritative.

| Op | Name | Operands | Handler | Semantics |
|---|---|---|---|---|
| `00` | FRAME | `V N bob×(N+1)` | `+0x10988` | set animation frame list and delay; bob numbers start at 1 (0 = none); bit 15 = indirect, `obj.(bob&0x7fff)`. Delay `#9999` ends the program |
| `04` | MOVE | `w w V` | `+0x109E8` | v = (vx, vy); pos += v for t+1 ticks |
| `08` | ACCELV | `w w w w V` | `+0x10A94` | v = (vx, vy) once, then pos += v; v += (ax, ay) each tick |
| `0c` | ACCEL | `w w V` | `+0x10B76` | pos += v; v += (ax, ay) each tick |
| `10` | SOUNDR | `w w w` | `+0x113E6` | as `24`, period += `(RNG >> 4) & 63` |
| `14` | SET | `V A` | `+0x10DEC` | field = value |
| `18` | ADD | `V A` | `+0x10E42` | field += value |
| `1c` | SUB | `V A` | `+0x10E98` | field −= value |
| `20` | (sub-op) | `xx …` | `+0x11DE4` | dispatch through the sub-op table, see below |
| `24` | SOUND | `w w w` | `+0x113DE` | sample, period, volume; silences the object's previous voice first |
| `28` | IFEQ | `V A T` | `+0x11070` | jump if value == field |
| `2c` | IFNE | `V A T` | `+0x110CA` | jump if value != field |
| `30` | IFLT | `V A T` | `+0x1112E` | jump if value < field |
| `34` | IFGT | `V A T` | `+0x11188` | jump if value > field |
| `38` | SPAWN | `w w` | `+0x114A8` | create object (type×4, HP/flags) at own position |
| `3c` | SPAWNREL | `V V w w w w` | `+0x11434` | create object at offset |
| `40` | GOTO | `T` | `+0x111E4` | jump |
| `44` | SNDMOD | `w w w w` | `+0x113B2` | slide own voice: volume target/step, period target/step (−1 = keep) |
| `48` | EFFECT | `w w w` or `w 8000 A A` | `+0x114C6` | explosion/debris effect (separate pool) at literal or field offset |
| `4c` | LOOP | `A T V` | `+0x11244` | counter ≤ 0 → load V and jump; > 1 → decrement and jump; = 1 → fall through (body runs V+1 times) |
| `50` | END | — | `+0x11240` | delete object |
| `54` | DELAY | `w` | `+0x112BE` | freeze VM **and motion** for n+1 ticks (`obj.7c`) |
| `58` | MUL | `V A` | `+0x10EEE` | field = field × value / 256 (disassembler: `COND58`) |
| `5c` | DIV | `V A` | `+0x10F4A` | field = (field × 256) / value (disassembler: `COND5C`) |
| `60` | ANIMDELAY | `w` | `+0x112C6` | `obj.78` = n, end tick |
| `64` | ANIMCYC | `w w A w` | `+0x10FA8` | field += 1; on reaching `to`, reset to `from`; then wait `delay` |
| `68` | ANIM68 | `w w A w` | `+0x10FE0` | descending cycle: field −= 1, wrap |
| `6c` | ANIM6C | `w w A w` | `+0x11018` | ping-pong cycle, direction in bit 14 of the field |
| `70` | MOVE70 | `w w V` | `+0x10CE6` | pos += v; v = v·f/256 per axis (f < 256 drag, f > 256 gain) |
| `74` | POD | `w w w w w` | `+0x11CA2` | power-up pod at (dx, dy) with three icon choices |
| `78` | SCORE | `w w w` | `+0x112CE` | flag, BCD long; flag 0 = the player who shot it, ≠0 = both; added with `abcd` |
| `7c` | WOBBLE | `w×8` | `+0x1137A` | sine overlay on the drawn position: phase steps, amplitude steps, initial phases and amplitudes per axis |
| `80` | WOBBLE2 | `w×4` | `+0x1139E` | change overlay phase and amplitude steps |
| `84` | HOME84 | `w w w A V` | `+0x1160A` | direction to target in 8 (mode < 0) or 16 sectors → field = dir·mult + base; for t ticks (V < 0 once) |
| `88` | HOME88 | `w w w A V` | `+0x11694` | same, direction of own velocity |
| `8c` | EFFECTV | `w w w V V` | `+0x114EA` | as `48`, offset from values. **Unused** |
| `90` | SETPROG | `w T` | `+0x11836` | `obj+field` = script base + T; `0x0c` movement, `0x28` animation (clears `obj.78`), `0x2c` death |
| `94` | HOMING | `w w w` | `+0x11850` | inertia k, strength s, time; every 2nd tick v = v·k/4096 + s·û + (0, 16); off-screen → delete; t = 0 → one step |
| `98` | SWITCHRATING | `T w w` | `+0x1198C` | jump table indexed by player rating (`glob.3c4`): base, offset, divisor. Used only by script-spawned homing rockets: L1 type `0x3c`, L3 `0x2c`/`0x30` |
| `9c` | (penalty) | `w w w` | `+0x119A6` | subtract BCD points from the hitting player, add to rating correction `glob.3c2`. **Unused** |
| `a0` | CLOUDS | `w` | `+0x119E4` | cloud layer control: 0 start, 4/12 colour fade up/down, 8/16 stop flag |
| `a4` | WRECK | `V w w` | `+0x11BAC` | add a static bob (wreck) to the background list |
| `a8` | SMARTBOMB | — | `+0x119DA` | screen-wide smart bomb (`glob.3ba` = 1) |
| `ac` | TARGET | — | `+0x11C2C` | `obj.08` = nearer player |
| `b0` | WAIT | `V` | `+0x10C46` | pos += v for t+1 ticks (coast) |

Two opcodes, `8c` and `9c`, are referenced by no script in any level.

## Sub-ops (`20 xx`)

Second word = byte offset into a second table at `hunk0+0x11DEA` (127
entries, `0x000`–`0x1F8`, step 4). Operands, if any, follow. Names are the
disassembler's; `—` = no name. **NR** = never returns (only "repeat" or
"delete"), so it terminates a program.

| xx | Name | Ops | Meaning |
|---|---|---|---|
| `00` | DEBUGCOL | `V` | debug raster bar (background colour to line `0x80`). Unused |
| `04` | REVDIR | | `obj.4a = (obj.50 − obj.4a) & 0x1c` |
| `08` | — | `V V` | shot in direction, bullet type |
| `0c` | AIMVEL | | v = (`obj.5e`, `obj.62`), vector set by the spawner |
| `10` | SPREAD | | bullet with random vx, spread widens with rating. Used only by script-spawned types: L1 `0x48`, `0x144`; L2 `0x28`, `0x7c`, `0x2b0`, `0x2b4`; L3 `0x44` |
| `14` | — | `T` | jump if the player is under the object within ±50 px |
| `18` | — | | warship with four turrets drawn as separate bobs |
| `30` | RANDDIR | | v from a 16-entry table (|v| = 2048) by `y & 15` |
| `34` | FAN3 | | three-bullet fan |
| `38` | — | `V V` | shot, RNG-dependent (not fully characterised) |
| `3c` | TOSS | | throw up and fall |
| `40` | — | `V V` | turret shot variant |
| `50` | — | `T` | drop a diver at the player's x from the top edge; ends program |
| `58` | SHARDS12 | | 12 debris from a table at `hunk0+0x16106` |
| `5c` | — | | debris variant (RNG step) |
| `60` | COREHP | `T` | fortress core: if `61 − glob.8f6 > 1` jump |
| `64` | CIRCLE | | 2 px/tick along angle `obj.4e`, angle += `obj.50`, for `obj.4c` ticks; random reversal |
| `68` | SHOOT | `V V V` | chance, type, flags: fire if `chance − 64 + RNG/2 < rating` |
| `70` | MIRRORDIR | | `obj.4a = obj.50 − obj.4a` |
| `74` | SHOTDIR | | bullet from direction table by frame `obj.50` |
| `78` | TURRET8 | | NR. turret, 8 directions, tracks player, fires every 40 ticks |
| `7c` | TURRET4 | | NR. as `78`, 4 directions |
| `84` | SPRBLK3_L1 | | attach AGA sprite block [3] (level 1 boss superstructure) |
| `88` | LEVEL_END | | `glob.5e8` = 1 |
| `8c` | SPRBLK3 | | attach sprite block (level 2) with its copper list |
| `90` | COPPER | | restore the default copper list |
| `94` | — | | NR. boss core rides a horizontal rail following the player |
| `98` | FAN3B | | three-bullet fan |
| `9c` | SIDESHOT | | sideways bullet with random vy |
| `a0` | — | | shot + sound (boss phase) |
| `a4`/`a8` | — | | chain segment position from a shared table; `a8` also steps the RNG |
| `b8` | ANIMALS | | if civilians are not hittable, `obj.3e |= 7` |
| `bc` | — | | NR. two guns with independent counters (level 1 boss) |
| `c0` | BULLETFLY | | NR. straight flight to the screen edge, speed × difficulty |
| `c4` | — | | tumbling ballistic debris. Unused |
| `c8` | DOWN3 | | three bullets downwards |
| `cc` | ARMBODY | | NR. mid-boss body with arms (~350 instructions of code) |
| `d0` | ARMSEG | | arm segment position from table `glob.57a` |
| `d4` | TURRET16 | | gun, 16 directions |
| `d8` | ANGLEFRAME | | frame from angle |
| `e0`/`e4` | HELI_A/B | | NR. helicopter: thrust table + drag |
| `f0` | MINELAYER | | NR. mine interval `(0x290 − rating)/8` ticks |
| `f4`, `11c` | — | | bullet flight to edge variants |
| `f8` | SETLOOP | | set background loop point (`glob.354`) |
| `fc` | SHOT8 | | fire in the next of 8 directions |
| `100` | SPRBLK4 | | attach sprite block [4] |
| `104` | DIRECTOR | | NR. level 2 boss director |
| `108`/`10c` | — | | attached-to-parent motion |
| `114` | — | | six bullets in a hexagon |
| `124`/`128` | FAN4B/FAN3C | | fans |
| `12c` | BOSSBOUND | `w w` | player flight boundary (`glob.33c`) |
| `130` | BURST | | NR. burst |
| `134` | DRIFT | | NR. drift |
| `138` | BOSSPTR | | register as boss (`glob.8f0`) |
| `140` | — | | NR. track a position (`glob.440/442`) until the boss ends |
| `144` | — | | bullet held in the mid-boss's hands; only used by an unspawned type |
| `14c` | ARMMID | | arm segment midpoint |
| `150` | DROPPER | | NR. drop from a nest |
| `154` | LEVEL_END2 | | `glob.5e8` = 1 |
| `158` | WALKER | | walker step from table (−3,+3) (−7,−1) (−12,−2) |
| `15c` | BARREL | `V` | turret/barrel angle → `obj.50` |
| `160` | BARRELSHOT | `V` | fire from the barrel |
| `164` | UPDOWNFIRE | | boat bob ±256 in a 100-tick cycle |
| `16c`/`170` | FRAMES_M3/P3 | | frames −3/+3 (bank) |
| `174` | TRACK | | x += train speed `glob.3e6`, hide outside track window |
| `178` | LOCO | | NR. locomotive braking physics |
| `17c`/`180` | LOCO_L/R | | locomotive start left/right |
| `184` | WAGON | | wagon: take track bounds |
| `188` | WAGONSHOT | | wagon shot |
| `18c` | — | | booster: v × 266/256, downward bias; off-screen → delete |
| `190` | GNDMARK | | NR. save ground decoder state (loop return point) |
| `194` | FORTSTART | | NR. start fortress counter and boss bar |
| `198` | SLOTTAKE | `T` | take a fortress slot; jump if already destroyed |
| `19c` | SLOTKILL | | mark slot destroyed |
| `1a0` | SLOTRAND | `T` | as `198`, random appearance by counter |
| `1a4` | GUN5 | | gun, 5 directions, steps toward player, fires every `0x32` ticks |
| `1a8`/`1b0` | — | | aiming variants |
| `1ac` | — | `T` | jump if `2·|dx| ≥ |dy|` (player more beside than ahead) |
| `1b4` | — | `T T T` | random branch: RNG byte < `0x30` → T1, ≥ `0xd0` → T2, else T0 |
| `1b8` | — | `T T T` | player branch: dx ≥ 30 → T1, < −30 → T2, else T0 |
| `1bc` | COUNTDOWN | | count `obj.4a` down |
| `1c0` | FAN4 | | four-bullet fan |
| `1c4`/`1c8` | BOSS_DIRECTOR_A/B | | final boss directors (random spike / turret scheduling) |
| `1cc` | RING6 | | ring of 6 bullets |
| `1d0` | JITTER | | mech step |
| `1d4` | COPPER_ON | | final boss mini copper list (sprite priority split) |
| `1d8` | FINALBOSS_AI | | final boss ship movement |
| `1dc` | SCROLLSTOP | | fortress sprite y |
| `1e0` | TURRETSHOT | `V` | turret shot from direction table |
| `1e4` | AIMFRAME | | NR. frame from velocity direction. Unused |
| `1e8` | MIDBOSS_SPR | | mid-boss sprite copper list |
| `1ec` | — | | NR. periodic side drop of a rover |
| `1f0` | STICK_BOSS | | NR. stick to the boss |
| `1f4` | DEBRIS | `V V` | explosion at a random screen point (mask, offset) |
| `1f8` | — | | explosion near centre at a random point |

**Not characterised** (operand counts known, behaviour not described):
`1c 20 24 28 2c 44 48 4c 54 6c 80 b0 b4 dc e8 ec 110 118 120 13c 148 168`.
All take no operands except `e8` and `110` (one `T`) and `ec` (one `V`). Unused in every level:
`00`, `c4`, `1e4`, and `144` (reachable only from a type no spawn creates).

## Death scripts

The death-program pointer (`+10` in the definition, or `SETPROG 2c …`) points
at a **flags word**, and the script starts at the next word. On death the
engine loads the word into `obj.3e` (so a wreck can become unhittable or
harmless) and switches the movement program to the script (`hunk0+0x103AC`,
`hunk0+0x1071A`). `SETPROG 2c T` therefore stores T+2 as the program.

Typical death script (level 1 type `0x1b4`): `SCORE 0 0 0x15` (15 points to
the shooter), `SOUND`, `EFFECT 4 0 0` (explosion), `WAIT #1`, `END`. Bosses
use long death scripts: explosion chains, `SETPROG 28` to a wreck animation,
`20 88` to end the level.

## Multi-part objects

`SET #≥0x100 obj.7e` followed by `DELAY` hands the object to
`hunk0+0x100E0`, which reads `obj.0c` as data: `{angle speed.w, angle.w,
count−1.w}` followed by 12-byte part records `{x, y, counter, dx, dy, —}`.
Parts are rotated with the sine table and squashed ×3/4 vertically. Used by
the swinging arm in level 1 and by the final boss.

## Units and timing

| Quantity | Unit |
|---|---|
| Tick | **1/25 s** — logic runs every second PAL frame (measured in emulation) |
| Scroll | +1 px per tick in world y (`glob.340`), i.e. 25 px/s |
| Position | 16.16 px, world coordinates, y up the map; x 0…384 (about 320 visible) |
| Velocity | 1/256 px per tick; v_px/s = v · 25/256 |
| Acceleration | 1/256 px per tick²; a_px/s² = a · 625/256 |
| Angle | **2048 units per turn**; sine table of 1,024 signed words at `hunk1+0x6132` |
| Overlay amplitude | A/16 px |

An object with vy = +256 is stationary on screen; vy = 0 stands on the ground
and scrolls down at 25 px/s.

## Anomalies in the game data

* Level 2 types `0xfc`/`0x100` and level 4 type `0x9c` have `SETPROG 0x2c`
  (death) pointing directly at `FRAME #9999` with no flags word in front; read as a
  death pointer the engine would take the opcode as flags. Probably a data bug;
  not checked in emulation.
* Three scripts reach a sub-op that does not return in that context (level 2
  type `0x210` `20 d4`, level 4 type `0x140` `20 164`, level 3 type `0x14`
  animation after `FRAME #99`), so a linear disassembler continues into data.

## Disassembling

`tools/scriptdis.py` takes an unpacked `levelNf`/`bossf`:

```
python tools/scriptdis.py level1f > level1_scripts.txt
```

For every type used by the spawn list it prints the type, spawn count and
definition offset, then the movement, animation and death programs, one
instruction per line with its file offset, e.g.

```
022f2  MOVE 0 -512 #9
022fc  SUB.68/SHOOT #35 #76 #16384
```

Each program is followed until an end condition (above) or 80 instructions;
the last line lists unknown opcodes (empty for all five files). Jump targets
print as `->offset` (file offsets); the `SETPROG` field and plain `w`
operands print in decimal (`SETPROG 40` = field `0x28`). It does not follow jumps or spawned child
types; the movement tools in [15-enemy-movement.md](15-enemy-movement.md) do.

The recursive reachability pass behind the counts above and behind
[20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) is
`--reach` (follows jumps, `SPAWN`/`SPAWNREL` children, sub-op operand types
and, with `--exe`, types spawned from native code, computed from `bans.exe`):

```
python tools/scriptdis.py --reach --exe bans.exe level1f level2f level3f level4f bossf
```

## Open questions

1. Behaviour of the 22 uncharacterised sub-ops (above), mostly boss-part and
   code-created bullet logic.
2. Whether the three `SETPROG 44` cases above actually misbehave in the game.
3. Full condition list of `20 cc` (mid-boss body); only its effect is described.
