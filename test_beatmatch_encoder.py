"""Tests for the DJ Beatmatch Encoder CLI tool."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from beatmatch_encoder import (
    calculate_pitch_adjustment,
    generate_new_filename,
    scan_directory,
    rename_tracks,
    parse_args,
    TrackInfo,
)


class TestCalculatePitchAdjustment:
    """Tests for the pitch adjustment calculation."""

    def test_same_bpm_returns_zero(self):
        assert calculate_pitch_adjustment(128, 128) == "0"

    def test_track_slower_than_base_returns_positive(self):
        # Track at 125, need to speed up to 130
        result = calculate_pitch_adjustment(125, 130)
        assert result.startswith("+")
        assert float(result) == pytest.approx(4.0, rel=0.01)

    def test_track_faster_than_base_returns_negative(self):
        # Track at 140, need to slow down to 130
        result = calculate_pitch_adjustment(140, 130)
        assert result.startswith("-")
        assert float(result) == pytest.approx(-7.14, rel=0.01)

    def test_small_adjustment(self):
        result = calculate_pitch_adjustment(128, 130)
        assert result.startswith("+")
        assert float(result) == pytest.approx(1.56, rel=0.01)

    def test_large_adjustment(self):
        result = calculate_pitch_adjustment(100, 130)
        assert result.startswith("+")
        assert float(result) == pytest.approx(30.0, rel=0.01)


class TestGenerateNewFilename:
    """Tests for filename generation with pitch adjustments."""

    def test_with_track_number_and_period(self):
        result = generate_new_filename("01. Artist - Track - 128.mp3", "+1.56")
        assert result == "01. (+1.56) Artist - Track - 128.mp3"

    def test_with_track_number_no_period(self):
        result = generate_new_filename("01 Artist - Track - 128.mp3", "+1.56")
        assert result == "01 (+1.56) Artist - Track - 128.mp3"

    def test_with_single_digit_track_number(self):
        result = generate_new_filename("1. Artist - Track - 128.mp3", "+1.56")
        assert result == "1. (+1.56) Artist - Track - 128.mp3"

    def test_with_double_digit_track_number(self):
        result = generate_new_filename("12. Artist - Track - 128.mp3", "-2.5")
        assert result == "12. (-2.5) Artist - Track - 128.mp3"

    def test_without_track_number(self):
        result = generate_new_filename("Artist - Track - 128.mp3", "-2.5")
        assert result == "(-2.5) Artist - Track - 128.mp3"

    def test_zero_adjustment(self):
        result = generate_new_filename("01. Artist - Track - 130.mp3", "0")
        assert result == "01. (0) Artist - Track - 130.mp3"

    def test_without_track_number_zero_adjustment(self):
        result = generate_new_filename("My Song - 130.wav", "0")
        assert result == "(0) My Song - 130.wav"


class TestScanDirectory:
    """Tests for directory scanning."""

    def test_finds_files_with_bpm_pattern(self, tmp_path):
        # Create test files
        (tmp_path / "01. Artist - Track - 128.mp3").touch()
        (tmp_path / "02. Artist - Song - 140.wav").touch()

        tracks = scan_directory(tmp_path, base_bpm=130)

        assert len(tracks) == 2
        bpms = {t.bpm for t in tracks}
        assert bpms == {128.0, 140.0}

    def test_skips_files_without_bpm_pattern(self, tmp_path):
        # Create files without BPM pattern
        (tmp_path / "Artist - Track.mp3").touch()
        (tmp_path / "random_file.txt").touch()
        # Create one valid file
        (tmp_path / "01. Artist - Track - 128.mp3").touch()

        tracks = scan_directory(tmp_path, base_bpm=130)

        assert len(tracks) == 1
        assert tracks[0].bpm == 128.0

    def test_skips_directories(self, tmp_path):
        # Create a subdirectory with BPM-like name
        (tmp_path / "Artist - 128.mp3").mkdir()
        # Create a valid file
        (tmp_path / "01. Track - 130.mp3").touch()

        tracks = scan_directory(tmp_path, base_bpm=130)

        assert len(tracks) == 1

    def test_empty_directory(self, tmp_path):
        tracks = scan_directory(tmp_path, base_bpm=130)
        assert tracks == []

    def test_calculates_correct_adjustments(self, tmp_path):
        (tmp_path / "01. Track - 125.mp3").touch()

        tracks = scan_directory(tmp_path, base_bpm=130)

        assert len(tracks) == 1
        assert tracks[0].pitch_adjustment == "+4.0"


class TestRenameTracks:
    """Tests for the file renaming functionality."""

    def test_dry_run_does_not_rename(self, tmp_path, capsys):
        original_file = tmp_path / "01. Track - 128.mp3"
        original_file.touch()

        track = TrackInfo(
            original_path=original_file,
            original_name="01. Track - 128.mp3",
            bpm=128.0,
            pitch_adjustment="+1.56",
            new_name="01. (+1.56) Track - 128.mp3",
        )

        count = rename_tracks([track], dry_run=True)

        assert count == 1
        assert original_file.exists()
        assert not (tmp_path / "01. (+1.56) Track - 128.mp3").exists()

    def test_renames_files(self, tmp_path):
        original_file = tmp_path / "01. Track - 128.mp3"
        original_file.touch()

        track = TrackInfo(
            original_path=original_file,
            original_name="01. Track - 128.mp3",
            bpm=128.0,
            pitch_adjustment="+1.56",
            new_name="01. (+1.56) Track - 128.mp3",
        )

        count = rename_tracks([track], dry_run=False)

        assert count == 1
        assert not original_file.exists()
        assert (tmp_path / "01. (+1.56) Track - 128.mp3").exists()

    def test_handles_multiple_files(self, tmp_path):
        files = [
            ("01. Track A - 128.mp3", "01. (+1.56) Track A - 128.mp3"),
            ("02. Track B - 140.wav", "02. (-7.14) Track B - 140.wav"),
        ]

        tracks = []
        for original, new in files:
            path = tmp_path / original
            path.touch()
            tracks.append(
                TrackInfo(
                    original_path=path,
                    original_name=original,
                    bpm=0,
                    pitch_adjustment="",
                    new_name=new,
                )
            )

        count = rename_tracks(tracks, dry_run=False)

        assert count == 2
        for original, new in files:
            assert not (tmp_path / original).exists()
            assert (tmp_path / new).exists()


class TestParseArgs:
    """Tests for argument parsing."""

    def test_required_arguments(self):
        args = parse_args(["-d", "/some/path", "-b", "128"])
        assert args.directory == Path("/some/path")
        assert args.bpm == 128.0

    def test_dry_run_flag(self):
        args = parse_args(["-d", "/path", "-b", "128", "--dry-run"])
        assert args.dry_run is True

    def test_dry_run_short_flag(self):
        args = parse_args(["-d", "/path", "-b", "128", "-n"])
        assert args.dry_run is True

    def test_verbose_flag(self):
        args = parse_args(["-d", "/path", "-b", "128", "-v"])
        assert args.verbose is True

    def test_quiet_flag(self):
        args = parse_args(["-d", "/path", "-b", "128", "-q"])
        assert args.quiet is True

    def test_missing_directory_raises(self):
        with pytest.raises(SystemExit):
            parse_args(["-b", "128"])

    def test_missing_bpm_raises(self):
        with pytest.raises(SystemExit):
            parse_args(["-d", "/path"])

    def test_bpm_as_float(self):
        args = parse_args(["-d", "/path", "-b", "127.5"])
        assert args.bpm == 127.5


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self, tmp_path):
        # Create test files
        (tmp_path / "01. Artist - Song A - 125.mp3").touch()
        (tmp_path / "02. Artist - Song B - 140.mp3").touch()
        (tmp_path / "Random Track - 128.wav").touch()

        # Scan and process
        tracks = scan_directory(tmp_path, base_bpm=130)
        assert len(tracks) == 3

        # Rename
        count = rename_tracks(tracks, dry_run=False)
        assert count == 3

        # Verify results
        files = list(tmp_path.iterdir())
        filenames = {f.name for f in files}

        assert "01. (+4.0) Artist - Song A - 125.mp3" in filenames
        assert "02. (-7.14) Artist - Song B - 140.mp3" in filenames
        assert "(+1.56) Random Track - 128.wav" in filenames