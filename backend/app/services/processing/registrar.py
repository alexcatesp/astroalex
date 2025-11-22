"""
Image registration/alignment service
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ImageRegistrar:
    """
    Aligns/registers images using star matching (Astroalign).
    """

    @staticmethod
    def register_frame(
        source_path: str,
        reference_path: str,
        output_path: str,
        detection_sigma: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Register a source image to a reference image.

        Args:
            source_path: Path to image to be aligned
            reference_path: Path to reference image
            output_path: Path for aligned output
            detection_sigma: Star detection threshold

        Returns:
            Dictionary with registration statistics
        """
        try:
            import astroalign as aa
            from astropy.io import fits
            from astropy.nddata import CCDData

            logger.info(f"Registering {Path(source_path).name} to reference")

            # Load images
            source = CCDData.read(source_path)
            reference = CCDData.read(reference_path)

            # Register (align) source to reference
            try:
                registered_data, footprint = aa.register(
                    source.data.astype(float),
                    reference.data.astype(float),
                    detection_sigma=detection_sigma
                )

                # Get transformation info
                transf, (source_list, ref_list) = aa.find_transform(
                    source.data.astype(float),
                    reference.data.astype(float),
                    detection_sigma=detection_sigma
                )

                num_matches = len(source_list)
                logger.info(f"Registration successful: {num_matches} control points")

            except aa.MaxIterError:
                logger.error("Registration failed: max iterations reached")
                raise ValueError("Could not find enough matching stars")
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                raise

            # Create output CCD
            registered = CCDData(
                data=registered_data,
                header=source.header,
                unit=source.unit
            )

            # Update header
            registered.header['ALIGNED'] = (True, 'Image has been aligned')
            registered.header['ALIGNREF'] = (Path(reference_path).name, 'Alignment reference')
            registered.header['NMATCHES'] = (num_matches, 'Number of control points')

            # Save
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            registered.write(str(output_path_obj), overwrite=True)

            logger.info(f"Registered frame saved: {output_path_obj}")

            return {
                "source": source_path,
                "reference": reference_path,
                "output": str(output_path_obj),
                "num_matches": num_matches,
                "success": True,
            }

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astroalign and Astropy required for registration")
        except Exception as e:
            logger.error(f"Error registering {source_path}: {e}")
            raise

    @staticmethod
    def register_batch(
        source_paths: List[str],
        reference_path: str,
        output_dir: str,
        detection_sigma: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        Register multiple images to a reference.

        Args:
            source_paths: List of images to align
            reference_path: Reference image path
            output_dir: Directory for aligned outputs
            detection_sigma: Star detection threshold

        Returns:
            List of registration results
        """
        output_dir_obj = Path(output_dir)
        output_dir_obj.mkdir(parents=True, exist_ok=True)

        results = []

        for source_path in source_paths:
            try:
                # Skip if source is the reference
                if Path(source_path).resolve() == Path(reference_path).resolve():
                    logger.info(f"Skipping reference image: {source_path}")
                    continue

                # Generate output filename
                input_name = Path(source_path).stem
                output_path = output_dir_obj / f"{input_name}_registered.fits"

                # Register
                result = ImageRegistrar.register_frame(
                    source_path=source_path,
                    reference_path=reference_path,
                    output_path=str(output_path),
                    detection_sigma=detection_sigma,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to register {source_path}: {e}")
                results.append({
                    "source": source_path,
                    "reference": reference_path,
                    "success": False,
                    "error": str(e),
                })

        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Batch registration complete: {successful}/{len(source_paths)} successful")

        return results

    @staticmethod
    def select_reference(file_paths: List[str], quality_metrics: Optional[List[Dict]] = None) -> str:
        """
        Select the best reference image from a list.

        If quality metrics are provided, selects the image with the best (lowest) FWHM.
        Otherwise, returns the first image.

        Args:
            file_paths: List of image paths
            quality_metrics: Optional quality metrics from QualityAnalyzer

        Returns:
            Path to selected reference image
        """
        if not file_paths:
            raise ValueError("No files provided for reference selection")

        if quality_metrics:
            # Select image with best (lowest) median FWHM
            valid_metrics = [m for m in quality_metrics if m.get("fwhm_median") is not None]

            if valid_metrics:
                best = min(valid_metrics, key=lambda m: m["fwhm_median"])
                reference = best["file"]
                logger.info(
                    f"Selected reference: {Path(reference).name} "
                    f"(FWHM={best['fwhm_median']:.2f}px)"
                )
                return reference

        # Default: use first image
        reference = file_paths[0]
        logger.info(f"Selected reference (default): {Path(reference).name}")
        return reference
