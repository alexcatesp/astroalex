"""
Service for Smart Scout analysis (Step 4)
Analyzes a test frame to determine optimal exposure settings
"""
from pathlib import Path
from typing import Dict, Optional
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder

from app.models.session import ScoutAnalysis, SensorProfile


class SmartScout:
    """
    Service for analyzing test frames and calculating optimal exposure

    Analyzes:
    - Sky background level (electrons/second)
    - Saturation detection (HDR requirement)
    - Optimal exposure time per filter
    - SNR estimation
    """

    def analyze_test_frame(
        self,
        frame_path: str,
        sensor_profile: SensorProfile,
        exposure_time: float,
        filter_name: str = "L"
    ) -> ScoutAnalysis:
        """
        Analyze a test frame to determine optimal exposure settings

        Args:
            frame_path: Path to test FITS frame
            sensor_profile: Camera sensor characterization
            exposure_time: Exposure time of test frame (seconds)
            filter_name: Filter used for test frame

        Returns:
            ScoutAnalysis with recommendations
        """
        # Load frame
        with fits.open(frame_path) as hdul:
            data = hdul[0].data.astype(float)

        # Calculate sky background
        sky_background = self._calculate_sky_background(data, sensor_profile)

        # Detect saturation
        saturation_info = self._detect_saturation(data, sensor_profile)

        # Calculate optimal exposure
        optimal_exposures = self._calculate_optimal_exposure(
            sky_background,
            sensor_profile,
            saturation_info['hdr_required']
        )

        # Estimate FWHM and star count
        fwhm, star_count = self._analyze_stars(data)

        # Calculate SNR
        snr = self._estimate_snr(data, sensor_profile, exposure_time)

        return ScoutAnalysis(
            sky_background=sky_background,
            saturation_detected=saturation_info['detected'],
            saturation_percentage=saturation_info['percentage'],
            saturated_pixels=saturation_info['count'],
            hdr_required=saturation_info['hdr_required'],
            optimal_exposure=optimal_exposures,
            snr_estimate=snr,
            fwhm=fwhm,
            star_count=star_count
        )

    def _calculate_sky_background(self, data: np.ndarray, sensor_profile: SensorProfile) -> float:
        """
        Calculate sky background in electrons/second

        Returns sky background flux in e-/s
        """
        # Use sigma-clipped statistics to exclude stars
        mean, median, std = sigma_clipped_stats(data, sigma=3.0)

        # Convert ADU to electrons
        sky_electrons = median * sensor_profile.gain

        return float(sky_electrons)  # This is per-exposure, need to divide by time for e-/s

    def _detect_saturation(self, data: np.ndarray, sensor_profile: SensorProfile) -> dict:
        """
        Detect saturation in the frame

        Returns:
            Dict with saturation info
        """
        # Assume 16-bit ADC: saturation near 65535
        saturation_threshold = 60000  # 91% of max

        saturated_pixels = np.sum(data > saturation_threshold)
        total_pixels = data.size
        saturation_percentage = (saturated_pixels / total_pixels) * 100

        # HDR required if >3% of pixels saturated
        hdr_required = saturation_percentage > 3.0

        return {
            'detected': saturated_pixels > 0,
            'count': int(saturated_pixels),
            'percentage': float(saturation_percentage),
            'hdr_required': hdr_required
        }

    def _calculate_optimal_exposure(
        self,
        sky_background_e: float,
        sensor_profile: SensorProfile,
        hdr_required: bool
    ) -> Dict[str, int]:
        """
        Calculate optimal exposure time using SNR optimization

        Formula: Optimal when SkyNoise >> ReadNoise
        Target: SkyNoise > 10 * ReadNoise^2
        """
        read_noise = sensor_profile.read_noise

        # Target: sky noise should be 10x read noise squared
        target_sky_noise_sq = 10 * (read_noise ** 2)

        # Sky noise = sqrt(sky_background * time)
        # We want: sky_background * time > target_sky_noise_sq
        # Therefore: time > target_sky_noise_sq / sky_background

        if sky_background_e > 0:
            optimal_time = target_sky_noise_sq / sky_background_e
        else:
            # Very dark sky: use longer exposures
            optimal_time = 300

        # Round to reasonable values
        optimal_time = self._round_exposure(optimal_time)

        # HDR strategy: calculate short exposure too
        if hdr_required:
            short_exposure = max(30, optimal_time // 4)
            short_exposure = self._round_exposure(short_exposure)
        else:
            short_exposure = None

        # Different filters have different recommendations
        exposures = {
            "H-alpha": int(optimal_time * 1.2),  # Longer for narrowband
            "OIII": int(optimal_time * 1.2),
            "SII": int(optimal_time * 1.3),
            "L": int(optimal_time),
            "R": int(optimal_time * 0.8),
            "G": int(optimal_time * 0.7),
            "B": int(optimal_time * 0.9)
        }

        if short_exposure:
            exposures["HDR_short"] = int(short_exposure)

        return exposures

    def _round_exposure(self, exposure: float) -> float:
        """Round exposure to reasonable increment"""
        if exposure < 60:
            return round(exposure / 10) * 10  # 10s increments
        elif exposure < 300:
            return round(exposure / 30) * 30  # 30s increments
        else:
            return round(exposure / 60) * 60  # 60s increments

    def _analyze_stars(self, data: np.ndarray) -> tuple:
        """
        Detect stars and calculate FWHM

        Returns:
            (fwhm, star_count)
        """
        try:
            # Calculate background for star detection
            mean, median, std = sigma_clipped_stats(data, sigma=3.0)

            # Find stars
            daofind = DAOStarFinder(fwhm=3.0, threshold=5.0 * std)
            sources = daofind(data - median)

            if sources is None or len(sources) == 0:
                return None, 0

            # Estimate FWHM from detected stars
            fwhm_values = sources['fwhm']
            median_fwhm = np.median(fwhm_values)

            return float(median_fwhm), len(sources)

        except Exception:
            # If star detection fails, return None
            return None, 0

    def _estimate_snr(self, data: np.ndarray, sensor_profile: SensorProfile, exposure_time: float) -> float:
        """
        Estimate Signal-to-Noise Ratio

        SNR = Signal / sqrt(Signal + Sky + ReadNoise^2)
        """
        mean, median, std = sigma_clipped_stats(data, sigma=3.0)

        # Signal in electrons
        signal_e = median * sensor_profile.gain

        # Sky background
        sky_e = median * sensor_profile.gain

        # Read noise
        read_noise = sensor_profile.read_noise

        # Total noise
        total_noise = np.sqrt(signal_e + sky_e + read_noise**2)

        # SNR
        snr = signal_e / total_noise if total_noise > 0 else 0

        return float(snr)

    def generate_recommendations(self, analysis: ScoutAnalysis, sensor_profile: SensorProfile) -> str:
        """
        Generate human-readable recommendations from analysis

        Returns:
            Formatted message string
        """
        messages = []

        # Sky background
        messages.append(f"Sky background: **{analysis.sky_background:.1f} e-**.")

        # Saturation
        if analysis.saturation_detected:
            messages.append(
                f"⚠️ Detectada saturación en **{analysis.saturation_percentage:.1f}%** de píxeles "
                f"({analysis.saturated_pixels:,} píxeles)."
            )

        # HDR requirement
        if analysis.hdr_required:
            messages.append(
                "**Estrategia HDR necesaria** para núcleos estelares. "
                f"Usa exposiciones cortas ({analysis.optimal_exposure.get('HDR_short', 30)}s) "
                "combinadas con largas."
            )

        # Optimal exposures
        ha_exp = analysis.optimal_exposure.get("H-alpha")
        rgb_exp = analysis.optimal_exposure.get("R")

        if ha_exp and rgb_exp:
            messages.append(
                f"Exposición óptima: **{ha_exp}s** (H-alpha), **{rgb_exp}s** (RGB)."
            )

        # FWHM
        if analysis.fwhm:
            messages.append(f"FWHM medido: **{analysis.fwhm:.2f} pixels**.")

        # Star count
        if analysis.star_count:
            messages.append(f"Estrellas detectadas: **{analysis.star_count}**.")

        # SNR
        if analysis.snr_estimate > 20:
            messages.append(f"SNR excelente: **{analysis.snr_estimate:.1f}**.")
        elif analysis.snr_estimate > 10:
            messages.append(f"SNR bueno: **{analysis.snr_estimate:.1f}**.")
        else:
            messages.append(f"SNR bajo: **{analysis.snr_estimate:.1f}**. Considera exposiciones más largas.")

        return " ".join(messages)
