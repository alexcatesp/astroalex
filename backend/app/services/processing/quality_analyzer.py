"""
Image quality analysis service
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """
    Analyzes image quality metrics (FWHM, eccentricity, star count).
    """

    @staticmethod
    def analyze_frame(file_path: str, threshold_sigma: float = 3.0) -> Dict[str, Any]:
        """
        Analyze quality metrics for a single frame.

        Args:
            file_path: Path to FITS file
            threshold_sigma: Detection threshold in sigma above background

        Returns:
            Dictionary with quality metrics
        """
        try:
            from astropy.io import fits
            from photutils.detection import DAOStarFinder
            from astropy.stats import sigma_clipped_stats

            logger.debug(f"Analyzing quality: {file_path}")

            # Load image data
            with fits.open(file_path) as hdul:
                data = hdul[0].data.astype(float)

            # Calculate background statistics
            mean, median, std = sigma_clipped_stats(data, sigma=3.0)

            # Detect sources
            daofind = DAOStarFinder(fwhm=3.0, threshold=threshold_sigma * std)
            sources = daofind(data - median)

            if sources is None or len(sources) == 0:
                logger.warning(f"No sources detected in {file_path}")
                return {
                    "file": file_path,
                    "star_count": 0,
                    "fwhm_mean": None,
                    "fwhm_median": None,
                    "fwhm_std": None,
                    "roundness_mean": None,
                    "sharpness_mean": None,
                    "background_mean": float(mean),
                    "background_median": float(median),
                    "background_std": float(std),
                }

            # Calculate quality metrics
            fwhm_values = sources['fwhm']
            roundness_values = sources['roundness1']
            sharpness_values = sources['sharpness']

            metrics = {
                "file": file_path,
                "star_count": len(sources),
                "fwhm_mean": float(np.mean(fwhm_values)),
                "fwhm_median": float(np.median(fwhm_values)),
                "fwhm_std": float(np.std(fwhm_values)),
                "roundness_mean": float(np.mean(roundness_values)),
                "sharpness_mean": float(np.mean(sharpness_values)),
                "background_mean": float(mean),
                "background_median": float(median),
                "background_std": float(std),
            }

            logger.debug(
                f"Quality metrics: {metrics['star_count']} stars, "
                f"FWHM={metrics['fwhm_median']:.2f}px"
            )

            return metrics

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astropy and Photutils required for quality analysis")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                "file": file_path,
                "error": str(e),
                "star_count": 0,
            }

    @staticmethod
    def analyze_batch(
        file_paths: List[str],
        threshold_sigma: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Analyze quality metrics for multiple frames.

        Args:
            file_paths: List of FITS file paths
            threshold_sigma: Detection threshold

        Returns:
            List of quality metrics dictionaries
        """
        results = []

        for file_path in file_paths:
            try:
                metrics = QualityAnalyzer.analyze_frame(file_path, threshold_sigma)
                results.append(metrics)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "error": str(e),
                    "star_count": 0,
                })

        logger.info(f"Analyzed {len(results)} frames")
        return results

    @staticmethod
    def filter_by_quality(
        metrics_list: List[Dict[str, Any]],
        min_stars: Optional[int] = None,
        max_fwhm: Optional[float] = None,
        min_fwhm: Optional[float] = None,
    ) -> List[str]:
        """
        Filter frames based on quality criteria.

        Args:
            metrics_list: List of quality metrics
            min_stars: Minimum star count
            max_fwhm: Maximum allowed FWHM (reject if worse)
            min_fwhm: Minimum allowed FWHM

        Returns:
            List of file paths that pass quality criteria
        """
        passed = []

        for metrics in metrics_list:
            if "error" in metrics:
                continue

            # Check star count
            if min_stars and metrics.get("star_count", 0) < min_stars:
                logger.debug(f"Rejected {metrics['file']}: too few stars")
                continue

            # Check FWHM
            fwhm = metrics.get("fwhm_median")
            if fwhm is None:
                continue

            if max_fwhm and fwhm > max_fwhm:
                logger.debug(f"Rejected {metrics['file']}: FWHM {fwhm:.2f} > {max_fwhm}")
                continue

            if min_fwhm and fwhm < min_fwhm:
                logger.debug(f"Rejected {metrics['file']}: FWHM {fwhm:.2f} < {min_fwhm}")
                continue

            passed.append(metrics["file"])

        logger.info(f"Quality filter: {len(passed)}/{len(metrics_list)} frames passed")
        return passed
