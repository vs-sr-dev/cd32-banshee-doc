# Audio

Three sources: two Red Book tracks played out of the drive, two music modules
played through Paula, and two banks of sound effects.

## Red Book, played while the game runs

> **Correction (2026).** Two errors in this chapter. (1) `io_Command #44` is
> **`CD_ATTENUATE`**, not `CD_ADDCHANGEINT` (which is 20): `io_Offset =
> 0x7fff` (volume), `io_Length = 0`, used once to set full volume. (2) **No
> music plays during gameplay**, on CD or floppy: the game sends `AbortIO` to
> the CD track at game start and no `CD_PLAYTRACK` for the whole level; the
> Red Book tracks are menu (track 3) and high-score (track 2) music, and all
> four Paula channels belong to effects in play. The section title above is
> therefore wrong. Also, the offsets in the two listings below are `hunk0+`
> offsets (file = +0x34); the five-line `io_Command` table uses file offsets.
> Evidence: [18-runtime.md](18-runtime.md) §5.

Track 2 is 2:05.33 and track 3 is 3:00.37 — **five minutes six seconds** of
44.1 kHz stereo on a disc that could hold seventy-four.

`bans.exe` opens `cd.device` and drives it directly. The `io_Command`
immediates in the code are:

```
file 0x00019e   io_Command #9    IND_ADDHANDLER    input.device
file 0x000274   io_Command #10   IND_REMHANDLER    input.device
file 0x00059a   io_Command #44   CD_ATTENUATE      cd.device   (corrected 2026)
file 0x0005dc   io_Command #37   CD_PLAYTRACK      cd.device
file 0x0006fc   io_Command #32   CD_INFO           cd.device
```

The play request, at file offset 0x0058E, is unambiguous:

```
00058e  50 f9 00 00 07 39     st.b    $739.l                ; "a track is playing"
000594  42 39 00 00 06 2a     clr.b   $62a.l
00059a  48 e7 c0 c2           movem.l d0-d1/a0-a1/a6,-(a7)
00059e  23 c0 00 00 05 8a     move.l  d0,$58a.l             ; remember the track
0005a4  43 fa 07 9e           lea.l   $d78(pc),a1           ; the IORequest
0005a8  33 7c 00 25 00 1c     move.w  #$25,$1c(a1)          ; io_Command = CD_PLAYTRACK
0005ae  42 a9 00 28           clr.l   $28(a1)               ; io_Data = 0
0005b2  23 40 00 2c           move.l  d0,$2c(a1)            ; io_Offset = first track
0005b6  72 01                 moveq   #$1,d1
0005b8  23 41 00 24           move.l  d1,$24(a1)            ; io_Length = 1 track
0005c2  4e ae fe 32           jsr     -$1ce(a6)             ; SendIO
```

`io_Offset` is the track number and `io_Length` is `1`, so it plays exactly
one track and does not chain.

### And there is a watchdog around it

At file offset 0x006B2, on a counter that fires every `$96` = 150 frames —
**three seconds at 50 Hz** — the program asks the drive what it is doing and
restarts the track if it has stopped:

```
0006b2  10 3a ff 76           move.b  $65e(pc),d0        ; enabled?
0006b8  41 fa ff 71           lea.l   $65f(pc),a0
0006bc  53 10                 subq.b  #$1,(a0)           ; count down
0006be  66 40                 bne.b   ...
0006c0  10 bc 00 96           move.b  #$96,(a0)          ; reload 150
0006c4  43 fa 04 fe           lea.l   $bf8(pc),a1
0006c8  33 7c 00 20 00 1c     move.w  #$20,$1c(a1)       ; io_Command = CD_INFO
0006ce  23 7c 00 00 07 02 00 28  move.l #$702,$28(a1)    ; io_Data  = a buffer
0006d6  23 7c 00 00 00 22 00 24  move.l #$22,$24(a1)     ; io_Length = 34 bytes
0006e4  4e ae fe 38           jsr     -$1c8(a6)          ; DoIO
0006ea  30 3a 00 2e           move.w  $74e(pc),d0        ; a status word from the reply
0006ee  02 40 00 63           andi.w  #$63,d0
0006f2  0c 40 00 03           cmpi.w  #$3,d0             ; disc there, nothing playing?
0006f6  66 08                 bne.b   ...
0006f8  20 3a fe 90           move.l  $5be(pc),d0        ; the remembered track
0006fc  61 00 fe d0           bsr.w   ...                ;   -> play it again
```

`io_Length` of 34 is the size of the `CDInfo` structure. So the game polls the
drive twice a second... no: **once every three seconds**, for the whole
session, and re-issues `CD_PLAYTRACK` whenever the drive reports the disc
present and idle. That is how a track loops without an interrupt, and it is
also a defence against the CD32's drive stopping when a `CD_READ` interleaves
with playback.

### It never reads the table of contents

`CD_TOCMSF` (34) and `CD_TOCLSN` (35) do not appear. The game names tracks by
number and takes what it gets. So the platform checklist's question about
filtering the TOC by `CONTROL` bits — which on HeroQuest II is the difference
between two reachable audio tracks and twelve — does not arise here: **the
disc has exactly two audio tracks and the program addresses them as constants.**

Worth recording as the negative case: a title can play Red Book perfectly well
with no TOC parsing at all, and on a disc it shipped with itself there is no
reason to do more.

## The Player 6.0A

`P60.intro` (16,105 bytes on disc, 24,730 unpacked) and `P60.end` (23,003 /
33,512) are music modules in **The Player 6.0A** format, by Jarno Paananen.
The disc credits him:

```
file 0x01c833   Jarno Paananen
```

on the credits screen, under the music credit — which makes Banshee one of the
few commercial titles to name the replayer author on screen.

The replayer is linked into `bans.exe` and carries its own strings:

```
file 0x005efc   audio.device
file 0x005f09   ciax.resource
file 0x005f18   P60TimerInterrupt
file 0x005348   P60A            -- inside a cmpi.l, the format check
```

`ciax.resource` and a named timer interrupt mean the replayer takes a CIA
timer rather than riding the vertical blank, which is what The Player does to
get non-50 Hz playback speeds.

Neither module carries a `M.K.` signature or a `P60A` tag of its own —
The Player's converter strips those — so a magic scan does not find them and
the identification comes from the replayer, not from the files.

## Sound effects

`soundfx` (129,459 / 153,946) and `soundfx4` (108,871 / 128,584) are sample
banks with a fixed 16-byte record header per sample:

```
00000000: 0001 6394  1f56 ffff  0000 0000  005a 0000
00000010: 0001 a240  0d28 0000  0000 0000  5c00 0001
00000020: 0001 bc90  1135 0000  0000 0000  0064 0000
```

— a 32-bit offset, a 16-bit length, a 16-bit loop field (`ffff` for
non-looping), and a period. The two banks are otherwise unrelated:
`soundfx4` is the level-4 bank and the loader gives it `soundfx`'s buffer,
25,362 bytes larger than it needs ([05-loader.md](05-loader.md)).

Paula is programmed by absolute address, not through a base register:

```
$DFF0A0 AUD0LCH x1   $DFF0A8 AUD0VOL x2
$DFF0B0 AUD1LCH x1   $DFF0B8 AUD1VOL x2
$DFF0C0 AUD2LCH x1   $DFF0C8 AUD2VOL x2
$DFF0D0 AUD3LCH x1   $DFF0D8 AUD3VOL x2
```

Four channels, and the volume registers are also reached as `d16(a6)` after a
`lea $dff000,a6` — which is why both register scans have to be run
([05-loader.md](05-loader.md)).

## What is not here

No digitised speech, no CDXL, no `CD_READXL`, and no streaming of any kind.
The 5.06 MB of game data is loaded from the file system and the 5 minutes of
music comes off the disc as Red Book. For a 1994 CD32 title that is a
conservative use of the medium, and it is the same choice Dragonstone made a
year later with two minutes of audio instead of five.
