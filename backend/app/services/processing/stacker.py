"""
Image stacking/integration service
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
import numpy as np

logger = logging.getLogger(__name__)


class ImageStacker:
    """
    Stacks/integrates multiple aligned images.
    """

    @staticmethod
    def stack_images(
        file_paths: List[str],
        output_path: str,
        method: Literal["median", "average", "sum"] = "median",
        rejection: Optional[Literal["sigma_clip", "minmax"]] = "sigma_clip",
        sigma_low: float = 3.0,
        sigma_high: float = 3.0,
        minmax_min: int = 1,
        minmax_max: int = 1,
    ) -> Dict[str, Any]:
        """
        Stack multiple images into a single integrated image.

        Args:
            file_paths: List of aligned FITS images
            output_path: Path for stacked output
            method: Stacking method
            rejection: Rejection method
            sigma_low: Low sigma threshold for sigma clipping
            sigma_high: High sigma threshold for sigma clipping
            minmax_min: Number of min values to reject
            minmax_max: Number of max values to reject

        Returns:
            Dictionary with stacking statistics
        """
        try:
            from astropy.io import fits
            from astropy.nddata import CCDData
            from ccdproc import Combiner
            import astropy.units as u

            if not file_paths:
                raise ValueError("No files provided for stacking")

            logger.info(f"Stacking {len(file_paths)} images using {method}")

            # Load all images
            ccd_list = []
            for file_path in file_paths:
                try:
                    ccd = CCDData.read(file_path, unit='adu')
                    ccd_list.append(ccd)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue

            if not ccd_list:
                raise ValueError("No valid images could be loaded")

            # Create combiner
            combiner = Combiner(ccd_list)

            # Apply rejection
            if rejection == "sigma_clip":
                combiner.sigma_clipping(
                    low_thresh=sigma_low,
                    high_thresh=sigma_high,
                    func=np.ma.median
                )
                logger.debug(f"Applied sigma clipping: low={sigma_low}, high={sigma_high}")

            elif rejection == "minmax":
                combiner.minmax_clipping(min_clip=minmax_min, max_clip=minmax_max)
                logger.debug(f"Applied minmax clipping: min={minmax_min}, max={minmax_max}")

            # Stack images
            if method == "median":
                stacked = combiner.median_combine()
            elif method == "average":
                stacked = combiner.average_combine()
            elif method == "sum":
                # Sum is not directly available in CCDProc, use numpy
                data_stack = np.array([ccd.data for ccd in ccd_list])
                stacked_data = np.sum(data_stack, axis=0)
                stacked = CCDData(data=stacked_data, unit=ccd_list[0].unit, header=ccd_list[0].header)
            else:
                raise ValueError(f"Invalid stacking method: {method}")

            # Update header with stacking info
            stacked.header['STACKED'] = (True, 'Image is a stack')
            stacked.header['NSTACKED'] = (len(ccd_list), 'Number of images stacked')
            stacked.header['STKMETOD'] = (method, 'Stacking method used')
            if rejection:
                stacked.header['STKREJCT'] = (rejection, 'Rejection method used')

            # Save stacked image
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            stacked.write(str(output_path_obj), overwrite=True)

            logger.info(f"Stacked image saved: {output_path_obj}")

            # Calculate statistics
            stats = {
                "output": str(output_path_obj),
                "num_images": len(ccd_list),
                "method": method,
                "rejection": rejection,
                "mean": float(np.mean(stacked.data)),
                "median": float(np.median(stacked.data)),
                "std": float(np.std(stacked.data)),
                "min": float(np.min(stacked.data)),
                "max": float(np.max(stacked.data)),
            }

            return stats

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astropy and CCDProc required for stacking")
        except Exception as e:
            logger.error(f"Error stacking images: {e}")
            raise

    @staticmethod
    def stack_by_filter(
        file_paths: List[str],
        output_dir: str,
        method: Literal["median", "average", "sum"] = "median",
        rejection: Optional[Literal["sigma_clip", "minmax"]] = "sigma_clip",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Stack images grouped by filter.

        Args:
            file_paths: List of FITS image paths
            output_dir: Directory for stacked outputs
            method: Stacking method
            rejection: Rejection method
            **kwargs: Additional parameters for stack_images

        Returns:
            Dictionary mapping filter names to stack results
        """
        from astropy.io import fits

        # Group files by filter
        filter_groups = {}

        for file_path in file_paths:
            try:
                with fits.open(file_path) as hdul:
                    filter_name = hdul[0].header.get('FILTER', 'UNKNOWN')

                if filter_name not in filter_groups:
                    filter_groups[filter_name] = []

                filter_groups[filter_name].append(file_path)

            except Exception as e:
                logger.warning(f"Failed to read filter from {file_path}: {e}")
                continue

        # Stack each filter group
        results = {}

        for filter_name, group_files in filter_groups.items():
            try:
                output_path = Path(output_dir) / f"stacked_{filter_name}.fits"

                stats = ImageStacker.stack_images(
                    file_paths=group_files,
                    output_path=str(output_path),
                    method=method,
                    rejection=rejection,
                    **kwargs
                )

                results[filter_name] = {
                    "success": True,
                    "stats": stats,
                    "num_files": len(group_files),
                }

                logger.info(f"Stacked {filter_name}: {len(group_files)} images")

            except Exception as e:
                logger.error(f"Failed to stack filter {filter_name}: {e}")
                results[filter_name] = {
                    "success": False,
                    "error": str(e),
                    "num_files": len(group_files),
                }

        return results
