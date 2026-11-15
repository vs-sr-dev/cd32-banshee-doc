# `picture.exe` — a self-decrunching HAM8 slide

274,764 bytes, and **nothing on the disc runs it**. The boot script names only
`bans.exe`; `bans.exe` contains no `picture`, no `.exe` and no `LoadSeg` path
of any kind, and its 37-entry file table
([05-loader.md](05-loader.md)) does not list it. The string `picture` occurs
nowhere in the volume outside this file's own directory record.

It is a standalone program that puts one picture on the screen for about
fifteen seconds and exits, it is 9.5 % of the data track, and it is
unreachable. It is also the most interesting single file on the disc.

## Address convention for this file

`picture.exe` is a hunk executable with **zero relocations**, so the
convention in [00-overview.md](00-overview.md) does not apply and a different
one is needed. Addresses below are **file offsets** except inside the two
listings, which are offsets **from the start of the hunk body**, stated at the
top of each listing. The hunk bodies are at:

| Hunk | Kind | Memory | Declared | Stored | Body at |
|---:|---|---|---:|---:|---|
| 0 | CODE | any | 484 | 484 | 0x00002c |
| 1 | CODE | any | 544 | 392 | 0x00021c |
| 2 | DATA | **chip** | 916 | 856 | 0x0003b0 |
| 3 | DATA | **chip** | 327,752 | 272,948 | 0x000714 |

The stored bodies of hunks 1–3 are **shorter than what the header table asks
`LoadSeg` to allocate**, which is the signature of the whole arrangement.

## The stub

Hunk 0 is 484 bytes of position-independent code with no relocations at all,
and it does two jobs. The annotated listing is in
[notes/picture-depacker.txt](../notes/picture-depacker.txt); offsets there are
from the start of hunk 0.

**Job one: walk the segment list and decrunch every hunk in place.**

```
000000  48 7a 01 de     pea.l   $20c(pc)          ; return address after the stub
000004  48 e7 ff fe     movem.l d0-d7/a0-a6,-(a7)
000008  48 7a ff f2     pea.l   -4(pc)            ; the current segment's next-BPTR
00000c  2a 57           movea.l (a7),a5           ; -- loop over segments --
00000e  4a 95           tst.l   (a5)
000010  67 00 01 b6     beq.w   ...               ; end of list -> finish
000014  2a 55           movea.l (a5),a5
000016  db cd           adda.l  a5,a5             ; BPTR << 2
000018  db cd           adda.l  a5,a5
00001a  2e 8d           move.l  a5,(a7)
00001c  58 4d           addq.w  #$4,a5            ; a5 = this hunk's data
00001e  41 ed 00 08     lea.l   $8(a5),a0         ; skip the 8-byte prefix
000022  0c 98 52 4e 43 02  cmpi.l #'RNC'<<8|2,(a0)+ ; not crunched? next segment
000028  66 e2           bne.b   ...
```

Every crunched hunk body therefore looks like

```
+0   the original hunk's length in bytes            (4 bytes)
+4   the original hunk table entry: longwords + memory flags
+8   'RNC' 02
+12  unpacked length
+16  packed length
+20  CRC-16 unpacked, CRC-16 packed
+24  leeway, chunk count
+26  the packed stream
```

and the eight-byte prefix is not decoration: `adda.l (a4),a4` at offset 0x74
uses it to find where, inside the *decrunched* image, the original hunk's data
ends and its relocation tables begin.

**Job two: relocate.** After decrunching, the stub walks the tail of each
decrunched hunk looking for `HUNK_RELOC32`:

```
000192  0c 94 00 00 03 ec  cmpi.l #$3ec,(a4)      ; a HUNK_RELOC32 table?
000198  66 00 fe 72        bne.w  ...             ; no -> next segment
00019c  42 9c              clr.l  (a4)+           ; and erase it as we go
00019e  22 14              move.l (a4),d1         ; count
0001a0  67 f0              beq.b  ...             ; 0 -> table done
0001a2  42 9c              clr.l  (a4)+
0001a4  20 14              move.l (a4),d0         ; target hunk number
0001a6  42 9c              clr.l  (a4)+
0001a8  41 fa fe 52        lea.l  -4(pc),a0       ; head of the segment list
0001ac  20 50              movea.l (a0),a0        ; -- follow d0+1 links --
0001ae  d1 c8              adda.l  a0,a0
0001b0  d1 c8              adda.l  a0,a0
0001b2  51 c8 ff f8        dbra    d0,...
0001b6  24 08              move.l  a0,d2
0001b8  58 82              addq.l  #$4,d2         ; d2 = target segment's data
0001ba  20 14              move.l  (a4),d0        ; -- for each offset --
0001bc  42 9c              clr.l   (a4)+
0001be  d5 b5 08 00        add.l   d2,(a5,d0.l)   ; patch
0001c2  53 81              subq.l  #$1,d1
0001c4  66 f4              bne.b   ...
```

which is why the file's own `HUNK_RELOC32` count is zero: **the relocation
tables were moved inside the compressed data and the program applies them
itself.** This is the second sighting in this series of a hunk file that
decrunches *and* relocates itself — HeroQuest II does it in 584 bytes — and
the two are unrelated implementations of the same idea.

One detail worth recording because it will bite anyone reading the tables by
hand: the stub follows `d0 + 1` segment links from the head, so a table whose
target hunk number is `N` relocates against **segment N+1**. The packer
inserted itself as hunk 0 and left the original program's hunk numbering
alone. Read literally, `lea $27c.l,a0` in hunk 1 with target "hunk 2" points
past the end of hunk 2's 916 bytes at offset 636 — read correctly, against
hunk 3, it lands 0x40 bytes into the 327,752-byte picture, which is where the
picture starts.

## RNC ProPack method 2

`tools/rnc2.py` transcribes the decompressor from the stub's own bytes. The
bit stream is MSB-first in a byte register with a sentinel below it
(`add.b d7,d7`; on a zero result `move.b (a3)+,d7` then `addx.b d7,d7`), and
the **first two bits of every stream are read and thrown away**.

The grammar, as the code implements it:

```
0            -> emit one literal byte, then test again
1            -> a match follows:
   0  bb     -> length = 4 + b ; then one more bit:
                  0  -> offset
                  1  -> length = 2*(length-1) + b   (6..9)
                        9 -> LONG LITERAL RUN: 4 bits n, then 4*(n+3) bytes
   1 0       -> length 2, one-byte offset, no high bits
   1 1  0    -> length 3, offset
   1 1  1    -> byte b; b == 0 -> end of stream / next chunk
                          else -> length = b + 8, offset
offset:
   0         -> one byte, 0..255
   1 ...     -> 1 to 4 more bits into the high byte, then one byte
copy `length` bytes from (out - offset - 1), overlapping
```

All three streams decode and all three CRC-16/ARCs check:

```
hunk 1  ulen     536  plen     364  leeway 4  chunks  1   CRC ok
hunk 2  ulen     904  plen     829  leeway 7  chunks  1   CRC ok
hunk 3  ulen 327,744  plen 272,922  leeway 5  chunks 27   CRC ok
```

Note that hunk 1's prefix says its original length was 452 bytes while it
unpacks to 536: the extra 84 bytes are the relocation table the packer moved
into the stream. Hunks 2 and 3 have no relocations and their prefixes equal
their unpacked lengths exactly.

**Method 2 appears nowhere else on this disc.** All 37 data files are method
1. Two crunchers in one build chain, and only the one that can wrap an
executable was used on the one executable worth wrapping.

## What the picture is

Hunk 1, decrunched, is 452 bytes of display code. Hunk 2 is a copper list plus
a palette; hunk 3 is 327,744 bytes of bitmap.

The code reads out cleanly:

```
000000  lea     $40.l,a0            ; hunk 3 + 0x40  -- the bitmap
000006  ...     longword-align it
000010  move.l  #$4fff,d7           ; 0x5000 * 16 = 327,680 bytes
00001e  move.l (a0)+,(a1)+  x4 / dbra
00002a  lea     $27c.l,a0           ; hunk 2 + 0x27c -- eight bitplane pointers
000030  move.w  #$7,d7
000034  ... write a2 into the copper, a2 += $50 (80) each time
00004a  lea     $218.l,a0           ; hunk 2 + 0x218 -- eight sprite pointers
000050  lea     $10.l,a2            ; all eight -> hunk 3 + 0x10, sixteen zero bytes
00006c  lea     $2c8.l,a0           ; hunk 2 + 0x2c8 -- 64 x 3 bytes of RGB
000072  lea     $10e.l,a2           ; the LOCT copper entries
000078  lea     $6.l,a1             ; the high-nibble copper entries
000082  ... 2 x 32 iterations, splitting each 24-bit RGB triplet
        ... into a $0RGB word and a $0rgb word
```

so hunk 2 is `[copper list, 712 bytes][64 colours x 3 bytes = 192 bytes]` =
904 bytes, and the palette in the copper list as it sits in the file is a
**stale copy** that the code overwrites at startup — the same 16 words also
appear at hunk 3 + 0x20, in front of the bitmap, where nothing reads them.

> **Correction (2026).** Not stale: the colour words in the CD copper list
> are exactly what the start-up code writes. Compared with the floppy
> release's uncrunched `picture.exe` (same code except 8 bytes, identical
> bitmap hunk), the CD copy has the frame counter at code `+0x1bc` = 727
> against the floppy's 250, and the bitmap pointer (code `+0x1be` =
> `$00132040`), the eight sprite and eight bitplane pointers and the colour
> words already filled in — the values the start-up code and the first
> odd-field update compute with hunk 3 at chip `$132000`. The floppy copy has
> all of them zero. The **CD build is a separate build written out from memory
> after it had run** (assemble-run-write in an in-memory assembler), then
> RNC-crunched. See [12-open-questions.md](12-open-questions.md) Q8.

The copper list's display registers:

```
DIWSTRT  $2c81       V 44,  H 129
DIWSTOP  $2cc0       V 300, H 448     -> 320 colour clocks x 256 lines
DDFSTRT  $0038   DDFSTOP $00d0
BPLCON0  $8a14       HIRES, BPU = 8, HAM, LACE, COLOR
BPLCON1  $0011   BPLCON2 $0024   BPLCON3 $0000
BPL1MOD  $04a8       1192
BPL2MOD  $04a8       1192
FMODE    $0003       64-bit bitplane fetch
```

`BPLCON0 = $8A14` sets `HIRES` (bit 15), `HOMOD` (bit 11), `BPU3` (bit 4) and
`LACE` (bit 2), so it is **HAM8, hires, interlaced, eight bitplanes** — and
the 64 palette entries are exactly what HAM8 wants, since in HAM8 the six data
bits index a 64-colour base palette and the two control bits hold, or modify
one channel.

The interlace is done by hand. The main loop waits on `VHPOSR` for `$70` then
`$80` and alternates two subroutines that rewrite the eight bitplane pointers,
one of them adding `$280` = 640 bytes — one interleaved row — to every
pointer:

```
000184  movea.l $1be.l,a2
00018a  adda.w  #$280,a2            ; odd field: start one row down
00018e  bra.w   ...
000192  movea.l $1be.l,a2           ; even field: start at the top
000198  lea.l   $27c.l,a0
00019e  move.w  #$7,d7
0001a2  ... eight pointers, a2 += $50 each
```

Eight planes × 80 bytes = 640 bytes per row; 327,680 bytes ÷ 640 = **512
rows**; the display window is 256 lines and `LACE` is on. So the picture is

> **640 × 512, eight bitplanes, HAM8, interlaced, with a 64-entry 24-bit
> palette** — 327,680 bytes of bitmap, the largest single image on the disc
> and, in this series, in a display mode nothing else uses.

The plane order is rotated by two: the copper entries written in address order
are `BPL3PT, BPL4PT, BPL5PT, BPL6PT, BPL7PT, BPL8PT, BPL1PT, BPL2PT`, so
memory plane *i* carries display bit *(i + 2) mod 8*. In HAM8 that puts the
six **data** planes first in memory and the two **control** planes last, which
is a sensible thing for a converter to do and a fatal thing for a renderer to
guess wrong about.

Render it with

```
python3 tools/rnc2.py exe _work/ext/picture.exe _work/picture
python3 tools/planar.py _work/picture/hunk3.bin out.png \
        --w 640 --h 512 --planes 8 --offset 0x40 --interleaved --ham8 \
        --order 2,3,4,5,6,7,0,1 \
        --pal-rgb24 _work/picture/hunk2.bin:0x2c8:64
```

The picture is a rendered scene: the Banshee aircraft banking through a
cloudscape, propeller blurred, with a second aircraft above it, missiles in
flight and two large explosions. It is at a resolution and colour depth
nothing else on the disc uses, and no player ever saw it.

## And the rest of the program

```
0000ce  cmpi.b  #$80,$dff006      ; wait for a scanline
0000d8  move.l  #$0,$dff080       ; COP1LC = 0 -- temporarily
0000e2  move.w  $dff002,d4        ; save DMACONR
0000ec  ori.w   #$8000,d4
0000f0  move.w  $dff004,d0        ; VPOSR
0000f6  andi.w  #$7fff,d0         ; clear LOF
0000fa  move.w  d0,$dff02a        ; VPOSW
000100  move.w  #$8300,$dff096    ; DMACON = SET | BPLEN | DMAEN
000108  move.w  #$4000,$dff09a    ; INTENA = CLR INTEN -- interrupts off
...
000158  subq.w  #$1,$1bc.l        ; a frame counter, initial value $02d7 = 727
00015e  bne.w   ...
000140  btst.b  #$6,$bfe001       ; fire on port 1
00014c  btst.b  #$7,$bfe001       ; fire on port 0
000162  move.w  d4,$dff096        ; restore DMACON
000168  move.w  #$c000,$dff09a    ; interrupts back on
000170  movea.l $4.l,a6           ; ExecBase
000176  movea.l $9c(a6),a1        ;   ->  GfxBase
00017a  move.l  $26(a1),$dff080   ;   ->  copinit, put the system copper back
000182  rts
```

727 fields at 50 Hz is **14.5 seconds**, or until either fire button is
pressed — and it tests **both** joystick ports, which is what a CD32 title has
to do since either pad can be player one. The program leaves the machine
exactly as it found it: `DMACON` restored from the value it saved, interrupts
re-enabled, and `graphics.library`'s `copinit` written back to `COP1LC`. That
is a well-behaved program, and it is worth contrasting with the game, which
takes the machine and keeps it.

> **Update (2026).** What ran it: on the floppy release the hard-disk
> installation's start script (`scrpt2`: `picture.exe`, then `bans.exe`).
> On the CD `scrpt2` is empty and nothing runs it. The floppy build waits 250
> fields (5 s); the 727 here is a CD-era change.
> [12-open-questions.md](12-open-questions.md) Q8.
