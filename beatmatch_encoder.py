#!/usr/bin/env python3
"""
DJ Beatmatch Encoder - CLI Tool

Scans a directory for music files with BPM information in their filenames
and renames them to include the pitch adjustment percentage needed to match
a target BPM.

Expected filename pattern: "... - XXX.ext" where XXX is the BPM (2-3 digits).
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Configure logging
logging.basicConfig(
    format="%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Regex pattern to match BPM in filename (e.g., " - 128.mp3")
BPM_PATTERN = re.compile(r"\s-\s(\d{2,3})\.")

# Regex pattern to match track number prefix (e.g., "01. " or "01 " or "1. ")
TRACK_NUMBER_PATTERN = re.compile(r"^(\d+\.?\s)")


class TrackInfo(NamedTuple):
    """Information about a track to be processed."""

    original_path: Path
    original_name: str
    bpm: float
    pitch_adjustment: str
    new_name: str


def calculate_pitch_adjustment(track_bpm: float, base_bpm: float) -> str:
    """
    Calculate the pitch adjustment percentage needed to match the base BPM.

    Args:
        track_bpm: The BPM of the track.
        base_bpm: The target BPM to match.

    Returns:
        A string representing the pitch adjustment (e.g., "+2.5" or "-1.3").
    """
    if base_bpm == track_bpm:
        return "0"

    # Calculate percentage change needed on the track
    percentage = ((base_bpm - track_bpm) / track_bpm) * 100

    if percentage > 0:
        return f"+{round(percentage, 2)}"
    else:
        return str(round(percentage, 2))


def generate_new_filename(original_name: str, pitch_adjustment: str) -> str:
    """
    Generate the new filename with the pitch adjustment inserted.

    If the filename starts with a track number (e.g., "01. " or "01 "),
    the adjustment is inserted after the number and space.
    Otherwise, the adjustment is prepended to the filename.

    Args:
        original_name: The original filename.
        pitch_adjustment: The pitch adjustment string to insert.

    Returns:
        The new filename with pitch adjustment.
    """
    match = TRACK_NUMBER_PATTERN.match(original_name)
    if match:
        # Insert after track number prefix (e.g., "01. " -> "01. (+2.5)")
        prefix = match.group(1)
        rest = original_name[len(prefix) :]
        return f"{prefix}({pitch_adjustment}) {rest}"
    else:
        # Prepend to the beginning of the filename
        return f"({pitch_adjustment}) {original_name}"


def scan_directory(directory: Path, base_bpm: float) -> list[TrackInfo]:
    """
    Scan a directory for music files with BPM information.

    Args:
        directory: The directory to scan.
        base_bpm: The target BPM for pitch adjustment calculations.

    Returns:
        A list of TrackInfo objects for files that match the BPM pattern.
    """
    tracks = []

    for entry in directory.iterdir():
        if not entry.is_file():
            continue

        match = BPM_PATTERN.search(entry.name)
        if match is None:
            logger.debug(f"Skipping (no BPM pattern): {entry.name}")
            continue

        try:
            bpm = float(match.group(1))
        except ValueError:
            logger.warning(f"Invalid BPM value in filename: {entry.name}")
            continue

        pitch_adjustment = calculate_pitch_adjustment(bpm, base_bpm)
        new_name = generate_new_filename(entry.name, pitch_adjustment)

        tracks.append(
            TrackInfo(
                original_path=entry,
                original_name=entry.name,
                bpm=bpm,
                pitch_adjustment=pitch_adjustment,
                new_name=new_name,
            )
        )

    return tracks


def rename_tracks(tracks: list[TrackInfo], dry_run: bool = False) -> int:
    """
    Rename tracks with their pitch adjustment information.

    Args:
        tracks: List of TrackInfo objects to rename.
        dry_run: If True, only print what would be done without renaming.

    Returns:
        The number of files successfully renamed.
    """
    renamed_count = 0

    for track in tracks:
        new_path = track.original_path.parent / track.new_name

        if dry_run:
            print(f"  {track.original_name}")
            print(f"    -> {track.new_name}")
            print(f"    (BPM: {track.bpm}, Adjustment: {track.pitch_adjustment})")
            renamed_count += 1
            continue

        try:
            track.original_path.rename(new_path)
            logger.info(f"Renamed: {track.original_name} -> {track.new_name}")
            renamed_count += 1
        except OSError as e:
            logger.error(f"Failed to rename {track.original_name}: {e}")

    return renamed_count


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DJ Beatmatch Encoder - Add pitch adjustment percentages to music filenames.",
        epilog="Example: %(prog)s -d ~/Music/DJSet -b 128",
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        required=True,
        help="Directory containing music files to process.",
    )

    parser.add_argument(
        "-b",
        "--bpm",
        type=float,
        required=True,
        help="Base BPM of the DJ set to match against.",
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming files.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output.",
    )

    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the CLI tool.

    Args:
        args: Command-line arguments (defaults to sys.argv if None).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parsed_args = parse_args(args)

    # Configure logging level
    if parsed_args.quiet:
        logger.setLevel(logging.ERROR)
    elif parsed_args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate directory
    directory = parsed_args.directory.resolve()
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return 1

    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        return 1

    # Validate BPM
    if parsed_args.bpm <= 0:
        logger.error("BPM must be a positive number.")
        return 1

    if parsed_args.bpm < 60 or parsed_args.bpm > 200:
        logger.warning(f"BPM {parsed_args.bpm} is outside typical range (60-200).")

    # Scan directory
    logger.info(f"Scanning directory: {directory}")
    logger.info(f"Base BPM: {parsed_args.bpm}")

    tracks = scan_directory(directory, parsed_args.bpm)

    if not tracks:
        logger.warning("No files found matching the BPM pattern (e.g., ' - 128.mp3').")
        return 0

    logger.info(f"Found {len(tracks)} file(s) with BPM information.")

    # Process files
    if parsed_args.dry_run:
        print("\n[DRY RUN] The following files would be renamed:\n")

    renamed_count = rename_tracks(tracks, dry_run=parsed_args.dry_run)

    if parsed_args.dry_run:
        print(f"\n[DRY RUN] {renamed_count} file(s) would be renamed.")
    else:
        logger.info(f"Successfully renamed {renamed_count} file(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
