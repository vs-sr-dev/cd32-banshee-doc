# Runtime: RNG, input, two players, shell, sound, display

What `bans.exe` does once it is running. Everything here was read from the
code and, where marked, measured by running the program from a cold start in
a 68020 emulator with a software Blitter and a Paula interrupt model.

**Addresses.** Code and data are written `hunkN+0x…` as in
[00-overview.md](00-overview.md) (`hunk0+N` = file offset `N + 0x34`,
`hunk1+N` = `N + 0x19894`, `hunk4+N` = `N + 0x20678`). The game keeps its
globals in one block addressed through `A5` = `hunk5+0x723DC`; a global is
written `A5+0x3e0`. Chapter 13's "Ghidra addresses" are runtime addresses with
the hunks packed from `0x21f000`; subtract `0x21f000` for `hunk0+`.

**Confidence.** **High** = code plus measurement; **medium** = code read, not
measured, or an interpretation; **low** = hypothesis.

Game logic runs at **25 ticks per second** (one tick every two vertical
blanks, PAL).

## 1. Random numbers

### 1.1 The generator (high)

Not an LCG and not an LFSR: a **Weyl counter plus two accumulators stirred by
the players' positions**. State is four bytes of globals:

| Field | Role |
|---|---|
| `A` = word `A5+0x3e0` | accumulator, sum of `d` |
| `B` = word `A5+0x3e2` | Weyl counter, `+0x19a3` per tick |
| `C` = byte `A5+0x3e5` | byte accumulator, minus `d` |
| byte `A5+0x3e4` | never written, always 0 — so the word at `+0x3e4` reads as `C` (0–255) |

One step per tick, at the top of the enemy-script interpreter
(`hunk0+0x101CE`–`0x101E4`, called from the tick loop at `hunk0+0x6500`):

```
B += 0x19a3
d  = B + P1.x + P2.y          ; A5+0x216, A5+0x2ac
A += d
C -= d & 0xff
```

`B` depends on nothing but the tick count since the level started
(`B = n·0x19a3 mod 65536`, except on level 1 where one sub-op rotates it). The
commonest test in the enemy scripts, "`B` negative?", therefore alternates
**five ticks yes, five ticks no** — and an enemy that rolls at spawn time,
spawns being tied to the scroll and the scroll to the tick, gets **the same
roll in every game**. Only `A` and `C` vary, and only through player movement.
In one-player games the inactive P2's y follows the scroll, so the only real
entropy is P1's x history.

### 1.2 Seeding (high, one caveat medium)

* **Every level start** clears the global block (`hunk0+0xF37A`, `clr.l` over
  `A5…A5+0x3AE3`), RNG included. Measured across a level 2→3 transition:
  `(40501, 10645, 146)` before, `(0, 0, 0)` after.
* Immediately after, `hunk0+0xF87A` does `A = ror16(A − w, 2); B −= A` with
  `w` the word at `6(a6)`. `A6` is not set by that routine; on this path it
  still holds `GfxBase`, and `+6` is the low word of the library node's
  `ln_Pred`. Constant for a given ROM and memory layout, **not necessarily
  zero** (medium). In emulation it is 0. So a real CD32 runs the same
  sequence as the emulator shifted by a constant: statistics agree, exact rolls
  need not.
* Time on the title screen does not matter: starting the game at frames 900,
  1300, 1700, 3000 and 6000 always gives `(0,0,0)` then `(6773, 6563, 139)` on
  the first two ticks of level 1.
* Attract mode starts a level by the same path, so it gets the same seed —
  which is why replaying a recorded joystick stream works (§4.6).

### 1.3 Consumers

Writers (all verified in emulation):

| Where | Who | Effect |
|---|---|---|
| `hunk0+0x10E92` | script op `18` ADD | `A += 4291`; one use, level 1 |
| `hunk0+0xFDC4` | spawn, two players | `A += A`; sign picks the target player |
| `hunk0+0x1230E` | sub-op `20.10`, bullet spread | `C += 0x2a`; spread `(C−0x80)·(rating/2+192)/64` |
| `hunk0+0x13506` | sub-op `20.a8` (L1) | `B = ror16(B, 5)` |
| `hunk0+0x1389C`, `+0x1652A` | `20.1f8`, `20.1f4` debris at a random point | `A = ror16(…, 5)` |
| `hunk0+0x160C4`, `+0x16296` | `20.58`, `20.5c` | `C = ror8(C ^ 0x48, 3)` |
| `hunk0+0x16630` | `20.1a0` (L3 bunker) | `C ^= 0xa7` |
| `hunk0+0x1741C` | `20.1b4` (L4 branch) | `C = ror8(C, 1)`, three-way split |

Readers: script comparisons against `B` and `C` on every level (2 + 4 on L1,
21 on L2, 9 on L3, 4 on the boss), enemy fire (`20.68`, fires when
`C/2 + chance − 0x40 < rating`), boss directors, drop timing from nests, hit
sparks, damaged-player smoke, smart-bomb flashes, and the random pitch of
script op `10`. One thing that looks random and is not: sub-op `20.30`
"random direction" uses `y & 15`. Power-up drops are placed by hand in the
spawn lists.

### 1.4 A second generator: pod drift (high)

At pod creation (`hunk0+0x11D3E`):

```
P += 0x1376 ; Q += P                     ; words at hunk0+0x11DAA / +0x11DAC
vx = (rol16(P + P1.x, 3) & 0x1f) − 16
vy = (rol16(Q + P2.x, 3) & 0x1f) + 16
```

The state lives **in the code hunk** with initial values `P=0xa743, Q=0x71ae`
and is **never reset** — not per level, not per game. It counts pods since
power-on: at the start of level 2, `P = 0xa743 + 39·0x1376`, i.e. 39 pods from
level 1. Pods from attract mode and earlier games change the drift in later
ones.

### 1.5 Determinism (high)

With identical per-tick input from the start of a level, play is
reproducible. Measured over 900 ticks:

| Variant | Frames | RNG after 900 ticks | P1 score |
|---|---:|---|---|
| start at frame 900, 280k cycles/frame | 1862 | (38873, 21868, 39) | 0x285 |
| start at frame 1700 | 1862 | same | same |
| 140k cycles/frame | 1862 | same | same |
| 600k cycles/frame | 1862 | same | same |

The 4 KB global block hashes identically in all four. Logic never reads real
time: the VBlank counter is used only to wait for the end of a tick, pause
does not run the interpreter, and no `VHPOSR` or CIA-timer reads occur during
play. Overload slows the game; it never drops ticks.

What breaks reproducibility: any input difference (P1.x enters `A` and `C`
every tick), the pod generator's power-on history, the `GfxBase+6` word on a
different machine, the options (§4.3), the number of players and when P2
joined, and mouse deltas.

### 1.6 Verification

A Python model ([`tools/rng/banshee_rng.py`](../tools/rng/banshee_rng.py):
step, level init, every writer above) was checked against the
emulator with a hook on every instruction that writes `A5+0x3e0…0x3e5`:
**16,268 of 16,268 ticks match** across level 1, level 2 ×3, level 3 ×2,
level 4 ×2 and the boss ×2. The only writer outside the model is the
level-start clear. The pod generator matched 7 of 7 pods with `P` continuous
between them.

## 2. Input

Read once per tick at `hunk0+0x7BCE`, before player movement.

| Control | Source | Notes |
|---|---|---|
| Directions | per-player option word (`hunk0+0x32B4` P1 / port 1, `+0x32B6` P2 / port 0) | **0 = Joypad** (default): `lowlevel.library ReadJoyPort`. **1 = Mouse**: `JOYxDAT` counter delta, ±4 units per tick dead zone, converted to digital directions. **<0 = Joystick** (`JOYxDAT` XOR decode): unreachable on CD, the menu toggles 0↔1 only (§4.3) |
| Fire | CIA-A `$BFE001` bit 7 (P1) / bit 6 (P2) | always from the CIA — pad red button, joystick fire and left mouse button alike |
| Second button = **loop** (evasive roll) | `POTGOR` pin 9, bit 14 (P1) / bit 10 (P2), edge-triggered | pad blue button, right mouse button. Masking of P2's button tests **P1's** control type — harmless on CD |
| Pad PLAY | `ReadJoyPort` bit 17 | pause toggle |
| Pad REVERSE+FORWARD together | bits 18+19 | paused: same as ESC (quit to title); unpaused, with the developer cheat on: end level ([20](20-unused-content-and-cheats.md)) |
| Green, yellow, single shoulder | — | unused |
| Keyboard | CIA keyboard interrupt, action table `hunk0+0x7D5C` (index `0x7F − keycode`) | Space/Return/Shift/Ctrl/Alt/Amiga → P1 loop; numeric keypad → P2 loop; any letter → pause (`P` toggles, others only set); ESC → quit to title; F1–F10 → end level with cheat. **No movement from the keyboard** |

* **Autofire** is built in: holding fire shoots at the maximum rate for the
  current weapon (every 7/6/6/5/5 ticks); tapping gains nothing.
* **Diagonals** are not normalised: about 30 % faster than either axis.
* **Latency** (medium, from code order): pad read at tick start, move and draw
  in the same tick, buffer swap on the next VBlank — roughly 20–80 ms.

## 3. Two players and credits

**Simultaneous co-op with drop-in.** There is no player-count option.

* A player joins by pressing fire on their port — at level start, on the
  continue countdown, or **mid-level** if credits remain (`hunk0+0x7E60`).
  Every join, including the first, **spends one shared credit**
  (`hunk0+0xF5DC`). A new game sets credits to **4** (`hunk0+0xF4B2`).
  Measured: 1P start → 3 credits left, 2P start → 2, P2 joining at tick 100 → 2.
* A joining player gets 2 spare lives, 3 loops, score 0, full shield (18).
* When both are dead: a **125-tick** countdown to continue if credits remain,
  otherwise game over.
* **Separate:** lives, loops, shield, weapons, score, the 10,000-point extra
  life, high-score entry. **Shared:** credits, and the single **difficulty
  rating** that drives enemy fire, which is computed over both players.
* No player–player collision and no friendly fire (medium: no such path
  found).
* Camera x follows `P1.x + P2.x − 0x101`, clamped. "Keep players on screen"
  limits each ship to the camera window.
* Enemy targeting: at spawn with two players, the sign of `A` picks P1 or P2;
  the `TARGET` op picks the nearer by `|dx|+|dy|`.
* Each drop creates **two pods**. With "Split powerups" on (the default),
  one carries P1's icons and one P2's, each collected by its owner; off, both
  pods are shared.
* Scaling with two players: rating ×9/16 (less enemy fire, smaller spread)
  and player bullet damage ≈66 %. **Enemy HP, spawn counts and boss scripts do
  not change.**
* Attract mode always runs **two players** on normal difficulty.

## 4. Shell flow

### 4.1 From boot to the menu (high)

The entry point checks `DENISEID` and exits with code 20 on a non-AGA
machine, opens libraries, and calls the shell at `hunk0+0x14BC`.

```
language select (250 VBL)  -- ESC skips the intro
  -> intro: 7 introseq frames, P60.intro, fire skips
  -> Core logo + PRESENTS (level 1 loads behind it)
  -> title (224 VBL) -> title (187 VBL)
  -> main menu (500 VBL)
       Start Game     -> game
       Options        -> options (1500 VBL; timeout -> title)
       <language>     -> cycles EN -> DE -> DA -> FR
       View Highscores-> table (1000 VBL; fire -> menu, timeout -> title)
       ESC (keyboard) -> exit program
       timeout        -> table (250 VBL) -> attract mode
                          -> credits (250 VBL) -> title
```

Timeouts count vertical blanks at 50 Hz. Intro pages stay up for 350, 350,
140, 310, 310, 310 and 330 VBL; French and Danish use a second page table with
different x positions for pages 5 and 6, whose lines are longer. The intro is
in the language chosen seconds earlier. The menu cursor reads both ports
through `ReadJoyPort` with wrap-around; highlight is done with sprites; fire on
either port selects.

The background of the text screens depends on **which disk number the most
recently loaded file came from** (a floppy-layout field the CD keeps): disks
1–2 → `introscreen`, 3 → `banspic2`, 4 → `banspic1`. After a game over on
level 2 the menu therefore shows `banspic2`, after level 3 or 4 `banspic1`.

### 4.2 Game sequence

Levels 1–4 then the boss, each preceded by a briefing page shown **while the
level loads** — a loading screen, not a wait-for-fire screen. No end-of-level
tally, no bonus. Level 4 also loads `plyrmisc4` and `soundfx4`.

The level runner returns 0 = completed, +1 = game over, −1 = aborted (ESC, or
REVERSE+FORWARD while paused). Carried between levels: active-player mask,
the credit counter, and per player weapons, lives, loops, power and score.
Not carried: shield (refilled).

Pause silences Paula and saves channel DMA and volumes, restoring them on
resume (§5.2). Abort goes to the title **with no high-score entry**.

### 4.3 Options and their effects (high)

Values live in RAM only; all start at 0.

| Option | Variable | Values | Effect |
|---|---|---|---|
| Player 1 uses | `hunk0+0x32B4` | **0 Joypad**, 1 Mouse | input path, §2; also the name-entry device |
| Player 2 uses | `hunk0+0x32B6` | same, port 0 | same |
| Keep players on screen | `hunk0+0x32B2` | **0 On**, 1 Off | On clamps ship x to the camera window |
| Difficulty level | `hunk0+0x32BC` | **0 Normal**, −1 Hard, 1 Easy | below |
| Split powerups | `hunk0+0x32BB` | **0 On**, 1 Off | two owned pods or two shared pods (2P only) |

Difficulty:

| | Easy | Normal | Hard |
|---|---|---|---|
| Rating offset | +0 | +64 | +128 (max 255) |
| Enemy bullet speed | ×0.75 | ×1 | ×1.25 |
| Player damage table | higher | normal | normal |
| Hits to destroy a pod | 16 | 16 | **9** |
| Minimum power | +2 | — | +2 |
| Game over | **no high-score entry** | entry | entry, name marked with a star glyph |
| Beating the boss | a "now try it harder" page, **no ending, no entry** | ending + entry | ending + entry |

Lives (3), credits (4), shield and loops do not depend on difficulty.

### 4.4 Continues and game over

Four shared credits per game, the start included (one player: start plus three
continues). Losing the last life appends that player's score and number to a
pending list — **each drop-out is a separate entry**. A continue keeps the
weapons the player died with and resets the score to 0. The game-over
sequence turns the frozen frame sepia (§6.5), runs 108 frames of a sine wave
on the light layer while fading sound, and slides the HUD out.

### 4.5 The high-score table

Eight entries in the data hunk (ranks `hunk1+0x2C6A`, scores `hunk1+0x2C8A` =
file 0x1C51E as 8 × 8 bytes of six ASCII digits plus `0xFF`, names
`hunk1+0x2CDB`, 8 × 20 bytes). Defaults are the team's names
([11-leftovers.md](11-leftovers.md)).

* After the boss, active players are appended; after a game over the list
  already holds the drop-outs. Leading zeros become spaces; bubble sort
  descending.
* If the best entry is **strictly** greater than 8th place, a name-entry
  screen opens for that player: a 15 × 5 character grid (A–Z with Æ Ø Å,
  lower case, punctuation) plus Clr / Del / OK, driven by that player's
  configured device or by the keyboard (Shift for case, Return = OK).
  **Max 16 characters, no time limit.**
* **Every** pending entry of that player that beats 8th place is inserted
  under the same name. Then a second pass for the other player — at most two
  entry screens.
* Only six score digits are stored; the in-game score has eight.
* **No persistence.** `nonvolatile.library` is not referenced, and the DOS
  `Open(MODE_NEWFILE)` / `Write` wrappers (`hunk0+0x7FA`, `+0x838`) have no
  callers. The table dies at power-off.
* The two cheat names are checked on this screen
  ([20-unused-content-and-cheats.md](20-unused-content-and-cheats.md)).

No passwords and no save states anywhere.

### 4.6 Attract mode (high)

Entered from the menu timeout via a 250-VBL table view (`hunk0+0x3002`). It
forces normal difficulty and two players, sets a demo flag that **mutes sound
effects**, and plays **whichever level is in memory** (level 1 after boot or
after the boss; the level where the last game ended otherwise; the boss has no
recording).

It replays an **input recording**, not a canned animation: 8-byte records at
`levelNf+0x3c` — `{ticks, P1 direction, P2 direction, buttons}` — fed into the
same input slots the pad would fill (`hunk0+0x7E9E`), with the game simulated
normally. It works only because the RNG is deterministic.

| Recording | Records | Length | P1 / P2 moving | P1 / P2 firing |
|---|---:|---|---|---|
| `level1f` +0x7a8e | 1008 | 1710 ticks ≈ 68 s | 70 % / 47 % | 36 % / 26 % |
| `level2f` +0x98be | 845 | 1584 ≈ 63 s | 69 % / 37 % | 27 % / 24 % |
| `level3f` +0x6460 | 1158 | 1767 ≈ 71 s | 65 % / 41 % | 44 % / 63 % |
| `level4f` +0x6a62 | 785 | 1310 ≈ 52 s | 72 % / 47 % | 45 % / 77 % |

The first P1 word of the level-1 recording carries junk high bits (`0x2c14`):
the raw input word was recorded and only bits 0/1/8/9 are used (medium).

## 5. Sound

### 5.1 No music during play (high)

**Nothing plays music while a level is running — on CD or on floppy.** All
four Paula channels belong to sound effects. Measured: the game issues
`AbortIO` on the CD track at game start and then not one `CD_PLAYTRACK` for
the whole of level 1; the gameplay VBlank server (`hunk0+0x6358`) never calls
the module replayer, which runs only from the text-screen server
(`hunk0+0x43CC`). Effects and modules are never active at the same time, so
there is no channel arbitration between them.

| Phase | Paula | CD (Red Book) | Floppy instead |
|---|---|---|---|
| Intro | `P60.intro` | — | same |
| Title, menus, briefings, game over | — | **track 3** | `p60.calm bottom4` from position 0 |
| High-score entry | — | **track 2** (if nothing is playing) | same module from position 0x35 |
| Gameplay | effects only, 4 channels | silent | silent |
| Ending and credits | `P60.end`, faded with the text scroll | — | same |
| Attract mode | effects muted | — | same |

The switch is one routine (`hunk0+0x5294`): if the "loaded set" byte
(`hunk0+0x32C1`) is `0xc0` it plays a CD track, otherwise it starts the
module in the buffer. One variable (`hunk0+0x52EA`) means "track 2" to the CD
path and "start position 53" to the module path.

### 5.2 Effects engine (high)

| Routine | Function |
|---|---|
| `hunk0+0xE870` | init: four channel structures, `SetIntVector` for AUD0–3, `DMACON=$000F` |
| `hunk0+0xEAB4` | **play**: sample id, period, volume 0–64 → channel or −1 (rejected) plus a handle |
| `hunk0+0xE956` | modify a playing sound by handle (volume 0 = stop) |
| `hunk0+0xE9D2` | per-frame slide of period and volume toward targets |

Sample ids `> 0` index the global bank (`soundfx`, or `soundfx4` from level
4); ids `≤ 0` index the level bank (block 0 of `levelNc`/`bossc`). The 16-byte
record ([09-audio.md](09-audio.md), [13](13-level-formats-and-floppy.md)) is
fully decoded:

| Offset | Field |
|---|---|
| +0 | offset.l |
| +4 | length in words |
| +6 | **repeat count** (−1 = forever; not a loop point — the sample always plays whole) |
| +8 | tail count, **0 in every bank** (unused feature) |
| +a…+d | **priority on channels 0…3** (0 = not allowed) |
| +e | **priority drop after start** (0 or 1) |

Channel selection (`hunk0+0xEABC`):

```
for c in 3, 2, 1, 0:
    p = record.prio[c]; if p == 0: continue
    if channel[c] free:          take it
    if p > channel[c].prio:      steal it (volume 0, DMA off, wait 4 lines)
reject
after start: channel.prio = p - record.drop
```

* Strict `>`: on a tie the sound already playing wins.
* Greedy: the first eligible channel is taken even if a later one is free —
  63 times in 4,745 steals on level 1.
* Drop 1 lets a sound pre-empt itself (the player's gun restarts every shot);
  drop 0 does not (an engine loop never retriggers itself).
* Volume is set by the first audio interrupt after DMA starts, and a stolen
  channel is zeroed first: no clicks.
* An object owns **at most one voice**; a new `SOUND` op silences its previous
  one. Removing an object fades level-bank (looping) sounds over a few frames
  instead of cutting them.
* The player's engine is restarted **every frame until it gets a channel back**
  after being stolen.

Channel roles, fixed by the priority bytes in the data:

| Ch | Role | Priorities |
|---|---|---|
| 3 | P1 engine, hit, death; P2 gun and hit | 0x5a–0x64 |
| 2 | P1 gun; P2 engine, death; player missiles | 0x5a–0x64 |
| 1 | one-shot enemy effects: explosions, ricochet, pods, pick-ups, enemy shots | 0x14–0x7c |
| 0 | level loops: enemy engines, ships, trains, bosses | 0x28–0x7e |

Some enemy effects also carry low priorities on channels 2/3 and spill onto
them only when the player is silent. Level 1 occupancy (autopilot, firing):
ch0 77 %, ch1 81 %, ch2 99 %, ch3 99 %; all four busy in 64 % of samples.
Of 7,282 requests: 7 % to a free channel, **65 % steals, 28 % rejected** —
in heavy action most enemy sounds never play.

Event summary (period → Hz: 3,546,895 / period):

| Event | Sample | Period / vol | Notes |
|---|---|---|---|
| Player engine | fx00 / fx05 | 226–350, from bank, roll and reverse; L4/boss 1243–1925 | fades in 0→32 after respawn |
| Player gun | fx01 / fx06 | 440 / 24 (L4, boss 540 / 32) | drop 1 |
| Player hit | fx04 / fx09 | **100** / 40 | below the hardware minimum of 124 (effect on real hardware: low confidence) |
| Death spin, death blast | fx03, fx02 (P2: fx08, fx07) | 300 / 28, 700 / 64 | |
| Missiles, piercing shot, bomb blast | fx27–31 | 600–900 | |
| Pod appears / hit / destroyed | fx12 / fx11 / fx13 | 550–600 | |
| Pick-up, extra life | fx18, fx33 | 230, 400 | |
| Smart bomb | fx10 twice, periods 700 and 701 | | meant as a detuned double; the algorithm puts both on channel 1, the second stealing the first (medium on intent) |
| Level 2 thunder | lv16 | 1000 / 64, 1140 / 24 | channel 1 only |
| Enemy explosions | fx14–17 | 780–906 | often randomised pitch |
| Big explosion | level-bank sample | 1000–1200 / 64 | priority 0x7a on ch2/3 — steals a player channel |
| Infantry scream | fx23 / fx24, chosen at random | 478 + 0…63 | |
| Enemy aircraft | level bank | 630–1500 | **fake Doppler**: script slides volume up and pitch down on approach, down and lower on exit |

In `soundfx4`, records fx03, fx08, fx19, fx25 and fx26 point at 16 bytes of
silence: no death spin on level 4 and the boss, and the enemy-cannon sound is
mute.

### 5.3 CD audio (high)

* Tracks addressed as constants: **3** for menus and between-level screens,
  **2** for high-score entry. No TOC read, no `CD_PLAYMSF`, no cross-fade.
* Looping is the 150-frame `CD_INFO` watchdog
  ([09-audio.md](09-audio.md)); the gap at the end of a track is up to 3 s
  (1.5 s on average).
* Stop is `AbortIO` plus a 1 s wait. The watchdog is called during gameplay
  but disabled.
* `io_Command #44` is **`CD_ATTENUATE`**, not `CD_ADDCHANGEINT` (which is 20):
  `io_Offset = 0x7fff` (volume), `io_Length = 0`. It is used once to set full
  volume; the matching mute routine has no callers.

### 5.4 The Player 6.0A

| Module | Where | Positions | Length |
|---|---|---|---|
| `P60.intro` | intro | 24 | 85.7 s |
| `P60.end` | ending and credits | 5 | 31.0 s |
| `p60.calm bottom4` (floppy only, one copy on each of disks 2–4) | menus, between levels, game over; position 53 = high-score entry | 58 (the main loop never reaches 53–57) | 116.7 s to loop |

The replayer is **timed from the vertical blank**, not a CIA: its timer-mode
variable is never written, so the `ciax.resource` / `P60TimerInterrupt` code
is dead. Master volume slides by 1 per tick toward a target; on the credits it
drops by one every four scroll steps, so the music fades with the text.

The floppy build loads `calm bottom4` from whichever disk is in the drive —
three identical copies so the player never has to swap for music — and uses a
larger configuration of the same replayer with ~3.8 KB more effect commands
that this module needs.

## 6. Display

### 6.1 One copper list (high)

A **single copper list for the whole game** at `hunk4+0x1466` (file
0x21ADE). Every frame it loads **all 256 colours** (16 blocks of `BPLCON3` +
32 `COLORxx`, high then low nibbles — about ten lines of copper time, finished
before the display), sprite pointers at line 0x14, bitplane pointers and
display registers at line 0x28, then `COPJMP2` into a **tail** chosen by the
CPU:

| Tail | Address | Effect |
|---|---|---|
| empty | `hunk4+0x1D66` | `WAIT $ffff` |
| boss | `hunk4+0x1D6A` | from line v, `BPLCON2 $0200`: playfield above sprites, so the boss ship (sprites) **emerges from under an edge that scrolls with the background** |
| sprite window | `hunk4+0x1D76` | `BRDSPRT` only inside the display window, hides sprite junk above and below |
| weather | `hunk4+0x1D92` | re-points four sprite channels at lines 0x2b and 0xab (§6.4) |
| mid-boss L2/L4 | built in chip BSS | per-line `BRDSPRT` on/off mid-line: HUD stays in the left border, the 192-px mid-boss body cannot spill into the right one |

No copper rainbows, no mid-screen palette changes, no copper split between HUD
and playfield. Every colour effect is the CPU editing values in this list once
per frame.

Display: **256×256**, six lores bitplanes (64 colours), `FMODE=3`. The **HUD is
one attached pair of 64-px sprites** (SPR0/1, colours 128–143) sitting
entirely in the **left border**, made visible by `BPLCON3 BRDSPRT`: player 1
at the top, boss bar in the middle, player 2 at the bottom. Player, enemies,
bullets and explosions are all Blitter bobs; hardware sprites are used only
for the HUD, mid-boss and boss bodies, and weather.

Palette layout: 0–63 playfield (`levelNf` palette set 0), 64–127 plane 7
(set 1; on level 2 the night palette), 128–159 sprites, 160–191 unused,
192–255 planes 7+8 (set 2; on level 2 the lightning palette).

### 6.2 Double buffering and scrolling (high)

* Six planes `0x6000` apart, 96-byte rows (two 384-px halves), **double
  buffered** by swapping two pointers (`hunk0+0xE58A`).
* The VBlank server alternates: one frame does the swap, sprite blocks,
  weather, planes 7–8 and `BPLCON0`, shake/flash, level 2 night and colour
  cycling; the other only the cloud pointers. **Logic and drawing run at
  25 fps**, scrolling 1 px per frame (600 VBL = 300 px, measured).
* **Vertical:** the CPU decodes 16×16 tiles into a 7-plane ring buffer
  (`hunk0+0xDC28`, `+0xDE72`). Each frame the visible 272×256 strip is copied
  into the back buffer by a **chain of six blits driven from the Blitter
  interrupt** (`hunk0+0xE300`, handler `+0xE358`) while the CPU copies, with
  `movem`, whatever part the Blitter has not reached yet (`hunk0+0xE3BC`,
  polling `BBUSY`). Then bobs are cookie-cut on top.
* **Horizontal:** the camera follows the players with inertia (velocity
  stepped ±1 against a threshold table: smooth acceleration and braking).
  Coarse steps of 16 px move the source column; odd columns shift drawing by
  2 bytes; the remainder goes into **`BPLCON1` at ½-pixel resolution** (AGA).

### 6.3 Planes 7–8: clouds and light (high)

* **Levels 1 and 3:** a cloud (L1) or dust (L3) layer from the map at
  `levelNf+0x24`, tiles at `+0x28`. It scrolls **2 px per frame against the
  ground's 1** — vertical parallax. Each tile word is stored twice, 32 px
  apart, so a pointer aligned to 8 bytes can still step by 32 px; `BPLCON1`
  covers the rest. Translucency is **baked into the palette**: colours 64–127
  and 192–255 are pre-blended versions of the 64 ground colours (L1 ≈63 % and
  ≈31 % toward grey; L3 toward pale dust). The layer ends at scroll 6316 (L1)
  and 5010 (L3).
* **Level 4 and boss:** a **light layer** for electrical arcs, cleared by the
  Blitter and drawn by OR-ing masks each frame, also used for player
  collision. Normally 7 planes with bank remapping in the copper list (plane 7
  shows the greenish glow set); 8 planes with a white core while barriers are
  active; 6 when no player is alive. The same 32 copper entries are assigned
  to different colour banks depending on mode — the layer changes colour
  without rewriting a value.

### 6.4 Weather (high)

Rain (L1, L2) and snow (L3) are **four 64-px sprites across the full 256-px
width**. One 128-line pattern is shown twice: the weather tail re-points the
sprite data at lines 0x2b and 0xab. Six animation frames of 4 KB are drawn
procedurally with `bchg` diagonal streaks; density ramps up to 100 (L2) or
200. To stop, the generator is **reseeded and run again with XOR**, so the
rain disappears in the order it appeared. Rain spans scroll 5460–5978 on L1
and 2430–3742 on L2; snow runs from the start of L3 to 3777.

### 6.5 Palette effects and shake (high)

Colour interpolation is shared (`hunk0+0xB36A`): `c + (target − c)·k/256` in
8 bits per channel, split into high and low nibbles — fades are smooth 24-bit
AGA fades, not 16-step OCS ones.

| Effect | Trigger | Behaviour |
|---|---|---|
| Flash to white | counter `A5+0x3ae` (`hunk0+0xBB34`) | colours 0–63 and HUD blended toward (255,250,240); flicker above 8, shake above 32 |
| Smart bomb (picked up) | | flash 8 + shake: white fades over 8 frames |
| Smart bomb (scripted) | | long flicker 0x28 + shake 0x2c |
| Big explosion | | flash held at level 6 until it ends |
| **Shake** | `A5+0x3b0` (`hunk0+0x6C38`) | **horizontal only**: `BPLCON1` alternates base and offset every frame, amplitude decaying linearly; HUD stays still |
| Colour cycling | always | L1 colours 60–62 at three speeds; L2/L3 colour 63; L4/boss colour 31 |
| Level 2 day → night → day | script at scroll 1600 / 3992 | ground palette lerps to set 1, 8 colours per frame, full night after 1024 frames (~41 s); player sprites darkened every 32 frames |
| Level 2 lightning | from scroll 2783, once night is full | white → ½ → ⅛ → night in three steps with thunder, pauses of 4–45 frames |
| **Sepia** game over | no players and no credits (`hunk0+0xB9D0`) | frame freezes, palette 0–127 and sprites move to the sepia palette at `levelNf+0x16` |
| GAME OVER | after sepia | a 240×162 2-plane bitmap in chip data (`hunk4+0x1DDE`) attached as planes 7–8, brightened along a sine, then fade and HUD slide-out |
| **Fades** | level start / end, abort | 17 steps to/from **dark blue (0,4,25)** (`hunk0+0xB240`), sprites included; the end fade also ramps all four channels to silence |

Low confidence: a small oval "heat-haze" distortion object on level 3
(objects copy the image from two lines below inside a mask) — its on-screen
appearance was not confirmed.

## Corrections to earlier chapters

* [09-audio.md](09-audio.md): `io_Command #44` is `CD_ATTENUATE`. The Red Book
  tracks are **not** played while the game runs; they are menu and high-score
  music. The P60 replayer runs from the VBlank; its CIA code is dead. The
  offsets labelled "file" in its listings are `hunk0+` offsets (add 0x34).
* [13-level-formats-and-floppy.md](13-level-formats-and-floppy.md):
  `p60.calm bottom4` is the floppy's **menu** music, not in-game music.
* [11-leftovers.md](11-leftovers.md) §6: see
  [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §3.

## Open questions

* The value of the `GfxBase+6` word on real CD32 hardware (fixes the exact
  RNG sequence).
* Whether a player-hit period of 100, below the DMA minimum, sounds as
  intended on real Paula.
* Two-player audio contention and levels 2–4 audio were analysed from code and
  data only; only level 1 single-player was emulated.
* The on-screen look of the level 3 distortion object.
