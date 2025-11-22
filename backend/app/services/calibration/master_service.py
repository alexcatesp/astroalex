"""
Master calibration frame management service
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any

from app.models.metadata import MasterCalibration, CalibrationSession
from app.services.calibration.combiner import CalibrationCombiner

logger = logging.getLogger(__name__)


class MasterCalibrationService:
    """Service for managing master calibration frames"""

    def __init__(self, project_path: str):
        """
        Initialize the master calibration service.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.masters_dir = self.project_path / "02_processed_data" / "masters"
        self.metadata_file = self.masters_dir / ".masters.json"
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        """Ensure the masters metadata file exists"""
        self.masters_dir.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            self.metadata_file.write_text(json.dumps({
                "sessions": [],
                "masters": []
            }, indent=2))

    def _read_metadata(self) -> dict:
        """Read masters metadata from file"""
        try:
            return json.loads(self.metadata_file.read_text())
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return {"sessions": [], "masters": []}

    def _write_metadata(self, data: dict):
        """Write masters metadata to file"""
        try:
            self.metadata_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            raise

    def create_session(self, name: str, date: str, telescope: Optional[str] = None,
                       camera: Optional[str] = None) -> CalibrationSession:
        """
        Create a new calibration session.

        Args:
            name: Session name
            date: Session date (YYYY-MM-DD)
            telescope: Optional telescope name
            camera: Optional camera name

        Returns:
            Created CalibrationSession
        """
        session_id = str(uuid.uuid4())
        session = CalibrationSession(
            id=session_id,
            name=name,
            date=date,
            telescope=telescope,
            camera=camera,
            created_at=datetime.now()
        )

        metadata = self._read_metadata()
        metadata["sessions"].append(session.model_dump())
        self._write_metadata(metadata)

        logger.info(f"Created calibration session: {name} (ID: {session_id})")
        return session

    def get_sessions(self) -> List[CalibrationSession]:
        """Get all calibration sessions"""
        metadata = self._read_metadata()
        return [CalibrationSession(**s) for s in metadata["sessions"]]

    def get_session(self, session_id: str) -> Optional[CalibrationSession]:
        """Get a calibration session by ID"""
        metadata = self._read_metadata()
        for s in metadata["sessions"]:
            if s["id"] == session_id:
                return CalibrationSession(**s)
        return None

    def scan_calibration_frames(
        self,
        session_name: str,
        frame_type: Literal["bias", "darks", "flats"]
    ) -> List[Dict[str, Any]]:
        """
        Scan for calibration frames in a session directory.

        Args:
            session_name: Name of the calibration session
            frame_type: Type of frames to scan for

        Returns:
            List of frame information dictionaries
        """
        frames_dir = (
            self.project_path / "01_raw_data" / "calibration" / session_name / frame_type
        )

        if not frames_dir.exists():
            logger.warning(f"Frames directory does not exist: {frames_dir}")
            return []

        frames = []
        fits_extensions = ['.fit', '.fits', '.FIT', '.FITS']

        for file_path in frames_dir.iterdir():
            if file_path.is_file() and file_path.suffix in fits_extensions:
                try:
                    info = CalibrationCombiner.get_frame_info(str(file_path))
                    frames.append(info)
                except Exception as e:
                    logger.error(f"Error getting info for {file_path}: {e}")
                    continue

        logger.info(f"Found {len(frames)} {frame_type} frames in session {session_name}")
        return frames

    def create_master(
        self,
        session_id: str,
        frame_type: Literal["Bias", "Dark", "Flat"],
        file_paths: List[str],
        method: Literal["average", "median"] = "median",
        rejection: Optional[Literal["minmax", "sigma_clip"]] = "sigma_clip",
        exposure_time: Optional[float] = None,
        gain: Optional[int] = None,
        filter_name: Optional[str] = None,
        **kwargs
    ) -> MasterCalibration:
        """
        Create a master calibration frame.

        Args:
            session_id: Calibration session ID
            frame_type: Type of master frame (Bias, Dark, Flat)
            file_paths: List of frame files to combine
            method: Combination method
            rejection: Rejection method
            exposure_time: Exposure time (for darks/flats)
            gain: Gain setting
            filter_name: Filter name (for flats)
            **kwargs: Additional parameters for combiner

        Returns:
            Created MasterCalibration object
        """
        # Validate session
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Validate frames
        validation = CalibrationCombiner.validate_frames(file_paths)
        if validation["dimension_mismatch"]:
            raise ValueError("Frame dimensions do not match")
        if validation["valid_count"] == 0:
            raise ValueError("No valid frames to combine")

        # Generate master filename
        master_id = str(uuid.uuid4())
        filename_parts = ["master", frame_type.lower()]
        if exposure_time:
            filename_parts.append(f"{int(exposure_time)}s")
        if gain:
            filename_parts.append(f"gain{gain}")
        if filter_name:
            filename_parts.append(filter_name)
        filename = "_".join(filename_parts) + ".fits"

        # Output path
        session_dir = self.masters_dir / session.name
        session_dir.mkdir(parents=True, exist_ok=True)
        output_path = session_dir / filename

        # Combine frames
        logger.info(f"Creating master {frame_type} from {len(file_paths)} frames")
        stats = CalibrationCombiner.combine_frames(
            file_paths=file_paths,
            output_path=str(output_path),
            method=method,
            rejection=rejection,
            **kwargs
        )

        # Create master calibration object
        master = MasterCalibration(
            id=master_id,
            session_id=session_id,
            type=frame_type,
            exposure_time=exposure_time,
            gain=gain,
            filter=filter_name,
            filename=filename,
            num_frames=len(file_paths),
            combination_method=method,
            rejection_method=rejection,
            created_at=datetime.now()
        )

        # Save to metadata
        metadata = self._read_metadata()
        metadata["masters"].append(master.model_dump())
        self._write_metadata(metadata)

        logger.info(f"Created master calibration: {filename} (ID: {master_id})")
        return master

    def get_masters(self, session_id: Optional[str] = None) -> List[MasterCalibration]:
        """
        Get master calibration frames.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of master calibration frames
        """
        metadata = self._read_metadata()
        masters = [MasterCalibration(**m) for m in metadata["masters"]]

        if session_id:
            masters = [m for m in masters if m.session_id == session_id]

        return masters

    def get_master(self, master_id: str) -> Optional[MasterCalibration]:
        """Get a master calibration frame by ID"""
        metadata = self._read_metadata()
        for m in metadata["masters"]:
            if m["id"] == master_id:
                return MasterCalibration(**m)
        return None

    def delete_master(self, master_id: str, delete_file: bool = False) -> bool:
        """
        Delete a master calibration frame.

        Args:
            master_id: Master frame ID
            delete_file: Whether to delete the FITS file

        Returns:
            True if deleted, False if not found
        """
        metadata = self._read_metadata()
        master = None

        # Find and remove master
        for i, m in enumerate(metadata["masters"]):
            if m["id"] == master_id:
                master = m
                metadata["masters"].pop(i)
                break

        if not master:
            return False

        # Delete file if requested
        if delete_file:
            session = self.get_session(master["session_id"])
            if session:
                file_path = self.masters_dir / session.name / master["filename"]
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted master file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting master file: {e}")
                        raise

        # Save metadata
        self._write_metadata(metadata)
        logger.info(f"Deleted master calibration: {master['filename']} (ID: {master_id})")
        return True
