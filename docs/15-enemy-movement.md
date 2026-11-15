# Enemy movement: model and archetype catalogue

How enemies move, read from the VM programs of [14-enemy-vm.md](14-enemy-vm.md)
and checked tick by tick against emulation. The result is a catalogue of 27
movement archetypes and 4 bullet archetypes covering every moving type in
levels 1–4 and the boss level, with numbers in screen units.

Addresses follow the [address convention](00-overview.md#address-convention)
(hunk offsets; runtime = hunk 0 at `0x21f000`, see chapter 14). Type numbers are
`type×4` values as stored in spawn records, prefixed with the level (`L1:1b4`,
`LB` = boss level).

## The model

### State and integration

* Position `obj.10`/`obj.14` is 16.16 px in world coordinates, **y up the
  map**; velocity `obj.34`/`obj.38` is a longword in 1/256 px per tick, applied
  as `pos += v << 8`.
* **Only motion instructions integrate position**: `04 MOVE`, `08 ACCELV`,
  `0c ACCEL`, `70 MOVE70`, `b0 WAIT`, `94 HOMING`, and some sub-ops. Between
  them the object does not move in the world.
* `54 DELAY n` freezes the VM *and* the object for n+1 ticks. On screen the
  object then slides down with the scroll — this is the whole mechanism behind
  "stop-and-go" and the jerky crawl of ground vehicles.
* The scroll adds 1 px per tick to world y (`glob.340`). Hence vy = +256 is
  stationary on screen (hover), vy = 0 stands on the ground (25 px/s down the
  screen), vy = −512 flies down the screen at 75 px/s.
* Removal: y below scroll − 40, x outside the bounds a script tests (typically
  < −50 or > 434), or off-screen inside homing/booster sub-ops.
* Field x is 0…384; the camera pans horizontally by `glob.348/2`, about 320 px
  visible.

### Conversions

| VM quantity | Real unit |
|---|---|
| tick | 1/25 s |
| v (1/256 px/tick) | v · 25/256 px/s |
| a (1/256 px/tick²) | a · 625/256 px/s² |
| angle step (2048/turn) per tick | step · 25 · 360/2048 °/s |
| overlay amplitude A | A/16 px |

### Motion instructions

Time `t` runs t+1 ticks; `#9999` = forever.

| Op | Operands | Per tick |
|---|---|---|
| `04 MOVE` | `vx vy t` | v = (vx, vy); pos += v |
| `08 ACCELV` | `ax ay vx vy t` | first v = (vx, vy); then pos += v; v += a |
| `0c ACCEL` | `ax ay t` | pos += v; v += a |
| `70 MOVE70` | `fx fy t` | pos += v; v = v · f/256 per axis |
| `b0 WAIT` | `t` | pos += v |
| `54 DELAY` | `n` | nothing moves for n+1 ticks |
| `94 HOMING` | `k s t` | every 2nd tick: v = v·k/4096 + s·û + (0, 16), û = unit vector to target with octagonal norm (max + min/2); off-screen → delete |
| `7c`/`80 WOBBLE` | | sine overlay on the **drawn** position (collision uses it too); phase += step (2048 = 360°), amplitude += step |
| `28`–`34 IFxx` | `V field T` | branch on player x/y (`tgt.10`/`tgt.14`), RNG (`glob.3e0/3e2/3e4`) or player rating (`glob.3c4`) |
| `ac TARGET` | | aim at nearer player |
| `90 SETPROG` | | swap movement program, or swap the animation (bank silhouette on turns) |

Motion sub-ops: `20 0c` velocity from parent, `20 30` random direction (16
entries, |v| = 2048), `20 64` circle, `20 18c` booster (×266/256 per tick with
downward bias), `20 1b4` random 3-way branch, `20 1b8` player-position 3-way
branch, `20 e0`/`e4` helicopter, `20 158`/`1d0` walker step, `20 164` boat
bob, `20 174`/`178`/`184` train, `20 c0` bullet to edge, `20 3c` toss.

### Facing

Sprite direction comes from (1) explicit `SET #bob obj.4a` / animation swaps at
segment boundaries (straight / bank / hard bank, or 90° steps in a U-turn),
(2) `84 HOME84` — direction to the player in 8 or 16 sectors mapped to a frame,
(3) `88 HOME88` — the same from own velocity, (4) `20 64` circle: frame =
`(angle >> 7) & 7` + 1, (5) a loop of `ACCEL ±96 0 #1` repeated until the frame
reaches a target (L4 `28`/`2c`).

## Archetype catalogue

"Types / spawns / instances": types assigned to the archetype, spawn records
using them, and objects seen in a full emulated play-through (includes
children and bullets). "Verified": types whose every compared instance matched
the emulation with mean error < 2 px, out of types compared, and the mean
error over those types. Numbering has gaps (no A02, A26).

| ID | Archetype | Levels | Types / spawns / inst. | Key numbers | Verified | Confidence |
|---|---|---|---|---|---|---|
| A01 | Static ground object | all | 154 / 805 / 952 | moves only with scroll, 25 px/s | 14/15, 0.3 px | high |
| A03 | Straight line, constant speed | all | 36 / 162 / 183 | 25 / 50 / 75 / 102 px/s for 3–6 s | 33/34, 0.3 px | high |
| A04 | Step crawl (vehicles) | L1–L4 | 40 / 395 / 433 | 4 px every 0.08 s = 50 px/s, 3–40 steps | 21/38, 3.8 px | high |
| A05 | Accelerating dive | L3 | 1 / 18 / 22 | v0 62.5 px/s, a 39 px/s² | 1/1, 0.0 px | high |
| A06 | Dive + fixed peel-off | L1, L3 | 8 / 188 / 190 | 0.8 s straight, lateral a 98–146 px/s², exit 45° ~315 px/s | 5/8, 1.5 px | high |
| A07 | Dive + turn toward player | L1, L3, L4 | 4 / 89 / 157 | one decision after 0.2–0.56 s, lateral a 59–117 px/s² | 3/4, 0.5 px | high |
| A08 | Side-entry arc | L1, L3 | 14 / 100 / 109 | entry 40 px/s, arc a (59, ±117) px/s² for 2.2 s | 13/14, 0.4 px | high |
| A09 | U-turn | L1, L3 | 16 / 234 / 234 | pass 62–121 px/s, brake 270–500 px/s², turn 0.36–0.48 s, R ≈ 25 px | 15/16, 0.4 px | high |
| A10 | Half-loop / "J" (rotating a) | L4 | 8 / 103 / 103 | entry 150–175 px/s, 6–9 segments of 0.12–0.16 s, 114–421° | 6/8, 1.1 px | high |
| A11 | Enter – hover – leave | L1–L4 | 21 / 120 / 120 | entry 50–75 px/s, hover 3–4 s, leave 50 px/s up | 16/21, 3.3 px | high/medium |
| A12 | Slide in from side, park, withdraw | L1, L2, L4 | 33 / 102 / 102 | 50–100 px/s, brake 39–78 px/s², park 3.6–4 s | 24/28, 4.0 px | high |
| A13 | X-axis pursuit (bang-bang) | L1 | 3 / 31 / 31 | a_x 44 px/s², |v_x| ≤ 100 px/s | 2/3, 0.3 px | high |
| A14 | Inertial homing + booster | L4 | 3 / 102 / 195 | steer every 0.08 s, terminal 47–352 px/s, ~78°/s, booster ×2.6/s | 2/3, 0.7 px | high |
| A15 | Helicopter: thrust + drag | L2 | 3 / 74 / 74 | τx 0.64 s, τy 0.16 s, v_max 100 px/s, 22.5° per step | 0/1, 5.1 px | medium |
| A16 | Circling | L3 | 1 / 5 / 5 | 50 px/s, 44°/s, R 65 px, reversal p = 0.76 %/tick | 1/1, 0.2 px | high |
| A17 | Sine overlay | L1–L4 | 13 / 68 / 93 | amplitude 3–33 px, 9–176°/s, axes independent | 9/10, 1.5 px | medium |
| A18 | Ballistic throw / jump | L1–L4 | 35 / 59 / 429 | g 78–488 px/s², v0 59–150 px/s | 18/35, 10.8 px | medium |
| A19 | Random 3-way fork | L4 | 1 / 23 / 23 | p = 62.5 / 18.75 / 18.75 %, every 0.48 s | 0/1, 9.9 px | medium |
| A20 | Fork by player position | L4 | 3 / 8 / 39 | dead zone ±30 px, decision every 0.16 s | 0/3, 7.2 px | medium |
| A21 | Walker | L4, LB | 5 / 19 / 19 | steps 3/7/12 px, 0.8 s cycle, ~27 px/s | 2/5, 8.9 px | medium/low |
| A22 | Train on a track | L3, L4 | 6 / 17 / 17 | shared global speed for the whole train | 1/3 | low |
| A23 | Boat: bob + rocket salvo | L4 | 5 / 26 / 26 | vy within ±25 px/s, 4 s cycle, 4–5 rockets | 1/1, 0.0 px | medium/low |
| A24 | Boss entry and hover | L1, L2, L4, LB | 15 / 19 / 21 | 98 px/s → 0 at 49 px/s² (2.5 s), or 394 px/s → 0 (1.3 s) from the side | 11/14, 4.9 px | medium |
| A25 | Carrier / formation | L1, L3, L4 | 12 / 71 / 82 | children every 1–1.6 s, offset ±10 px | 8/12 | medium |
| A27 | Pulsed bursts | L3 | 2 / 49 / 49 | reset to 75 px/s, brake 24 px/s², period 0.2–1 s | 1/2, 1.6 px | medium |
| A28 | Boss part (code-driven) | L2, L4, LB | 12 / 6 / 128 | position computed in a sub-op | 2/6 | — |
| B1 | Aimed bullet | L1–L4 | 14 / – / 2,304 | vector from shooter | not compared | medium |
| B2 | Fixed-direction bullet | all | 38 / – / 3,438 | 75–106 px/s, fans 0 / 15 / 25.7 / 45° | 4/4, 0.0 px | high |
| B3 | Bullet with one-off aim | L1, L3, L4 | 4 / – / 586 | 100–150 px/s | not compared | medium |
| B4 | Random debris | L1, L2, LB | 3 / – / 154 | 200 px/s, drag ×0.66/tick | 3/3, 0.2 px | high |

Mean errors for A22, A25 and A28 are dominated by globally driven or
code-positioned objects and are not meaningful.

## Archetype rules

Units: px/s, px/s², seconds. VM values in program fragments are raw.

**A01 Static.** No motion instruction (`DELAY 9999` or `MOVE 0 0 #9999`).
Fires: turrets with 4/5/8/16 directions, `HOME84` barrel tracking, offset
spawns.

**A03 Straight.** `MOVE vx vy #n`, or `MOVE … #0` inside a `LOOP n`. Ends on
time, on an `IFLT/IFGT obj.10` edge test, or parks with `MOVE 0 0 #9999`.

**A04 Step crawl.** Loop n+1 times `{ MOVE ±1024 0 #0 ; DELAY 0 }` — 4 px, one
tick still — then `DELAY 9999`, a 90° change of direction (`MOVE 0 -768`), or a
turn frame. Variants ±256 (1 px), diagonal ±512/−512, ±1152/±1408 (56–69 px/s).
The most common ground movement.

**A05 Accelerating dive.** `ACCELV 0 -16 0 -640 #11` then `ACCEL 0 -16 #9999`.

**A06 Dive + peel-off.** L1 `1b4` (first wave):
`MOVE 0 -512 #9` ×2 (75 px/s on screen; a chance shot `20 68` between),
`ACCEL 40 -20 #3`, `#5` (bank frame), `ACCEL 60 -35 #13` (hard bank),
`ACCEL 40 -40 #49` (exit ~45°). Mirrored pairs (`1b0`/`1b4`).

**A07 Dive + turn to player.** `ACCELV 0 -16 0 -640 #11`, then **one**
`IFLT tgt.10 obj.10` decision, then `ACCEL ±32 -16` segments. No later
correction — the player can sidestep.

**A08 Side arc.** `ACCELV ±8 0 ±412 0 #39` (1.6 s horizontal, 40→71 px/s), then
`ACCEL ±24 ±48` for 2.2 s: an arc up or down the screen, diagonal exit.

**A09 U-turn.** L1 `1d8`/`1dc`: `MOVE 0 -640 #39`, `ACCEL 0 110 #3` ×3
(269 px/s², vy → +680), then two diagonal `ACCEL` segments away. Horizontal
variant: 102 px/s for 2.6 s, `ACCEL ∓170` ×12 ticks (415 px/s², R ≈ 25 px).
Rotation frames swapped in three steps.

**A10 Half-loop.** L4 `30`/`34`: `ACCELV 0 128 0 -1536 #10`, then 6–9 `ACCEL`
segments of 4 ticks whose vector rotates (`-160 -60`, `-200 60`, `-200 160`,
`-50 160`, `40 160` …) — a discretised loop.

**A11 Enter – hover – leave.** L1 `11c`: ~4.1 s down at 75 px/s,
`MOVE 0 256 #75` + `WAIT #23` (4 s hover), then six ~1 s `MOVE 0 768` segments
up the screen with bomb spawns gated by rating thresholds 50…175.

**A12 Side slide / park.** L2 `8c`–`a8`: ~3 s at 50 px/s, `MOVE70 217 217 #15`
(×0.85 per tick to a stop), `DELAY 89–99`, then `ACCELV ±32 0 0 0` until
off-field, `END`.

**A13 X pursuit.** L1 `9c`: down at 50 px/s; each tick `ACCEL ±18 0 #0` toward
the player while |vx| < 1024, else coast; once past the player
`MOVE70 240 270` (x ×0.94, y ×1.055 per tick). Bang-bang without prediction.

**A14 Inertial homing.** L4 `c8`: entry `ACCELV 0 128 0 -1024 #7`, then
`HOMING 3584 60 15`, `HOMING 3884 130 7`, `HOMING 3914 160 19`, then booster
`20 18c` until off-screen. Turn per step ≈ atan(s/|v|). Variants switch phase
count by rating (`IFLT #200 glob.3c4`) or by a parameter from the parent.

**A15 Helicopter.** Each tick vx −= vx/16, vy −= vy/4, vy += 32, v += T[h],
with a 9-entry thrust table from (64, 0) through (0, −128) to (−64, 0). Every
2nd tick the heading h moves one of 16 sectors toward the player; after 10
ticks on target it fires. Modelled qualitatively (mean 5 px).

**A16 Circling.** `20 64` with `obj.4c` = 40, `obj.4e` = 1280, `obj.50` = 10:
2 px per tick, angle step 10 (44°/s), R 65 px; random reversal when the RNG
exceeds `0xfe0`.

**A17 Sine overlay.** `7c WOBBLE` on the drawn position. Examples: Lissajous
3:2 (x 6.25 px / 2 s, y 10.6 px / 3 s); 32.5 px both axes; falling leaf
(x 22 px, descent 25 px/s). Checked from code: emulation logs record the
logical position only.

**A18 Ballistic.** `ACCELV` with ay < 0 as gravity; g = 78–488 px/s², v0
59–150 px/s. Some types pick one of three arcs from a parent parameter
(`obj.5e`).

**A19 Random fork.** L4 `c4`: 13 × `20 1b4` choosing straight (62.5 %) or
±64 sideways (18.75 % each, only within ±4 px of the start x), then a random
diagonal, then the A14 homing chain.

**A20 Player fork.** L4 `120`/`134`/`138`: every 4 ticks `20 1b8` (±30 px
dead zone) chooses `ACCEL 0 -32` or `ACCEL ±16 -32`; six rounds, then drag and
exit.

**A21 Walker.** `20 158` with `DELAY 2, 2, 13`: steps (−3,+3), (−7,−1),
(−12,−2); boss walker `20 1d0`. Simulator model simplified.

**A22 Train.** The locomotive writes speed `glob.3e6` and direction
`glob.3f0`; wagons add `glob.3e6` to x each tick and are unhittable outside the
track window (tunnel).

**A23 Boat.** `20 164` changes vy by 8 or 16 per tick within ±256 following
bit patterns over a 100-tick cycle; between calls 4–5 `SPAWNREL` homing rockets
(A14) at fixed offsets.

**A24 Boss entry.** `ACCELV 0 20 0 -1004 #62` then `MOVE 0 256 #9999` (hover).
Mid-bosses enter from the side with `ACCELV 128 0 -4032 256 #31` plus a
Lissajous overlay, then wait loops with RNG-gated short bursts.

**A25 Formations.** There is no leader/follower formation. "Formations" are
spawn records 8 px of scroll apart (alternating mirrored types), or parents
spawning children every 1–1.6 s.

**A27 Pulsed bursts.** L3 `158`: repeated `ACCELV -10 0 768 0 #n`
(n = 22, 4, 9, 25, 4, 13) — speed reset to 75 px/s, braked at 24 px/s², a
rowing motion.

**A28 Boss parts.** Position computed in sub-ops (stuck to the body, arm
segments, slots); not a motion pattern.

**Bullets.** B1 `20 0c` + `20 c0` (vector from shooter, straight flight);
B2 fixed vectors (0, −768), (±543, −543), (±768, −768), (±452, −937),
(±265, −989) — fans built from separate types; B3 `TARGET` + `HOMING 0 s 0`
(one-step aim, 100/120/150 px/s); B4 `20 30` (200 px/s in 1 of 16 directions)
+ `MOVE70 170` (×0.66 per tick).

### Movement and fire

Aircraft fire with `20 68` at a fixed point of the path, before the turn;
hovering types fire salvos and drop bombs gated by `IFGT #threshold glob.3c4`;
the helicopter fires only after holding its heading for 10 ticks; ground
turrets aim with `HOME84`. Steering toward the player is deliberately crude:
a single decision (A07), bang-bang with a limit (A13), three lanes with a dead
zone (A20), or homing every second tick with inertia 0.875–0.98 (A14).

## Verification

1. **Extraction.** `tools/movement/vmextract.py` reads each unpacked level
   file, follows every type's movement program (jump graph) and the types it
   spawns → `vm_types.json` (553 types).
2. **Simulation.** `tools/movement/vmsim.py` implements the motion
   instructions and motion sub-ops above, using the game's own sine table
   (`hunk1+0x6132`) and direction tables, read from `bans.exe`.
   `python tools/movement/vmsim.py --exe bans.exe --levels <dir> L1 1b4` prints the
   simulated track every 5 ticks.
3. **Reference tracks.** Full play-throughs of every level in an emulator log
   every live object every tick; `traces.py` assigns each object to its type by
   the program counter of its movement program.
4. **Comparison.** `verify.py` places the simulated object at the logged spawn
   point with the logged player positions and compares positions tick by tick,
   up to 8 instances per type → `weryfikacja.json`. A type counts as matching
   when every compared instance has mean error < 2 px.
5. **Classification.** `classify.py` assigns types to archetypes;
   `report.py`/`build_json.py` produce the per-archetype parameters
   (`archetypes.json`).

Steps 1 and 2 are in [`tools/movement/`](../tools/movement/) and run from
the unpacked level files and `bans.exe` alone (see
[`tools/README.md`](../tools/README.md)). Steps 3–5 need the emulator harness
and its logs, which are not part of this repository.

Result: **294 types compared, 216 match (73 %)**; 135 of those with maximum
error exactly 0.0 px.

| Level | Compared | Match |
|---|---:|---:|
| L1 | 92 | 78 |
| L2 | 86 | 53 |
| L3 | 66 | 53 |
| L4 | 42 | 24 |
| LB | 8 | 8 |

The 78 mismatches fall into: random types (RNG state not reproduced),
types driven by globals (train, boss directors), objects shot down mid-path
(the death program takes over — flagged `end`), objects at rest or off-screen
(`rest`, `offscreen`), and three sub-ops modelled approximately (helicopter
`20 e0`, walker `20 158`/`1d0`, boat `20 164`).

## Confidence and limits

* **High** where the simulator matches emulation to the pixel: all
  segment-based paths (A03–A13, A16) and fixed bullets.
* **Medium** for archetypes reproduced qualitatively or from code only: the
  sine overlay (not present in the logs), helicopter, forks (RNG/player
  dependent), ballistic children (parameter from the parent).
* **Low** for the train and the walker step: modelled from code, globals not
  simulated.
* Logs sample the logical position only, not the drawn one, and no internal
  fields; A21–A23 and boss variants are approximations.

## Open questions

1. Seeded RNG reproduction would let A18–A20 be verified exactly.
2. Train (A22) and boss parts (A28) need the globals they read simulated.
3. Exact helicopter model (A15): the thrust/drag constants fit the code, but
   mean error remains 5 px.
