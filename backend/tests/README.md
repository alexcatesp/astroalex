# Astroalex Backend Tests

## Test Suite Overview

This directory contains the test suite for the Astroalex backend application.

## Test Structure

```
tests/
├── __init__.py
├── README.md              # This file
├── test_utils.py          # Test fixtures and utilities
├── test_directory.py      # Directory management tests
├── test_metadata_parser.py # Metadata parsing tests
└── test_api.py            # API integration tests
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_api.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests Matching Pattern

```bash
pytest -k test_parse
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and classes
- Fast execution
- No external dependencies

### Integration Tests (`@pytest.mark.integration`)
- Test API endpoints
- Test service interactions
- May be slower

### Slow Tests (`@pytest.mark.slow`)
- Tests that process large files
- Tests with significant I/O
- Can be skipped with: `pytest -m "not slow"`

## Writing New Tests

### Test File Naming
- Files: `test_*.py`
- Classes: `Test*`
- Functions: `test_*`

### Example Test

```python
import pytest
from app.utils.directory import DirectoryManager

def test_sanitize_name():
    """Test project name sanitization"""
    result = DirectoryManager._sanitize_name("Test Project")
    assert result == "Test_Project"
```

### Using Fixtures

```python
def test_with_temp_dir(temp_dir):
    """Test using temporary directory fixture"""
    # temp_dir is automatically created and cleaned up
    assert Path(temp_dir).exists()
```

## Fixtures Available

- `temp_dir`: Temporary directory (auto-cleanup)
- `sample_fits_file`: Sample FITS file for testing
- `sample_project_dir`: Complete project structure

## Continuous Integration

Tests should pass before:
- Creating pull requests
- Merging to main branch
- Deploying to production

## Troubleshooting

### Astropy Not Found
```bash
pip install astropy
```

### Tests Fail with ImportError
Ensure you're in the backend directory and virtual environment is activated:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Skipped Tests
Some tests require optional dependencies (Astropy, Photutils, etc.).
Install all dependencies for complete test coverage.
