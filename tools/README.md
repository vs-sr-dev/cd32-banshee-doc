# tools

Python 3. `capstone` for anything that disassembles, `Pillow` for images. Every tool reads
files you extracted from your own copy of the game; nothing here contains game data.

## Address convention
Runtime addresses printed by the tools use the Ghidra layout: bans.exe hunks packed back to back
from 0x21f000 (hunk0 0x21f000, 1 0x236cdc, 2 0x23d610 BSS, 3 0x290f64, 4 0x291084, 5 0x2951f4 BSS).
The docs quote `hunkN+off` or file offsets; `bansexe.py` converts between all three.

## Files and containers
- `isodump.py` ISO 9660 walk of the CD data track; `inventory.py` file inventory with sizes and SHA-1
- `adf.py` extract files from an OFS/FFS ADF; `census.py` compression census over extracted files
- `rnc.py` RNC method 1 decompressor; `rnc2.py` RNC method 2 and the self-decrunching picture.exe
- `relocs.py` hunk layout and HUNK_RELOC32 lookup; `bansexe.py` relocated bans.exe image + address conversion
- `loadertable.py` loader file table; `text.py` four-language string table; `strings.py` printable strings

## Code
- `dis68k.py`, `m68kdis.py` capstone disassembly with branch targets fixed from the raw bytes
- `regscan.py` custom-chip register scan; `copper.py` copper-list disassembler; `akiko.py` Akiko C2P scan

## Graphics, sound, levels
- `planar.py` planar/HAM8 renderer; `bobs.py` bob sheet; `ground.py`, `map.py` level backgrounds
- `spawns.py` spawn positions over a level map; `samples.py` Paula samples to WAV
- `scriptdis.py` enemy-script VM disassembler and reachability report
- `movement/vmextract.py` movement graph of every type to JSON; `movement/vmsim.py` path simulator
- `rng/banshee_rng.py` RNG model; `rng/rng_xref.py` RNG references in code; `rng/scan_vm_rng.py` in scripts

## answers/ (one tool per question in the docs)
`adfdates.py` ADF dates/hashes, `session.py` CD vs floppy write session, `picture_diff.py` floppy vs CD
picture.exe, `disk1fit.py` would disk 1 fit, `code_addrconv.py` hunk table / conversion,
`code_copscan.py` copper lists in hunk 4, `code_dis.py` disassemble at runtime address,
`code_xref.py` references to an address, `code_font.py` menu font (+PNG).

## Usage of the bans.exe / level tools
    python bansexe.py bans.exe [0x22ecd0 hunk1+0x10 file:0x2586] [--dump N out.bin]
    python scriptdis.py level1f
    python scriptdis.py --reach --exe bans.exe level1f level2f level3f level4f bossf
    python movement/vmextract.py --levels <unpacked dir> out.json
    python movement/vmsim.py --exe bans.exe --levels <unpacked dir> L1 1b4
    python rng/banshee_rng.py;  python rng/rng_xref.py bans.exe
    python rng/scan_vm_rng.py level1f level2f ...
    python answers/adfdates.py disk.adf
    python answers/session.py track1.iso disk1.adf disk2.adf disk3.adf disk4.adf
    python answers/picture_diff.py <floppy picture.exe> <CD picture.exe | rnc2 hunk dir>
    python answers/disk1fit.py disk1.adf bans.exe picture.exe [--exclude NAME]
    python answers/code_addrconv.py bans.exe [addr ...]
    python answers/code_copscan.py bans.exe
    python answers/code_dis.py bans.exe 0x22f1b4 0x40
    python answers/code_xref.py bans.exe 0x22ecd0
    python answers/code_font.py bans.exe [--png out.png] [codes]
Level files are the RNC-unpacked `level1f..level4f`, `bossf` (`rnc.py`). vmsim level keys: L1..L4, LB.

## Not included
Analysis scripts that need the emulator harness (memory dumps, save states, trace logs):
movement traces/verify/classify/report/build_json/disall/sigs/subscan/tickrate;
rng boot_seed/determinism/tracer/verify/verify_pod/twoplayer_start; answers code_copper/code_playfield/code_emu.
