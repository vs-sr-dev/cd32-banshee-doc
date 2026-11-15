# cd32-banshee-doc

Reverse-engineering notes on **Banshee** (Core Design, 1994) for the **Amiga
CD32** — a vertically scrolling shooter set in an alternate 1999 where nobody
has invented the microwave oven, and the twelfth disc in this series.

This repository documents the European release: three tracks, 45 directory
records, 37 of them RNC ProPack streams, and a title picture in a display mode
nothing else on the format uses.

**Documentation only.** No game assets, no extracted art, no audio, no
executable code is committed here. The tools in [`tools/`](tools/) reproduce
every figure, table and image in these pages from your own legally obtained
copy.

## What is documented

| Doc | Contents |
|---|---|
| [00-overview.md](docs/00-overview.md) | The release, the file inventory, two clocks and a link stamp, and the address convention |
| [01-disc-image.md](docs/01-disc-image.md) | Cue sheet, sector map, five minutes of Red Book, and a 232-sector run that should be 32 |
| [02-filesystem.md](docs/02-filesystem.md) | ISO 9660 by the field, the `.TM` block, two clocks nineteen months apart, and a floppy-speed write log under the wrong one |
| [03-boot-chain.md](docs/03-boot-chain.md) | A boot script with a live developer hook and four floppy volume names |
| [04-compression.md](docs/04-compression.md) | RNC method 1 over the files, method 2 *inside* an executable, and three ways to measure the same disc |
| [05-loader.md](docs/05-loader.md) | `bans.exe`: six hunks, 1,948 relocations, 71 library calls, and a file table that is a floppy layout |
| [06-text.md](docs/06-text.md) | Four languages, code page 437, and three Danish letters on punctuation keys |
| [07-graphics.md](docs/07-graphics.md) | Two eight-bitplane AGA screens, 256 colours at 24 bits, and the three Blitter questions answered |
| [08-picture-exe.md](docs/08-picture-exe.md) | A 484-byte stub that decrunches *and* relocates itself, and a 640×512 HAM8 picture nothing runs |
| [09-audio.md](docs/09-audio.md) | `CD_PLAYTRACK`, a three-second `CD_INFO` watchdog, and The Player 6.0A |
| [10-core-design-control.md](docs/10-core-design-control.md) | **Banshee against Dragonstone**, point by point — the first same-label control in this series |
| [11-leftovers.md](docs/11-leftovers.md) | A debug hook, two empty files, an empty directory, a dead filename, a halt loop, and a message about killing animals |
| [12-open-questions.md](docs/12-open-questions.md) | Everything unresolved, with the measurement beside it |
| [13-level-formats-and-floppy.md](docs/13-level-formats-and-floppy.md) | Level file formats, palettes, and the A1200 floppy release by files and strings |
| [14-enemy-vm.md](docs/14-enemy-vm.md) | The enemy/object scripting VM: object definitions, 45 opcodes, 127 sub-ops, death scripts, `scriptdis.py` |
| [15-enemy-movement.md](docs/15-enemy-movement.md) | Enemy movement: 27 movement and 4 bullet archetypes, checked tick by tick against emulation |
| [16-levels-and-bosses.md](docs/16-levels-and-bosses.md) | Each level and boss by scroll position, the two endings, and blocks [3]/[4] of `levelNc` |
| [17-player-scoring-difficulty.md](docs/17-player-scoring-difficulty.md) | Ship, weapons, shield, pods, score rules, the player rating and the difficulty curve |
| [18-runtime.md](docs/18-runtime.md) | RNG, input, two players and credits, the shell, sound (no music in play) and display effects |
| [19-floppy-vs-cd.md](docs/19-floppy-vs-cd.md) | Floppy against CD instruction by instruction: what the CD32 port changed |
| [20-unused-content-and-cheats.md](docs/20-unused-content-and-cheats.md) | Unused sub-ops, types, bobs and samples, debug leftovers, and every cheat |
| [notes/file-inventory.md](notes/file-inventory.md) | All 45 directory records with LBA, three sizes, timestamp and SHA-1 |
| [notes/](notes/) | Raw output of every tool: PVD, sector map, census, copper lists, register scan, string and text tables, and the annotated depacker listing |
| [cd32-platformnotes-doc](https://github.com/vs-sr-dev/cd32-platformnotes-doc) | **Platform checklist** — what to look for on *any* CD32 or CDTV disc, shared by every Amiga CD pipeline here |

## Highlights

**The first same-label control this series has had, and almost nothing
matches.** Dragonstone is Core Design; Banshee is Core Design. Predictions
were written before the measurements. What the two discs share is a Commodore
file every developer was sent (the `.TM` block), an operating-system file that
tracks which Kickstart release was on the build machine (`SetPatch` 40.14,
byte-identical — but three of the four other version-groups in the set pair
*unrelated* studios, so the match carries no label information), and a
commercial cruncher. Everything either team actually wrote differs: 71 library
calls against **zero**, `dos.library` against a hand-written ISO 9660 parser,
variable-length file records against a fixed-width name table, four control
bytes against two, and Akiko driving the CD drive on one disc and **not
appearing at all** on the other. See
[10-core-design-control.md](docs/10-core-design-control.md).

**And the one cross-disc regularity it did turn up points somewhere nobody
proposed.** Banshee's data-preparer field is `D J Pocock`, character for
character the same as **Liberation**'s — a different studio, a different
publisher, three months earlier. Eight discs in this series leave 32 zero
sectors at the end of the volume; those two leave **232**, in volumes of 1,687
and 82,502 sectors. The only unit of shared practice this comparison found
runs through **the person who ran the mastering tool**.

**A debug hook, live, in a pressed retail boot script.** Lines 2–6 of
`/s/startup-sequence` check for a volume called `DebugDisk:` and, if it is
there, assign `T:` to RAM and **execute a script off it** before the game
starts. A CD32 has no `DebugDisk:` so it never fires. It survived because it
is not in the program: nothing about building the program would have removed
it.

**A 274 KB program nothing runs, holding an image nobody saw.** `picture.exe`
is 9.5 % of the data track and is named by nothing on the disc — not the boot
script, not the game, not the loader's 37-entry file table. Behind three RNC
ProPack **method 2** streams and a 484-byte stub that decrunches *and applies
its own relocation tables*, it holds a **640 × 512 interlaced HAM8** picture
with a 64-entry 24-bit palette: 327,680 bytes, the largest single image on the
disc, in a display mode nothing else in this series uses. A census over
*files* calls it "hunk executable, not compressed"; its entropy of 7.84 is
what gives it away.

**Two clocks nineteen months apart, and the wrong one is still a
stopwatch.** Forty-one of the 45 records are stamped 1992-12-21, on a disc
mastered 1994-07-08. The executable dates itself: at file offset 0x50, between
an `rts` and the next routine, `8/7-94 12:59 CD32 slutp` — a link stamp
seventeen minutes before the master, written day/month-year with a dash, with
the Danish word *slut* in it. The wrong clock is not noise either: its gaps
track file size at about 7–10 KB/s, floppy speed, in the retail floppies'
per-disk write order. The 1992 stamps are a real write log from a second
machine with no battery clock, which restarted at nearly the same reading on
every boot, and the files were carried into the mastering tree with their
dates intact. The first reading of this disc fitted that log inside the
17-minute mastering window; the A1200 floppy release showed that it does not
fit. [02-filesystem.md](docs/02-filesystem.md) keeps both the original
arithmetic and the correction.

**Four languages, and the fourth one has its own alphabet.** German and French
use ordinary code page 437 (`0x81` ü, `0x94` ö, `0xE1` ß). Danish does not:
`"` is Æ, `$` is Å, `+` is æ, `=` is å, `~` is ø — five ASCII punctuation
characters plus `0x9C` for Ø, which is not arbitrary at all, because the
hall-of-fame alphabet stores them in the order `… X Y Z " 9C $`, and Æ Ø Å is
where the Danish alphabet goes after Z.

**The floppy release, reconstructed from the CD.** The boot script assigns
`banshee1:` through `banshee4:` to `CD0:`, and the loader's file table carries
a disk number in every record. Level 3's two halves are on **different disks**,
which is what happens when a level will not fit on one 880 KB floppy and is
not something anybody would invent for a compact disc. The real four-disk A1200
release later confirmed it, and compared instruction by instruction it plays
the same game: the CD32 build is the later branch of the same source
([19-floppy-vs-cd.md](docs/19-floppy-vs-cd.md)).

**Inside the game (2026, contributed by Gnacik).** Chapters 13–20 go past the
loader into the game itself: the enemy scripting VM (45 opcodes, 127 sub-ops),
enemy movement checked tick by tick against emulation, every level and boss,
scoring and the difficulty curve, the RNG, and what was cut. They also answer
most of [12-open-questions.md](docs/12-open-questions.md). The message about
killing animals turns out to be the confirmation of a cheat: without it,
civilians and animals cannot be hit at all
([20-unused-content-and-cheats.md](docs/20-unused-content-and-cheats.md)).

**Where the frame ends up: nowhere interesting, and that is the answer.** The
three Blitter questions take ten minutes and settle it. The only `BLTCON1`
write on a live path carries a B-shift and no fill bits. `BLTSIZE` heights are
256, 192, 162, 96 and 81 — whole rectangles, not scanlines. The minterm `$CA`
is there but with `USEA` **set**, which makes it the ordinary masked bob blit
and not Guardian's cookie-cut span fill. Akiko is zero on both halves: zero
`$B80000` pointer loads, zero `$B80038`.

## Reproducing

Everything here is generated from the disc image by the scripts in
[`tools/`](tools/), which need Python 3, [Pillow](https://pypi.org/project/Pillow/)
for the image renderers and [Capstone](https://www.capstone-engine.org/) for
the two disassembly listings.

```sh
python3 tools/isodump.py     "<track1>.iso" --extract _work/ext --json _work/inv.json
python3 tools/census.py      _work/ext --out _work/unp
python3 tools/inventory.py   "<track1>.iso" > notes/file-inventory.md
python3 tools/loadertable.py _work/ext/bans.exe
python3 tools/text.py        _work/ext/bans.exe
python3 tools/regscan.py     _work/ext/bans.exe
python3 tools/akiko.py       _work/ext/bans.exe _work/ext/picture.exe
python3 tools/rnc2.py exe    _work/ext/picture.exe _work/picture
python3 tools/copper.py      _work/picture/hunk2.bin 0 904
python3 tools/planar.py      _work/picture/hunk3.bin logo.png \
        --w 640 --h 512 --planes 8 --offset 0x40 --interleaved --ham8 \
        --order 2,3,4,5,6,7,0,1 --pal-rgb24 _work/picture/hunk2.bin:0x2c8:64
```

| Tool | What it does |
|---|---|
| `isodump.py` | PVD field by field, the `.TM` pointer, the directory tree, the sector map, extraction |
| `inventory.py` | `notes/file-inventory.md` — every record with three sizes and a SHA-1 |
| `census.py` | Container identification, RNC decode, and bytes on disc / unpacked / used |
| `rnc.py` | RNC ProPack **method 1** — carried unchanged from `cd32-dragonstone-doc` |
| `rnc2.py` | RNC ProPack **method 2**, transcribed from `picture.exe`'s own stub, plus the self-decrunching hunk walker |
| `relocs.py` | Hunk layout and "which hunk is this constant an offset into" — from `cd32-guardian-doc` |
| `loadertable.py` | The loader's 37 file records and the headerless thirty-eighth name |
| `text.py` | The four-language string table, with the Danish substitutions applied |
| `strings.py` | Printable strings with file offsets |
| `regscan.py` | Custom-chip registers, both absolute and base-tracked — from `cd32-guardian-doc` |
| `akiko.py` | The Akiko scan, both halves — from `cd32-guardian-doc` |
| `copper.py` | Copper-list disassembly with register names |
| `planar.py` | Planar bitmap renderer: interleaved or not, indexed or HAM8, arbitrary plane order |
| `dis68k.py` | Capstone M68K with branch targets recomputed from the raw bytes |
| `m68kdis.py` | The plain Capstone wrapper — from `cd32-guardian-doc` |
| `adf.py`, `ground.py`, `bobs.py`, `map.py`, `spawns.py`, `samples.py` | Floppy images and level formats ([13](docs/13-level-formats-and-floppy.md)) |
| `bansexe.py` | Relocated `bans.exe` image and runtime ↔ `hunkN+` ↔ file-offset conversion |
| `scriptdis.py` | Enemy-script disassembler and `--reach` reachability report ([14](docs/14-enemy-vm.md)) |
| `movement/`, `rng/` | VM movement extractor and simulator ([15](docs/15-enemy-movement.md)); RNG model ([18](docs/18-runtime.md)) |
| `answers/` | The scripts behind the 2026 answers in [12-open-questions.md](docs/12-open-questions.md) |

Usage for the newer tools is in [`tools/README.md`](tools/README.md).

**A warning that applies to every listing in these pages.** Capstone's M68K
backend prints wrong-but-plausible branch displacements, immediates and
absolute addresses on this code. The byte column is the authority; every
constant quoted here was re-read from it, and `dis68k.py` exists because the
branch targets had to be recomputed by hand.

## Sibling repositories

Eleven other Amiga CD pipelines share the platform checklist:
[Dragonstone](https://github.com/vs-sr-dev/cd32-dragonstone-doc) ·
[Marvin's Marvellous Adventure](https://github.com/vs-sr-dev/cd32-marvinsmarvellousadventure-doc) ·
[Prey](https://github.com/vs-sr-dev/cd32-prey-doc) ·
[The Speris Legacy](https://github.com/vs-sr-dev/cd32-thesperislegacy-doc) ·
[Legends](https://github.com/vs-sr-dev/cd32-legends-doc) ·
[Liberation](https://github.com/vs-sr-dev/cd32-liberation-doc) ·
[Microcosm](https://github.com/vs-sr-dev/cd32-microcosm-doc) ·
[Gloom](https://github.com/vs-sr-dev/cd32-gloom-doc) ·
[HeroQuest II](https://github.com/vs-sr-dev/cd32-heroquest2-doc) ·
[Guardian](https://github.com/vs-sr-dev/cd32-guardian-doc)
