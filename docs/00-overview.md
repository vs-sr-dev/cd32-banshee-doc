# Overview

**Banshee**, Core Design, 1994. Amiga CD32. A vertically scrolling two-player
shooter set in an alternate 1999 where the Second World War never ended and
nobody has invented the microwave oven.

This repository documents the European CD32 release: **three tracks, 45
directory records, 37 of them RNC ProPack streams, 1,455 sectors of a 333,000
sector disc**, and a title screen in a display mode no other disc in this
series uses.

## The release, from the disc

| | |
|---|---|
| Volume identifier | `Banshee` |
| Publisher | `Core` |
| Application identifier | `Banshee CD32` |
| Data preparer | `D J Pocock - ISOCD 1.04 by Pantaray, Inc. USA -` |
| PVD created | **1994-07-08 13:16:10** GMT |
| Tracks | 1 data (`MODE1/2048`), 2 audio |
| Declared volume | 1,687 sectors; image 1,773 |
| Files | 45 records in 4 directories, **two of them zero bytes long** |
| Bytes on disc | 2,879,663 (2.88 MB) |
| Bytes after unpacking | 5,768,936 (5.77 MB) |
| Catalogue number | `5020717200444` (a real UK EAN-13) |

The game is credited on its own credits screen to a two-person team:

```
Programming and Design      Søren Hannibal
Graphics and Design         Jacob "Jade" Andersen
Music and soundfx           Martin Iveson
Lots of ideas and gameplay tweaking   Adrian Smith
Storyboard etc.             Guy "The Dictionary" Miller
                            © 1994 Jeremy Heath Smith
```

Core Design is the publisher and the disc says so twice — `Core` in the PVD
and "*and the rest at Core*" in the thank-you list — but the two people who
made it are Danish, and the disc says that too, three times over: a **fourth
language, Danish**, beside English, German and French; a build banner written
`8/7-94` in day/month-year order; and the word `slut` (Danish for *end*) in
that banner. See [10-core-design-control.md](10-core-design-control.md), which
is what this disc is really for.

## What is on the data track

37 of the 45 files are RNC ProPack method 1 streams and they are the whole
game. Grouped the way the loader groups them:

| Group | Files | On disc | Unpacked |
|---|---:|---:|---:|
| Levels (`levelNc` / `levelNf`) | 8 | 1,669,998 | 3,170,702 |
| Boss (`bossc` / `bossf`) | 2 | 153,475 | 298,904 |
| Pictures (`introscreen`, `banspic1`, `banspic2`) | 3 | 160,204 | 494,592 |
| Cut-scene frames (`introseq.*`, `endseq1.*`, `endseq2.*`) | 17 | 88,838 | 696,320 |
| Music (`P60.intro`, `P60.end`) | 2 | 39,108 | 58,242 |
| Sound and sprites (`soundfx*`, `plyrmisc*`, `core`) | 5 | 322,670 | 604,806 |
| Programs (`bans.exe`, `picture.exe`) | 2 | 424,288 | — |
| AmigaDOS (`C/SetPatch`, `C/Assign`, `C/Execute`) | 3 | 20,852 | — |
| Boot script | 1 | 230 | — |
| **Zero-length** (`scrpt2`, `C/Installer`) | 2 | **0** | — |

The `c`/`f` suffix on the level and boss files is a chip-RAM / other-RAM
split: the `c` half is the graphics, the `f` half is everything else.

## The build, from the timestamps

The disc has two clocks in it and they disagree by nineteen months, which is
the most useful thing about them — because the executable stamps its own link
time inside itself and that pins the wrong one down exactly:

```
1994-07-08 12:59       bans.exe links       (its own banner, inside the file)
1992-12-21 15:11:46    picture.exe          \
      ...              41 game files         > a wrong clock, 15 min 48 s of it
1992-12-21 15:27:34    soundfx4             /
1994-07-08 13:13:22    /s directory         ISOCD, on a correct clock
1994-07-08 13:14:37    /C directory
1994-07-08 13:16:10    the master
```

The wrong clock's **relative** times span 15 minutes 48 seconds and the real
window between the link stamp and the master is **17 minutes 10 seconds**.
The copy fits inside the window with 82 seconds to spare, so the two clocks
describe one session and the whole master is accounted for to the second.
[02-filesystem.md](02-filesystem.md) does the arithmetic.

> **Correction (2026).** The floppy release shows the 1992 stamps were
> written at floppy speed (7–10 KB/s) on a second machine, so they do not fit
> inside the 17-minute window and are not part of the mastering session; see
> the correction in [02-filesystem.md](02-filesystem.md).

Three files sit outside the game group and they are exactly the three
AmigaDOS commands: `Assign` and `Execute` share one timestamp to the second
(1993-06-17 14:40:04, copied together off a Workbench disk) and `SetPatch` is
five months later.

## Documents

| Doc | Contents |
|---|---|
| [01-disc-image.md](01-disc-image.md) | Cue sheet, sector map, the 232-sector run, five minutes of Red Book |
| [02-filesystem.md](02-filesystem.md) | ISO 9660 by the field, two clocks, and the session reconstructed |
| [03-boot-chain.md](03-boot-chain.md) | A boot script with a debug hook and four floppy volume names |
| [04-compression.md](04-compression.md) | RNC method 1 over the files, method 2 *inside* an executable, and three ways to measure a disc |
| [05-loader.md](05-loader.md) | `bans.exe`: hunks, relocations, the file table, 71 library calls and `cd.device` |
| [06-text.md](06-text.md) | Four languages, code page 437, and three Danish letters on punctuation keys |
| [07-graphics.md](07-graphics.md) | Two AGA screens, 256 colours at 24 bits, and where the frame ends |
| [08-picture-exe.md](08-picture-exe.md) | A 484-byte stub that decrunches and relocates itself, and a HAM8 640×512 title picture |
| [09-audio.md](09-audio.md) | `CD_PLAYTRACK`, a three-second watchdog, and The Player 6.0A |
| [10-core-design-control.md](10-core-design-control.md) | **Banshee against Dragonstone, point by point** — the first same-studio control in this series |
| [11-leftovers.md](11-leftovers.md) | Two empty files, an empty directory, a dead filename, a debug hook, a halt loop, and a message about killing animals |
| [12-open-questions.md](12-open-questions.md) | Everything unresolved, with the measurement beside it |
| [13-level-formats-and-floppy.md](13-level-formats-and-floppy.md) | Level file formats, palettes, and the A1200 floppy release by files and strings |
| [14-enemy-vm.md](14-enemy-vm.md) | The enemy/object scripting VM: object definitions, 45 opcodes, 127 sub-ops, death scripts, `scriptdis.py` |
| [15-enemy-movement.md](15-enemy-movement.md) | Enemy movement: 27 movement and 4 bullet archetypes, checked tick by tick against emulation |
| [16-levels-and-bosses.md](16-levels-and-bosses.md) | Each level and boss by scroll position, the two endings, and blocks [3]/[4] of `levelNc` |
| [17-player-scoring-difficulty.md](17-player-scoring-difficulty.md) | Ship, weapons, shield, pods, score rules, the player rating and the difficulty curve |
| [18-runtime.md](18-runtime.md) | RNG, input, two players and credits, the shell, sound (no music in play) and display effects |
| [19-floppy-vs-cd.md](19-floppy-vs-cd.md) | Floppy against CD instruction by instruction: what the CD32 port changed |
| [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) | Unused sub-ops, types, bobs and samples, debug leftovers, and every cheat |
| [notes/](../notes/) | Raw output of every tool |
| [cd32-platformnotes-doc](https://github.com/vs-sr-dev/cd32-platformnotes-doc) | The platform checklist this pipeline follows |

## Address convention

**Every address in these documents is a file offset into the named file
unless it says otherwise**, and where a hunk offset is meant it is written
`hunk0+0x1234`. This matters because `bans.exe` is an AmigaDOS hunk
executable with 1,948 relocations: its absolute constants are hunk offsets
that `LoadSeg` rewrites, and the same numbers read as file offsets point
somewhere else. The conversion for this file is:

| Hunk | Kind | Memory | Length | File offset of body |
|---:|---|---|---:|---|
| 0 | CODE | any | 97,500 | 0x000034 |
| 1 | DATA | any | 26,932 | 0x019894 |
| 2 | BSS | any | 342,356 | — |
| 3 | CODE | **chip** | 288 | 0x020490 |
| 4 | DATA | **chip** | 16,752 | 0x020678 |
| 5 | BSS | **chip** | 1,285,052 | — |

so `hunk0+N` is file offset `N + 0x34`, and `hunk4+N` is `N + 0x20678`.
`tools/relocs.py --at <file offset>` answers "is this constant covered by a
relocation, and if so into which hunk" — and a constant that is *not* covered
is a literal, not an address. `picture.exe` needs a different convention
again and [08-picture-exe.md](08-picture-exe.md) states it there.
