"""
FITS file metadata parser supporting multiple formats
"""
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataParser:
    """
    Parser for extracting metadata from FITS filenames and headers.
    Supports ASIAIR format and generic FITS header parsing.
    """

    # ASIAIR filename pattern:
    # Example: M31_Andromeda_Galaxy_Light_Filter_L_300s_gain100_2025-10-26_001.fit
    ASIAIR_PATTERN = re.compile(
        r"^(?P<object>.+?)_(?P<type>Light|Dark|Bias|Flat)"
        r"(?:_Filter_(?P<filter>[A-Za-z0-9]+))?"
        r"(?:_(?P<exposure>\d+)s)?"
        r"(?:_gain(?P<gain>\d+))?"
        r"(?:_(?P<date>\d{4}-\d{2}-\d{2}))?"
        r"(?:_(?P<sequence>\d+))?"
        r"\.(?:fit|fits|FIT|FITS)$"
    )

    # Alternative simpler pattern for other naming conventions
    # Example: M31_300s_L_001.fits
    SIMPLE_PATTERN = re.compile(
        r"^(?P<object>[^_]+)"
        r"(?:_(?P<exposure>\d+)s)?"
        r"(?:_(?P<filter>[A-Za-z0-9]+))?"
        r"(?:_(?P<sequence>\d+))?"
        r"\.(?:fit|fits|FIT|FITS)$"
    )

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, Any]:
        """
        Parse metadata from a FITS filename.

        Args:
            filename: Name of the FITS file

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "filename": filename,
            "image_type": None,
            "object_name": None,
            "filter": None,
            "exposure_time": None,
            "gain": None,
            "date": None,
            "sequence": None,
        }

        # Try ASIAIR pattern first
        match = MetadataParser.ASIAIR_PATTERN.match(filename)
        if match:
            logger.debug(f"Matched ASIAIR pattern for: {filename}")
            data = match.groupdict()

            metadata["image_type"] = data.get("type")
            metadata["object_name"] = data.get("object", "").replace("_", " ")
            metadata["filter"] = data.get("filter")
            metadata["exposure_time"] = float(data["exposure"]) if data.get("exposure") else None
            metadata["gain"] = int(data["gain"]) if data.get("gain") else None
            metadata["date"] = data.get("date")
            metadata["sequence"] = data.get("sequence")

            return metadata

        # Try simple pattern
        match = MetadataParser.SIMPLE_PATTERN.match(filename)
        if match:
            logger.debug(f"Matched simple pattern for: {filename}")
            data = match.groupdict()

            metadata["object_name"] = data.get("object", "").replace("_", " ")
            metadata["filter"] = data.get("filter")
            metadata["exposure_time"] = float(data["exposure"]) if data.get("exposure") else None
            metadata["sequence"] = data.get("sequence")

            # For simple pattern, try to infer type from directory or default to Light
            metadata["image_type"] = "Light"

            return metadata

        logger.warning(f"Could not parse filename: {filename}")
        return metadata

    @staticmethod
    def parse_fits_header(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from FITS file headers using Astropy.

        Args:
            file_path: Path to the FITS file

        Returns:
            Dictionary with header metadata
        """
        try:
            from astropy.io import fits

            metadata = {}

            with fits.open(file_path) as hdul:
                header = hdul[0].header

                # Common FITS keywords
                metadata["object_name"] = header.get("OBJECT", None)
                metadata["exposure_time"] = header.get("EXPTIME", header.get("EXPOSURE", None))
                metadata["gain"] = header.get("GAIN", None)
                metadata["filter"] = header.get("FILTER", None)
                metadata["date"] = header.get("DATE-OBS", None)
                metadata["temperature"] = header.get("CCD-TEMP", header.get("SET-TEMP", None))
                metadata["binning"] = header.get("XBINNING", None)
                metadata["instrument"] = header.get("INSTRUME", None)

                # Image type (if available)
                image_type = header.get("IMAGETYP", None)
                if image_type:
                    # Normalize common variations
                    image_type = image_type.strip().lower()
                    if "light" in image_type or "science" in image_type:
                        metadata["image_type"] = "Light"
                    elif "dark" in image_type:
                        metadata["image_type"] = "Dark"
                    elif "bias" in image_type:
                        metadata["image_type"] = "Bias"
                    elif "flat" in image_type:
                        metadata["image_type"] = "Flat"

                logger.debug(f"Extracted FITS header metadata from: {file_path}")
                return metadata

        except ImportError:
            logger.error("Astropy not installed, cannot read FITS headers")
            return {}
        except Exception as e:
            logger.error(f"Error reading FITS header from {file_path}: {e}")
            return {}

    @staticmethod
    def merge_metadata(filename_meta: Dict[str, Any], header_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge metadata from filename and FITS header, preferring header values.

        Args:
            filename_meta: Metadata extracted from filename
            header_meta: Metadata extracted from FITS header

        Returns:
            Merged metadata dictionary
        """
        merged = filename_meta.copy()

        # Header values take precedence over filename
        for key, value in header_meta.items():
            if value is not None:
                merged[key] = value

        return merged

    @staticmethod
    def extract_metadata(file_path: str, read_header: bool = True) -> Dict[str, Any]:
        """
        Extract complete metadata from a FITS file.

        Args:
            file_path: Path to the FITS file
            read_header: Whether to read FITS header (requires Astropy)

        Returns:
            Complete metadata dictionary
        """
        path = Path(file_path)
        filename = path.name

        # Parse filename
        filename_meta = MetadataParser.parse_filename(filename)

        # If requested, read header and merge
        if read_header:
            header_meta = MetadataParser.parse_fits_header(file_path)
            return MetadataParser.merge_metadata(filename_meta, header_meta)

        return filename_meta

    @staticmethod
    def infer_image_type_from_path(file_path: str) -> Optional[str]:
        """
        Infer image type from directory path.

        Args:
            file_path: Full path to the file

        Returns:
            Inferred image type or None
        """
        path_lower = file_path.lower()

        if "/darks/" in path_lower or "\\darks\\" in path_lower:
            return "Dark"
        elif "/flats/" in path_lower or "\\flats\\" in path_lower:
            return "Flat"
        elif "/bias/" in path_lower or "\\bias\\" in path_lower:
            return "Bias"
        elif "/science/" in path_lower or "\\science\\" in path_lower:
            return "Light"

        return None
