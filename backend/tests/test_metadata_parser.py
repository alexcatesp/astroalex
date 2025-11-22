"""
Tests for metadata parser
"""
import pytest
from app.utils.metadata_parser import MetadataParser


def test_parse_asiair_filename():
    """Test ASIAIR filename parsing"""
    filename = "M31_Andromeda_Galaxy_Light_Filter_L_300s_gain100_2025-10-26_001.fit"
    metadata = MetadataParser.parse_filename(filename)

    assert metadata["image_type"] == "Light"
    assert metadata["object_name"] == "M31 Andromeda Galaxy"
    assert metadata["filter"] == "L"
    assert metadata["exposure_time"] == 300.0
    assert metadata["gain"] == 100
    assert metadata["date"] == "2025-10-26"
    assert metadata["sequence"] == "001"


def test_parse_dark_filename():
    """Test Dark frame filename parsing"""
    filename = "Dark_300s_gain100_2025-10-26_001.fits"
    metadata = MetadataParser.parse_filename(filename)

    assert metadata["image_type"] == "Dark"
    assert metadata["exposure_time"] == 300.0
    assert metadata["gain"] == 100


def test_parse_simple_filename():
    """Test simple filename format"""
    filename = "M31_300s_L_001.fits"
    metadata = MetadataParser.parse_filename(filename)

    assert metadata["object_name"] == "M31"
    assert metadata["exposure_time"] == 300.0
    assert metadata["filter"] == "L"


def test_infer_image_type_from_path():
    """Test image type inference from path"""
    assert MetadataParser.infer_image_type_from_path("/path/darks/file.fits") == "Dark"
    assert MetadataParser.infer_image_type_from_path("/path/flats/file.fits") == "Flat"
    assert MetadataParser.infer_image_type_from_path("/path/bias/file.fits") == "Bias"
    assert MetadataParser.infer_image_type_from_path("/path/science/file.fits") == "Light"
