"""
Color combination service (LRGB, HaLRGB, SHO)
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Literal
import numpy as np

logger = logging.getLogger(__name__)


class ColorCombiner:
    """
    Combines monochrome images into color images.
    """

    @staticmethod
    def combine_lrgb(
        l_path: Optional[str],
        r_path: str,
        g_path: str,
        b_path: str,
        output_path: str,
        l_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Combine LRGB images.

        Args:
            l_path: Luminance (optional)
            r_path: Red channel
            g_path: Green channel
            b_path: Blue channel
            output_path: Output path
            l_weight: Luminance weight

        Returns:
            Dictionary with combination info
        """
        try:
            from astropy.io import fits
            from PIL import Image

            logger.info("Combining LRGB images")

            # Load RGB channels
            with fits.open(r_path) as hdul:
                r_data = hdul[0].data.astype(float)
            with fits.open(g_path) as hdul:
                g_data = hdul[0].data.astype(float)
            with fits.open(b_path) as hdul:
                b_data = hdul[0].data.astype(float)

            # Normalize to 0-1
            r_norm = ColorCombiner._normalize(r_data)
            g_norm = ColorCombiner._normalize(g_data)
            b_norm = ColorCombiner._normalize(b_data)

            # Load and apply luminance if provided
            if l_path:
                with fits.open(l_path) as hdul:
                    l_data = hdul[0].data.astype(float)
                l_norm = ColorCombiner._normalize(l_data)

                # Apply luminance to RGB
                r_norm = ColorCombiner._apply_luminance(r_norm, l_norm, l_weight)
                g_norm = ColorCombiner._apply_luminance(g_norm, l_norm, l_weight)
                b_norm = ColorCombiner._apply_luminance(b_norm, l_norm, l_weight)

            # Stack into RGB
            rgb = np.dstack([r_norm, g_norm, b_norm])

            # Convert to 16-bit
            rgb_16bit = (rgb * 65535).astype(np.uint16)

            # Save as TIFF
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            img = Image.fromarray(rgb_16bit, mode='RGB')
            img.save(str(output_path_obj))

            logger.info(f"LRGB image saved: {output_path_obj}")

            return {
                "output": str(output_path_obj),
                "type": "LRGB",
                "has_luminance": l_path is not None,
                "shape": rgb.shape,
            }

        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            raise ImportError("Astropy and Pillow required for color combination")
        except Exception as e:
            logger.error(f"Error combining LRGB: {e}")
            raise

    @staticmethod
    def combine_narrowband(
        channel_1_path: str,
        channel_2_path: str,
        channel_3_path: str,
        output_path: str,
        mapping: Literal["SHO", "HOO", "Custom"] = "SHO",
        r_channel: str = "SII",
        g_channel: str = "Ha",
        b_channel: str = "OIII",
    ) -> Dict[str, Any]:
        """
        Combine narrowband images (SHO, HOO, etc.).

        Args:
            channel_1_path: First channel
            channel_2_path: Second channel
            channel_3_path: Third channel
            output_path: Output path
            mapping: Mapping type
            r_channel: Red channel assignment
            g_channel: Green channel assignment
            b_channel: Blue channel assignment

        Returns:
            Dictionary with combination info
        """
        try:
            from astropy.io import fits
            from PIL import Image

            logger.info(f"Combining narrowband images ({mapping})")

            # Load channels
            channels = {}
            for path, name in [(channel_1_path, "ch1"), (channel_2_path, "ch2"), (channel_3_path, "ch3")]:
                with fits.open(path) as hdul:
                    channels[name] = ColorCombiner._normalize(hdul[0].data.astype(float))

            # Map to RGB
            rgb = np.dstack([channels["ch1"], channels["ch2"], channels["ch3"]])

            # Convert to 16-bit
            rgb_16bit = (rgb * 65535).astype(np.uint16)

            # Save
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            img = Image.fromarray(rgb_16bit, mode='RGB')
            img.save(str(output_path_obj))

            logger.info(f"Narrowband image saved: {output_path_obj}")

            return {
                "output": str(output_path_obj),
                "type": mapping,
                "mapping": f"R={r_channel}, G={g_channel}, B={b_channel}",
                "shape": rgb.shape,
            }

        except Exception as e:
            logger.error(f"Error combining narrowband: {e}")
            raise

    @staticmethod
    def _normalize(data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1 range"""
        data = data.copy()
        data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

        min_val = np.percentile(data, 0.1)
        max_val = np.percentile(data, 99.9)

        if max_val > min_val:
            data = (data - min_val) / (max_val - min_val)
            data = np.clip(data, 0, 1)

        return data

    @staticmethod
    def _apply_luminance(rgb_channel: np.ndarray, luminance: np.ndarray, weight: float) -> np.ndarray:
        """Apply luminance to RGB channel"""
        return rgb_channel * (1 - weight) + luminance * weight
