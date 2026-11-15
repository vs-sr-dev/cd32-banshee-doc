# Leftovers

Eleven CD32 titles into this series the question has stayed inverted: *is
there a disc that was cleaned up, and what does it look like?* Banshee is not
it. This is the seven things it left behind, in order of how much they say.

## 1. A debug hook, live, in the shipped boot script

```
c:assign >NIL: DebugDisk: exists
if not warn
   c:assign t: ram:
   c:execute DebugDisk:debugscript
endif
```

Lines 2–6 of `/s/startup-sequence`. If a volume called `DebugDisk:` is
present, the retail boot script assigns `T:` to the RAM disk and **runs a
script off it** before starting the game. On a CD32 there is no `DebugDisk:`,
so the branch never fires and nobody noticed.

The strings `DebugDisk` and `debugscript` occur exactly once each in the whole
volume, in this file. `bans.exe` contains neither. Whatever the hook did, it
lived entirely at the AmigaDOS level — which is exactly why it survived: it is
not in the program, so nothing about building the program would have removed
it.

Two discs in this series ship the *previous* boot script as a `.bak`. This one
ships the current boot script with the developer's own way in still wired up.

## 2. A 274 KB program nothing runs, holding a picture nobody saw

`picture.exe` is 274,764 bytes — **9.5 % of the data track** — and is
unreachable. The boot script runs `bans.exe` and nothing else; `bans.exe`
contains no `picture`, no `.exe`, no path to it, and its 37-entry file table
does not list it; the string `picture` appears nowhere in the volume outside
the file's own directory record.

Inside it, behind three RNC ProPack method 2 streams, is a **640 × 512
interlaced HAM8 image with a 64-entry 24-bit palette** — 327,680 bytes of
bitmap, the largest single image on the disc, in a display mode no other disc
in this series uses. It is a rendered scene of the Banshee aircraft banking
through a cloudscape with explosions behind it, and the program displays it
for 727 fields (14.5 seconds) or until either fire button is pressed, then
tidily restores `DMACON`, the interrupt enables and `graphics.library`'s
copper list and exits.

It is also the **first** file written in the copy session
([02-filesystem.md](02-filesystem.md)) — 36 seconds before the game
executable. Whatever it was for, it was at the front of the directory when
somebody dragged the tree across.

[08-picture-exe.md](08-picture-exe.md) takes it apart.

## 3. Two files with a name, a directory record, and no content

```
LBA  size  timestamp             path
  0     0  1978-01-01 00:00:00   /scrpt2
  0     0  1978-01-01 00:00:00   /C/Installer
```

Both have extent **0** and length **0** in their directory records, and every
field of their timestamps is zero — not the AmigaDOS epoch with an uptime in
it, but genuinely nothing, which is what ISOCD writes when the source file has
no date and no content.

> **Correction (2026).** The date fields are not zero: they are
> `4E 01 01 00 00 00` = **1978-01-01 00:00:00**, AmigaDOS DateStamp 0, the
> same value as the root directory record (which has no source object).
> *Inference:* ISOCD wrote both entries without reading a source file. On the
> floppy release `scrpt2` is 39 bytes and `Installer` 63,436 bytes; see
> [12-open-questions.md](12-open-questions.md) Q8 and Q12.

`C/Installer` is Commodore's Installer utility, the thing an Amiga hard-disk
install script runs. `scrpt2` is a script — the name is `script 2` with the
vowel dropped to fit an eight-character habit. Together they are **the
hard-disk installer chain of the A1200 floppy release**, present as two names
and zero bytes.

Legends and Gloom both ship the floppy release's installer *working*, on a CD
that cannot use it. Banshee ships the two files empty. Which is arguably worse
and is certainly funnier: somebody did remove the installer, by truncating it,
and left the directory entries.

## 4. An empty directory

```
/icons   LBA 1454   2,048 bytes   1994-07-08 13:13:49
```

`/icons` holds no files. It sits at the very end of the file area, one sector
before the 232-sector trailing run, and ISOCD wrote its record 27 seconds
before `/C`'s.

The disc carries **no `.info` file at all** — no `Banshee.info`, no
`s/startup-sequence.info`, no icon of any kind. There is therefore no desktop
entry point and no `IconX` in `C:`, and whatever `/icons` was for was not
there when the master was cut.

This is also the negative result for a check that has paid twice elsewhere:
Guardian and Gloom ship the identical 396-byte `s/startup-sequence.info`, a
Blitz Basic 2 project icon that on Guardian is the only evidence of that tool
in the whole build chain. Hashing the `.info` files on Banshee finds nothing
because there are none.

> **Update (2026).** On the floppy release `/icons` holds `banshee.info`, the
> installed game's IconX project icon. See
> [12-open-questions.md](12-open-questions.md) Q9.

## 5. A thirty-eighth filename that is not a file

At file offset 0x2BCA in `bans.exe`, immediately after the 37th record of the
loader's file table and with **no record header** — no buffer size, no disk
number, no flag byte:

```
0x002bca  62 61 6e 73 31 3a 66 6c 65 76 00     'bans1:flev'
```

Two things are wrong with it. The volume name is `bans1:`, and the boot script
assigns `banshee1:` through `banshee4:` — `bans1:` is assigned by nothing and
would fail. And `flev` is not a file on the disc, is not a name any of the 37
records uses, and is not referenced anywhere else in the volume.

`flev` reads as *f level*, in the disc's own `c` / `f` convention where
`level1c` is a level's chip-RAM half and `level1f` is the rest. So it is a
level file, under an older and shorter volume-naming scheme, that the table
outgrew — the string survived a rename of the four floppy volumes and the
record that owned it did not.

> **Update (2026).** `bans1:` is the volume label of floppy disk 1, used
> directly, so the path was valid on floppy. `flev` is unreferenced in both the
> CD and the floppy build and is on no floppy. See
> [12-open-questions.md](12-open-questions.md) Q5 and
> [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §2.

Dragonstone's equivalent leftover is a row of seven `0xFFFF` entries where
level 4's files would have been. Both discs kept the shape of something that
went; neither kept the thing.

## 6. A halt loop with a flashing border

At file offset 0x53C, between two ordinary routines:

```
00053c  4e 71                    nop
00053e  33 fc 0f 0f 00 df f1 80  move.w  #$0f0f,$dff180     ; COLOR00 = magenta
000546  33 fc 00 00 00 df f1 80  move.w  #$0000,$dff180     ; COLOR00 = black
00054e  60 ec                    bra.b   $53c
000550  4a fc                    illegal
```

Flash the screen for ever, and an `ILLEGAL` instruction behind it in case
anything falls through. This is the Amiga assembler programmer's panic handler
— the one you wire into an exception vector while you are debugging so that a
crash is visible from across the room rather than silent — and it shipped.

Note the pair of writes are to `$DFF180` written **absolutely**, not through a
base register, which is what you type when you are adding four lines to a file
in a hurry.

> **Correction (2026).** Not a panic handler and not dead code. The offset
> 0x53C is a `hunk0+` offset (file 0x570). A `bne` at `hunk0+0x51E` jumps here
> when **`OpenDevice("input.device")` fails**: it is the program's
> fatal-start-up-error path. See
> [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §3.

## 7. A message about killing animals

At file offset 0x1F1C4, eight lines of nineteen columns, each terminated by
`0xFF` and right-padded with spaces to the field width:

Paraphrased (2026; the full text is not reproduced here): the player is told
they need a mental examination for wanting to kill animals and civilians.

It is not in the four-language table. The whole of the rest of the game's text
is `english FF german FF french FF danish FF … FE`; this block has one variant
per line and no `0xFE` group terminator anywhere in it, so it is English-only
and structurally separate from everything around it. The 160 bytes of it end
sixteen bytes before the hall-of-fame name-entry alphabet at 0x1F274.

The message is itself the evidence that the game has animals and civilians in
it that can be shot, and the obvious reading is that this is what it says to a
player who shoots them. The repository cannot run the game to confirm that,
and nothing in the text region around the block identifies its trigger. What is measured is the block itself:
eight lines, nineteen columns, `0xFF`-terminated, space-padded, one language,
outside the table that holds every other string in the game.

> **Answer (2026).** It is the confirmation of a cheat: the high-score name
> `Mary Whitehouse` or a keyboard sequence copies this block into the
> hall-of-fame name table and enables a flag without which civilians and
> animals cannot be hit at all. See [12-open-questions.md](12-open-questions.md)
> Q7 and [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §1b.

It is one of the two things on this disc written in the first person by
somebody with an opinion. The other is a joke about the hero's name, in
Danish, that the other three languages do not get.

## And the small ones

* **The build banner.** `8/7-94 12:59 CD32 slutp` at file offset 0x50 of
  `bans.exe`, between an `rts` and the next routine, with the length byte
  `0x14` after it. Not a `$VER:` string, so a `$VER:` sweep never finds it —
  and it is the single most useful string on the disc, because it dates the
  master to the minute and proves the 1992 file timestamps are a wrong clock
  ([02-filesystem.md](02-filesystem.md)).
* **A stale palette, twice.** `picture.exe`'s copper list ships with sixteen
  colour values that the startup code overwrites before the display is
  enabled, and the same sixteen words appear again at offset 0x20 of the
  327,744-byte picture hunk, in front of the bitmap, where nothing reads them
  at all. *(Corrected 2026: the copper colours are not stale but saved after
  a run; see [08-picture-exe.md](08-picture-exe.md).)*
* **The names in the high-score table** are the team:
  `Hannibal`, `Jade`, `Martin`, `Mac and Roberto`, `Adrian`, `8th Day`,
  `Dan and Toby`, `Jezza` — the programmer, the artist, the musician, Core's
  designer, and `Jezza` for Jeremy Heath-Smith.
* **`And Corner Kitchen`**, the last line of the thank-you list, which is
  presumably a restaurant.
* **The default high-score table** at file offset 0x1C51E is eight scores in
  right-aligned eight-column fields — `20000`, `19999`, `15000`, `10000`,
  `7500`, `5000`, `2500`, **`23`** — paired with the eight names above. The
  programmer gave himself 20,000, the artist 19,999, and `Jezza` twenty-three.
* **`soundfx4` was written 7 minutes 28 seconds after everything else**, in a
  copy session whose other 40 gaps all track file size at 150–200 KB/s. It is
  108,871 bytes; its size predicts nine seconds. Something happened in those
  seven minutes and the disc does not say what. *(Corrected 2026: the gaps
  run at about 7–10 KB/s, floppy speed; see
  [12-open-questions.md](12-open-questions.md) Q6.)*
* **`CREDITS` is a working credits display** (added 2026). The `CREDITS` +
  digit bob each level header points at looks unused in a single-player run,
  but it blinks for 300 ticks whenever one of the four shared credits is spent
  ([18-runtime.md](18-runtime.md) §3,
  [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §6).
