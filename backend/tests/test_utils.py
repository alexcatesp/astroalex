"""
Test utilities and fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_fits_file(temp_dir):
    """Create a sample FITS file for testing"""
    try:
        from astropy.io import fits
        from astropy.nddata import CCDData
        import astropy.units as u

        # Create sample data
        data = np.random.rand(100, 100) * 1000
        ccd = CCDData(data, unit='adu')

        # Add header info
        ccd.header['EXPTIME'] = 300.0
        ccd.header['GAIN'] = 100
        ccd.header['FILTER'] = 'L'
        ccd.header['IMAGETYP'] = 'Light'

        # Save
        file_path = Path(temp_dir) / "sample.fits"
        ccd.write(file_path)

        return str(file_path)

    except ImportError:
        pytest.skip("Astropy not installed")


@pytest.fixture
def sample_project_dir(temp_dir):
    """Create a sample project directory structure"""
    from app.utils.directory import DirectoryManager

    project_path = DirectoryManager.create_project_structure(temp_dir, "TestProject")
    return project_path


def create_test_fits(path: str, data: np.ndarray = None, **header_kwargs):
    """Helper to create test FITS files"""
    try:
        from astropy.io import fits
        from astropy.nddata import CCDData
        import astropy.units as u

        if data is None:
            data = np.random.rand(100, 100) * 1000

        ccd = CCDData(data, unit='adu')

        for key, value in header_kwargs.items():
            ccd.header[key] = value

        ccd.write(path, overwrite=True)
        return path

    except ImportError:
        pytest.skip("Astropy not installed")
