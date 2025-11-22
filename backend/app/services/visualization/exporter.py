"""
Image export service
"""
import logging
from pathlib import Path
from typing import Dict, Any, Literal, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ImageExporter:
    """
    Exports FITS images to various formats.
    """

    @staticmethod
    def export(
        fits_path: str,
        output_path: str,
        format: Literal["fits", "tiff", "jpg", "png"] = "tiff",
        bit_depth: Literal[8, 16] = 16,
        stretch: bool = True,
        stretch_method: str = "asinh",
    ) -> Dict[str, Any]:
        """
        Export FITS image to specified format.

        Args:
            fits_path: Input FITS file
            output_path: Output file path
            format: Output format
            bit_depth: Bit depth for TIFF/PNG (8 or 16)
            stretch: Whether to apply stretch
            stretch_method: Stretch method if stretch=True

        Returns:
            Export information dictionary
        """
        try:
            from astropy.io import fits
            from PIL import Image
            from app.services.visualization.stretcher import HistogramStretcher

            logger.info(f"Exporting {fits_path} to {format}")

            # Load FITS data
            with fits.open(fits_path) as hdul:
                data = hdul[0].data.astype(float)
                header = hdul[0].header

            # Apply stretch if requested
            if stretch:
                data = HistogramStretcher.stretch(data, method=stretch_method)
            else:
                # Just normalize
                data = HistogramStretcher._normalize_input(data)

            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            if format == "fits":
                # Save as FITS
                output_hdu = fits.PrimaryHDU(data=data, header=header)
                output_hdu.writeto(str(output_path_obj), overwrite=True)

            elif format in ["tiff", "png"]:
                # Convert to appropriate bit depth
                if bit_depth == 16:
                    img_data = (data * 65535).astype(np.uint16)
                    mode = 'I;16'
                else:
                    img_data = (data * 255).astype(np.uint8)
                    mode = 'L'

                img = Image.fromarray(img_data, mode=mode)
                img.save(str(output_path_obj))

            elif format == "jpg":
                # JPG is always 8-bit
                img_data = (data * 255).astype(np.uint8)
                img = Image.fromarray(img_data, mode='L')
                img.save(str(output_path_obj), quality=95)

            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Exported to: {output_path_obj}")

            return {
                "input": fits_path,
                "output": str(output_path_obj),
                "format": format,
                "bit_depth": bit_depth if format in ["tiff", "png"] else 8,
                "stretched": stretch,
                "shape": data.shape,
            }

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astropy and Pillow required for export")
        except Exception as e:
            logger.error(f"Error exporting image: {e}")
            raise
