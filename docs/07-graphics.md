# Graphics

Banshee is a 2D scrolling shooter, so the expected answer to the platform
checklist's question — *where does the frame end up?* — is the boring one:
planar assets blitted into a planar display, no chunky stage anywhere. That is
what the disc does. It is worth recording as the **fifth** distinct answer the
series has collected, and it is worth recording *how* it was established,
because the three Blitter questions settle it in about ten minutes.

What is not boring is the display it does it into.

## Two AGA screens, both eight bitplanes

`bans.exe`'s chip DATA hunk (hunk 4, file offset 0x20678) holds two copper-list
templates. Both are dumped in
[notes/copper-lists.txt](../notes/copper-lists.txt).

### The game screen — 320×256 lores, 256 colours

> **Correction (2026).** This template (copper list A, `hunk4+0x32`) is the
> **intro and ending screen**, rewritten to hires for the picture files; it is
> not the game screen. The game screen is a fourth list, D at `hunk4+0x1466`:
> six planes (plus planes 7–8 for the cloud or light layer), `DDF $48–$B0`,
> `FMODE $F`, modulo 56, a 256 × 256 window on a 96-byte double-buffered row.
> The game does use AGA sprites (boss and mid-boss bodies, the final ship;
> [16-levels-and-bosses.md](16-levels-and-bosses.md)). See
> [12-open-questions.md](12-open-questions.md) Q3 and Q4.

```
DIWSTRT   $2c81      V 44,  H 129
DIWSTOP   $2cc1      V 300, H 449      -> 320 lores pixels x 256 lines
DDFSTRT   $0038
DDFSTOP   $00d0
BPLCON0   $0211      BPU = 8, lores, COLOR on, ECSENA set
BPLCON1   $0000
BPLCON2   $0224      PF1P = 4, PF2P = 4, KILLEHB set
BPLCON3   $0080      SPRES = 70 ns
BPLCON4   $0000      BPLAM = 0
BPL1MOD   $0070      112
BPL2MOD   $0070      112
FMODE     $0007      64-bit bitplane fetch, 32-bit sprite fetch
```

`BPLCON0` bit 4 is `BPU3`, so `$0211` is **eight** bitplanes, not zero.
`ECSENA` is set and `KILLEHB` is set in `BPLCON2`, so there is no ambiguity of
the kind the platform checklist warns about: this is not six planes with
Extra-Half-Brite quietly on, it is a genuine AGA 256-colour display.

The palette is written as **sixteen blocks of `BPLCON3` + 32 `COLORxx`
moves**:

```
0106 0000  bank 0, high nibbles   0180..01be   32 colours
0106 2000  bank 1                 ...
0106 4000  bank 2
...
0106 e000  bank 7
0106 0200  bank 0, LOCT = 1       low nibbles
0106 2200  bank 1, LOCT
...
0106 e200  bank 7, LOCT
```

8 banks × 32 colours × 2 passes = **256 colours at 8 bits per channel**. All
of the picture files carry their palettes in exactly that form (below).

### The picture screen — 640×256 hires, 256 colours

The second template, at file offset 0x21966, differs in five registers:

```
BPLCON0   $8211      HIRES set, BPU = 8, ECSENA
BPL1MOD   $0228      552
BPL2MOD   $0228      552
```

with the same `DIWSTRT`/`DIWSTOP` (320 colour clocks = **640 hires pixels**),
the same `DDFSTRT`/`DDFSTOP`, the same `FMODE $0007`, and the same sixteen
palette banks. Eight bitplanes in hires needs the 64-bit fetch that `FMODE 3`
provides, and this is the only disc in this series that asks for it.

## The picture files

`introscreen`, `banspic1` and `banspic2` all unpack to exactly **164,864
bytes** and have the same layout:

```
0x00000  1,024 bytes   256 colours, 2 words each: 0RGB high nibbles, 0rgb low
0x00400  163,840 bytes 640 x 256, 8 bitplanes, interleaved, 80 bytes per plane row
```

1,024 = 256 × 4 is the AGA `BANK`/`LOCT` pair format the copper list wants, so
the file is a straight copy of what the copper writes.

Render one with

```
python3 tools/planar.py _work/unp/introscreen out.png \
        --w 640 --h 256 --planes 8 --offset 0x400 --interleaved \
        --pal-rgb24 <palette>:0:256
```

`introscreen` is the game's title logo, `banspic1` and `banspic2` are
rendered aircraft. `banspic2` uses only 119,760 of its 164,864 bytes
(72.6 %) — a smaller picture in the same buffer.

The screen-clear blit confirms the layout independently:

```
BLTCON0/1  $01000000     minterm $00, USED only, no A/B/C   -- clear
BLTDMOD    $0230         560
BLTSIZE    $4028         height 256, width 40 words = 80 bytes
```

repeated with the destination stepping **+80 bytes** each time. 80 fetched +
560 modulo = 640 bytes per display row, and 640 × 256 = **163,840**, the exact
size of the bitmap half of a picture file. Eight of those blits, at 80-byte
intervals, clear all eight interleaved planes.

## The three Blitter questions

The platform checklist's ten-minute test for "fills planar directly" versus
"rasterises chunky and converts":

**1. Is there a `BLTCON1` write anywhere?** Yes — exactly one that is reached
from a `$dff000` base load, at file offset 0xA09A, and what it writes is:

```
0000a082  3c 00              move.w  d0,d6
0000a084  02 46 00 0f        andi.w  #$f,d6          ; the low 4 bits of the x position
0000a088  e8 5e              ror.w   #$4,d6          ; into bits 15..12
...
0000a09a  33 46 00 42        move.w  d6,$42(a1)      ; BLTCON1 = BSH only
0000a09e  8c 6f 00 0a        or.w    $a(a7),d6       ; | minterm passed by the caller
0000a0a2  33 46 00 40        move.w  d6,$40(a1)      ; BLTCON0
```

`BLTCON1` carries the B-shift and **nothing else** — no `FILL` bits, no
`DESC`, no `FCI`. So there is no area fill on this disc, and the shift is a
pixel-accurate horizontal position for a sprite, which is what a shooter
needs.

**2. What is `BLTSIZE`'s height, and what are the modulos?** Screen-sized
rectangles, not scanlines:

```
h=256 w=40 words  BLTDMOD 560     the full-screen clear
h=256 w=17 words  BLTAMOD 302  BLTDMOD 62
h=192 w=17 words  BLTDMOD 14
h=162 w=15 words  BLTAMOD 26   BLTDMOD 66
h= 96 w=17 words  BLTDMOD 62
h= 81 w=40 words
h=<object height> w=2 words     the object blit, once per plane
```

Nothing has a height equal to the plane count and nothing has modulos of the
form `bytes_per_row − width` applied per scanline. This is not Guardian's
one-blit-per-scanline polygon filler; it is whole-rectangle copies and whole
screen clears.

**3. Is the minterm `$CA` with `USEA` clear?** `$CA` is there — four
sites write `BLTCON0 = $0FCA` — but with **`USEA` set**, not clear:

```
$0FCA   minterm $CA   USEA=1 USEB=1 USEC=1 USED=1
$0BFA   minterm $FA   USEA=1 USEB=0 USEC=1 USED=1
$0B0A   minterm $0A   USEA=1 USEB=0 USEC=1 USED=1
$09F0   minterm $F0   USEA=1 USEB=0 USEC=0 USED=1
$0100   minterm $00   USED only
$0FFE   minterm $FE   all four channels
```

`$CA` with all four channels enabled is `D = AB + ¬AC` — the ordinary masked
bob blit, A the mask, B the sprite, C the background, D the destination.
Guardian's cookie-cut is the same minterm with `USEA` **clear** and `BLTADAT`
loaded once outside the loop, which is a different operation with the same
number in it. **The minterm alone does not identify the operation; read
`USEA`.**

Together the three answers are: no fill, rectangles not scanlines, ordinary
masked bobs. Banshee fills planar because its assets are planar and its
display is planar, and there is no point in the pipeline at which a frame
exists as chunky pixels.

## The object blit

The one routine that draws a moving object, at file offset 0xA062:

```
0000a062  lea     $dff000,a1
0000a06c  move.w  d7,d2           ; d7 = object height
0000a06e  lsl.w   #$6,d2
0000a070  addq.w  #$2,d2          ; BLTSIZE = (height << 6) | 2   -- 2 words wide
...
0000a07e  lea     $2(a3),a2       ; B = mask+2      (mask and data interleaved)
0000a09a  move.w  d6,$42(a1)      ; BLTCON1 = shift
0000a0a2  move.w  d6,$40(a1)      ; BLTCON0 = shift | minterm
0000a0a6  movem.l a0/a2-a4,$48(a1); BLTCPT, BLTBPT, BLTAPT, BLTDPT in one instruction
0000a0ac  move.w  d2,$58(a1)      ; BLTSIZE -- go
0000a0b4  move.w  #$4,d1          ; and then five more times:
0000a0b8  addq.w  #$2,a2
0000a0ba  lea     $6000(a4),a4    ;   next plane, 0x6000 = 24,576 bytes on
...
0000a0de  dbra    d1,...
```

`movem.l a0/a2-a4,$48(a1)` writes `BLTCPTH`, `BLTBPTH`, `BLTAPTH` and
`BLTDPTH` as four consecutive longwords in **one instruction** — the standard
Amiga trick, and it is why a scan that counts individual `move.l` writes to
the Blitter pointers under-reports.

Six passes (`d1 = 4` plus the one before the loop) at 0x6000 bytes apart
means **six bitplanes per object** into a non-interleaved buffer whose plane
stride is 24,576 bytes. The `bossc`/`levelNc` files are the chip-RAM halves
that feed it.

## What is not here

* **No Akiko.** Zero `lea $B80000,aN`, zero `movea.l #$B80000,aN`, zero
  `$00B80038`, zero `$00B8003C`, zero `$C0DE0000`, over both code hunks and
  both data hunks of `bans.exe` and over `picture.exe`. The five raw
  `00 B8 00 38` byte hits in the whole volume are all inside unpacked level
  data, where no pointer load could reach them.
* **No sprites in the game screen.** The template points all eight sprite
  pointers at a zeroed longword.
* **No dual playfield.** `BPLCON0` bit 10 is clear in both templates.
* **No `BPLCON4` colour tricks.** `BPLAM` is zero in both, so unlike Guardian
  there is no palette-bank offsetting.
