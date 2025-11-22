"""
Science frame calibration service
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class ScienceFrameCalibrator:
    """
    Applies master calibration frames to science frames.
    """

    @staticmethod
    def calibrate_frame(
        science_path: str,
        output_path: str,
        master_bias_path: Optional[str] = None,
        master_dark_path: Optional[str] = None,
        master_flat_path: Optional[str] = None,
        dark_scale: bool = True,
    ) -> Dict[str, Any]:
        """
        Calibrate a science frame using master calibration frames.

        Args:
            science_path: Path to science frame
            output_path: Path for calibrated output
            master_bias_path: Path to master bias (optional)
            master_dark_path: Path to master dark (optional)
            master_flat_path: Path to master flat (optional)
            dark_scale: Whether to scale dark by exposure time

        Returns:
            Dictionary with calibration statistics

        Raises:
            ImportError: If required libraries not available
            IOError: If file operations fail
        """
        try:
            from astropy.io import fits
            from astropy.nddata import CCDData
            import astropy.units as u
            from ccdproc import subtract_bias, subtract_dark, flat_correct

            logger.info(f"Calibrating: {science_path}")

            # Load science frame
            science = CCDData.read(science_path, unit='adu')
            calibrated = science.copy()

            steps_applied = []

            # Subtract bias
            if master_bias_path:
                master_bias = CCDData.read(master_bias_path, unit='adu')
                calibrated = subtract_bias(calibrated, master_bias)
                steps_applied.append("bias_subtraction")
                logger.debug("Applied bias subtraction")

            # Subtract dark
            if master_dark_path:
                master_dark = CCDData.read(master_dark_path, unit='adu')

                if dark_scale:
                    # Scale dark by exposure time ratio
                    science_exptime = science.header.get('EXPTIME', 1.0)
                    dark_exptime = master_dark.header.get('EXPTIME', 1.0)

                    if science_exptime and dark_exptime:
                        scale_factor = science_exptime / dark_exptime
                        calibrated = subtract_dark(
                            calibrated, master_dark,
                            dark_exposure=dark_exptime * u.second,
                            data_exposure=science_exptime * u.second,
                            scale=True
                        )
                        steps_applied.append(f"dark_subtraction_scaled_{scale_factor:.2f}x")
                        logger.debug(f"Applied dark subtraction (scaled {scale_factor:.2f}x)")
                    else:
                        calibrated = subtract_dark(
                            calibrated, master_dark,
                            scale=False
                        )
                        steps_applied.append("dark_subtraction_unscaled")
                        logger.debug("Applied dark subtraction (unscaled)")
                else:
                    calibrated = subtract_dark(calibrated, master_dark, scale=False)
                    steps_applied.append("dark_subtraction_unscaled")
                    logger.debug("Applied dark subtraction (unscaled)")

            # Flat field correction
            if master_flat_path:
                master_flat = CCDData.read(master_flat_path, unit='adu')
                calibrated = flat_correct(calibrated, master_flat)
                steps_applied.append("flat_correction")
                logger.debug("Applied flat correction")

            # Save calibrated frame
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Add calibration history to header
            calibrated.header['CALIBRTD'] = (True, 'Frame has been calibrated')
            calibrated.header['CALSTEPS'] = (', '.join(steps_applied), 'Calibration steps applied')

            if master_bias_path:
                calibrated.header['MBIAS'] = (Path(master_bias_path).name, 'Master bias used')
            if master_dark_path:
                calibrated.header['MDARK'] = (Path(master_dark_path).name, 'Master dark used')
            if master_flat_path:
                calibrated.header['MFLAT'] = (Path(master_flat_path).name, 'Master flat used')

            calibrated.write(str(output_path_obj), overwrite=True)
            logger.info(f"Calibrated frame saved: {output_path_obj}")

            # Calculate statistics
            stats = {
                "input": science_path,
                "output": str(output_path_obj),
                "steps_applied": steps_applied,
                "master_bias": master_bias_path,
                "master_dark": master_dark_path,
                "master_flat": master_flat_path,
                "mean": float(np.mean(calibrated.data)),
                "median": float(np.median(calibrated.data)),
                "std": float(np.std(calibrated.data)),
            }

            return stats

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astropy and CCDProc required for calibration")
        except Exception as e:
            logger.error(f"Error calibrating frame: {e}")
            raise

    @staticmethod
    def calibrate_batch(
        science_paths: List[str],
        output_dir: str,
        master_bias_path: Optional[str] = None,
        master_dark_path: Optional[str] = None,
        master_flat_path: Optional[str] = None,
        dark_scale: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Calibrate multiple science frames.

        Args:
            science_paths: List of science frame paths
            output_dir: Directory for calibrated outputs
            master_bias_path: Path to master bias
            master_dark_path: Path to master dark
            master_flat_path: Path to master flat
            dark_scale: Whether to scale dark

        Returns:
            List of calibration statistics for each frame
        """
        output_dir_obj = Path(output_dir)
        output_dir_obj.mkdir(parents=True, exist_ok=True)

        results = []

        for science_path in science_paths:
            try:
                # Generate output filename
                input_name = Path(science_path).stem
                output_path = output_dir_obj / f"{input_name}_calibrated.fits"

                # Calibrate
                stats = ScienceFrameCalibrator.calibrate_frame(
                    science_path=science_path,
                    output_path=str(output_path),
                    master_bias_path=master_bias_path,
                    master_dark_path=master_dark_path,
                    master_flat_path=master_flat_path,
                    dark_scale=dark_scale,
                )

                results.append({"success": True, "stats": stats})

            except Exception as e:
                logger.error(f"Failed to calibrate {science_path}: {e}")
                results.append({
                    "success": False,
                    "input": science_path,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Batch calibration complete: {successful}/{len(science_paths)} successful")

        return results
