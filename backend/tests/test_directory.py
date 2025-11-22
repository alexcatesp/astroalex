"""
Tests for directory management
"""
import pytest
from pathlib import Path
from app.utils.directory import DirectoryManager


def test_sanitize_name():
    """Test project name sanitization"""
    assert DirectoryManager._sanitize_name("Test Project") == "Test_Project"
    assert DirectoryManager._sanitize_name("M31 @ Andromeda!") == "M31_Andromeda"
    assert DirectoryManager._sanitize_name("   ") == "project"


def test_create_project_structure(temp_dir):
    """Test project structure creation"""
    project_path = DirectoryManager.create_project_structure(temp_dir, "TestProject")

    # Check main directories exist
    assert Path(project_path).exists()
    assert (Path(project_path) / "00_ingest").is_dir()
    assert (Path(project_path) / "01_raw_data").is_dir()
    assert (Path(project_path) / "02_processed_data").is_dir()
    assert (Path(project_path) / "03_scripts").is_dir()

    # Check subdirectories
    assert (Path(project_path) / "01_raw_data" / "calibration").is_dir()
    assert (Path(project_path) / "01_raw_data" / "science").is_dir()


def test_validate_project_structure(sample_project_dir):
    """Test project structure validation"""
    assert DirectoryManager.validate_project_structure(sample_project_dir)

    # Test invalid structure
    assert not DirectoryManager.validate_project_structure("/nonexistent/path")


def test_create_calibration_session_dirs(sample_project_dir):
    """Test calibration session directory creation"""
    dirs = DirectoryManager.create_calibration_session_dirs(
        sample_project_dir, "session_2025-01-22"
    )

    assert "darks" in dirs
    assert "flats" in dirs
    assert "bias" in dirs

    for dir_path in dirs.values():
        assert Path(dir_path).exists()
