# DJ-Beatmatch-Encoder

A CLI tool that calculates pitch adjustment percentages for DJ tracks, helping you beatmatch on CDJs without sync functionality.

## Background

When performing on CDJs that lack sync functions, you need to manually match the speed of each song to your set's BPM. Rather than doing this by ear, this tool calculates the exact percentage adjustment needed.

The tool scans your music files, reads the BPM from the filename, and renames each file to include the pitch adjustment percentage needed to match your target BPM.

## Requirements

- Python 3.10+
- Music files with BPM in the filename (e.g., from Mixed In Key)

## Installation

```bash
git clone https://github.com/yourusername/DJ-Beatmatch-Encoder.git
cd DJ-Beatmatch-Encoder
```

No additional dependencies required - uses only Python standard library.

## Usage

```bash
python3 beatmatch_encoder.py -d <directory> -b <bpm> [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `-d, --directory` | Directory containing music files |
| `-b, --bpm` | Base BPM of your DJ set |

### Optional Arguments

| Argument | Description |
|----------|-------------|
| `-n, --dry-run` | Preview changes without renaming files |
| `-v, --verbose` | Enable detailed output |
| `-q, --quiet` | Suppress non-error messages |
| `-h, --help` | Show help message |

### Examples

Preview what changes would be made:
```bash
python3 beatmatch_encoder.py -d ~/Music/DJSet -b 128 --dry-run
```

Rename files with pitch adjustments for a 130 BPM set:
```bash
python3 beatmatch_encoder.py -d ~/Music/DJSet -b 130
```

Verbose output for debugging:
```bash
python3 beatmatch_encoder.py -d ~/Music/DJSet -b 128 -v
```

## File Naming Requirements

Your music files must include the BPM in the filename with this pattern:
```
<track info> - <BPM>.<extension>
```

**Examples of valid filenames:**
- `01. Artist - Track Name - 128.mp3`
- `Song Title - 140.wav`
- `My Track - 125.flac`

**Output after processing (with base BPM of 130):**
- `01. (+1.56) Artist - Track Name - 128.mp3`
- `(-7.14) Song Title - 140.wav`
- `(+4.0) My Track - 125.flac`

The pitch adjustment placement depends on the filename format:
- **With track number** (e.g., `01. `, `01 `, `1. `): inserted after the number
- **Without track number**: prepended to the beginning of the filename

## How It Works

The pitch adjustment formula calculates the percentage change needed:

```
adjustment = ((base_bpm - track_bpm) / track_bpm) × 100
```

- **Positive values (+)**: Speed up the track (track is slower than set)
- **Negative values (−)**: Slow down the track (track is faster than set)
- **Zero (0)**: Track already matches set BPM

## Limitations

- Filenames must follow the expected BPM pattern (` - XXX.`)
- Non-UTF-8 characters in filenames may cause issues
