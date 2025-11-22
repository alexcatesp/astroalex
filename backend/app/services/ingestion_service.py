"""
File ingestion and organization service ("El Mayordomo")
"""
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.models.metadata import FileMetadata
from app.utils.metadata_parser import MetadataParser
from app.utils.directory import DirectoryManager

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting and organizing astrophotography files"""

    def __init__(self, project_path: str):
        """
        Initialize the ingestion service for a project.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.ingest_path = self.project_path / "00_ingest"

    def scan_ingest_directory(self) -> List[FileMetadata]:
        """
        Scan the ingestion directory and extract metadata from all FITS files.

        Returns:
            List of FileMetadata objects for each discovered file
        """
        if not self.ingest_path.exists():
            logger.warning(f"Ingest directory does not exist: {self.ingest_path}")
            return []

        files = []
        fits_extensions = ['.fit', '.fits', '.FIT', '.FITS']

        for file_path in self.ingest_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in fits_extensions:
                try:
                    # Extract metadata (filename parsing only for performance)
                    metadata_dict = MetadataParser.extract_metadata(
                        str(file_path), read_header=False
                    )

                    # Create FileMetadata object
                    file_metadata = FileMetadata(**metadata_dict)
                    files.append(file_metadata)

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue

        logger.info(f"Found {len(files)} FITS files in ingestion directory")
        return files

    def organize_file(
        self,
        filename: str,
        metadata: FileMetadata,
        session_name: Optional[str] = None,
        copy: bool = False
    ) -> str:
        """
        Organize a single file from ingest directory to its proper location.

        Args:
            filename: Name of the file in ingest directory
            metadata: Extracted metadata for the file
            session_name: Calibration session name (for calibration frames)
            copy: If True, copy instead of move

        Returns:
            Destination path where file was moved/copied

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If metadata is insufficient to determine destination
        """
        source_path = self.ingest_path / filename

        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")

        # Determine destination based on image type
        if metadata.image_type in ["Dark", "Flat", "Bias"]:
            # Calibration frame
            dest_path = self._get_calibration_dest(metadata, session_name)
        elif metadata.image_type == "Light":
            # Science frame
            dest_path = self._get_science_dest(metadata)
        else:
            raise ValueError(f"Unknown image type: {metadata.image_type}")

        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move or copy file
        try:
            if copy:
                shutil.copy2(source_path, dest_path)
                logger.debug(f"Copied: {filename} -> {dest_path}")
            else:
                shutil.move(str(source_path), str(dest_path))
                logger.debug(f"Moved: {filename} -> {dest_path}")

            return str(dest_path)

        except Exception as e:
            logger.error(f"Error organizing file {filename}: {e}")
            raise

    def _get_calibration_dest(
        self,
        metadata: FileMetadata,
        session_name: Optional[str] = None
    ) -> Path:
        """
        Determine destination path for calibration frames.

        Args:
            metadata: File metadata
            session_name: Session name, or auto-generated from date

        Returns:
            Destination path
        """
        # Use provided session name or generate from date
        if not session_name:
            if metadata.date:
                session_name = f"session_{metadata.date}"
            else:
                session_name = "session_default"

        # Get calibration type subdirectory
        type_dir = metadata.image_type.lower() + "s"  # "dark" -> "darks"

        dest_dir = (
            self.project_path / "01_raw_data" / "calibration" / session_name / type_dir
        )

        return dest_dir / metadata.filename

    def _get_science_dest(self, metadata: FileMetadata) -> Path:
        """
        Determine destination path for science frames.

        Args:
            metadata: File metadata

        Returns:
            Destination path

        Raises:
            ValueError: If object name or date is missing
        """
        if not metadata.object_name:
            raise ValueError("Object name required for science frames")

        # Sanitize object name
        from app.utils.directory import DirectoryManager
        safe_object = DirectoryManager._sanitize_name(metadata.object_name)

        # Use date from metadata or "unknown_date"
        date = metadata.date or "unknown_date"

        # Build path: 01_raw_data/science/OBJECT/DATE/[FILTER]/filename
        dest_dir = self.project_path / "01_raw_data" / "science" / safe_object / date

        if metadata.filter:
            dest_dir = dest_dir / f"Filter_{metadata.filter}"

        return dest_dir / metadata.filename

    def organize_all_files(
        self,
        session_name: Optional[str] = None,
        copy: bool = False
    ) -> Dict[str, Any]:
        """
        Organize all files from ingestion directory.

        Args:
            session_name: Calibration session name for calibration frames
            copy: If True, copy instead of move

        Returns:
            Dictionary with organization results (success, failures, counts)
        """
        files = self.scan_ingest_directory()

        results = {
            "total": len(files),
            "success": 0,
            "failed": 0,
            "errors": [],
            "organized_files": []
        }

        for file_metadata in files:
            try:
                dest_path = self.organize_file(
                    file_metadata.filename,
                    file_metadata,
                    session_name=session_name,
                    copy=copy
                )
                results["success"] += 1
                results["organized_files"].append({
                    "filename": file_metadata.filename,
                    "destination": dest_path,
                    "type": file_metadata.image_type
                })

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "filename": file_metadata.filename,
                    "error": str(e)
                })
                logger.error(f"Failed to organize {file_metadata.filename}: {e}")

        logger.info(
            f"Organization complete: {results['success']} success, "
            f"{results['failed']} failed out of {results['total']} files"
        )

        return results

    def get_ingest_stats(self) -> Dict[str, Any]:
        """
        Get statistics about files in the ingestion directory.

        Returns:
            Dictionary with file counts by type, filter, etc.
        """
        files = self.scan_ingest_directory()

        stats = {
            "total_files": len(files),
            "by_type": {},
            "by_filter": {},
            "by_object": {},
            "by_date": {},
        }

        for file_meta in files:
            # Count by type
            img_type = file_meta.image_type or "Unknown"
            stats["by_type"][img_type] = stats["by_type"].get(img_type, 0) + 1

            # Count by filter
            if file_meta.filter:
                stats["by_filter"][file_meta.filter] = (
                    stats["by_filter"].get(file_meta.filter, 0) + 1
                )

            # Count by object
            if file_meta.object_name:
                stats["by_object"][file_meta.object_name] = (
                    stats["by_object"].get(file_meta.object_name, 0) + 1
                )

            # Count by date
            if file_meta.date:
                stats["by_date"][file_meta.date] = (
                    stats["by_date"].get(file_meta.date, 0) + 1
                )

        return stats
