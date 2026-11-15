# Player, scoring and difficulty

The player's ship, its weapons, shield and lives, the pods, the score rules,
the **player rating** at `(0x3c4)` that drives the dynamic difficulty, what
the three difficulty settings change, and the shape of the difficulty curve
across the game. The per-level content is in
[16-levels-and-bosses.md](16-levels-and-bosses.md).

## Method and conventions

* **Static:** disassembly of hunk 0 (the player, collision, pod, rating and
  score code) and the per-level tables.
* **Emulator:** measurements in a machine68k-based emulator. Values marked
  *measured* were checked there against the code; all other values are read
  from code or data.
* The curve figures in the last section come from **one run per level**:
  the player was **invincible**, fired continuously, and an autopilot aimed
  at the lowest-HP object and collected pods. They are **emulator-only**.
* **1 tick = 1/25 s.** The game waits for two VBlanks per logic step. The
  rate did not change at 0.28, 0.6 or 2 million CPU cycles per frame, so it
  is deliberate, not a CPU limit; this still needs confirming on hardware.
  px/tick × 25 = px/s.
* **Coordinates:** x grows to the right (the world is 384 px wide). World y
  grows **upward**; screen height above the bottom edge =
  `player.y − (0x340)`, and the player may fly between 15 and 236.
* **Addresses:** `hunk0+0x…` as in [00-overview.md](00-overview.md),
  converted from runtime addresses as in chapter 16 (`hunk0+N` = `0x21f000+N`).
  `(0xNNN)` is the word at `A5+0xNNN`, with A5 = `hunk5+0x723dc` (in chip BSS). Player 1's
  structure is at `A5+0x206` and player 2's at `A5+0x298`; `player.X` is a
  field in it.

## The ship

### Hitbox (`hunk0+0xd164`; four extra words in each `plyrmisc` descriptor)

| Part | Size | Relative to the ship's point |
|---|---|---|
| sprite | 32 × 31 px, hot spot (16, 15) | — |
| B, fuselage | **12 × 33** | x −6…+5, y −15…+17 |
| A, wings (no horizontal movement this tick) | **32 × 8** | x −16…+15, y +4…+11 |
| A, wings while banking | **24 × 8** | x −12…+11, y +3…+10 |

A hit means an overlap with A **or** B. The hitbox is a cross that covers
the whole wingspan, about 56 % of the sprite area, so this is **not** a small
bullet-hell hitbox. The same cross collects pods, which are 16 × 16 squares.

### Movement (`hunk0+0xce3c`, state table `hunk0+0xd9d0`)

* **Vertical:** a constant `player.68 = speed/2 + 4` px per tick, with no
  inertia.
* **Horizontal:** a 13-state banking machine (`player.48`, centre 0x84). Each
  state stores a velocity for four speed levels, and the stick input
  (left / none / right) selects the next state. Acceleration, braking and
  reversal all come out of the table.

| Speed (`player.66`) | Vertical | Horizontal max | From rest | Stick released (5 ticks) | Reverse R→L |
|---|---|---|---|---|---|
| 0 | 4 | 5 | 2, 5 | 4, 2, 1, −1, −1 | 2, 0, −2, −5 |
| 2 (game start) | 5 | 6 | 3, 6 | 4, 3, 2, −1, −1 | 3, 0, −3, −6 |
| 4 | 6 | 7 | 3, 7 | 5, 3, 2, −1, −1 | 3, 0, −3, −7 |
| 6 | 7 | 8 | 4, 8 | 6, 4, 3, −1, −1 | 4, 0, −4, −8 |
| 8 (max) | 8 | 8 | 4, 8 | 6, 4, 3, −1, −1 | 4, 0, −4, −8 |

* Full speed is reached in 2 ticks. After the stick is released the ship
  drifts on for 11–13 px and bounces back 2 px.
* *Measured* at speed 4: 3, 7, 7, 7… and 5, 3, 2, −1, −1 after release, as
  the table says.

**Limits:**

* Screen height 15…236, held in `(0x33e)` (lower) and `(0x33c)` (upper).
  Some bosses lower `(0x33c)` so that the player cannot fly above them.
* World x 14…370 in `(0x336)/(0x338)`; arenas narrow it to 78…306.
* A view window of `(0x348)/2 + 15 … + 243`, unless camera tracking is
  switched off in the options (`hunk0+0x32b2`).

**Start and respawn:** P1 starts at x = 0x90 and P2 at 0xf0, both at
scroll + 64. After a death the ship respawns **where it died**, with no
rollback.

## Main gun (`hunk0+0x66c6`)

* **Autofire** while fire is held.
* Each shot is a **pair** of bullets ±8 px either side of the ship (±5 px
  while banking). The two bullets hit separately; when both hit the same
  target in the same tick, the damage is doubled (`hunk0+0x1065c`).
* Bullets fly 25 px per tick, plus scroll compensation, and live 11 ticks
  (about 275 px).

### Fire rate (`player.60`, steps of 0x10; table `hunk0+0x74d0`, 16 B per step)

| Step | Interval (ticks) | Pairs/s | Bullet hitbox w × h, variant 0/1/2 |
|---|---|---|---|
| 0 | 7 | 3.57 | 3 / 5 / 7 × 26 |
| 1 | 6 | 4.17 | 4 / 7 / 9 × 26 |
| 2 | 6 | 4.17 | 5 / 9 / 11 × 26 |
| 3 | 5 | 5.0 | 6 / 11 / 14 × 26 |
| 4 | 5 | 5.0 | 7 / 13 / 16 × 26 |

The intervals are *measured* (7/6/6/5/5). The cap depends on the level:
`levelNf+0x38` → `(0x3ac)`, and a fire-rate pod only works while
`(0x3ac)` > `player.60`. At level start fire rate and speed are raised to the
level minimum (`hunk0+0xfb0e`).

| Level | Max step | Min step (start, after a death) | Min speed (+2 on Easy and Hard) |
|---|---|---|---|
| 1 | 2 | 0 | 0 |
| 2 | 3 | 1 | 2 |
| 3 | 4 | 2 | 2 |
| 4 | 4 | 2 | 4 |
| boss | 4 | 2 | 6 |

### Damage per bullet (`hunk0+0x67b2`)

The index is the word from the fire-rate table (it depends on the step and
the variant) plus `((rating >> 1) & 0x10)`. The tables are at `hunk0+0x73d0`
(normal, one player) and `hunk0+0x7350` (Easy); two-player tables sit +0x80
bytes further on.

| Step \ variant (`player.62`) | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 32 | 42 | 51 |
| 1 | 37 | 47 | 56 |
| 2, 3 | 42 | 47 | 56 |
| 4 | 47 | 51 | 61 |

* When rating bit 5 is set (32–63, 96–127, 160–191, 224–255), the values are
  about 7 % lower: 30/39/47, 35/43/52, 39/43/52, 43/47/56.
* Easy: about +25 %. Two players on normal: about −34 % (21–40). Two players
  on Easy equals one player on normal.
* **Dead table rows:** each table has 8 rows, falling from 32 to 12, but the
  mask `& 0x10` only ever selects row 0 or row 1. `& 0x70` (eight rating
  bands) was probably intended. In practice the rating hardly changes player
  damage. Earlier notes said "the better you play, the weaker your shots";
  that overstates it.

DPS with both bullets hitting (one player, normal): step 0 / variant 0 =
**229 per s**; step 2 / variant 2 = 467; step 4 / variant 2 = **610 per s**
(×2.7).

### Spread (`player.52` = 0/8/16, table `hunk0+0x7338`)

Successive shots take their path type from a cycle (`player.3e += 2`):

| Spread | Cycle | Effect |
|---|---|---|
| 0 | straight ×4 | — |
| 8 (pod 18) | straight, ±2, straight, ±2 | bullets angled ±2 px per tick |
| 16 (pod 18 twice) | straight, ±2, ±6, ±2 | fan up to ±6 px per tick (about 13.5°) |

Pod 19 narrows the spread by 8.

## Side guns (`player.4c` / `player.4d`, pods 16 / 17)

Earlier notes called these "left" and "right". Both actually fire
symmetrically to both sides; the difference is the direction.

| | A (`4c`, pod 16) | B (`4d`, pod 17) |
|---|---|---|
| path | horizontal both ways, ±20 px per tick, +1 up | 45° both ways, ±14 / +14 |
| life | 12 ticks | 18 ticks |
| hitbox | 32 × 5 | 20 × 20 |
| damage | first word of the damage row: 32 (30 with rating bit 5), Easy 40, 2P 21 | same |

The interval is `(0xA0 − player.60)/16 + 5` ticks, which gives 15/14/13/12/11
for steps 0–4 (*measured*). A and B share it. On death A is lost first,
then B.

## Secondary weapon (`player.50`, level `player.6a` = 0/2/4)

It fires with the main gun once its reload (`player.34`) has run out.
Collecting the same pod again raises the level by 2 (max 4). A different
secondary replaces the current one and keeps the level.

| `player.50` | Pod | Behaviour | Damage, level 0/2/4 | Reload (ticks) |
|---|---|---|---|---|
| 0, rocket bomb | only via type 3 (pod 12) | flies straight for 29 ticks, decelerating; delayed area blast in a **90 / 106 / 122 px** square, with shake and flash; the rocket itself does not collide with enemies. **Does not fire while a boss bar is shown** (except in L3) | 170 / 245 / 320 | 50 / 44 / 37 (+1) |
| 1, homing (pod 13) | | steers to `(0x3bc)`, the highest-priority enemy: `v = v·d + K·(target − pos)/dist`, with d = 250/247/240 /256 and K = 0x3800/0x5800/0xa000 /65536; top speed about 9.3–10 px per tick; lives 38 ticks; one hit | **45** | 20 / 13 / 13 (+1); *measured* 21/14 |
| 2, piercing (pod 14) | | launched at 16 px per tick, slows to 2, then accelerates after 12 ticks; lives 31 ticks; **after a kill it flies on with the remaining damage** | 250 / 310 / 370 | 60 / 42 / 30 (+1); *measured* 31 at level 4 |
| 3, special (pod 12) | | the first shot is rocket type 0x24 (as type 0 with a stronger shake), then `player.50 = 0` | as 0 | as 0 |

**Smart bomb** (pod 11 "skull", or script op `a8`): a flash and shake, then
about 2 ticks later **600 damage** to every hittable object on screen
(`hunk0+0x10376`). **Smart-bomb kills score nothing**: the killer is set to 0x80,
and `SCORE` checks the sign of that byte. There is no bomb button.

## Shield, death, lives, invulnerability

| Item | Value | Where |
|---|---|---|
| shield | **0–18**; refilled at level start, on respawn and on continue | `player.64` |
| hit by a bullet (an HP-0 object) | **−1**, or **−2** at rating ≥ 168; then 6 ticks (0.24 s) of protection | `hunk0+0xff5a` |
| collision with an enemy | **−3 − rating/64**: −3 / −4 / −5 / −6, and **−7** above 250; then 14 ticks (0.56 s) | `hunk0+0xff82` |
| damage dealt to the enemy by ramming | 12 HP, or 32 HP per tick during a loop | `hunk0+0xffc0` |
| shield reaches 0 | 47-tick explosion (1.9 s), then respawn | `hunk0+0xffa8` → `hunk0+0xfb6c` |
| protection after respawn | **75 ticks (3 s)**, *measured* | `player.3c` |
| protection at level start or after a continue | 50 ticks (2 s) | `hunk0+0xfb0e` |
| shield pod | +6 (max 18) and 50 ticks of protection | `hunk0+0xf1f2` |
| lives | start with **2 spare (3 ships)**, max 9 | `player.5c` |
| **extra life** | **every 10,000 points** (BCD threshold in `player.54`), per player | `hunk0+0x1134c` |
| loops | start with 3; **refilled to at least 3 after every death**; max 9 | `player.5e` |
| fatal obstacles (`obj.3e & 0xd0`) | kill through the shield | — |
| light-layer polygon (L4/boss) | −5 shield per tick of contact | `hunk0+0x100a2` |

The protection timer is `player.36` ≠ 0; the ship blinks while bit 0 of
`player.3c` is 0.

**Loop** (second button, `hunk0+0xce5a`, path `hunk0+0xd4f8`):

* It costs one charge. The ship is untouchable for the whole manoeuvre and
  the gun is silent, except in L4 and the boss level (`(0x906)` ≠ 0).
* The ship climbs at +8 px per tick to the top edge, turns, dives to y=42 and
  exits. This takes at most 88 ticks, typically about 58.
* **After the loop come 175 ticks (7 s) of blinking protection.** *Measured:*
  about 9 s of invulnerability per charge, which is very generous.

**Death losses and insurance** (`hunk0+0xfb6c`, `player.4e` 0–3, pod 5):
insurance drops by 1 on every death, and the value before the death decides
the loss.

| Insurance before death | Loss |
|---|---|
| 3 | **nothing** |
| 2 | fire rate to the level minimum, spread −8 |
| 1 | as above, plus speed −2 (if above the minimum) and one side gun |
| 0 | as above, plus **the secondary weapon** and bullet variant −1 |

Every death also zeroes points-since-death and time-alive, and sets the
shield to 18, loops to at least 3 and 75 ticks of protection.

**Continues** (`hunk0+0x7e4c`, `hunk0+0xf5dc`):

* **4 credits, shared** by both players (`(0x32a)`).
* A player with no lives can rejoin at any moment with fire (drop-in).
* A continue sets the score to 0, 2 spare lives and 3 loops, keeps the
  weapons as they were after the death, and sets the next extra-life
  threshold to 10,000.
* When both players are dead there are 125 ticks (5 s) to decide.

## Pods (power-ups)

**Who drops them.** Only spawns with a non-zero `drop` field: they are
placed by hand and there is **no random drop rate**.

* Per level: L1 41, L2 55, L3 44, L4 62, boss 7.
* A pod appears only if the enemy dies at x 8…376.
* In the emulator a pod appeared every 15–21 s, 3–4 per minute.

**Behaviour** (`hunk0+0xee68`, created at `hunk0+0x11cbc`; 8 slots at `A5+0x11a8`,
20 B each):

* **Launch:** an impulse with vx −16…15 (pushed toward the centre when x < 96
  or ≥ 288) and vy +16…47, both halved every tick. The pod drifts about
  ±30 px sideways and 32–94 px up.
* **Fall:** after that it moves −1 px per tick in the world, about 2 px per
  tick down the screen at the normal scroll. It vanishes 10 px below the
  bottom edge, about 3 s from mid-screen.
* **Randomness:** an LCG (step 0x1376) mixed with the players' positions.
* **Icons:** a pod carries 3 icons. The icon shown changes **only when the
  pod is shot**, never on a timer.
  * After a hit there is a 9-tick animation during which the pod cannot be
    collected or changed; then the next icon shows and the pod is pushed
    +20 up.
  * The first visible icon is **number 1** (the middle of the three), then
    2 → 0 → 1.
  * **16 hits destroy a pod, or 9 on Hard** (`hunk0+0x32bc` < 0; earlier
    notes said "9 on Easy", which is wrong). A destroyed pod scores nothing.
* **Two players:** each drop makes **two** pods. Depending on the option
  `hunk0+0x32bb`, there is one for each player or two shared ones.

**Effects** (index = icon − base; base P1 0xad, P2 0x93, shared 0xe4; jump
table `hunk0+0xf168`):

| # | Effect | Cap | # | Effect | Cap |
|---|---|---|---|---|---|
| 0 | **speed** +2 (`player.66`) | 8 | 10 | +5000 points | — |
| 1 | fire rate +1 step | level cap | 11 | smart bomb | — |
| 2 | bullet variant 1 (only from 0) | — | 12 | secondary type 3 → rocket bomb (or +level) | level 4 |
| 3 | bullet variant 2 | — | 13 | homing (or +level) | level 4 |
| 4 | +1 life | 9 | 14 | piercing (or +level) | level 4 |
| 5 | +1 insurance | 3 | 15 | shield +6 and 2 s protection | 18 |
| 6 | +1 loop | 9 | 16 | side gun A (horizontal) | — |
| 7 | nothing | — | 17 | side gun B (diagonal) | — |
| 8 | +1000 points | — | 18 | spread +8 | 16 |
| 9 | +2000 points | — | 19 | spread −8 | 0 |

Effect 0 is the ship's speed, not gun power; the gun never reads
`player.66`.

**Mix across the game:**

* First visible icon: shield 48, speed 38, insurance 27, loop 18, fire rate
  14, homing 13, side gun A 12, variant 1 10, life 9, spread 8, points 5,
  smart bomb 4.
* All three icons: insurance 140, shield 81, fire rate 67, speed 64.

About half of the icons are defensive.

## Score

**Per enemy:** op `78 SCORE flag BCD.l` in the death script.

* The points go to the player in `obj.84` (the last hit). A flag ≠ 0 means
  both players get them.
* The four bytes are added with `abcd`, so values with non-BCD digits carry
  oddly: `0x14a1` adds about 1501, and the final ship's `0x1282a` about
  12,830.
* The same sum also goes to the points-since-death counter `(0x3ce)`.

| Enemy HP | Types | Points (median; range) |
|---|---|---|
| < 60 | 49 | 15 (8–75) |
| 60–149 | 22 | 40 (4–77) |
| 150–399 | 90 | 50 (10–305) |
| 400–999 | 51 | 125 (15–402) |
| ≥ 1000 (boss parts) | 24 | 402 (131–12,830) |

The median is **about 0.27 points per HP** (quartiles 0.14–0.52).

* **Sum over each level's spawns** (excluding script children and pods):
  L1 ≈ 24,200, L2 ≈ 20,700, L3 ≈ 15,600, L4 ≈ 38,300, boss ≈ 20,100. That
  is **2–3 extra lives per level** at the 10,000 threshold.
* Pods add +1000 / +2000 / +5000 points.
* **No multipliers, no combos, no completion bonus.** `hunk0+0x6276` only saves
  the players' state and fades out.
* The score is 8 BCD digits (`player.58`).
* Op `9c` (subtract BCD from the killer's score and adjust the rating)
  exists in the engine, but **no script uses it**.
* On Easy the end-of-game path skips the high-score table.

## Player rating `(0x3c4)`

### Formula (`hunk0+0xcb5a`, called every tick; four phases in turn, so each part refreshes every 4 ticks)

```
rating = 32 × (side guns A+B, P1+P2)
       + 40 × (number of players with a secondary weapon)
       + ( S_time/2 + S_score + S_sincedeath ) / 2
       +  4 × (bullet variant P1+P2)            ; player.62 = 0/4/8
       +  2 × (speed P1+P2 − 2·min_speed)       ; min from levelNf+0x3a
       +      (fire rate P1+P2 − 2·min_rate)    ; player.60 in 0x10 steps → +16 per step
       +      (secondary level P1+P2)           ; 0/2/4
       + 32 × (insurance P1+P2)
       + (0x3c2)                                ; script adjustments, zeroed at level start
two players: × 9/16;  then Easy +0, Normal +64, Hard +128;  clamped to 255
```

* **S_time** `(0x3ca)` = min(time since death / 128 ticks, 32) + 2 × lives
  (P1+P2) + loops (P1+P2). It gains +1 every 5.1 s and maxes out after 2:44.
* **S_score** `(0x3c6)` = the mean of the P1 and P2 score ranks. A rank is
  4 × the number of thresholds at or below the score, from 1000, 2000, 3000,
  4000, 5000, 10k, 15k … 55k (0–60). In one-player games P2's score is 0, so
  this term is halved.
* **S_sincedeath** `(0x3c8)` = the rank of points scored since the last
  death; thresholds 200, 300, 400, 500, 1000 … 16,000 (0–60).
* **One-player quirk:** the inactive P2 carries 2 lives, 3 loops and speed
  max(2, min), which always adds about +3 to +6.
* **Script adjustments** last until the end of the level: L2 arm-machine
  body +50, L4 mid-boss +50, L1 mid-boss 2 +40, and +9 for each big boulder
  in L3. Only these types write `(0x3c2)`.
* The rating rises with every upgrade, every insurance point, time and points
  without a death. It falls on death (two statistics zeroed, weapons lost)
  and when lives are lost.

Examples (one player, computed from the formula):

| Situation | Easy | Normal | Hard |
|---|---|---|---|
| game start, L1 | 11 | 75 | 139 |
| L1 after about 3 min: speed 4, step 1, variant 1, one side gun, 8,000 points | 106 | 170 | 234 |
| L1 fully armed (no insurance), 20,000 points | 239 | **255** | 255 |
| just after a death (insurance 0) | 32 | 96 | 160 |

On Normal the rating starts above 64 and **reaches the 255 cap quickly** once
the player is well armed. It really moves only between Easy and Normal, and
just after a death.

*Emulator, autopilot:* the mean rating was L2 193 (max 235), L3 165, L4 146
(max 232), boss 81. In L3 an unupgraded invincible player went 0 → 69
(scroll 550) → 123 → 173 → 212 (scroll 11,550) on score and time alone. The
rating was not logged in the L1 run.

### Consumers (R = rating)

| Where | Rule | Scope |
|---|---|---|
| chance shot `20.68 V type flags` (`hunk0+0x12444`) | fires when `rnd(0…127) < R + 64 − V`, i.e. **P = clamp((R + 64 − V)/128, 0, 1)**. At V=50: R=0 → 11 %, R=64 → 61 %, R ≥ 114 → 100 % | L1 (V = 35…90) and L3 (V = 15…70) only |
| L1 `0x78` (16) | second shot if R ≥ 60 | always true on Normal |
| L1 `0x84` (7) | keeps firing forever after its scripted salvos if R > 80 | |
| L1 gunboat `0x11c` (12), `0x204` (4) | second 3-shot fan if R ≥ 110 | |
| L1 gunboat mines | one mine per threshold ≤ R from 50, 75, 100, 125, 150, 175: **0–6 mines** | |
| L1 `0x164` (9) | next shot while `obj.50` (+10 per shot) ≤ R, max 5 | about R/10 extra shots per turret |
| homing rockets, op `98 SWITCHRATING` (spawned L1 type `0x3c`, L3 `0x2c`/`0x30`; L1 `0x38`/`0x40`/`0x44` and L3 `0x34` share the program but are never spawned) | variant = R/64: 0–63 one phase (force 90, 59 ticks); 64–127 one phase (100, 89); 128–191 two phases with re-aim (140); 192–255 three (160) | stronger players face harder-turning, longer-lived rockets |
| L4 ground missile `0x4` | R < 200: 4 short homing phases; R ≥ 200: 2 longer | L4 |
| L2 minelayer `20.f0` | mine interval `(656 − R)/8` ticks: 82 → 50 | L2 |
| player shield | bullet −2 at R ≥ 168; collision −3 − R/64 (max −7) | all levels |
| main and side gun damage | bit 5 of R picks row 0 or 1 (about −7 %) | all levels |
| `20.10` bullet scatter | vx = (rnd − 128)·(R/2 + 192)/64, vy = −5 px per tick | script-spawned bullets: L1 `0x48`, `0x144`; L2 `0x28`, `0x7c`, `0x2b0`, `0x2b4`; L3 `0x44` (see the note under open questions) |

**What does not depend on the rating:** spawn counts and HP, enemy bullet
speed, boss directors, turret sub-ops, and anything in L2 apart from the
minelayer, the shield and the damage row. With a typical in-game rating of
150–230, nearly every `20.68` fires, so in practice the screw tightens
through the thresholds, the homing variants and the shield damage, and
mostly through level content.

## Difficulty settings

The setting is the byte at `hunk0+0x32bc`: > 0 Easy, 0 Normal, < 0 Hard.

| Effect | Easy | Normal | Hard |
|---|---|---|---|
| rating offset | +0 | +64 | +128 |
| enemy bullet speed (`20.c0`, `hunk0+0x12570`) | **×0.75** | ×1 | **×1.25** |
| player bullet damage | about +25 % (own table) | — | — |
| minimum speed per level | +2 | — | +2 |
| hits to destroy a pod | 16 | 16 | **9** |
| ending and high-score table | **none** | yes | yes |

## Two players

* Rating × 9/16, applied before the difficulty offset.
* Gun damage uses the two-player table, about 66 % of the one-player values.
* Two pods per drop (see above).
* Points go to the killer; scripts with a non-zero flag pay both players.
  The points-since-death counter `(0x3ce)` is shared.
* Lives, loops, shield, weapons and the 10,000 threshold are kept per player.
  The 4 continues are shared.
* The enemy and pod RNGs mix in both players' x positions.
* The final boss ship switches its target between the players.

## Difficulty and pacing curve

*Emulator-only*, one invincible autopilot run per level (see Method).
Definitions:

* an **enemy** is a hittable object with HP > 0 that is not a bullet, mine or
  rocket;
* a shot counts as **aimed** if its direction at birth is within 15° of the
  player;
* a **gap** is ≥ 2 s with no enemy and no bullet on screen.

| | L1 | L2 | L3 | L4 | Boss |
|---|---|---|---|---|---|
| run time | 11:24 | 14:15 | 11:31 | 10:55 | 2:27 |
| enemies spawned | 690 | 675 | 778 | 792 | 10 |
| enemies per minute (excl. bosses) | 67 | 57 | 72 | 76 | — |
| median enemy HP | **29** | 110 | 170 | 170 | 1,500 |
| HP per minute (objects < 5,000) | ~6,000 | ~8,700 | ~13,000 | ~16,500 | — |
| enemy bullets per minute (excl. bosses) | **74** | **190** | 160 | 149 | 41 |
| bullets per minute at bosses | 51 | 175 | 30 | 15 | 76 |
| aimed (%) | 44 | 27 | 36 | 43 | 32 |
| bullet speed, median (p10–p90), px per tick | 4.0 (3.3–5.4) | 5.3 (4.8–6.6) | 4.0 (3.5–5.1) | 4.6 (3.4–5.6) | 6.1 (5.3–8.3) |
| bullets on screen, p95 / max | 5 / 13 | 9 / 20 | 8 / 22 | 6 / 14 | 7 / 13 |
| homing rockets fired | 11 | 0 | 33 | **108** | 0 |
| mines | 5 | 13 | 36 (static) | 0 | **75** |
| pods seen / records with a drop | 39 / 41 | 41 / 55 | 38 / 44 | 44 / 62 | 7 / 7 |
| gaps ≥ 2 s: count / longest | 7 / 8.8 s | 8 / 12.8 s | 8 / 10.9 s | 10 / 6.4 s | 3 / 20.9 s |
| screen without an enemy (% of time) | 12 | 9 | 16 | 11 | 24 |
| mean rating | — | 193 | 165 | 146 | 81 |

**Key numbers:**

* **Difficulty grows through toughness, not numbers.** Enemies per minute
  stay at 57–76, while median HP goes 29 → 110 → 170 and HP per minute
  6k → 9k → 13k → 16.5k.
* Bullet density jumps once (L1 → L2: 74 → 190 per minute) and then eases.
* Stops: a first mid-boss at about 2.5–4 min, a second at 4–8 min, the boss at
  about 10:45. Stops last 15–45 s, and **fire drops during bosses** (except
  the L2 boss, which has its own guns): a boss is a damage check, not a
  bullet wall.
* Breathing room: 16–18 gaps of ≥ 1 s per level (median 1.6–2.7 s), the
  longer ones (6–13 s) right before and after bosses.
* Waves have a median of 10–30 s. Spawns per 30 s swing about 5× (10 ↔ 55, up
  to 80 in L4), pulsing every 1–2 minutes.
* Bullets are slow and readable: 3.3–6.6 px per tick (80–165 px/s), and only
  ⅓–½ are aimed. Faster bullets (6–8) come only in the finale.
* One new threat per level: L1 rating-driven salvos and mines; L2 fatal
  spires and armoured trains; L3 the canyon, charges and static mines; L4
  homing missiles and generator barriers; the boss level a time limit.
* Per-level hardest stretches: L1 the last 2,000 px before the boss; L2 the
  train and churches (up to 172 bullets per 20 s); L3 the opening 2,500 px
  (98–167 per 20 s, the hardest start in the game); L4 the middle
  (8,000–9,500).

**Limits of these numbers:** they come from one autopilot run per level.
Boss and L2 durations are inflated, because the autopilot is weaker than a
good player. Bullet counts outside bosses depend on how fast shooters are
killed. The "ground" and "aimed" classes are heuristics. L3, L4 and the boss
level started without carried-over upgrades.

## Open questions

1. ~~**Sources disagree about op `98` and `20.10`.**~~ **Resolved (2026):
   both are used.** A recursive scan of all five level files
   (`tools/scriptdis.py --reach`, following jumps, `SPAWN`/`SPAWNREL`
   children, sub-op operand types and native-code spawns) finds op `98` in
   the movement program of L1 type `0x3c` (spawned by the scripts of types
   `0x78` and `0x1a0`) and of L3 types `0x2c` and `0x30`, and sub-op `20.10`
   in L1 `0x48`, `0x144`, L2 `0x28`, `0x7c`, `0x2b0`, `0x2b4` and L3 `0x44`.
   None of these types is in a spawn list; they are created by other
   scripts, which is why a scan of spawn-list types alone reported both as
   unused. Levels 4 and the boss use neither. Consistent with
   [14-enemy-vm.md](14-enemy-vm.md) and
   [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §4.
2. The 25 Hz logic rate is measured in the emulator only.
3. Whether the high-score entry is really skipped on Easy has not been
   confirmed in the emulator.
4. Whether the light-layer contact drain (−5 per tick) happens on hardware.

## Confidence

* **High (code, several items measured):** hitbox, movement table, fire
  rates, bullet speeds and lives, damage tables, shield and protection
  timers, loop, insurance losses, pod behaviour and effects, score rules,
  the rating formula and the consumers listed with an address.
* **Medium:** the reading of the dead damage-table rows as a bug (`& 0x10`
  against an intended `& 0x70`).
* **Emulator-only, single run:** the whole pacing table, the mean ratings and
  the pod rate per minute.
