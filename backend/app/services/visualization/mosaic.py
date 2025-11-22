"""
Mosaic assembly service
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class MosaicAssembler:
    """
    Assembles mosaic panels using WCS information.
    """

    @staticmethod
    def assemble_mosaic(
        panel_paths: List[str],
        output_path: str,
        background_match: bool = True,
        projection: str = "TAN",
    ) -> Dict[str, Any]:
        """
        Assemble multiple panels into a mosaic.

        Args:
            panel_paths: List of panel FITS files
            output_path: Path for mosaic output
            background_match: Whether to match backgrounds
            projection: WCS projection type

        Returns:
            Dictionary with mosaic statistics
        """
        try:
            from reproject.mosaicking import find_optimal_celestial_wcs, reproject_and_coadd
            from reproject import reproject_interp
            from astropy.io import fits
            from astropy.nddata import CCDData
            import astropy.units as u

            logger.info(f"Assembling mosaic from {len(panel_paths)} panels")

            # Load all panels
            hdus = [fits.open(path)[0] for path in panel_paths]

            # Find optimal WCS for the mosaic
            wcs_out, shape_out = find_optimal_celestial_wcs(hdus)

            logger.debug(f"Optimal mosaic shape: {shape_out}")

            # Reproject and coadd
            array, footprint = reproject_and_coadd(
                hdus,
                wcs_out,
                shape_out=shape_out,
                reproject_function=reproject_interp,
            )

            # Background matching if requested
            if background_match:
                logger.debug("Applying background matching")
                # Simple background matching by scaling
                for i, hdu in enumerate(hdus):
                    data = hdu.data
                    if data is not None:
                        bg_level = np.median(data)
                        if bg_level > 0:
                            array = array * (1.0 / bg_level)

            # Create output HDU
            header = wcs_out.to_header()
            header['MOSAIC'] = (True, 'Image is a mosaic')
            header['NPANELS'] = (len(panel_paths), 'Number of panels')
            header['BGMATCH'] = (background_match, 'Background matching applied')

            output_hdu = fits.PrimaryHDU(data=array, header=header)

            # Save mosaic
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            output_hdu.writeto(str(output_path_obj), overwrite=True)

            # Close input HDUs
            for hdu in hdus:
                hdu.close()

            logger.info(f"Mosaic saved: {output_path_obj}")

            return {
                "output": str(output_path_obj),
                "num_panels": len(panel_paths),
                "shape": shape_out,
                "background_matched": background_match,
                "mean": float(np.nanmean(array)),
                "median": float(np.nanmedian(array)),
            }

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Reproject and Astropy required for mosaic assembly")
        except Exception as e:
            logger.error(f"Error assembling mosaic: {e}")
            raise
