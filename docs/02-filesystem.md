# The file system

## The primary volume descriptor, field by field

```
system identifier      'CDTV' + 28 spaces
volume identifier      'Banshee' + NUL padding
volume space size      1687 sectors (LE and BE agree)
path table size        44
L path table           20      L path table optional  20
M path table           19      M path table optional  19
root dir extent        22, 2048 bytes, dated 1978-01-01 00:00:00
volume set identifier  (empty)
publisher identifier   'Core'
data preparer          'D J Pocock - ISOCD 1.04 by Pantaray, Inc. USA -'
application identifier 'Banshee CD32'
creation date          1994-07-08 13:16:10.00 +0
modification date      (NUL)
expiration date        (NUL)
effective date         (NUL)
file structure version 1
```

Every ISOCD 1.04 habit this series has catalogued is present:

* the descriptor is written **twice**, at 16 and 17, byte for byte identical,
  with the terminator at 18;
* the **optional** path-table pointers are filled with copies of the mandatory
  ones (L 20/20, M 19/19) rather than left zero;
* every string field it was given a value for is **NUL**-padded where ISO 9660
  asks for spaces — except the system identifier, which is the space-padded
  constant `CDTV`;
* mixed-case file names, path tables before the files, an image longer than
  the declared volume.

The system identifier says `CDTV` on a CD32 disc, as it does on every other
disc in this series. It is not evidence of anything.

### The free-text fields

Ten discs, and this is the first to fill in **three** of the four boxes with
three different kinds of answer at once: the volume identifier is the title,
the publisher is the label, and the application identifier is **the title plus
the console** — `Banshee CD32`. The volume-set identifier is empty.

Whoever typed these knew what they were doing, and the application identifier
is the tell: `Banshee CD32` is a name for a *master*, not for a game.

### The preparer, and where else that name is

```
D J Pocock - ISOCD 1.04 by Pantaray, Inc. USA -
```

This is the same string, character for character, as
[Liberation](https://github.com/vs-sr-dev/cd32-liberation-doc)'s — a Byte
Engineers game published by Mindscape and mastered three months earlier. Two
studios, two publishers, one operator.

This matters more than a coincidence of names, because of what the series
already knew about that person: on Liberation, `D J Pocock` appears **nowhere
else in 169 MB** — no credits screen, no version string, no file name. On
Banshee the same is true: `Pocock` occurs nowhere in the data track outside
this field, and the game's own credits screen names five people, none of them
him.

So the preparer field is not a credit. It names the person who ran the
mastering tool, and on these two discs that person worked for neither studio.
Section 1 of the platform checklist asks whether the preparer name can be
found in the title's own data; the answer here is no, for the second time, and
the two "no"s are the same name.

The other thing this settles: **this field carries no studio information at
all.** Core Design's other disc in this series, Dragonstone, says
`Sajjad Majid`. Same publisher, same year, different name — and Banshee's name
belongs to a different studio's disc entirely.

## The `.TM` block

The pointer is in the application-use area in the standard ISOCD shape:

```
offset 884:  46 53 00 00        'FS'
offset 888:  54 4D 00 14        'TM', 0x0014 = 20   (a constant, not the path table LBA)
offset 892:  00 00 08 00        2048               the block's length
offset 896:  00 00 00 15        21                 the block's LBA
```

Following it gives 2,048 bytes at LBA 21:

```
SHA-1  c5ffcef2a5e33d2df606185823cd95d1c174d65f   the whole sector
SHA-1  8d84115154d70360b3469acc99cdad3db0ed2c92   banner, 0x000..0x44C
SHA-1  690aae24a96b69659066e691d0b07db301260572   object file, 0x44C..0x7B8
```

All three match the other nine CD32-era discs in this series exactly. This is
the **tenth** byte-identical copy of Commodore's `CD32.TM` — the ASCII-art
copyright banner with 876 bytes of stale `exec` object code stuck to the end
of it, in a sector nothing on the disc reads. There is no `.TM` file in the
root.

Ten discs, ten studios, ten publishers, thirty-eight months, one file. The
useful reading is unchanged: this measures how widely one Commodore
distribution file circulated, and a *mismatch* is the interesting result.

## Two clocks, and how the session comes out of them

Sorted by timestamp, the 45 records fall into five groups:

| Records | Timestamp | What |
|---:|---|---|
| 2 | `1978-01-01 00:00:00` | the two **zero-length** files — every field zero |
| 41 | `1992-12-21 15:11:46` … `15:27:34` | the whole game, in write order |
| 2 | `1993-06-17 14:40:04` | `C/Assign` and `C/Execute`, the same second |
| 1 | `1993-11-11 09:50:58` | `C/SetPatch` |
| 1 | `1994-06-22 14:34:18` | `s/startup-sequence` |
| 3 dirs | `1994-07-08 13:13:22` … `13:14:37` | ISOCD's own records |
| PVD | `1994-07-08 13:16:10` | the master |

> **Correction (2026).** The two zero-length records are not "every field
> zero": their date bytes are `4E 01 01 00 00 00` = 1978-01-01 00:00:00,
> AmigaDOS DateStamp 0 — the same value as the root directory's record, which
> has no source object to take a date from. *Inference:* ISOCD wrote these two
> entries without reading a source file (names in the build list whose files
> were missing or empty). See [12-open-questions.md](12-open-questions.md) Q12.

A block of files nineteen months before the master is exactly the case the
platform checklist says to resolve **by asking the file**, before looking for
a control disc. The file answers.

At file offset 0x50 of `bans.exe`, between an `rts` and the next routine:

```
4E 75  38 2F 37 2D 39 34 20 31 32 3A 35 39 20 43 44 33 32 20 73 6C 75 74 70  14 4E 75
       "8/7-94 12:59 CD32 slutp"
```

**8 July 1994, 12:59.** The date is written day/month-year with a dash, which
is the Danish convention, and `slut` is Danish for *end* or *final*. The
executable was linked seventeen minutes before the master and its own
directory record claims 1992-12-21 15:12:22.

So the 1992 dates are **a wrong clock on the machine that copied the tree**,
not an inherited earlier build. There is no earlier release of Banshee for the
dates to have come from, and the file's internal stamp is nineteen months
after its own directory record. Two independent facts, one conclusion, no
control disc required.

### And the wrong clock still measures the session

The wrong clock's *absolute* readings are useless and its *relative* ones are
not, because a second correct clock brackets it:

```
12:59:00    bans.exe linked          from inside the file
   +0       first file copied        1992-12-21 15:11:46
   ...      41 files                 15 min 48 s of wrong-clock time
   +15:48   last file copied         1992-12-21 15:27:34
13:13:22    ISOCD writes /s          a correct clock
13:14:37    ISOCD writes /C
13:16:10    PVD written
```

The real window from the link stamp to the master is **17 minutes 10
seconds**; the wrong clock's span is **15 minutes 48 seconds**. The copy fits
inside the window with 82 seconds to spare. Every one of the 45 records is now
accounted for inside one seventeen-minute session on 8 July 1994, and the
master was cut on top of a build that was still moving — the program was
linked *during* the same session.

> **Correction (2026) — the "seventeen-minute session" does not hold.** The
> A1200 floppy release ([13](13-level-formats-and-floppy.md),
> [19](19-floppy-vs-cd.md)) shows that the 1992 stamps were written at
> **floppy speed, about 7–10 KB/s** (`level1c` 272,677 B in 28 s, `level2c`
> 281,827 B in 31 s, identical in the retail floppy session), on a second
> machine without a battery clock, in the retail floppies' per-disk write
> order. The mastering machine's clock was correct (`/s`, `/icons`, `/C`).
> 15 min 48 s of floppy-speed writing plus copying 2.88 MB into the mastering
> tree (another 5–6 min at that speed) does not fit the 17 min 10 s between the
> link banner and the PVD, and the retail build carries the same
> `8/7-94 12:59` banner and the same kind of 1992 stamps, so the stamps need no
> CD mastering session to explain them. The relative times remain a real write
> log; they are not part of the mastering session. Which came first — the
> CD-variant floppy writes or the banner — cannot be pinned down from this
> data. Details: [12-open-questions.md](12-open-questions.md) Q2 and Q6.

That is worth stating as a method: **a wrong clock is still a stopwatch.**
When a second, trustworthy clock brackets the wrong one, subtract and check
that the span fits. If it does, the wrong-clock ordering is a real write log
and can be read as one.

Read as one, it is:

```
+00:00  picture.exe                 the title-picture viewer, first
+00:36  bans.exe                    the game
+00:40  introseq.001 .. .007        the intro cut scene, 13 s for 7 frames
+00:55  P60.intro, P60.end          the two music modules
+01:02  endseq1.001 .. endseq2.005  the two endings, 16 s for 10 frames
+01:34  bossc, bossf
+02:08  core
+02:36  level1c, level1f
+03:16  soundfx, plyrmisc
+03:38  introscreen
+04:56  level2f, level2c
+05:57  level3c, banspic2
+07:15  level3f
+07:37  level4f, level4c
+08:12  banspic1, plyrmisc4
+15:48  soundfx4
```

The gaps track file size at roughly 150–200 KB/s for most of it, which is a
hard disk, and then stop tracking it entirely: `soundfx4` is 108,871 bytes and
sits **7 minutes 28 seconds** after `plyrmisc4`, where its size predicts about
nine. Something else happened in those seven minutes and the disc does not say
what.

> **Correction (2026).** The rate above is wrong by a factor of about 20:
> the gaps track file size at **about 7–10 KB/s**, which is floppy speed, not
> a hard disk. The `soundfx4` delay belongs to this session only — on retail
> disk 4 the same file follows `plyrmisc4` by 15 s. See
> [12-open-questions.md](12-open-questions.md) Q6.

### The 1992-12-21 coincidence, unresolved

Marvin's Marvellous Adventure, an unrelated title from an unrelated studio and
publisher, carries **1992-12-21** on its PVD (15:15:40) and on all nine of its
directory records (15:24:31–15:26:43). Banshee's 41 file records are
**1992-12-21 15:11:46–15:27:34**.

Two discs, the same wrong date, and time-of-day ranges that overlap inside the
same quarter of an hour — on Marvin from the *mastering* machine's clock and
on Banshee from the *source* machine's. A dead battery gives 1978 on an Amiga,
not 1992-12-21 with a running time of day.

The shape that would explain it: an Amiga with **no battery-backed clock**,
where AmigaDOS takes the date from the boot volume at every boot and the time
then runs forward from there. Every session on such a machine starts at the
same stored date and the time-of-day depends only on how long the machine has
been up. Two sessions of similar length, on machines booted from disks last
written on the same day, land in the same quarter hour.

That is a hypothesis and this repository has no way to test it. It is recorded
in [12-open-questions.md](12-open-questions.md) with the two measurements
beside it, because the next disc that carries 1992-12-21 decides it.

## The directories

Four directories, three of which have a directory record with a date:

```
/                    lba   22   2048 bytes
/s                   lba   23   2048    1994-07-08 13:13:22
/C                   lba   25   2048    1994-07-08 13:14:37
/icons               lba 1454   2048    1994-07-08 13:13:49    -- and it is empty
```

`/icons` holds no files. It was written before `/C` and after `/s`, it sits at
the very end of the file area at LBA 1454, and the volume's entire icon
population is zero: there is no `.info` file anywhere on this disc, no
`Banshee.info`, no `s/startup-sequence.info`. Whatever was meant to be in
`/icons` was not there when the master was cut, and the directory shipped
anyway. See [11-leftovers.md](11-leftovers.md).
