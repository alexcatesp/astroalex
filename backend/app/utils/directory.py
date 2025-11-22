"""
Directory structure management utilities
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DirectoryManager:
    """Manages project directory structure creation and validation"""

    # Standard project directory structure
    STRUCTURE = {
        "00_ingest": {},
        "01_raw_data": {
            "calibration": {},
            "science": {}
        },
        "02_processed_data": {
            "masters": {},
            "science": {}
        },
        "03_scripts": {}
    }

    @staticmethod
    def create_project_structure(base_path: str, project_name: str) -> str:
        """
        Create the standard Astroalex project directory structure.

        Args:
            base_path: Base directory where projects are stored
            project_name: Name of the project (will be sanitized)

        Returns:
            Absolute path to the created project directory

        Raises:
            OSError: If directory creation fails
        """
        # Sanitize project name (remove special characters, spaces)
        safe_name = DirectoryManager._sanitize_name(project_name)
        project_path = Path(base_path) / safe_name

        # Check if project already exists
        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")

        logger.info(f"Creating project structure at: {project_path}")

        try:
            # Create the directory structure
            DirectoryManager._create_structure(project_path, DirectoryManager.STRUCTURE)
            logger.info(f"Successfully created project structure for: {project_name}")
            return str(project_path.absolute())

        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            # Clean up partial creation
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
            raise

    @staticmethod
    def _create_structure(base: Path, structure: dict) -> None:
        """Recursively create directory structure"""
        for dir_name, subdirs in structure.items():
            dir_path = base / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

            # Recursively create subdirectories
            if subdirs:
                DirectoryManager._create_structure(dir_path, subdirs)

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """
        Sanitize project name to be filesystem-safe.

        Args:
            name: Original project name

        Returns:
            Sanitized name safe for filesystem use
        """
        # Replace spaces with underscores
        safe = name.replace(" ", "_")
        # Remove or replace special characters
        safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-"))
        # Ensure it's not empty
        if not safe:
            safe = "project"
        return safe

    @staticmethod
    def validate_project_structure(project_path: str) -> bool:
        """
        Validate that a directory has the correct Astroalex structure.

        Args:
            project_path: Path to the project directory

        Returns:
            True if structure is valid, False otherwise
        """
        path = Path(project_path)
        if not path.exists():
            return False

        # Check for required top-level directories
        required_dirs = ["00_ingest", "01_raw_data", "02_processed_data"]
        for dir_name in required_dirs:
            if not (path / dir_name).is_dir():
                logger.warning(f"Missing required directory: {dir_name}")
                return False

        return True

    @staticmethod
    def get_ingest_path(project_path: str) -> str:
        """Get the ingestion directory path for a project"""
        return str(Path(project_path) / "00_ingest")

    @staticmethod
    def get_raw_data_path(project_path: str, data_type: str = "") -> str:
        """
        Get the raw data directory path.

        Args:
            project_path: Path to the project
            data_type: Optional subdirectory ('calibration' or 'science')
        """
        base = Path(project_path) / "01_raw_data"
        if data_type:
            return str(base / data_type)
        return str(base)

    @staticmethod
    def get_processed_data_path(project_path: str, data_type: str = "") -> str:
        """
        Get the processed data directory path.

        Args:
            project_path: Path to the project
            data_type: Optional subdirectory ('masters' or 'science')
        """
        base = Path(project_path) / "02_processed_data"
        if data_type:
            return str(base / data_type)
        return str(base)

    @staticmethod
    def create_calibration_session_dirs(project_path: str, session_name: str) -> dict:
        """
        Create directory structure for a calibration session.

        Args:
            project_path: Path to the project
            session_name: Name of the calibration session

        Returns:
            Dictionary with paths to created directories
        """
        base_path = Path(project_path) / "01_raw_data" / "calibration" / session_name

        dirs = {
            "darks": base_path / "darks",
            "flats": base_path / "flats",
            "bias": base_path / "bias"
        }

        for dir_name, dir_path in dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created calibration directory: {dir_path}")

        return {k: str(v) for k, v in dirs.items()}

    @staticmethod
    def create_science_object_dirs(
        project_path: str,
        object_name: str,
        date: str,
        filter_name: Optional[str] = None
    ) -> str:
        """
        Create directory structure for science frames of an object.

        Args:
            project_path: Path to the project
            object_name: Name of the astronomical object
            date: Observation date (YYYY-MM-DD)
            filter_name: Optional filter name (e.g., 'Filter_L', 'Filter_Ha')

        Returns:
            Path to the created directory
        """
        safe_object = DirectoryManager._sanitize_name(object_name)
        base_path = Path(project_path) / "01_raw_data" / "science" / safe_object / date

        if filter_name:
            base_path = base_path / filter_name

        base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created science directory: {base_path}")

        return str(base_path)
