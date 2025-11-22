"""
Histogram stretching service
"""
import logging
from typing import Dict, Any, Literal
import numpy as np

logger = logging.getLogger(__name__)


class HistogramStretcher:
    """
    Non-destructive histogram stretching for visualization.
    """

    @staticmethod
    def stretch(
        data: np.ndarray,
        method: Literal["linear", "asinh", "log", "sqrt"] = "asinh",
        shadow: float = 0.0,
        midtone: float = 0.5,
        highlight: float = 1.0,
    ) -> np.ndarray:
        """
        Apply histogram stretch to data.

        Args:
            data: Input data array
            method: Stretching method
            shadow: Shadow point (0-1)
            midtone: Midtone point (0-1)
            highlight: Highlight point (0-1)

        Returns:
            Stretched data (0-1 range)
        """
        # Normalize input
        data_norm = HistogramStretcher._normalize_input(data)

        # Apply stretch
        if method == "linear":
            stretched = HistogramStretcher._linear_stretch(data_norm, shadow, highlight)
        elif method == "asinh":
            stretched = HistogramStretcher._asinh_stretch(data_norm, midtone)
        elif method == "log":
            stretched = HistogramStretcher._log_stretch(data_norm)
        elif method == "sqrt":
            stretched = HistogramStretcher._sqrt_stretch(data_norm)
        else:
            raise ValueError(f"Unknown stretch method: {method}")

        return np.clip(stretched, 0, 1)

    @staticmethod
    def _normalize_input(data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1"""
        data = np.nan_to_num(data, nan=0.0)
        min_val = np.percentile(data, 0.1)
        max_val = np.percentile(data, 99.9)

        if max_val > min_val:
            return (data - min_val) / (max_val - min_val)
        return data

    @staticmethod
    def _linear_stretch(data: np.ndarray, shadow: float, highlight: float) -> np.ndarray:
        """Linear stretch"""
        return (data - shadow) / (highlight - shadow)

    @staticmethod
    def _asinh_stretch(data: np.ndarray, midtone: float) -> np.ndarray:
        """Asinh (arcsinh) stretch - good for HDR"""
        beta = midtone
        return np.arcsinh(data / beta) / np.arcsinh(1.0 / beta)

    @staticmethod
    def _log_stretch(data: np.ndarray) -> np.ndarray:
        """Logarithmic stretch"""
        return np.log1p(data * 999) / np.log1p(999)

    @staticmethod
    def _sqrt_stretch(data: np.ndarray) -> np.ndarray:
        """Square root stretch"""
        return np.sqrt(data)

    @staticmethod
    def auto_stretch(data: np.ndarray) -> Dict[str, Any]:
        """
        Automatically determine optimal stretch parameters.

        Args:
            data: Input data

        Returns:
            Dictionary with recommended parameters
        """
        # Calculate statistics
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        # Determine shadow and highlight
        shadow = max(0, median - 3 * mad)
        highlight = min(np.max(data), median + 10 * mad)

        # Determine midtone
        midtone = (highlight - shadow) * 0.25 + shadow

        return {
            "shadow": float(shadow),
            "midtone": float(midtone),
            "highlight": float(highlight),
            "median": float(median),
            "mad": float(mad),
        }
