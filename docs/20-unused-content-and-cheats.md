# Unused content, debug leftovers and cheats

What the CD build contains but never uses, what the programmer left in, and
every cheat. Addresses are `hunk0+` / `hunk1+` offsets as in
[00-overview.md](00-overview.md), with file offsets where they help. Bob
numbers count from 1; an enemy *type* is its byte offset into the level's
type table (`levelNf+0x0e`, [13](13-level-formats-and-floppy.md)).

**Method.** Reachability is static and recursive: start from every spawn
record, follow every script, add types created by scripts (`SPAWN`,
`SPAWNREL`, sub-op operands) and types created by native code (77 calls of the
spawn routine, `hunk0+0xFCD0`, each resolved to a type and a sub-op). It was
then checked against full runs of every level in emulation with hooks on
spawning, bob drawing (`hunk0+0x8B2E`) and sample playback: level 1 138/138
types and the boss 23/23 agree; on levels 2–4 emulation added only types
created from a register in native code, none from the unused list.

## 1. Cheats

**Two effects, each enabled two ways**: a name typed into the high-score
table, or a keyboard sequence typed on any text screen (the menus). The flags
are never cleared — they last until reset. All verified in emulation.
**High** confidence throughout.

### 1a. Developer mode: level skip and infinite lives (flag `hunk0+0x32BF`)

Enable with either:

* the high-score name **`KanniJade Krew`**, exactly — with a space between
  "Kanni" and "Jade" it does not work (compared at `hunk0+0x17A4`);
* the keys **`F L E V 1 7` RETURN** on a text screen (sequence table at
  `hunk0+0x4505`, stored as `(~byte) >> 1` keycodes).

Confirmation: the background flashes **blue** (`COLOR00 = $00F`). The name
cheat does not alter the table.

Effects:

| Effect | How |
|---|---|
| **F1–F10 end the level** | keyboard action table maps F-keys to a bit tested only with the flag (`hunk0+0x7DF8`); sets the same "level complete" flag a boss kill does |
| **Pad FORWARD + REVERSE ends the level** | when not paused (paused, the same pair quits). The only cheat usable on a bare CD32 — after entering the name with the pad |
| **Infinite lives** | on losing a ship (`hunk0+0xFB6C`) the game refills the shield, resets loops to 3, gives 75 ticks of invulnerability and **does not decrement lives** |

Measured: with zero shield for 3,000 frames, cheat on gave 8 deaths with
lives 3→3 and play continuing; cheat off gave 4 deaths, lives 3→0, game over.

### 1b. Civilians and animals can be shot (flag `hunk0+0x32BA`)

Enable with the name **`Mary Whitehouse`** (`hunk0+0x1806`) or the keys
**`I AM EXQUISITELY EVIL` RETURN** on a text screen (table at
`hunk0+0x44E9`).

Effects: the high-score table shows the "killing animals" message
([11-leftovers.md](11-leftovers.md) §7, `hunk1+0x5930` = file 0x1F1C4) in place
of the entry, **every score in the table becomes 999999**, the background
flashes pale blue (`$CCF`), and sub-op `20.b8` stops making civilians and
animals invulnerable. That settles §7's open trigger: the message is the
cheat's confirmation, not a reaction to play.

### 1c. What is not there

* No other name comparisons: a sweep for ASCII constants in `cmpi` finds only
  these two names and the replayer's `P60A`.
* No other key sequences: the keyboard byte is read only by name entry, the
  text-screen routine (two sequences), in-game controls and attract mode.
* Pad combinations in the whole program: bits 17/18/19 only (PLAY,
  FORWARD+REVERSE). No level select, no invulnerability without the cheat.
* **Floppy:** both keyboard tables exist in the data hunk, but no name
  comparisons were found in the code; the name cheats look CD-only (medium,
  [19-floppy-vs-cd.md](19-floppy-vs-cd.md)).
* The keyboard sequences need a keyboard on the CD32 (keyboard port or SX-1).

## 2. `flev` and `FLEV17`

`bans1:flev` (file 0x2BCA, `hunk0+0x2B96`) is a file name with no record and
no reference ([11-leftovers.md](11-leftovers.md) §5). The developer cheat's
key sequence is literally **`FLEV17`**, and what it does is skip levels.

**Hypothesis (low–medium confidence):** `flev` belongs to the programmer's
level-skipping aid — "f-level" or similar. It was once a file on disk 1
(a start-level flag or config read at boot), later replaced by the built-in
key sequence. The `17` matches nothing found: it is not a level number (there
are five).

**No trace of a cut level (high):** the level number takes only 1–5; every
jump table indexed by level has entries 0–5 (0 is a no-op or level 1); the
file table has a `c`/`f` pair for levels 1–4 and the boss; each level file's
number field matches its order. There is no slot for a sixth level in this
build.

## 3. Debug leftovers

| What | Where | Description | Confidence |
|---|---|---|---|
| **Raster bar, sub-op `20.00`** | `hunk0+0x11FE6` | takes a colour operand and, until line 0x80, writes `COLOR00 = 0`, five `nop`s, `COLOR00 = colour` — a coloured band in the top half of the screen, the classic CPU-time meter. **No script on any level uses it** | high |
| Magenta/black flashing loop | `hunk0+0x53C` (file **0x570**) | **Correction to [11-leftovers.md](11-leftovers.md) §6:** not dead code and not a stray exception handler. A `bne` at `hunk0+0x51E` jumps here when `OpenDevice("input.device")` fails: the fatal-startup-error path. The offset given there, 0x53C, is a hunk offset | high |
| White `COLOR00` flashes until fire | three places in the loader | file-read error handling, not debug | high |
| `DebugDisk:` hook | `/s/startup-sequence` | [11-leftovers.md](11-leftovers.md) §1 | — |

No write-never "read-only" switch exists among the flags at
`hunk0+0x32B0…0x32C8`: every flag has writers (menu, loader, cheats).

## 4. Unused sub-ops and opcodes

**Sub-ops never used on any level: 4 of 127.**

| Sub-op | Address | What it does |
|---|---|---|
| `00` | `hunk0+0x11FE6` | raster bar (§3) |
| `c4` | `hunk0+0x15FAC` | ballistic tumbling flight: frame +1 per tick (cycle 16), gravity on vy — a debris piece thrown in an arc, a variant of `20.3c` |
| `144` | `hunk0+0x146BC` | a projectile **held in the hands of the armed level 2 mid-boss**, released after 3 ticks with a speed taken from the RNG, driven by boss signal words. Its only caller is unused L2 type `0x29c` (§5). **Caveat (2026):** the cleaned `scriptdis.py --reach` (disassembler state reset per type) also reaches `20.144` statically in L4 type `0x194`, which the L4 mid-boss creates through `20.cc`; the original pass stopped that walk early at a `DELAY`. It was never executed in the emulated runs, so whether it is live is **open** |
| `1e4` | `hunk0+0x17C44` | animation frame from velocity direction (8 directions, every 3 ticks) |

Corrections to earlier notes: `20.1cc` is used (level 4, type `0x160`);
`20.114` is used by L2 types spawned by the boss director; `20.0c`, `20.54`
and `20.80` are used by types created from native code. `20.10` and opcode
`98` are used by types that **other scripts spawn** (`SPAWN`), never by
spawn-list types: `98` by L1 `0x3c` and L3 `0x2c`/`0x30` (homing rockets),
`20.10` by L1 `0x48`/`0x144`, L2 `0x28`/`0x7c`/`0x2b0`/`0x2b4` and L3 `0x44`
(checked 2026 with `tools/scriptdis.py --reach`; resolves the open question in
[17-player-scoring-difficulty.md](17-player-scoring-difficulty.md)).

**Opcodes never used: 2 of 45.**

* `8c` (`hunk0+0x114EA`): spawn an effect (explosion) like `48`, with the
  offset taken from object fields instead of immediates.
* `9c` (`hunk0+0x119A6`): **subtract BCD points** from the player who scored
  the hit (floored at 0) and adjust the difficulty rating. An unused **score
  penalty** — it would fit shooting civilians, but no script uses it;
  civilians are simply invulnerable without the cheat.

## 5. Enemy types defined but never spawned

"Never" = statically unreachable **and** absent from full emulated runs.
High confidence on unreachability; descriptions from data and from inserting
the type into a running level.

| Level | Types | What |
|---|---|---|
| L1 | `0x38`, `0x40`, `0x44` | homing-missile variants with other launch directions |
| L1 | **`0x60`** | a **lighthouse-like turret with a swaying head**, invulnerable; the only user of bobs `0x78`/`0x79` |
| L1 | `0xc0`, `0xe4` | mirrored side-entry helicopter/aircraft variants |
| L1 | `0x138` | gun variant with different movement |
| L2 | `0x00`–`0x24`, `0x34` | ten bullet types (three kinds × three directions, one homing): spare ammunition |
| L2 | `0x70`, `0x74` | duplicates of used weather-control types |
| L2 | `0x90`, `0x98` | rotating-turret tank variants |
| L2 | **`0xc0`** | a **freight wagon** steered by the train's direction, with a wreck; the only user of its bob |
| L2 | `0x1cc` | gun variant |
| L2 | **`0x29c`** | a **spiked mine thrown by the mid-boss** — the only user of sub-op `144`. Inserted during the mid-boss fight it only sways: the attack that would release it was cut |
| L3 | **`0x10`** | a **floating mine** with random drift and wobble |
| L3 | `0x34`, `0x134` | homing-missile and ground-vehicle variants |
| L4 | `0x88` | barrelled gun variant |
| L4 | `0xa0`, `0xa4`, `0xa8` | parts falling in an arc to a wreck; the only users of bobs `0x141`–`0x144` |
| boss | — | all 23 types used |

Totals: L1 7, L2 18, L3 3, L4 4, boss 0.

## 6. Bobs with no reference

Criterion: never drawn in a full run **and** the number does not appear as a
word in the script section or animation ranges. Light-layer cut-outs on L4 and
the boss are excluded. **Medium** confidence: frames computed in code
(direction + base) may give false positives.

| Bank | Unused | Notes |
|---|---:|---|
| L1, L3 | 0 | |
| L2 | 48 | including two **"help!" speech bubbles** next to the falling-man and parachutist bobs that are used — cut civilian cries; balloon halves/frames (perhaps a break-up animation, some possibly computed); explosions |
| L4 | 31 | a grabber claw, chain links, three jets, bunker turrets, a rocket |
| boss | 296 + 42 | the boss bank is **427 of 530 bobs a copy of level 4's** and uses almost none of it; 42 boss-only bobs are unused, many being descriptors pointing into the middle of other graphics (slices of HUD words and digits) — unswept editing leftovers |

The `CREDITS` + digit bob is **not** unused: each level header points at it
(with `PAUSE` and `GET READY`), and it blinks for 300 ticks whenever a credit
is spent ([18-runtime.md](18-runtime.md) §3). It never shows for a single
immortal player, which is why it looked dead.

## 7. Samples and text

* **No unique unused sample.** Every level-bank record plays in emulation
  (one L2 record that does not is a duplicate). In `soundfx`, unused records
  5–9 duplicate 0–4 and 27/29 duplicate 20; in `soundfx4`, 3/8/19/25/26 are
  16-byte silent stubs and 5–7, 9, 21 duplicates. High.
* **No unused text group.** All 77 four-language groups in hunk 1 have a
  direct pointer from the page tables or menu code. The only standalone texts
  are the cheat message and the build banner. Medium (the pointer tables
  themselves were not all traced to callers).

## Open questions

* What `17` in `FLEV17` stands for, and what `flev` contained.
* Whether the "help!" bubbles and the balloon frames are reached by computed
  frame numbers that the static scan misses.
* What the cut mid-boss mine attack (`0x29c` / sub-op `144`) looked like in
  motion; the boss never sends the signals that release it.
* Whether the static path to `20.144` in L4 type `0x194` (above, §4) can
  run; only an emulated L4 mid-boss fight with a hook on the handler settles
  it.
