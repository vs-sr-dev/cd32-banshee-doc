# Levels and bosses

Each level gets the same treatment: its sections by scroll position, how many
spawns and types it has, what it adds, and how its mid-bosses and boss work.
The boss level (`bossc`/`bossf`), the two endings, the formats of blocks
[3]/[4] and a short list of the boss patterns the game reuses follow at the
end. The file formats themselves are in
[13-level-formats-and-floppy.md](13-level-formats-and-floppy.md). The player
side (weapons, rating, scoring) is in
[17-player-scoring-difficulty.md](17-player-scoring-difficulty.md).

## Method, units and conventions

* **Static:** the spawn list (`levelNf+0x1c`), the type table (`+0x0e`) and
  the enemy VM scripts (`+0x12`) of every level, decoded in full. All five
  script sets disassemble recursively with no unknown opcodes (L1 2,478
  instructions, L2 3,446, L3 1,747, L4 1,964, boss 545).
* **Dynamic (emulator only):** `bans.exe` running under a machine68k-based
  emulator with stubbed libraries. The player was **invincible**, fired
  continuously, and an **autopilot** aimed at the object with the lowest
  HP. There was **one run per level**. Levels 3, 4 and the boss level were
  started by patching the level sequence, so the ship started with no
  upgrades in those runs. Boss fight times from these runs are therefore
  **upper bounds**. Section times that depend only on the scroll are
  reliable.
* **Time:** the game logic runs every second PAL frame, so **1 tick = 1/25 s**.
  The scroll advances 1 px per tick, so 1,000 px ≈ 40 s. Speeds are in
  1/256 px per tick unless given in px/tick.
* **Positions** are spawn triggers, i.e. the scroll position in pixels from
  the bottom of the map. When a background loop is running, the trigger is
  measured against `scroll − segment` (see the next section).
* **Addresses** follow [00-overview.md](00-overview.md): `hunkN+0x…` for
  `bans.exe` (converted from Ghidra/emulator addresses with the hunks packed
  from `0x21f000`; hunk 0 = `0x21f000`, hunk 1 = `0x236cdc`, hunk 2 =
  `0x23d610`, hunk 4 = `0x291084`, hunk 5 = `0x2951f4`), and plain offsets for level files. The level `f` file is loaded
  at `hunk2+0x0` (runtime `0x23d610`, the start of hunk 2's BSS), which is
  why object script pointers minus that base give file offsets.
  `(0xNNN)` means the word at `A5+0xNNN`, with A5 = `hunk5+0x723dc` (in chip BSS); `obj.X` is a
  field of an enemy object. These are the global and object fields used by
  this chapter, not a full map.
* Bob numbers in scripts **count from 1**: the descriptor is
  `bank + 4 + 20·(n−1)`, and bob 0 means "no bob".

## Machinery shared by all bosses

| Mechanism | How it works | Where |
|---|---|---|
| Boss bar | `(0x5de)` ≠ 0 shows a 32-segment bar drawn by `hunk0+0x82ac` as `32·(0x8f6)/(0x8f4)`. `(0x8f4)` is the total and `(0x8f6)` the damage done. Only hits on objects with **bit 10 (`0x400`) of `obj.3e`** count. On the kill the overshoot is subtracted again, so the bar is exact. `(0x5de)=17` hides it | every boss and mid-boss; L3 reuses it as a 0/60 counter |
| Hit immunity | bits 0–2 of `obj.3e` ≠ 0 means player shots do not hurt. Scripts switch `0x1000` ↔ `0x1007` (or `0x1400` ↔ `0x1407`), which gives **vulnerability windows** | L2 boss, L2 airship, final core B |
| Indestructible frame | bodies and arms get 10,000 HP **rewritten every tick** | L1 pendulum, L2/L4 arm machine, final spikes |
| Background loop | sub-op `20.f8` sets `(0x354)` = scroll + 256. When the scroll reaches it, the ground decoder state is restored from `hunk0+0xe860` and the segment `(0x350)` grows by 256. The ground repeats and **spawns stand still**. The boss clears `(0x354)` when it dies | all bosses and mid-bosses of L1, L2, L4 |
| Scroll stop / chase | `(0x35a)`: 0 normal, −1 stopped, −2 the camera follows the boss | boss level |
| Arena | `(0x334)=1` narrows the player's x limits `(0x336)/(0x338)` from 14…370 to **78…306**, 2 px per tick (`hunk0+0xcd4c`), and freezes horizontal camera tracking. `20.12c a b` sets the player's **upper** flight limit `(0x33c)` to `b` px below the object | L1 boss, L3 canyon, L4 mid-boss; `20.12c` at L1 boss (68 px) and L2 boss (62 px) |
| Director | an invisible object draws (RNG `(0x3e4)`) which part attacks and how long the pause is. Parts wait for their number in a global | L2 boss, both final stages, arm machine |
| Kill counter | a global mask or counter (`(0x3e8)`, `(0x3ea)`, `(0x3ec)`); each part adds a value; phase changes on a threshold | all |
| Fatal obstacle | `obj.3e & 0xd0` kills on contact **through the shield** | L2 church spires, L2 boss director |
| Rating bump | `ADD … (0x3c2)` raises the player rating until the end of the level | L1 MB2 +40, L2 MB1 +50, L3 boulders +9 each, L4 MB +50 |
| Level end | `(0x5e8)=1` (sub-op `20.154` or `20.88`, or a controller type). The level loop jumps to `hunk0+0x6276`, which copies the players' state to `hunk0+0x3308` and fades the palette in 16 steps. **There is no completion bonus** | all |

**No boss reads the player rating directly.** The rating reaches bosses only
through the shared effects in chapter 17 (shield damage, and the gun damage
row).

## Level sequence and transitions

The game sequence at `hunk0+0x2ba2` calls the five level routines in order:
`hunk0+0x3084` (L1), `hunk0+0x30e2` (L2), `hunk0+0x311a` (L3), `hunk0+0x3152` (L4),
`hunk0+0x3192` (boss). Between them it calls `hunk0+0x4f4c`. Earlier notes called
`hunk0+0x4f4c` a summary screen. It is not: it sets up the **text screen** (it
unpacks the menu font from `hunk1+0x602` and installs the text-screen frame
handler `hunk0+0x43cc`). It computes no statistics and no bonus. Each level
routine then shows its briefing page and loads its files through the file
table at `hunk0+0x2806` (records hold `bansheeN:file`, a length and a disk
number). The loaders for level 1/2/3/4/boss are `hunk0+0x22a6` / `hunk0+0x22ce` /
`hunk0+0x22ea` / `hunk0+0x2306` / `hunk0+0x2322`, and the current number is kept at
`hunk0+0x32c2`.

* **Upgrades carry over.** `hunk0+0x6276` saves side guns, secondary weapon,
  insurance, spread, lives, loops, fire rate, bullet variant, speed and score
  to `hunk0+0x3308`. The next level restores them at `hunk0+0xf53a` and then raises
  fire rate and speed to that level's minimum.
* Level 3 loads `level3c` from `banshee3:` and `level3f` from `banshee4:`. On
  floppy that is a disk swap in the middle of a load.
* Level 4 switches to `plyrmisc4` (the player becomes a jet) and `soundfx4`.
  The boss level keeps both.
* From level 4 on, `(0x906)=18` and `BPLCON0 = 0x0211` (eight bitplanes;
  levels 1–3 use `0x6201`). The extra two planes carry the light layer
  (blocks [3] below). `(0x908)` holds the level number.

## Level overview

| | L1 | L2 | L3 | L4 | Boss |
|---|---|---|---|---|---|
| Setting | sea, port, town, railway, hangar | city, cemetery, suburbs, factories | desert, swamp, canyon, fortress | space, orbital station, base | fortress and chase |
| Map height (px) | 15,488 (968 rows) | 14,880 (930) | 17,504 (1,094) | 16,032 (1,002) | 1,056 (66) |
| Spawn records | 677 | 631 | 778 | 781 | 26 |
| Types defined / in the spawn list | 145 / 110 | 174 / 121 | 107 / 77 | 104 / 70 | 23 / 16 |
| Bobs in bank | 561 | 697 | 654 | 513 | 530 |
| Cloud layer | yes | no | yes, only scroll 5010–7578 | no | no |
| Spawns with a pod drop | 41 | 55 | 44 | 62 | 7 |
| Mid-bosses | 2 | 2 | 0 | 1 | — |
| Final fight | hangar with pendulum | rail machine | fortress, counter 0/60 | none (goes to boss level) | two stages + timed chase |
| Emulator run | 11:24–11:48 | 14:15 | 11:31 | 10:54 | 2:27 |

The L2 bank count in [13](13-level-formats-and-floppy.md) is 697
descriptors; the L2 working notes say 670. This chapter uses 697.

## Level 1

| Scroll | Content |
|---|---|
| 0–3,400 | sea: aircraft waves, ships. First wave (8–40): types `0x1b4`/`0x1b0` alternate every 8 px, 29 HP, mirror-image paths, 15 points each |
| 3,423 / 3,495 | **mid-boss 1** (background loop from about 3,619) |
| 5,597–5,677 | **mid-boss 2** |
| 5,716–15,009 | port, town, railway: about 600 spawns. Gunboats `0x11c` (from 626, 200 HP) whose second salvo and mines depend on the rating |
| 15,009 / 15,137 | **boss**: background loop / boss parts |

New here, and reused later: the enemy VM, chance-to-fire shots `20.68`, the
rating, pods. Homing rockets (`0x3c`) appear at mid-boss 2 (11 fired in the
run). The level teaches on weak targets: median enemy HP 29.

**Mid-boss 1: two gunships (`0x1a4` x=88, `0x1a8` x=296).** Each has 4,000 HP
with flag `0x400`, so the bar is 8,000. They enter from the top at 0.5 px per
tick, the second 72 ticks after the first, then hold position and wobble
±3 px. Each ship carries four turrets drawn as separate bobs (sub-op
`20.18`). A turret turns one frame per tick within a five-frame arc, and each
covers a different quarter. The shot `0x1ac` has 3 HP (it can be shot down)
and travels about 4.5 px per tick in one of 16 directions. Side turrets fire
once per 64 ticks, the front turret three times. **Enrage:** when one ship
dies, the other's turrets fire twice as often (mask `&0x3f` → `&0x1f`). There
are no windows: the whole hull is the weak point. The first kill drops a
pod {shield ×3}, the second {life, life, +5000} and ends the loop.
Emulator run: 14 s and 23 s.

**Mid-boss 2: three ships, two lives each.** Centre `0x1a0` (x=192) and two
side ships `0x214`. Each refills to 900 HP once on its first death and
switches to a damaged animation. The bar is 5,400 = 3 × 2 × 900, and
`(0x3e8)=3` counts the survivors. They enter **from the bottom** at 1 px per
tick.

* Life 1: the centre ship opens for about 135 ticks (telegraph). Then it fires
  pairs of `0x48` downwards **only while the player is under it, within
  ±50 px** (`20.14`). The side ships do not attack until the first full kill.
  All three drop a diving plane `0x200` (140 HP) at the player's x every
  50 + RNG/4 ticks (`20.50`): one at a time with one player, two with two.
* Life 2: launchers on the back fire homing rockets `0x3c` (30 HP), about two
  per 40 ticks.
* Kills: at two survivors a pod {shield ×3}. At zero, a pod {life ×3}, the
  loop ends and the rating gets **+40**.

The spawn records carry 804/900/900 HP while the death script writes 900.
Which value the first life really uses was not checked.

**Boss: hangar with a pendulum.**

| Part | Type | HP | Role |
|---|---|---|---|
| superstructure | `0x220` | 1, immune | AGA sprites from block [3]; sets the arena; its death ends the level |
| armour | `0x224` ×2 (x 96/288), `0x228` ×2 (x 152/232) | 15,000, immune (bit 2) | `0x228` covers the two 16-px gaps between the sprite pieces and sets the flight limit 68 px below itself |
| **core** | `0x22c` | **7,500**, flag `0x400` | the only weak point; bar 7,500 |
| pendulum | 6 × `0x234`, 5 × `0x238`, ball `0x230` | 10,000 rewritten | a multi-part arm |

* Core (`20.94`, `hunk0+0x1316e`): runs along a rail between x 138 and 246 after
  the player (acceleration 1, top speed 3 px per tick). It picks a new target
  only when the pendulum is at an extreme (|angle| ≥ 45°), then waits 25
  ticks, so its movement is in step with the pendulum.
* Pendulum: the phase advances 0x10 per tick, so the **period is 128 ticks
  (5.1 s)**. The amplitude is **±65°**, with 11 links of about 11 px. The
  links bend with the angle and with the core's movement over the last 8
  ticks, so the arm whips when the core moves.
* Guns (`20.bc` in the superstructure, `hunk0+0x13598`): two, at x 117 and 267. A
  player inside a cone (|dy| < 2·dx) draws a 45° shot at 3 px per tick;
  otherwise the shot goes straight down at 4.25 px per tick. Changing
  direction is a **44-tick barrel turn**, a visible telegraph, and a gun
  fires only once aimed. The pause after a shot is 35 ticks (down) or 55
  (diagonal). The shot `0x50` has 3 HP.
* Core death: guns stop, pendulum links drop off every 5 ticks, points go to
  both players, and `20.154` ends the level. Emulator run: the core melted
  linearly in **29 s** (about 10 HP per tick).

The core's 7,500 comes from the spawn record and the L1 type table. An
earlier note of 6,668 HP is wrong.

## Level 2

No cloud layer. 631 records, 121 of 174 defined types used, 13 samples, 10 of
them new.

| Scroll | Emulator time | Terrain | Content |
|---|---|---|---|
| 0–2,700 | 0:00–1:46 | city streets | infantry, gun nests, armoured cars `0x80`, doors and windows releasing soldiers |
| 2,700–3,700 | 1:46–2:26 | cemetery, chapels | **church spires `0x198` kill on contact through the shield** |
| 3,769 | 2:30 | viaduct | **armoured train** from the right: locomotive `0xb0` 950 HP plus three cars (650/650/400) |
| 3,800–5,800 | 2:30–3:55 | city, park, river | balloons and airships, autogyros `0xcc` |
| 5,902–7,179 | 3:56–4:47 | avenue | **mid-boss 1** (loop 4 × 256 px) |
| 7,179–8,500 | 4:47–5:57 | city, second church | second train (7,561, from the left) |
| 8,500–10,470 | 5:57–7:40 | suburbs, warehouses | gun trucks `0xd8`/`0x250`, lorries dropping infantry |
| 10,472–11,584 | 7:40–8:05 | hangar | **mid-boss 2: the airship** |
| 11,584–14,352 | 8:05–10:36 | factories, quarry | balloons `0x288` 875 HP, tanks, ground guns |
| 14,352–14,480 | 10:36– | rails | **boss** |

Records per 1,000 px range from 22 to 61. The peak is at the second church
(8,000–9,000).

New here:

* Enemies fire on a **fixed animation rhythm**. No L2 script uses `20.68` or
  tests the rating.
* Ground vehicles turn their guns in 16 directions.
* 289 one-HP targets (infantry, civilians, doors). In a door, the spawn
  record's HP field is the opening delay.
* Civilians and animals are hit-immune unless a cheat flag (`hunk0+0x32ba`) is
  set; see [11-leftovers.md](11-leftovers.md).
* The minelayer `0x11c` drops mines every `(656 − rating)/8` ticks.

**Mid-boss 1: the arm machine (5,950).**

* Body `0x44`: hardware sprites from block [3], 192×98 px. It is immortal and
  builds its own copper list.
* Arms `0x48`/`0x2a4`: two segments each, immortal.
* **Hands `0x4c`/`0x2a0`: 2,500 HP each**, flag `0x400`. Bar 5,000.

The geometry (`20.cc`, `hunk0+0x148c4`): shoulders ±60 px from the body centre,
and each arm has two segments chosen from 17 directions 11.25° apart. After
96 ticks of waiting, a mode is drawn after every attack:

* **Grab, 10/16:** aimed contact, no bullets. The body drops 64–79 px and
  moves toward the player.
* **Clap, 3/16:** 9 alternating hand blows. Blows 1–7 release a **bomb
  `0x29c`** (400 HP), which lands 100–150 px below the machine within ±100 px
  of x. It is not aimed.
* **Crouch, 3/16:** 253 ticks of growing wobble.

A nest (`20.150`) drops a tank `0x2a8` (175 HP) from the top of the screen
every 70–197 ticks. A destroyed hand blows up its arm in a cascade, and the
machine switches to a **one-arm mode**: lower, swinging, no shots. Each hand
drops {shield ×3}, and the body's death gives **+50** rating. Emulator run:
36 s and 44 s for the hands, about 51 s in total.

**Mid-boss 2: the airship (10,472 roof / 10,592 ship).** The hangar roof `0x120`
explodes, the doors open and the bar is set to 6,000. The airship `0x160` has
**6,000 HP** and drops {life, +1000, +2000}. It rises and is **immune for its
first 67 ticks**. Fire (`20.130`): the first burst comes after 170 ticks;
then 8 shots `0x284` (6 px per tick, aimed when fired) every 8 ticks for 64
ticks, then a 100-tick pause. It fires **only when the player is at least
7 px ahead of its nose**. Two hull turrets turn toward the player as a
telegraph. It also releases gunners `0x290`, and **each gunner spawns its
replacement when it dies**. Emulator run: about 18 s.

**Boss: the rail machine (14,480).**

| Part | Type | HP | In bar |
|---|---|---|---|
| director | `0x214` | 10,000, fatal obstacle (`0xd0`) | — |
| body | `0x280` | immortal; sprites from block [4], 192×111 | — |
| nozzles | `0x244` ×2 | 1,500 each | yes |
| **core** | `0x248` | 1,500 | yes |
| side guns | `0x230` / `0x234` | 1,500 each | **no** (optional) |

The bar is 4,500. The director (`20.104`) gives orders through `(0x3ee)` and
counts kills in `(0x3ec)`:

* Drones from alternating launchers every `0x23 + RNG` ticks (`0x23c`/`0x240`,
  448 HP). Stronger drones come in once both nozzles are dead (`0x254`) and
  once `(0x8f6)` ≥ 2,000 (`0x258`): **escalation with progress**.
* About every 100 ticks, a random attack from the table at `hunk0+0x15ec8`.
* **Side gun window: 72 ticks** (variant B: 65). A 30-tick wind-up, with the
  battery barrels turning one by one, then 6 shots `0x238` every 10 ticks
  (variant B: 3 shots `0x278` every 6). These shots have 33 HP, accelerate to
  6 px per tick and then turn toward the player. **Regeneration:** below
  1,450 HP the gun gets **+50** after the window.
* **Nozzle window: 149 ticks.** It extends in 6 ticks and fires about 10
  shots. **Regeneration:** below 960 HP it gets **+40**, and the bar goes back
  by 40.
* When both nozzles are dead (`(0x3ec)` ≥ 0x2000), the counter ramps to
  0x27f0 (about 2 s) and order 10000 **exposes the core**. The core
  alternates a 4-shot fan (±10°, ±30°) and a 3-shot fan (0°, ±20°) at
  6 px per tick. The gaps in one fan are covered by the next, so the player
  has to move. About 9 fans come in 70 ticks, then an 80-tick pause.
* The side guns are not needed to win. Core death gives points to both
  players and ends the level.

Emulator run: about 3:30 and 22 loop turns. 190 hits landed inside windows
and 1 outside, which confirms the windows.

## Level 3

778 records, 77 types, map 17,504 px. There is no stop-and-wait loop
anywhere (`segment` stays 0). The level ends in a fortress with a rewind
instead of a boss.

| Scroll | Time | Terrain | Content |
|---|---|---|---|
| 0–320 | 0:00–0:13 | desert | 36 spiked mines `0x14c` (700 HP, static obstacles) |
| 400–3,980 | 0:16–2:39 | desert, road | convoys: buggies `0x158` (48), half-tracks `0x15c` (44, 250 HP); gun emplacements `0x150` (650 HP, 3-shot fan); launch domes `0x154`; 13 detonator/charge pairs |
| 4,000–4,900 | 2:40–3:16 | wall, rails | composite tanks, armoured trains `0xa0`/`0xc0` (650 HP), first aircraft |
| 5,000–7,600 | 3:20–5:04 | swamp, river, **under clouds** (5,010–7,578; clouds 2 px per tick, parallax) | about 90 aircraft, about 100 soldiers (1 HP), artillery |
| 7,600–9,600 | 5:04–6:24 | pyramids | missile silos `0x8c` (970 HP), heavy vehicles `0x98`/`0x9c` |
| **9,628–11,388** | 6:25–7:36 | **canyon** | play field narrowed; 76 boulders thrown from the walls |
| 11,388–13,840 | 7:36–9:14 | bunkers | pop-up guns `0x84`/`0x88` (450 HP), silos, tanks |
| **13,843–15,466** | 9:14–10:19 | **High Command fortress** | 38 guns, counter 0/60, rewind |

Spawn counts: aircraft 245, soldiers 115, vehicles 108, boulders 76, tanks 64,
emplacements 54, fortress 39, mines 36, detonator pairs 26.

New here:

* **Every aircraft has 170 HP** (L1: 29) and is worth 83 points (L1: 15).
* The `20.68` thresholds are lower (15–70 against 35–90), so the same rating
  fires more often. L3 has no rating thresholds in its scripts.
* **Detonator pairs (`0x78` + `0x74`):** each charge takes a number
  `++(0x3ea)` and each soldier `++(0x3ec)`. After about 90 ticks the soldier
  writes its number to `(0x3ee)`, and the matching charge explodes into
  **12 fragments** (`20.58`). Killing the soldier in time defuses it.
* **Canyon:** type `0x68` sets `(0x334)=1` (field 78…306 instead of 14…370,
  fixed camera) and `0x6c` clears it. In the emulator the player's x stayed
  in 78–306 in the canyon and 15–370 outside. Boulders (20–160 HP) arc in at
  6.6 px per tick, bounce and throw fragments; big ones split into three.
  **Every big boulder `0x48` adds +9 to `(0x3c2)`**. The canyon has the most
  targets of the game (78 per 500 px) and almost no enemy fire: a steering
  test.
* **Sand capsule `0x94`** (5 spawns from 9,234): it is invisible and
  unhittable at first, and draws a moving rippling oval in the ground (block
  [3] masks). After about 56 ticks it surfaces as a hittable capsule that
  shoots. The L3 type notes call it a small turret; that is wrong.
* Aircraft (`0xdc`, `0xe0`, `0x108`) also carry pods, which never happens in
  L1.

**The fortress: a counter instead of a boss.**

1. 13,843, type `0x1a0` (`20.194`): bar on, `(0x8f4)=60`, `(0x8f6)=0`, slot
   pointer `(0x57a)` = `A5+0x404`.
2. 13,856, type `0x19c` (`20.190`): saves the ground decoder state. This is
   the return point.
3. Guns, each taking a byte slot:

   | Gun | Count | HP | Attack | Counter |
   |---|---|---|---|---|
   | tower `0x7c` | 20 | 200 | 4-direction turret | +1 |
   | bunker `0x80` | 16 | 350 | 8-direction turret | +2 |
   | dome `0x194` | 2 | 480 | 3-shot fan down | +4 |

   The total is 20 + 32 + 8 = **60, so all 38 guns must die**. A bunker opens
   only if RNG beats `6·counter + 64`; otherwise it stays shut, does not
   fight, and cannot be destroyed.
4. Core `0x70` (15,252, 1 HP, unhittable): it pulses with a delay of
   `61 − counter` ticks, so it speeds up as you progress, a visual clock. At
   60 it flashes, awards +1501 and +1324 points to both players (non-BCD
   digits added with `abcd`), fires a smart bomb, sets off 69 random
   explosions and ends the level (`20.154`).
5. 15,466, type `0x198`: if the core is still alive, `(0x358)=1`. The map
   **rewinds** at up to 0x70 (about 14 px per tick) and brakes below 14,175;
   the player is locked at x=188. The decoder and spawn pointers return to
   step 2 and the slot pointer restarts. **A slot is marked only when a gun
   dies**, so destroyed guns stay destroyed and the counter is kept. Guns
   that scrolled off alive, and bunkers that stayed shut, come back. So do
   ordinary enemies.

Emulator run: pass 1 reached 44/60. The rewind took 6.6 s (330 frames).
Pass 2 met 0 towers, 0 domes and 4 bunkers. The counter hit 60 at scroll
15,086 and the core died at 15,361.

## Level 4

781 records, 70 types, map 16,032 px, no clouds. The player flies a jet
(`plyrmisc4`) and the screen has eight bitplanes.

| Position | Terrain | Time | Spawns per 1,000 px |
|---|---|---|---|
| 0–2,600 | open space, dust belts | 0:00–1:44 | 35–53: space crabs `0x18`, fighters `0x24–0x44`, drones |
| 2,600–5,700 | orbital station | 1:44–3:48 | 34–44: station guns `0x4c`, gunboats `0x124` (2,100 HP), rovers |
| 5,700–7,900 | station plates, craters; **mid-boss at 6,206** | 3:48–5:50 | 26–35 |
| 7,900–16,032 | fortress base, pipes, rail, green hangars | 5:50–10:54 | 52–75: launchers `0x7c` (84), ground guns `0x78` (63), swarm `0xc8` (72), zigzaggers `0xc4`, barriers |

Controllers without graphics: `0x19c` (trigger 2), `0x198` (6,158, arena and
loop) and `0x168` (15,576, `(0x5e8)=1`, end of level). **Level 4 has no boss
of its own**; the game goes straight on to the boss level.

New here:

* **Homing missiles** (op `94 HOMING inertia force time`). Every tick
  `v = v·b/4096 + force·dir/|d|`, plus 0x10 downward. 146 spawns can launch
  them (fighters `0x16c`, towers `0x10`, launchers `0x7c`, fortress `0x98`).
  108 were fired in the run. The ground missile `0x4` switches its homing
  pattern at **rating 200**: below it, four short homing phases; at or above,
  two longer ones.
* **Linked objects:** generators (`0xc0`, `0xe8`) take a number; their
  emitters `0xbc` and barriers `0xe4` disappear when `(0x3ec)` equals their
  number. **Destroying a generator switches off its barriers.**
* **Timed barriers** `0x68`/`0x6c` (34, active 289 ticks, counted in `(0x4ee)`)
  and **pillars** `0x70` (obstacles with no death script).
* **Rail trains** (`0x50`/`0x54` locomotives, `0x58`–`0x60` cars), clipped to
  a track window.
* **Random and relative branches:** `20.1b4` (three-way random), `20.1b8`
  (player within ±30 px, left or right), `20.1ac` (if 2·|dx| ≥ |dy|).
* In several types (`0x74`, `0x7c`, `0xc4`, `0xcc`–`0xd4`) the spawn HP field
  is a parameter, and the script sets the real HP.

**Mid-boss: the arm machine again (6,206).** The body comes from block [4],
which is byte-identical to L2's block [3] (9,616 B), and `20.cc` is shared.
`(0x906)` picks other frames and the shot `0x194`. Differences from L2:

* **pincers `0x180`/`0x188`, 3,500 HP each**, bar 7,000, each dropping
  {shield ×3};
* an **arena** (`0x198` at 6,158: field 78…306, 256-px loop);
* instead of tanks, a rover `0x9c`/`0xac` (300 HP) arrives from the side
  every 170–297 ticks (`20.1ec`);
* death: three explosion loops, **+50 rating**, arena and loop off.

Bug: `20.144` clears bullets when `(0x8f6)` = 5000, the L2 bar value
hard-coded, but the L4 bar is 7,000. Emulator run: the pincers fell at 16 s
and 35 s, about 38 s with the death sequence, 4 loop turns.

## The boss level

`bossf`: 26 spawn records, 23 types, a map of 384×1,056 px (the shortest in
the game). Almost all the action is scripted. There is no cloud layer and no
demo recording. `plyrmisc4` and `soundfx4` stay loaded from L4.

| Time (run) | Scroll | Event |
|---|---|---|
| 0 s | 0–102 | controller `0x28` turns the bar on (20,000); 4 walking mechs `0x3c`/`0x40` (670 HP) |
| 9.6 s | 228 | row of 9 spikes `0x1c` on a bridge |
| 13.4–18.8 s | 324–459 | fortress elements, core A `0x20`, hatches `0x14`/`0x18`, core B `0x24` |
| 19.5 s | **477, stop** | `(0x35a)=−1`, **director A** |
| +36 s | 477 → 535 | core A dead: the spikes go and the scroll resumes; 4 turrets at 484 |
| | **535, stop** | loop and **director B** |
| +46 s | 535 | core B dead: bar off; 80 ticks later the chase starts (`(0x35a)=−2`) |
| | 594 | **Blardax's ship** `0x44` (16,000 HP) and flames `0x54`; bar 16,000 |
| +37 s | — | time up: the ship escapes |

**Stage 1A: spike bridge and core A (scroll 477, stopped).** Core A has
10,000 HP and does not move. The bar is 20,000, cores A and B together.

Director A (`20.1c4`, `hunk0+0x17510`) draws a spike from the table at `hunk0+0x17538`:

* centre spike 6/16, outer pair 2/16 each, the other six 1/16 each;
* the delay before the next draw is 14–20 ticks.

A spike **telegraphs** by flashing three times with a sound (about 9 ticks),
extends in 4 frames to 96 px, holds for 10 ticks and retracts. Spikes have
10,000 HP rewritten every tick. The most likely spike is the one under the
best firing position. Core A drops {life ×3}.

**Stage 1B: the fortress "eyes" and core B (scroll 535, stopped).** Core B
(10,000 HP) is hit-immune while core A lives. Four turrets (1,500 HP each)
are outside the bar and optional; two of them drop pods.

Director B (`20.1c8`, table of 32 entries at `hunk0+0x175b6`) draws who fires
and the pause after:

| Shooter | Weight | Pause |
|---|---|---|
| outer turrets | 6/32 each | 32 ticks |
| inner turrets | 3/32 each | 36 ticks |
| hatches | 7/32 each | 45 ticks |

* A turret fires 4 shots 5 ticks apart in fixed directions (straight down and
  24–41° diagonals) at 10 px per tick. Together the turrets put a crossfire
  through the centre.
* A hatch opens over 10 frames (telegraph) and then spawns `0x2c`/`0x30`. The
  boss notes call this a "spinning fan of 4 bullets". It is actually a
  **rotating, growing quadrilateral filled into the light layer**: a
  multi-part object (`obj.7e` = 512) that lives 16 ticks.
* **A dead turret drops out of the draw**, so destroying parts lowers the
  fire.
* Core B drops {speed, variant 2, fire rate}.

**Stage 2: chase with a time limit.** The ship is made of AGA sprites from
block [4], an attached 64-px pair for the ship and a second pair for its
shadow, with 5 bank frames. A mini copper list switches `BPLCON2` at a line
that scrolls, so the ship **rises from under the dome**. Its 0×81 bob is only
a collision box.

Movement (`20.1d8`):

* vertically it accelerates from 4 to 17 px per tick over about 6 s, with the
  camera following and a 256-px crater loop behind;
* horizontally it chases the player, with the target x clamped to 128…256 and
  acceleration ±1 px per tick² up to ±16. It pauses 15 ticks on arrival and
  switches target between players in a two-player game.

Attacks run in the fixed cycle **M F M F F M F M**, the first after 150
ticks:

* **M**, 50 ticks: up to 10 mines `0x4c` (195 HP), one every 4 ticks;
* **F**, 44 ticks: 15 shots `0x50` (4 px per tick) every 2 ticks, sweeping
  side to side to ±78° from vertical. The sweep reverses each fan.

**Time limit.** The movement script sets 10,000, but the animation script
spawns the on-screen counter `0x48` after 149 ticks and overwrites the limit
with 775. That makes **about 925 ticks (37 s) in total, of which the counter
shows 30 s**.

The required damage rate is 16,000 / 925 ≈ **17 HP per tick**. The autopilot
with starting weapons left the ship on **466 HP**. With the ship's HP patched
to 3,000 it died in 6 s.

* Kill: points for both players (about 12,830 via `abcd`). `(0x3fa)=2`
  freezes the counter, followed by 178 ticks of explosions, a fall, a flash,
  `(0x5e8)=1` and `20.88`. About 8.6 s from the kill to the end of the level.
* Escape: upward acceleration with screen flashes, and `(0x5e8)=−1`.

This is the only place in the game where you can lose without losing a life.
No boss-level script reads the rating; the fire rate is fixed and depends
only on RNG.

## Endings (flow)

After `hunk0+0x3192` returns, D0 decides what happens:

* D0 < 0 (the game was aborted with ESC or Reverse+Forward in pause): no
  ending and no high-score entry; back to the title.
* D0 = +1 (game over): to the high-score routine, no ending.
* D0 = 0: high scores (`hunk0+0x2c14`), then `(0x5e8)` is copied to `hunk0+0x3970`
  and `hunk0+0x3818` runs.
* **On Easy there is no ending and no high-score table.**

`hunk0+0x3818` loads `P60.end` (31 s of music) and five 320×256×4 interleaved
frames:

| `(0x5e8)` | Frames | Scene | Afterwards |
|---|---|---|---|
| −1 (ship escaped) | `endseq1.001–005` | the planet explodes, no player ship | two text pages, **no credits** |
| 1 (ship destroyed) | `endseq2.001–005` | the same explosion with the Banshee flying off | text pages, then the credits (fire skips them) |

Both endings fade in with the sepia palette at `hunk0+0x39dc`, then fade to dark
blue, wait for the music, and reload `level1c/f` and `introscreen` for
attract mode. The good ending lasts about 65 s in the emulator without
pressing fire. **The bad ending is a loss on time, not a game over.**

In the emulator the bad ending stopped at `endseq1.005` because the file name
had been overwritten. **This was an emulator bug, not a game bug.** The game's
VBlank server writes custom registers through A0 (`$96(a0)`, `$9c(a0)`, …).
Exec calls VERTB servers with A0 = `0xdff000`, but the emulator did not set
it. With A0 set, all five frames load.

## Blocks [3] and [4] of `levelNc` / `bossc`

These are `levelNf+0x48` and `+0x4c`. The word before each block is its
length in words minus one (a `dbra` count). At level start `hunk0+0xf7fc`
moves both blocks to an 8-byte boundary, because sprite DMA with FMODE=3
needs it; the extra 2–10 bytes at the end are padding.

| File | Block | Size | Format | Used for |
|---|---|---|---|---|
| level1c | [3] | 13,648 | AGA sprites, patch mode (1) | boss superstructure, `20.84` |
| level2c | [3] | 9,616 | AGA sprites, static (0), 192×98 | mid-boss 1 body, `20.8c` |
| level2c | [4] | 19,504 | AGA sprites, animated (`0xffff`), 192×111 | boss body, `20.100` |
| level3c | [3] | 1,798 | 8 one-bit masks, 48 px wide | ground ripple (sand capsule) |
| level4c | [3] | 12,800 | one-bit sheet, 320×320 | light layer, planes 7–8 |
| level4c | [4] | 9,616 | **= level2c [3] byte for byte** | mid-boss body, `20.1e8` |
| bossc | [3] | 12,800 | one-bit sheet, 320×320, different content | light layer |
| bossc | [4] | 26,576 | AGA sprites, frame mode (`0x8000`) | final ship and its shadow, `20.1d4` |
| level1c [4], level3c [4] | — | — | null pointer | — |

**AGA sprite blocks.** The block has a 16-byte header:

```
+0 hot x   +2 hot y   +4 height<<8   +6 horizontal step (0x20 = 64 px, 0x28 = 80 px)
+8 S = stride between sprites   +a mode: 0 static, >0 patches (L1),
   0xffff table animation, 0x8000 one pair + frame (0x3f6)   +c 3 B frame cache
```

It is followed by six sprites S bytes apart: even, odd, even, odd…, i.e.
three **attached pairs** (16 colours each). Each sprite is in FMODE=3
layout: 16 bytes of control words (POS at +0, CTL at +8), H lines of
16 bytes (8 for plane A, 8 for plane B), then a 16-byte terminator. Any
space left in S holds animation frames.

| Block | Layout |
|---|---|
| L1 [3] | H=60, S=0x8e0, 80-px step: three 64-px pieces with 16-px gaps (covered by the `0x228` armour bobs) |
| L2 [3] = L4 [4] | H=98, S=0x640 |
| L2 [4] | H=111, S=0xcb0 |
| boss [4] | H=81; frame = 0x530 B; 5 bank frames per sprite, shadow at +0x33e0; frame chosen by `(0x3f6)` |

* A sub-op attaches a block by storing it in `(0x37a)` and the object in
  `(0x37e)`.
* `hunk0+0xa22c` draws it every frame. It writes POS/CTL straight into the
  block's control words (ATT on the odd sprites), and points **SPR2PT–SPR7PT**
  in the main copper list at `hunk4+0x1cc0` to them. Off screen, all six point
  at an empty sprite.
* The L2/L4 bodies build a 150-line copper list at `hunk5+0x3d158` that toggles
  `BPLCON3` 0x0040/0x0042 on every line (sprites in the border).
* Patch and animation modes copy 16-byte-entry patches from a table at
  `hunk0+0xa69e`.
* The main copper sets `BPLCON4 = 0x0098`, so attached pairs use **colours
  128–143**, the same bank as the player's ship.

**Level 3 masks.** The block starts with a table of 8-byte entries
`{offset, hot x, height, hot y}` (8 entries), followed by one-plane data,
6 bytes per row. The eight entries are one dithered oval rotated in 22.5°
steps.

The masks are drawn in mode 0x6000 (`hunk0+0x9b36`), which an object gets when
`obj.40` has bits 7–9 set and bit 6 clear. The blit uses minterm `0xCA` with
A = mask and B = the target **two lines lower**. Inside the mask, the picture
is replaced by the picture from two lines further down. The screen is
rebuilt from the ground buffer every frame, so the shift never accumulates,
and the sand appears to ripple.

**Level 4 / boss light layer.** The block is a 320×320 one-bit sheet with no
header. Cut-outs are described by a constant table **in the core** at
`hunk0+0xbff6`: 16-byte entries `{offset, width in bytes, height, dx, dy}`,
indexed by bob number − 0x1be. A byte table at `hunk0+0xbe32` marks cut-outs
that go to both planes. When `(0x906)` ≠ 0, bobs ≥ 0x1be are diverted to
`hunk0+0xbeaa`, which ORs the mask into the buffer `(0x38c)`. That buffer holds
two interleaved planes and is double-buffered with `(0x390)`.

The copper takes planes 7–8 from this buffer; in levels 1/3 the same planes
hold the clouds. In the L4 palette, colours 64–127 are brightened copies of
0–63. **So plane 7 brightens** whatever is under it: discharges, beams and
flashes.

* Multi-part objects (`obj.7e` ≥ 0x100) are also filled into this buffer as
  CPU-drawn polygons (`hunk0+0xc626`). In the whole game only the boss types
  `0x2c`/`0x30` use them.
* In frames where a polygon was drawn, a no-write blit (`hunk0+0xca98`) tests the
  player silhouette against the buffer. On overlap, the player loses **5
  shield points per tick**.
* `(0x3fa)=1` in L4 disables the layer until the mid-boss dies.
* L4 barriers do not use pixel collision: `(0xde0)` stayed 0 for the whole
  run. They hurt through normal object collision.

## Reusable boss patterns

| Pattern | Banshee instances | Key numbers |
|---|---|---|
| Parts guard a core | L2 boss (2 nozzles → core), final (core A → core B), L1 MB2 (side ships wait) | core reveal animation about 2 s; optional parts outside the bar |
| Vulnerability windows with regeneration | L2 nozzle and side gun | windows of 149 / 72 ticks; +40 / +50 HP below 960 / 1,450 |
| Weighted director | final A/B, L2 boss, arm machine | 16- or 32-entry tables; dead parts drop out of the draw |
| Telegraphed random hazard | final spikes | 9 positions, 9-tick warning, 10 ticks active, 14–20 ticks between draws |
| Destroy N or rewind | L3 fortress | 38 targets = 60 points; rewind 6.6 s; progress kept |
| Timed chase (damage check) | final ship | 16,000 HP in about 925 ticks ≈ 17 HP per tick; counter shows 30 s of 37 |
| Enrage on loss | L1 MB1 (×2 fire rate), L1 MB2, L2 boss drones | — |
| Second life | L1 MB2 | 2 × 900 HP; phase 2 switches from a zone shot to homing rockets |
| Immortal frame, killable tips | arm machine (L2/L4), L1 pendulum | hands 2,500 / 3,500 HP; pendulum ±65°, period 5.1 s |
| Conditional fire zone | L1 MB2 (±50 px below), L2 airship (≥ 7 px ahead), L1 boss cone | — |

Boss shots can be shot down (3–33 HP, rockets 30, bombs 400). Every mid-boss
leaves a pod (shield or life). Fight structure: an entry of 2–9 s, a main
phase with a director, a short core phase, a death sequence of 3–13 s. In the
emulator a steady target took 10–17 HP per tick, which matches the
game's time thresholds.

## Open questions

1. Blocks: what the 16-px gaps in L1 really look like on hardware (the
   geometry fits the `0x228` bobs to the pixel, but this is not emulated);
   which L4/boss bobs ≥ 0x1be are actually used; why table entries 0x202/0x203
   are empty in the L4 sheet.
2. Whether contact with the L1 pendulum, the final spikes and the
   arm-machine hands kills outright or drains the shield (flags `0x06`/`0x07`,
   not `0xd0`; untestable while invincible). Likewise whether the
   light-layer polygon really drains 5 shield points per tick on hardware
   (the code is unambiguous).
3. Whether the L1 armour `0x224`/`0x228` absorbs player shots or lets them
   through.
4. L1 MB2 first-life HP (records say 804/900/900; the script writes 900).
5. The fortress elements `0x34`/`0x38` of the boss level: their sprites are not
   in block [3] (that is the light-layer sheet), so where they come from is
   open.
6. Who clears `(0x3fa)` in L4 before the mid-boss arrives (it read 0 at
   scroll 6,200, with only three writes in the scripts).
7. L2/L4 data: types `0xfc`/`0x100` (L2) and `0x9c` (L4) have a `SETPROG 44`
   pointing straight at a `FRAME` with no flag word. This is probably a data
   bug in the game; not emulated.
8. Two-player turret rhythms of L1 MB1 come from the code, not from a run.

## Confidence

* **High:** spawn counts, types, HP, scripts, the boss bar, windows,
  directors, the fortress counter and rewind, the level sequence and the
  endings flow (all from code and data, with the dynamic parts confirmed in
  the emulator); the AGA sprite block format (rendered correctly with the
  palette taken from the copper).
* **Medium:** the light-layer interpretation (brightening, shield drain);
  the on-screen look of the L3 ripple (rendered from the emulator without a
  blitter).
* **Emulator-only, single autopilot run:** all fight durations, shot
  counts per fight, and the time column of the section tables.
