"""
Service for camera characterization: calculate Read Noise, Gain, and Full Well Capacity
"""
from pathlib import Path
from typing import List, Tuple
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats

from app.models.camera import CharacterizationInput, CharacterizationResult
from app.models.session import SensorProfile


class CameraCharacterizer:
    """
    Service for characterizing camera sensors

    Calculates:
    - Read Noise (electrons)
    - Gain (e-/ADU)
    - Full Well Capacity (electrons)
    """

    def characterize(self, input_data: CharacterizationInput) -> CharacterizationResult:
        """
        Perform complete camera characterization

        Method:
        1. Read Noise: Calculate from two bias frames
           RN = (std(bias1 - bias2) / sqrt(2)) * gain
        2. Gain: Calculate from two flat frames
           gain = (mean²) / (var(flat1 - flat2) / 2)
        3. Full Well Capacity: FWC = gain * (max_ADU - bias_level)

        Args:
            input_data: Characterization input with bias and flat frames

        Returns:
            CharacterizationResult with all measurements
        """
        warnings = []

        # Load bias frames
        bias1_data = self._load_fits(input_data.bias_frames[0])
        bias2_data = self._load_fits(input_data.bias_frames[1])

        # Load flat frames
        flat1_data = self._load_fits(input_data.flat_frames[0])
        flat2_data = self._load_fits(input_data.flat_frames[1])

        # Calculate bias statistics
        bias1_mean, bias1_median, bias1_std = sigma_clipped_stats(bias1_data, sigma=3.0)
        bias2_mean, bias2_median, bias2_std = sigma_clipped_stats(bias2_data, sigma=3.0)
        bias_level = (bias1_mean + bias2_mean) / 2

        # Calculate flat statistics
        flat1_mean, flat1_median, flat1_std = sigma_clipped_stats(flat1_data, sigma=3.0)
        flat2_mean, flat2_median, flat2_std = sigma_clipped_stats(flat2_data, sigma=3.0)

        # Check flat levels (should be around 40-60% of max)
        flat_level_percent = (flat1_mean / 65535) * 100  # Assuming 16-bit
        if flat_level_percent < 30 or flat_level_percent > 70:
            warnings.append(f"Flats at {flat_level_percent:.1f}% of max. Ideal range: 40-60%")

        # Calculate GAIN from flats (photon transfer method)
        # Gain = mean² / variance
        flat_diff = flat1_data.astype(float) - flat2_data.astype(float)
        flat_diff_var = np.var(flat_diff) / 2  # Divide by 2 (variance of difference)
        flat_mean = (flat1_mean + flat2_mean) / 2 - bias_level  # Subtract bias

        if flat_diff_var > 0 and flat_mean > 0:
            gain = (flat_mean ** 2) / flat_diff_var
        else:
            gain = 1.0
            warnings.append("Could not calculate gain reliably. Using default: 1.0")

        # Calculate READ NOISE from bias frames (in ADU first)
        bias_diff = bias1_data.astype(float) - bias2_data.astype(float)
        read_noise_adu = np.std(bias_diff) / np.sqrt(2)

        # Convert to electrons
        read_noise_electrons = read_noise_adu * gain

        # Calculate FULL WELL CAPACITY
        # FWC = gain * (saturation_ADU - bias_level)
        # Assume 16-bit sensor: saturation at ~65000 ADU
        saturation_adu = 65000
        fwc = int(gain * (saturation_adu - bias_level))

        # Confidence metric (based on data quality)
        confidence = 0.8
        if len(warnings) > 0:
            confidence -= 0.1 * len(warnings)
        if gain < 0.1 or gain > 10:
            confidence -= 0.2
            warnings.append(f"Gain value ({gain:.2f}) seems unusual. Typical range: 0.5-3.0")
        if read_noise_electrons < 0.5 or read_noise_electrons > 20:
            confidence -= 0.2
            warnings.append(f"Read noise ({read_noise_electrons:.2f}e-) seems unusual.")

        confidence = max(0.1, min(1.0, confidence))

        result = CharacterizationResult(
            read_noise=round(read_noise_electrons, 2),
            gain=round(gain, 3),
            full_well_capacity=fwc,
            bias_stats={
                "bias1_mean": float(bias1_mean),
                "bias2_mean": float(bias2_mean),
                "bias1_std": float(bias1_std),
                "bias2_std": float(bias2_std),
                "read_noise_adu": float(read_noise_adu)
            },
            flat_stats={
                "flat1_mean": float(flat1_mean),
                "flat2_mean": float(flat2_mean),
                "flat1_std": float(flat1_std),
                "flat2_std": float(flat2_std),
                "flat_level_percent": float(flat_level_percent)
            },
            confidence=confidence,
            warnings=warnings
        )

        return result

    def create_sensor_profile(
        self,
        result: CharacterizationResult,
        camera_model: str,
        gain_setting: int = None,
        offset: int = None,
        temperature: float = None,
        binning: str = "1x1"
    ) -> SensorProfile:
        """
        Create a SensorProfile from characterization results

        Args:
            result: Characterization results
            camera_model: Camera model name
            gain_setting: Gain setting used
            offset: Offset setting used
            temperature: Sensor temperature
            binning: Binning mode

        Returns:
            SensorProfile object
        """
        notes = None
        if result.warnings:
            notes = "; ".join(result.warnings)

        return SensorProfile(
            camera_model=camera_model,
            read_noise=result.read_noise,
            gain=result.gain,
            full_well_capacity=result.full_well_capacity,
            gain_setting=gain_setting,
            offset=offset,
            temperature=temperature,
            binning=binning,
            notes=notes
        )

    def _load_fits(self, file_path: str) -> np.ndarray:
        """Load FITS file and return data array"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with fits.open(path) as hdul:
            data = hdul[0].data

        return data.astype(float)
