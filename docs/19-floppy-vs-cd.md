# Floppy against CD: the game logic compared

[13-level-formats-and-floppy.md](13-level-formats-and-floppy.md) compared the
two releases by files and strings. This chapter compares them **instruction by
instruction**: `bans.exe` from the four-disk A1200 release against the CD32
`bans.exe`, plus every data file.

Addresses are CD `hunk0+` / `hunk1+` offsets as in
[00-overview.md](00-overview.md). Floppy offsets are into the unpacked floppy
hunks and are written `fl hunkN+0x…`.

## Result

* **Gameplay is identical.** The enemy script interpreter (45 opcodes, 127
  sub-ops), spawning, enemy types and scripts, HP, drop tables, the player
  rating, pods, bosses, scrolling and collision: not one instruction differs.
* **All 37 shared data files are byte-identical**: `levelN*`, `boss*`,
  `plyrmisc*`, `soundfx*`, `core`, the pictures, the intro and ending frames,
  `P60.intro` / `P60.end`.
* Every code difference falls into one of four classes: **platform**,
  **loading/packing**, **copy protection** (floppy only) and **cheats** (CD
  only). **No bug fixes and no balance changes in either direction.**
* The **CD32 build is the later branch** of the same source revision (high
  confidence in direction, none in the time gap).

## Material

| Build | Source | Shape |
|---|---|---|
| CD | `bans.exe` on the disc | plain hunk file, 6 hunks, 1,948 relocations |
| Floppy | `bans.exe` from 10 variants of disk 1 | RNC ProPack method 1 self-extracting; a 612-byte stub hunk, the rest packed together with the relocation tables |

Several dumps of disk 1 were compared. Most unpack to identical hunks 0–5;
the majority, unmodified version is used here as the reference.

Unpacked sizes:

| Hunk | Floppy | CD |
|---|---:|---:|
| code | 99,916 | 97,500 |
| data | 27,008 | 26,932 |
| chip data | 16,752 | 16,752 |
| BSS (both) | same | same |

Both builds carry the same link stamp, `8/7-94 12:59`, with `RNC Beta` on the
floppy where the CD has `CD32 slut`.

## Method

1. Unpack both formats to the same representation: hunks plus relocations,
   numbered as on the CD.
2. Disassemble both code hunks linearly (68020) and normalise each
   instruction: a relocated operand becomes a byte mask plus the target hunk
   number; branch targets become `L`; PC-relative displacements become `P`.
3. Align with a diff, then split by the 436 functions Ghidra found in hunks 0
   and 3.
4. Check every relocated operand in aligned instructions: the pairs (CD
   target, floppy target) must form **one monotonic mapping** per hunk. A
   break would mean an instruction now points at a different object.
5. Align the data hunks bytewise with relocated longwords replaced by symbols.
6. Compare the in-code tables bytewise: drop table, the interpreter's jump
   table (`hunk0+0x108D2`), sprite, debris and palette tables.

Result: **395 functions identical, 34 changed, 7 CD-only.** The relocation
check found one break, in the menu cursor (below), which is a rewritten input
routine, not a different game object. The sub-op table and one dispatch table
differ only by `bra.w` displacements and the absolute addresses of moved code;
the functions using them are identical after normalisation. Remaining raw
differences are linear-disassembly artefacts — data decoded as code — and
vanish under normalisation.

## What differs

| Class | CD | Floppy |
|---|---|---|
| Platform: audio | `cd.device`, `CD_PLAYTRACK` / `CD_ATTENUATE` / `CD_INFO` watchdog, seven CD-only routines (642 bytes, `hunk0+0x4BE`–`0x73A`), 576 bytes of IORequest buffers in the code hunk; cleanup on exit | none |
| Platform: menu music | Red Book track 3 / 2 | `p60.calm bottom4` through Paula; the CD's track-switch routine is an `rts` on floppy |
| Platform: replayer | The Player 6.0A, small configuration | same replayer, larger configuration (~3.8 KB more effect commands: fine slides, note cut/delay, retrigger, glissando…) needed by `calm bottom4` |
| Platform: input | `lowlevel.library ReadJoyPort` in game and menu; PLAY = pause; REVERSE+FORWARD | `JOYxDAT` / mouse counters; menu cursor from the vertical mouse counter |
| Platform: control option | two labels, `Joystick` and `Joypad`, toggled 0↔1 | three states: `One Button` / `Two Buttons` / `Mouse`, in four languages |
| Loading | data kept resident; 37-record file table | lazy loading from four disks; 40 records (three extra for the music module, one per disk 2–4) |
| Title wait | 0xe0 frames | 0xea frames, then stops the module |
| Copy protection | none | present (below) |
| Cheats | name checks on the high-score screen; level skip on the pad | none |

### The control option, and a patch mark

Both builds use the same per-player variable and the same in-game input code:
negative = one button (no `POTGOR` read), 0 = two buttons, positive = mouse.
The floppy cycles all three. The CD wrote two bare strings, `Joystick` and
`Joypad`, **into the slot of the four-language `One Button` entry**, without
the group terminator, and toggles with `eori #1` — so the negative
("Joystick") state survives in code and is unreachable.

### Dead loading calls

On the CD, the four level wrappers for levels 2–4 and the boss have a `bra.w`
inserted **in front of** the `bsr` that loads data, leaving the old call as
dead code. The floppy calls them normally.

### Data hunks

Outside the control-label table, the data hunks differ by one alignment byte
and two bytes at the end; all 161 data-hunk relocations hit corresponding
objects. Chip data is identical except for five bytes at offsets +1…+5, which
no code references. Probably buffer residue saved with the image;
**unexplained**.

## Copy protection (floppy only)

The floppy build carries a copy-protection check that the CD build does not.
This repository does not document the protection.

## Cheats are CD-only

The two high-score-name cheats (`KanniJade Krew`, `Mary Whitehouse`) are
compared only in the CD build. The pad level skip needs CD32 pad buttons and
does not exist on floppy. The "killing animals" text **and the routine that
displays it** are present in the floppy build too, with nothing triggering
them there. The keyboard-sequence tables also exist in the floppy data hunk
(medium confidence on whether anything uses them there: no name comparisons
were found). Details in
[20-unused-content-and-cheats.md](20-unused-content-and-cheats.md).

## Which build is newer

1. **Same source revision.** Identical link stamp, identical BSS layout
   (0x53954 / 0x139bbc bytes) and global offsets, 395 of 436 functions
   identical after relocation. The differences look like conditional-assembly
   switches (CD / floppy, replayer feature flags), not development.
2. **The CD carries patch marks over the floppy path:** the `bra.w`-over-`bsr`
   dead loads, the control labels squatting in the `One Button` entry, a
   third control state that survives unreachable. A floppy derived from the CD
   would not look like this.
3. The CD adds developer cheats. The text one of them shows is already in the
   floppy data, so they were either removed from the floppy release or added
   for the CD; this does not settle direction.
4. Dates: the CD master is 17 minutes after the link stamp; files on both
   media carry the wrong 1992-12-21 clock, so file dates do not order the
   builds.

**Conclusion (high on direction):** the CD32 version is a later branch of the
same revision, made by reworking the floppy's platform paths (Red Book for the
module, pad and `lowlevel` for `JOYxDAT`, resident data for lazy loading, no
protection) and adding cheats. Both stamps carry the same minute, so they may
have been built the same day from one tree. Gameplay, balance and bugs — for
example the enemy type records with a missing flags word on level 2 and level
4 — are shared.

`RNC Beta` in the floppy banner more likely refers to the ProPack packer than
to the state of the game (low).

## Level data

| Level | Files | Result |
|---|---|---|
| 1–3 | `levelNc`, `levelNf` | identical |
| 4 | `level4c`, `level4f` | identical in 2 of 3 dumps; the others are **bad dumps** (the RNC stream fails to decode), not different versions |
| boss | `bossc`, `bossf` | identical |
| shared | `plyrmisc(4)`, `soundfx(4)`, `core`, pictures, intro/ending, `P60.intro` / `P60.end` | identical |
| floppy only | `p60.calm bottom4` ×3 | menu music; replaced by tracks 2 and 3 on CD |
| differs | `picture.exe` | same code and bitmap; the CD copy was saved from memory after running ([13](13-level-formats-and-floppy.md)) |

Because `levelNf` (spawns, types, scripts, palettes, attract recording) and
the code that executes it are identical, there is nothing to compare record
by record.

## Open questions

* The five differing bytes at the start of chip data.
* The CD's pad REVERSE+FORWARD while paused writes keycode 0x75 (ESC); the
  case it was written for (demo or two-player exit) is unconfirmed.
