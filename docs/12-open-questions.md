# Open questions

Everything this repository could not settle, with the measurement beside it.
A question with a number attached is worth more than an answer without one.

**2026 update.** Answers found later — mostly from the A1200 floppy release
and from running `bans.exe` in an emulator — are added under each question as
*Answer (2026)* or *Partial answer (2026)* blocks, with evidence and
confidence. The original question text is kept as written. Addresses in the
answers follow [00-overview.md](00-overview.md) (`hunkN+0x…`, file offsets).
New open questions raised by chapters 14–20 are listed at the end of each of
those chapters.

## 1. What produces a 232-sector trailing run instead of 32?

```
disc         preparer      declared volume   trailing zero run
Liberation   D J Pocock            82,502    232
Banshee      D J Pocock             1,687    232
the other 8  various          772..255,552    32
```

Eight ISOCD discs leave 32, across a 331 : 1 span of volume sizes and two tool
versions. Two leave 232, and they are the two discs whose preparer field names
the same person — across two unrelated studios and two unrelated publishers,
three months apart. The size explanation is dead (1,687 against 82,502).

Two observations are not a correlation. **The test is one field comparison on
the next disc**: if a third `D J Pocock` disc turns up, check the trailing run
before anything else; if a 232 turns up under a different name, this is
coincidence. What it would mean if it holds is that an ISOCD option or a
padding setting travelled with an operator rather than with a tool version.

> **Partial answer (2026) — mechanism located, operator action open.**
> The trailing run is ISOCD's end-of-volume `<Empty Space>` entry, an item in
> the build list whose size the operator sets. Commodore's DevCon '93 *CD-ROM
> Tools* chapter (pp. 716–732; scan `CDROM_dev_doc.pdf` in
> [fuseoppl/isocd-win](https://github.com/fuseoppl/isocd-win)) says one empty
> space "is always needed at the end of the CD-ROM", that options are saved in
> the layout file and that layout files "can be re-used"; its printed example
> layout ends in `E0000 65536` — 65,536 bytes = **32 sectors**. Banshee's 232
> sectors are 475,136 bytes of the same entry.
>
> * Re-measured: LBA 1455–1686 is the only unclaimed run on the volume. In the
>   raw track, sectors 1455–1772 are uniform Mode 1 sectors (valid sync,
>   header = LBA, zero data, valid EDC) with **no seam at the declared size
>   1,687**, so the 232 is fixed where ISOCD computes the volume size, not at
>   mastering or pressing.
> * The test above has since been run three times: upstream
>   [cd32-platformnotes-doc](https://github.com/vs-sr-dev/cd32-platformnotes-doc)
>   measured Fire & Ice, Universe and Gunship 2000, all `D J Pocock`, all
>   **232**, each predicted before the sector map. 5 of 5 Pocock discs leave
>   232; every other ISOCD disc leaves 32. Volume sizes in the Pocock group span
>   65 : 1.
> * Ruled out: space reserved for removed files (everything on the floppy set
>   missing from the CD is 81 sectors, not 200), the Yellow Book data→audio
>   post-gap (150 ≠ 200, and it is outside ISO 9660), audio-track count, image
>   overrun, ISOCD version (all `ISOCD 1.04`).
> * Still open: whether the end entry itself was set to ≈475,136 bytes (H1) or
>   a second 409,600-byte ("400 K") space was added next to the default one
>   (H2). The image is identical either way. A Pocock `*.lay` file, or the
>   ISOCD 1.04 executable's default, would settle it.
>
> Confidence: **high** that the run is ISOCD's end Empty Space; **medium** that
> 65,536 is ISOCD 1.04's default rather than the manual's example value.

## 2. Why is `1992-12-21` on two unrelated discs, in the same quarter hour?

```
Banshee   41 file records          1992-12-21 15:11:46 .. 15:27:34
Marvin    PVD                      1992-12-21 15:15:40
Marvin    all 9 directory records  1992-12-21 15:24:31 .. 15:26:43
```

Two discs from unrelated studios and publishers, on the same wrong date, with
overlapping times of day inside the same sixteen-minute window — and on
different halves of the disc, Banshee's from the *source* file system and
Marvin's from the *mastering* machine.

A dead battery on an Amiga gives 1978, not this. The shape that would explain
it is a machine with **no battery-backed clock**, where AmigaDOS restores the
date from the boot volume at every boot and the time runs forward from there:
every session then starts at the same stored date and the time-of-day is a
function of uptime only.

This repository cannot test that. **The next disc carrying 1992-12-21 decides
it**, and the thing to record when one does is the *time of day*, not just the
date.

> **Partial answer (2026) — mechanism shown from Banshee's own data; the link
> to Marvin is still open.** The A1200 floppy release is stamped 1992-12-21
> too, but at *different* times of day for the same, byte-identical files
> (floppy header date − CD record date: `picture.exe` +5:10, disk 2 files
> +5:44, disk 3 +5:39, disk 4 +9:53). There are at least three sessions on the
> same wrong date with overlapping times: the CD's 41 files (15:11:46–15:27:34),
> retail disks 2–4 (roots created 15:19:35 / 15:22:02 / 15:28:35), and retail
> disk 1, whose root creation date (15:29:07, identical in all ten disk-1 dumps
> examined) is later than its own files. The CD and disk 2–4 sessions write
> at the same per-file speed (`level1c`: 272,677 B in 28 s in both), so they
> were not one boot copying twice in parallel. So the clock restarted at about
> the same reading on **every boot** — the AmigaDOS behaviour without a
> battery clock (date taken from the newest file on the boot disk), and the
> standard A1200 has no real-time clock. The hypothesis above holds.
>
> Correction: the 1992 stamps are not from the CD mastering machine (its clock
> was correct: `/s`, `/icons`, `/C` are 1994-07-08). They were written on a
> second machine at floppy speed (Q6) and carried into the mastering tree with
> dates preserved.
>
> Still open: why Marvin shows the same date. The thing to check is a boot disk
> both machines could have shared — e.g. the A1200 Workbench 3.0 set: a disk
> whose newest file is 1992-12-21, at or before 15:11:46, would explain both.
> Reproduce: [`tools/answers/session.py`](../tools/answers/session.py),
> [`tools/answers/adfdates.py`](../tools/answers/adfdates.py).
> Confidence: **high** for the per-boot restart; **low** for any explanation
> of the Marvin link.

## 3. Where do the copper modulos come from?

The two copper templates in `bans.exe` set

```
game screen     BPLCON0 $0211 (lores, 8 planes)   BPL1MOD = BPL2MOD = $0070 = 112
picture screen  BPLCON0 $8211 (hires, 8 planes)   BPL1MOD = BPL2MOD = $0228 = 552
```

with `FMODE $0007` (64-bit bitplane fetch) and `DDFSTRT $0038` / `DDFSTOP
$00D0` on both.

The picture files' geometry is settled independently and unambiguously —
`introscreen` renders correctly as 640 × 256, eight bitplanes, interleaved, 80
bytes per plane row, and the screen-clear blit's own numbers (width 80 bytes,
`BLTDMOD` 560, eight passes at 80-byte intervals) reproduce 640 bytes per
display row and 163,840 bytes total. A row advance of 640 with 80 bytes
fetched would want a modulo of 560, not 552.

So either the fetch is 88 bytes per plane per line under `FMODE 3` with this
`DDF` window, or the pointers are advanced somewhere else as well. The
repository has no emulator in the loop, and this is exactly the kind of number
that is easy to rationalise and hard to be sure of. **Recorded as measured,
not reconciled.**

The lores template's 112 is further from anything derivable and its screen's
geometry is not independently pinned down at all — the game's playfield buffer
is in chip BSS and the pointers are written at run time.

> **Answer (2026).** Modulo = row advance − bytes fetched, and with `FMODE`
> 4× bitplane fetch the fetch is rounded to whole 64-pixel units plus one:
> units = ⌊(`DDFSTOP` − `DDFSTRT`) / unit⌋ + 2, unit = `$20` lores / `$10`
> hires, 8 bytes per unit. With `$38–$D0` that is **48** bytes per plane per
> line in lores and **88** in hires — the hypothesis above was right, and 552
> is not a typo for 560 (the blit's 80 + 560 counts the visible 80 bytes; the
> display fetches 88). One rule reproduces all four copper lists in hunk 4,
> each row advance taken from the code's own pointer arithmetic:
>
> ```
> list  where           mode / DDF / FMODE           fetch  modulo  row  pointers set by the code
> A     hunk4+0x32      lores 8 pl, $38-$D0, $7         48     112   160  4 interleaved planes, 40 B apart
> A'    (A rewritten)   hires 8 pl, $38-$D0, $7         88     552   640  8 planes, 80 B apart (pictures)
> B     hunk4+0x94E     hires 3 pl, $38-$D0, $7         88     152   240  3 planes, 80 B apart (menu font)
> C     hunk4+0xA26     hires 8 pl, $38-$D0, $7         88     552   640  8 planes, 80 B apart
> D     hunk4+0x1466    lores 6 pl, $48-$B0, $F         40      56    96  6 planes $6000 apart (the game, Q4)
> ```
>
> Correction to [07-graphics.md](07-graphics.md): the `$0211` / `$0070`
> template is **not the game screen** but list A, the intro and ending screen
> (pointers written at `hunk0+0x3796` / `+0x37CE`, 4 planes × 40 bytes); the
> picture path rewrites its `BPLCON0`/`BPL1MOD`/`BPL2MOD` value words
> (`hunk4+0x918/+0x91C/+0x920`) to `$8211`/`$228`/`$228` at `hunk0+0x33AE` and
> `hunk0+0x3BD8`. The game screen is list D, which `COP1LC` points at in every
> saved in-game state. Reproduce:
> [`tools/answers/code_copscan.py`](../tools/answers/code_copscan.py),
> [`tools/answers/code_dis.py`](../tools/answers/code_dis.py).
> Confidence: **high** (one rule, three `DDF`/resolution combinations, four
> lists, no free parameter). Not a hardware measurement: a capture on real AGA
> with one modulo changed by ±8 would confirm it.

## 4. What is the playfield buffer's geometry?

The object blit ([07-graphics.md](07-graphics.md)) steps the destination by
`$6000` = 24,576 bytes six times, so the playfield is **six bitplanes,
non-interleaved, 24,576 bytes per plane**. 24,576 factors as 96 × 256 and as
64 × 384 and as 48 × 512, and the blits that touch it use destination modulos
of 62, 66 and 14 with widths of 34 and 30 bytes, giving row advances of 96, 96
and 48.

96 bytes per row is 768 pixels for a display window of 320. Whether that is a
scroll margin, a double buffer laid out side by side, or something else is not
established. The game screen's copper template asks for **eight** planes and
this buffer has six, so they are not the same buffer.

> **Answer (2026).** Six non-interleaved planes of **256 rows × 96 bytes**;
> each row holds **two 384-pixel (48-byte) buffers side by side**, and the game
> double-buffers between them. Left half at `hunk5+0x284`, right half at
> `hunk5+0x2B4`. The pointer writer at `hunk0+0xE58A` copies `BPLCON1` from
> `A5+0x34a`, swaps the longwords `A5+0x5c6` / `A5+0x5ca`, aligns the shown
> one to 8 bytes (`andi.l #$fffffff8`, for the 64-bit fetch) and writes six
> plane pointers `$6000` apart into copper list D (Q3). Stepping the game in an
> emulator shows one frame drawn every two VBlanks into the hidden half, then a
> flip; every playfield blit has a row advance of 96. 384 px is one ground-tile
> row (24 × 16 px, [13-level-formats-and-floppy.md](13-level-formats-and-floppy.md)).
>
> Two corrections to the question: the visible window is **256 × 256**
> (`DIWSTRT`/`DIWSTOP` `$2cc1`/`$2cc1`), not 320 wide; and the eight-plane
> `$0211` template is the intro screen (Q3), not a game buffer — the game's own
> list D has six planes, with planes 7–8 coming from separate buffers (cloud
> layer on L1/L3, light layer on L4/boss; see [18-runtime.md](18-runtime.md)).
> Confidence: **high** for geometry and double buffer. Not pinned down: which
> 256 of the 384 pixels are visible for a given `BPLCON1` value (fine delays
> of about 32–55 px are seen).

## 5. What was `flev`, and what is `bans1:`?

`bans1:flev` sits after the loader's 37 records with no record header
([11-leftovers.md](11-leftovers.md)). `bans1:` is assigned by nothing;
`banshee1:` is. `flev` is not on the disc.

An A1200 floppy release, or an ADF of one, would settle both in a single
string search. This repository has neither.

> **Partial answer (2026) — `bans1:` answered, `flev` still open.**
> `bans1:` is the **volume label of floppy disk 1**, used directly: the four
> floppies are labelled `bans1`…`bans4`, the floppy `startup-sequence` assigns
> `banshee1:`…`banshee4:` to them, and the floppy installer script also uses
> `bans1:` directly. AmigaDOS resolves a volume name while the disk is
> inserted, so `bans1:flev` was a valid path on floppy and would fail on the CD.
>
> `flev` is dead in **both** builds: in the CD `bans.exe` the string
> (`hunk0+0x2B96`, file `0x2BCA`) has no relocation, no absolute and no
> PC-relative reference; the floppy build has the same unheaded record at the
> end of its 40-record table, equally unreferenced; nothing walks the table
> sequentially (every load passes one record's own address); and none of the
> floppy images examined contains a file named `flev`. So the record and its
> caller were removed before both builds were linked. For a possible link to
> the developer level-skip, see
> [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §2.
> Reproduce: [`tools/answers/code_xref.py`](../tools/answers/code_xref.py).
> Confidence: **high** for `bans1:` and for "unreferenced"; what `flev` held
> is **open** (a pre-release build or source would settle it).

## 6. Why did `soundfx4` take seven and a half minutes?

The copy session's other 40 gaps track file size at roughly 150–200 KB/s.
`plyrmisc4` is written at wrong-clock 15:20:06 and `soundfx4`, 108,871 bytes,
at 15:27:34 — **7 minutes 28 seconds** where its size predicts about nine.
It is the last file written before ISOCD started, and the whole session only
had seventeen minutes in it.

> **Partial answer (2026) — localised to the session; cause still open.**
> The delay belongs to the session that stamped the CD's dates, not to the
> file. On retail disk 4 the same file (SHA-1 identical to the CD's) was
> written **15 s** after `plyrmisc4`, at the same rate as its neighbours, and
> every other disk-4 gap in the CD session matches the retail session to the
> second (`level4f` 22 s / 22 s, `level4c` 26 / 26, `banspic1` 9 / 9,
> `plyrmisc4` 8 / 7, `soundfx4` **448** / 15).
>
> Two corrections to the question as posed: the gaps run at **about
> 7–10 KB/s** (`level1c` 272,677 B / 28 s = 9.5 KB/s; `level2c` 281,827 B /
> 31 s = 8.9 KB/s), floppy speed, not the 150–200 KB/s stated above; and the
> "seventeen-minute session" no longer holds (see the correction in
> [02-filesystem.md](02-filesystem.md)). The CD's file order is also the retail
> floppies' **write order**, disk by disk, not their directory order, so the
> CD dates record a second run of the same per-disk floppy-writing procedure,
> with the CD32 `bans.exe` placed after `picture.exe`.
>
> A full disk is ruled out (retail disk 4 holds the same files plus an 81 KB
> module). *Speculation only:* a write/read error requester answered late, an
> operator pause, or a rewrite. Any second copy of the CD-variant floppy set or
> of the mastering tree, with its own dates, would settle it.
> Reproduce: [`tools/answers/session.py`](../tools/answers/session.py).
> Confidence: **high** that the delay is the session's; cause **open**.

## 7. What triggers the message about killing animals?

Eight lines at file offset 0x1F1C4, English only, outside the four-language
table ([11-leftovers.md](11-leftovers.md)). Nothing in the surrounding data
identifies a condition, and the repository does not run the game.

> **Answer (2026).** It is the **confirmation of a cheat**, not a reaction to
> shooting animals. The high-score name `Mary Whitehouse` (compared at
> `hunk0+0x1806`) or the keyboard sequence `I AM EXQUISITELY EVIL` + RETURN on
> a text screen (table at `hunk0+0x44E9`) copies the 160-byte block at
> `hunk1+0x5930` (file `0x1F1C4`) into the hall-of-fame name table, sets every
> score to 999999, flashes the background and sets the byte at `hunk0+0x32BA`.
> That flag's only reader is enemy-script sub-op `20.b8` (`hunk0+0x1255E`):
> with the flag clear it makes the object untouchable. The level scripts call
> `20.b8` for exactly the civilian and animal types, so by default they cannot
> be hit; the cheat makes them targets and the "message" appears as the
> high-score names. The block has fixed 19-column lines with `0xFF`
> terminators because it is an image of the name table (eight 20-byte
> entries), which is why it sits outside the four-language table.
> Details and the second (developer) cheat:
> [20-unused-content-and-cheats.md](20-unused-content-and-cheats.md) §1.
> Reproduce: [`tools/answers/code_xref.py`](../tools/answers/code_xref.py),
> [`tools/answers/code_dis.py`](../tools/answers/code_dis.py).
> Confidence: **high** (straight-line code; verified in emulation, see ch. 20).

## 8. What ran `picture.exe`?

274,764 bytes, 9.5 % of the data track, holding a 640 × 512 HAM8 image, and
nothing on the disc names it ([08-picture-exe.md](08-picture-exe.md)). It is
the first file in the copy session, 36 seconds before `bans.exe`.

Candidates the disc cannot distinguish: a title screen from an earlier build
that was replaced by `introscreen`; a viewer used to show the picture to
somebody during development; or the A1200 floppy release's title program,
carried across with everything else. A floppy release would settle it.

> **Answer (2026) — for the floppy release; nothing runs it on the CD.**
> The **hard-disk installation's launcher script** ran it. On floppy disk 1,
> `scrpt2` (39 bytes) is the two lines `banshee1:picture.exe` /
> `banshee1:bans.exe`; the Installer script `hdinstall` builds a `Banshee`
> start script from four `Assign BansheeN:` lines plus `scrpt2`, and the
> installed icon starts that script (Q9). The floppy boot itself never runs the
> picture. On the CD `scrpt2` is zero bytes, so nothing does.
>
> New: **the CD's `picture.exe` is a separate build, written out from memory
> after it had run.** Its code matches the floppy's (444 of 452 code-hunk bytes)
> and the 327,744-byte bitmap hunk is identical, but the CD copy has the frame
> counter at code `+0x1bc` = 727 fields (14.5 s) against the floppy's 250 (5 s),
> and the bitmap pointer (code `+0x1be`), the sprite and bitplane pointers and
> the colour words in its copper list already filled in — exactly the values
> the start-up code and the first odd-field update compute with hunk 3 at chip
> `$132000`. The floppy copy has all of these zero. That is the signature of
> assemble-run-write in an in-memory assembler, then RNC crunching (crunching
> was not needed to fit: `tools/answers/disk1fit.py`). Corrections in
> [08-picture-exe.md](08-picture-exe.md) and
> [13-level-formats-and-floppy.md](13-level-formats-and-floppy.md).
> Reproduce: [`tools/answers/picture_diff.py`](../tools/answers/picture_diff.py).
> Confidence: **high** for the floppy mechanism and for the memory-saved CD
> build. Open: whether anyone meant the CD to show the picture.

## 9. What was `/icons` for?

An empty directory at LBA 1454, written 27 seconds before `/C`, on a disc with
no `.info` file anywhere ([11-leftovers.md](11-leftovers.md)).

> **Answer (2026).** It is disk 1's `icons/` drawer, which carried the
> installed game's desktop icon. On every floppy disk-1 dump examined,
> `bans1:icons/` holds `banshee.info` (2,678 bytes, a `WBPROJECT` icon with
> default tool `sys:c/iconx`); `hdinstall` copies it next to the `Banshee`
> script built for Q8, so double-clicking it runs that script through IconX.
> On the CD the drawer is present and empty. *Inference (medium):* its
> 1994-07-08 13:13:49 date (mastering machine, correct clock) is the last
> change to the directory, which fits `banshee.info` being deleted on the
> mastering machine rather than the drawer being created empty; the CD has
> neither the `Banshee` script nor IconX, so the icon would have been useless.
> Reproduce: [`tools/answers/adfdates.py`](../tools/answers/adfdates.py).
> Confidence: **high** for content and purpose; **medium** for the deletion.

## 10. What does the loader's flag byte mean?

Every one of the 37 file-table records carries `0x01` at offset +5
([05-loader.md](05-loader.md)). A field that never varies cannot be decoded
from one disc. Worth checking on any other title by the same team.

> **Answer (2026).** `+5` means **"the file is RNC-packed: read it into the
> packed-file buffer and decrunch it into the destination"**. The loader
> (`hunk0+0x26D0`) reads `+0` buffer size, `+4` disk number ("insert disk N"),
> then tests `+5`: zero reads straight into the destination, non-zero reads
> into the packed buffer and calls the RNC method 1 decruncher at
> `hunk0+0x2964`. Every record carries `0x01` because every file it names is an
> RNC stream. The floppy build agrees: 40 records (37 of the CD's plus three
> copies of the menu music module), all `0x01`, all files beginning `RNC`. The
> intro-frame loader (`hunk0+0x2480`) skips the byte and decrunches each frame
> later. Reproduce: [`tools/answers/code_dis.py`](../tools/answers/code_dis.py).
> Confidence: **high**; the `0` branch exists but no shipped record uses it.

## 11. Is `0x9C` really Ø, or is the font not CP437 at all?

The Danish letters are `"` = Æ, `$` = Å, `+` = æ, `=` = å, `~` = ø and `0x9C`
= Ø, established from the hall-of-fame alphabet's ordering
([06-text.md](06-text.md)). CP437's `0x9C` is `£`, and the German and French
letters in the same table *are* CP437 (`0x81` ü, `0x82` é, `0x84` ä, `0x85` à,
`0x8A` è, `0x8B` ï, `0x94` ö, `0xE1` ß).

So either the font is CP437 with one glyph replaced, or it is a private font
that happens to agree with CP437 on eight positions. Rendering the font would
settle it; the font is inside a packed data file and has not been located.

> **Answer (2026).** `0x9C` is Ø, and **the font is not CP437**: it is a
> private 94-glyph font whose glyph table names each glyph's character code
> explicitly. The font bitmap is not in a separate data file but an RNC stream
> inside `bans.exe` at `hunk1+0x602` (file `0x19E96`; 640 × 81, three
> interleaved planes); the glyph table is at `hunk1+0x000`, 94 records of
> 16 bytes (`+0` code, `+2` bitmap offset, `+0xC` advance). `hunk0+0x5146`
> builds a 256-entry `map[code]` from it, and the text renderer draws each byte
> through that map. The record for `0x9C` (number 27) sits between `"` (Æ) and
> `$` (Å) and renders as **Ø**. All six Danish mappings of
> [06-text.md](06-text.md) and the eight German/French letters are confirmed
> the same way. The codes borrow CP437 for the German and French letters; the
> table has no entry for most of CP437 (nor `#`, `&`, `/`, `;`, `<`, `>`, `@`).
> `0x9C` is not Ø in CP865 either (Ø is `0x9D` there), so the value looks
> hand-picked. Reproduce:
> [`tools/answers/code_font.py`](../tools/answers/code_font.py).
> Confidence: **high** (the code-to-glyph mapping is data the program reads;
> each glyph checked by rendering).

## 12. Two things the platform checklist asks that this disc answers "nothing"

Recorded as results rather than as failed checks:

* **No `.bak` beside the boot script.** Two discs in eleven have one and both
  times it named the ancestor. This one has none.
* **No `.info` files at all**, so the hash comparison that identified Blitz
  Basic 2 on Guardian has nothing to compare.

> **Confirmed (2026) for the CD; the floppy release adds two icons.** No
> `.bak` on any of the 45 CD records or on any of the 17 floppy dumps
> examined; no `.info` on the CD. Floppy disk 1 carries two original icons,
> recorded here for the checklist's hash comparison:
>
> ```
> 2,678 B  87549bb6ba3ec0fa4afc7a1bd0972b265aa525ec  bans1:icons/banshee.info  WBPROJECT, tool sys:c/iconx
>   730 B  ab28bfa9f1b1abb6b54404e6f9dd70f8662ddc71  bans1:hdinstall.info      Installer project
> ```
>
> Neither is the 396-byte Blitz Basic 2 `startup-sequence.info` from
> Guardian/Gloom. Side result: floppy `bans1:assign` is byte-identical to the
> CD's `C/Assign` 37.4 but dated in the 1992 floppy session, while the CD copy
> is 1993-06-17, so the CD's `C:` was filled separately (from a Workbench
> disk), not from the floppy.
>
> Correction to [02-filesystem.md](02-filesystem.md) and
> [11-leftovers.md](11-leftovers.md): the two zero-length records (`scrpt2`,
> `C/Installer`) do not have "every field zero" — their date bytes are
> `4E 01 01 00 00 00` = **1978-01-01 00:00:00**, AmigaDOS DateStamp 0, the
> same value as the root directory record, which has no source object.
> *Inference:* ISOCD wrote both without reading a source file. Confidence:
> **high**.
