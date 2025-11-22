"""
Calibration frame combination using CCDProc
"""
import logging
from pathlib import Path
from typing import List, Optional, Literal
import numpy as np

logger = logging.getLogger(__name__)


class CalibrationCombiner:
    """
    Combines calibration frames using CCDProc for scientifically valid results.
    """

    @staticmethod
    def combine_frames(
        file_paths: List[str],
        output_path: str,
        method: Literal["average", "median"] = "median",
        rejection: Optional[Literal["minmax", "sigma_clip"]] = "sigma_clip",
        sigma_clip_low_thresh: float = 3.0,
        sigma_clip_high_thresh: float = 3.0,
        minmax_min: int = 1,
        minmax_max: int = 1,
    ) -> dict:
        """
        Combine multiple calibration frames into a master frame.

        Args:
            file_paths: List of paths to FITS files to combine
            output_path: Path where the master frame will be saved
            method: Combination method ('average' or 'median')
            rejection: Rejection method ('minmax', 'sigma_clip', or None)
            sigma_clip_low_thresh: Sigma clipping low threshold
            sigma_clip_high_thresh: Sigma clipping high threshold
            minmax_min: Number of minimum values to reject
            minmax_max: Number of maximum values to reject

        Returns:
            Dictionary with combination statistics

        Raises:
            ImportError: If astropy/ccdproc not installed
            ValueError: If invalid parameters or no files provided
            IOError: If file operations fail
        """
        if not file_paths:
            raise ValueError("No files provided for combination")

        try:
            from astropy.io import fits
            from astropy.nddata import CCDData
            import astropy.units as u
            from ccdproc import combine, Combiner

            logger.info(f"Combining {len(file_paths)} frames using {method} with {rejection or 'no'} rejection")

            # Load all frames
            ccd_list = []
            for file_path in file_paths:
                try:
                    ccd = CCDData.read(file_path, unit='adu')
                    ccd_list.append(ccd)
                    logger.debug(f"Loaded: {file_path}")
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
                    continue

            if not ccd_list:
                raise ValueError("No valid frames could be loaded")

            # Create combiner
            combiner = Combiner(ccd_list)

            # Apply rejection method
            if rejection == "sigma_clip":
                combiner.sigma_clipping(
                    low_thresh=sigma_clip_low_thresh,
                    high_thresh=sigma_clip_high_thresh,
                    func=np.ma.median
                )
                logger.debug(f"Applied sigma clipping: low={sigma_clip_low_thresh}, high={sigma_clip_high_thresh}")

            elif rejection == "minmax":
                combiner.minmax_clipping(min_clip=minmax_min, max_clip=minmax_max)
                logger.debug(f"Applied minmax clipping: min={minmax_min}, max={minmax_max}")

            # Combine frames
            if method == "average":
                master = combiner.average_combine()
            elif method == "median":
                master = combiner.median_combine()
            else:
                raise ValueError(f"Invalid combination method: {method}")

            # Save master frame
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            master.write(str(output_path_obj), overwrite=True)
            logger.info(f"Master frame saved to: {output_path_obj}")

            # Gather statistics
            stats = {
                "num_frames": len(ccd_list),
                "method": method,
                "rejection": rejection,
                "output_path": str(output_path_obj),
                "mean": float(np.mean(master.data)),
                "median": float(np.median(master.data)),
                "std": float(np.std(master.data)),
                "min": float(np.min(master.data)),
                "max": float(np.max(master.data)),
            }

            return stats

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError(
                "Astropy and CCDProc are required for calibration frame combination. "
                "Install with: pip install astropy ccdproc"
            )
        except Exception as e:
            logger.error(f"Error combining frames: {e}")
            raise

    @staticmethod
    def validate_frames(file_paths: List[str]) -> dict:
        """
        Validate calibration frames before combination.

        Args:
            file_paths: List of FITS file paths

        Returns:
            Dictionary with validation results
        """
        try:
            from astropy.io import fits

            valid_files = []
            invalid_files = []
            dimensions = set()

            for file_path in file_paths:
                try:
                    with fits.open(file_path) as hdul:
                        data = hdul[0].data
                        if data is not None:
                            dimensions.add(data.shape)
                            valid_files.append(file_path)
                        else:
                            invalid_files.append((file_path, "No data in primary HDU"))
                except Exception as e:
                    invalid_files.append((file_path, str(e)))

            # Check if all frames have same dimensions
            dimension_mismatch = len(dimensions) > 1

            return {
                "valid_count": len(valid_files),
                "invalid_count": len(invalid_files),
                "valid_files": valid_files,
                "invalid_files": invalid_files,
                "dimensions": list(dimensions),
                "dimension_mismatch": dimension_mismatch,
            }

        except ImportError:
            raise ImportError("Astropy is required for frame validation")

    @staticmethod
    def get_frame_info(file_path: str) -> dict:
        """
        Get information about a single FITS frame.

        Args:
            file_path: Path to FITS file

        Returns:
            Dictionary with frame information
        """
        try:
            from astropy.io import fits

            with fits.open(file_path) as hdul:
                header = hdul[0].header
                data = hdul[0].data

                info = {
                    "filename": Path(file_path).name,
                    "path": file_path,
                    "dimensions": data.shape if data is not None else None,
                    "dtype": str(data.dtype) if data is not None else None,
                    "mean": float(np.mean(data)) if data is not None else None,
                    "median": float(np.median(data)) if data is not None else None,
                    "std": float(np.std(data)) if data is not None else None,
                    "min": float(np.min(data)) if data is not None else None,
                    "max": float(np.max(data)) if data is not None else None,
                }

                # Add relevant header keywords
                for key in ['EXPTIME', 'GAIN', 'INSTRUME', 'CCD-TEMP', 'IMAGETYP']:
                    if key in header:
                        info[key.lower()] = header[key]

                return info

        except Exception as e:
            logger.error(f"Error getting frame info for {file_path}: {e}")
            return {"filename": Path(file_path).name, "error": str(e)}
