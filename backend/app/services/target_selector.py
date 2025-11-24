"""
Service for intelligent target selection (Step 3)
"""
import json
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
import astropy.units as u

from app.models.session import CelestialTarget, GeoLocation, Ephemeris, FOVSimulation


class TargetSelector:
    """
    Service for intelligent target selection

    Features:
    - Load objects catalog (NGC/IC/Messier)
    - Filter by visibility (altitude, time window)
    - Filter by size vs FOV
    - Filter by moon phase (narrowband vs broadband)
    - Generate FOV simulations
    """

    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            catalog_path = Path(__file__).parent.parent / "data" / "objects_catalog.json"

        self.catalog_path = Path(catalog_path)
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> List[CelestialTarget]:
        """Load objects catalog from JSON"""
        if not self.catalog_path.exists():
            return []

        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [CelestialTarget(**obj) for obj in data]

    def suggest_targets(
        self,
        location: GeoLocation,
        ephemeris: Ephemeris,
        sensor_width: float,
        sensor_height: float,
        pixel_size: float,
        focal_length: float,
        date: Optional[datetime] = None,
        max_suggestions: int = 10
    ) -> List[Tuple[CelestialTarget, dict]]:
        """
        Suggest targets based on conditions and equipment

        Args:
            location: Observer location
            ephemeris: Astronomical ephemeris
            sensor_width: Sensor width in pixels
            sensor_height: Sensor height in pixels
            pixel_size: Pixel size in micrometers
            focal_length: Focal length in mm
            date: Observation date (defaults to ephemeris darkness start)
            max_suggestions: Maximum number of suggestions

        Returns:
            List of (target, metadata) tuples sorted by suitability
        """
        if date is None:
            date = ephemeris.darkness_start

        # Calculate FOV
        fov_width = self._calculate_fov(sensor_width, pixel_size, focal_length)  # arcminutes
        fov_height = self._calculate_fov(sensor_height, pixel_size, focal_length)
        pixel_scale = (pixel_size / focal_length) * 206.265  # arcsec/pixel

        # Filter and score targets
        scored_targets = []

        for target in self.catalog:
            # Check visibility
            visibility = self._check_visibility(target, location, ephemeris, date)

            if not visibility['is_visible']:
                continue

            # Check size compatibility
            size_score = self._score_size_fit(target.size, fov_width, fov_height)

            if size_score < 0.1:  # Too small or too large
                continue

            # Check filter compatibility with moon phase
            filter_score = self._score_filters(target.optimal_filters, ephemeris.moon_illumination)

            # Calculate total score
            total_score = (
                visibility['altitude_score'] * 0.4 +
                size_score * 0.3 +
                filter_score * 0.2 +
                visibility['duration_score'] * 0.1
            )

            metadata = {
                'visibility': visibility,
                'size_score': size_score,
                'filter_score': filter_score,
                'total_score': total_score,
                'fov_width': fov_width,
                'fov_height': fov_height,
                'pixel_scale': pixel_scale
            }

            scored_targets.append((target, metadata))

        # Sort by score (descending)
        scored_targets.sort(key=lambda x: x[1]['total_score'], reverse=True)

        return scored_targets[:max_suggestions]

    def validate_target(
        self,
        target: CelestialTarget,
        location: GeoLocation,
        ephemeris: Ephemeris,
        sensor_width: float,
        sensor_height: float,
        pixel_size: float,
        focal_length: float,
        date: Optional[datetime] = None
    ) -> dict:
        """
        Validate if a manually selected target is feasible

        Returns:
            Dict with feasibility analysis and recommendations
        """
        if date is None:
            date = ephemeris.darkness_start

        # Calculate FOV
        fov_width = self._calculate_fov(sensor_width, pixel_size, focal_length)
        fov_height = self._calculate_fov(sensor_height, pixel_size, focal_length)
        pixel_scale = (pixel_size / focal_length) * 206.265

        # Check visibility
        visibility = self._check_visibility(target, location, ephemeris, date)

        # Analyze size fit
        fits_in_frame = target.size < min(fov_width, fov_height) * 0.9
        coverage = (target.size / min(fov_width, fov_height)) * 100

        # Generate recommendations
        recommendations = []

        if not visibility['is_visible']:
            recommendations.append(f"⚠️ Objeto bajo (max {visibility['max_altitude']:.1f}°). No observable esta noche.")
        elif visibility['max_altitude'] < 40:
            recommendations.append(f"⚠️ Objeto bajo (max {visibility['max_altitude']:.1f}°). Calidad reducida.")
        else:
            recommendations.append(f"✓ Buena altitud (max {visibility['max_altitude']:.1f}° a las {visibility['max_altitude_time'].strftime('%H:%M')})")

        if visibility['optimal_hours'] < 2:
            recommendations.append(f"⚠️ Ventana corta ({visibility['optimal_hours']:.1f}h)")
        else:
            recommendations.append(f"✓ Ventana amplia ({visibility['optimal_hours']:.1f}h)")

        if not fits_in_frame:
            recommendations.append(f"⚠️ Objeto muy grande ({target.size:.0f}' vs FOV {min(fov_width, fov_height):.0f}')")
        elif coverage < 30:
            recommendations.append(f"✓ Objeto pequeño ({coverage:.0f}% del FOV). Considera mosaico.")
        else:
            recommendations.append(f"✓ Tamaño ideal ({coverage:.0f}% del FOV)")

        # Filter recommendations based on moon
        if ephemeris.moon_illumination > 70:
            if any(f in target.optimal_filters for f in ["H-alpha", "OIII", "SII"]):
                recommendations.append(f"✓ Banda estrecha recomendada (Luna {ephemeris.moon_illumination}%)")
            else:
                recommendations.append(f"⚠️ Luna brillante ({ephemeris.moon_illumination}%). Mejor banda estrecha.")

        return {
            'feasible': visibility['is_visible'] and fits_in_frame,
            'visibility': visibility,
            'fov_analysis': {
                'fov_width': fov_width,
                'fov_height': fov_height,
                'pixel_scale': pixel_scale,
                'fits_in_frame': fits_in_frame,
                'coverage_percentage': min(coverage, 100)
            },
            'recommendations': recommendations
        }

    def simulate_fov(
        self,
        target: CelestialTarget,
        sensor_width: float,
        sensor_height: float,
        pixel_size: float,
        focal_length: float
    ) -> FOVSimulation:
        """Generate FOV simulation for a target"""
        fov_width = self._calculate_fov(sensor_width, pixel_size, focal_length)
        fov_height = self._calculate_fov(sensor_height, pixel_size, focal_length)
        pixel_scale = (pixel_size / focal_length) * 206.265

        fits = target.size < min(fov_width, fov_height) * 0.9
        coverage = min((target.size / min(fov_width, fov_height)) * 100, 100)

        return FOVSimulation(
            target=target.name,
            fits_in_frame=fits,
            coverage_percentage=coverage,
            pixel_scale=pixel_scale,
            fov_width=fov_width,
            fov_height=fov_height,
            target_size=target.size
        )

    def search_by_name(self, query: str) -> List[CelestialTarget]:
        """Search targets by name or catalog ID"""
        query_lower = query.lower()
        matches = []

        for target in self.catalog:
            if (query_lower in target.name.lower() or
                query_lower in target.catalog_id.lower()):
                matches.append(target)

        return matches

    def search_by_catalog_id(self, catalog_id: str) -> List[CelestialTarget]:
        """Search targets by exact catalog ID match"""
        catalog_id_upper = catalog_id.upper()
        matches = []

        for target in self.catalog:
            if target.catalog_id.upper() == catalog_id_upper:
                matches.append(target)

        return matches

    def _calculate_fov(self, sensor_pixels: float, pixel_size_um: float, focal_length_mm: float) -> float:
        """Calculate field of view in arcminutes"""
        sensor_size_mm = (sensor_pixels * pixel_size_um) / 1000
        fov_rad = 2 * np.arctan(sensor_size_mm / (2 * focal_length_mm))
        fov_arcmin = np.degrees(fov_rad) * 60
        return fov_arcmin

    def _check_visibility(
        self,
        target: CelestialTarget,
        location: GeoLocation,
        ephemeris: Ephemeris,
        date: datetime
    ) -> dict:
        """Check if target is visible during the night"""
        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        coord = SkyCoord(ra=target.ra * u.deg, dec=target.dec * u.deg, frame='icrs')

        # Sample times during darkness
        start = Time(ephemeris.darkness_start)
        end = Time(ephemeris.darkness_end)
        n_samples = 50
        times = start + np.linspace(0, (end - start).to(u.hour).value, n_samples) * u.hour

        # Calculate altitudes
        altaz = coord.transform_to(AltAz(obstime=times, location=observer))
        max_alt = np.max(altaz.alt.deg)
        max_alt_idx = np.argmax(altaz.alt.deg)
        max_alt_time = times[max_alt_idx].datetime

        # Check good observing time (alt > 30°)
        good_alt = altaz.alt.deg > 30
        optimal_hours = np.sum(good_alt) / n_samples * ephemeris.darkness_duration

        # Scoring
        altitude_score = min(max_alt / 70, 1.0)  # Best at 70° or higher
        duration_score = min(optimal_hours / 4, 1.0)  # Best if >4h available

        return {
            'is_visible': max_alt > 30,
            'max_altitude': float(max_alt),
            'max_altitude_time': max_alt_time,
            'optimal_hours': float(optimal_hours),
            'altitude_score': altitude_score,
            'duration_score': duration_score
        }

    def _score_size_fit(self, target_size: float, fov_width: float, fov_height: float) -> float:
        """Score how well target size fits in FOV (0-1)"""
        min_fov = min(fov_width, fov_height)

        # Ideal: target occupies 40-80% of frame
        coverage = target_size / min_fov

        if coverage < 0.05:  # Too small
            return coverage / 0.05 * 0.3
        elif coverage < 0.4:  # Small but acceptable
            return 0.3 + (coverage - 0.05) / 0.35 * 0.4
        elif coverage < 0.8:  # Ideal range
            return 1.0
        elif coverage < 1.2:  # Slightly large but ok
            return 1.0 - (coverage - 0.8) / 0.4 * 0.3
        else:  # Too large
            return max(0.1, 0.7 - (coverage - 1.2) * 0.5)

    def _score_filters(self, filters: List[str], moon_illumination: int) -> float:
        """Score filter suitability based on moon phase"""
        has_narrowband = any(f in filters for f in ["H-alpha", "OIII", "SII"])
        has_broadband = any(f in filters for f in ["L", "R", "G", "B"])

        if moon_illumination > 70:
            # Bright moon: prefer narrowband
            return 1.0 if has_narrowband else 0.5
        elif moon_illumination > 40:
            # Medium moon: both ok
            return 0.8 if has_narrowband else 0.7
        else:
            # Dark moon: prefer broadband
            return 0.8 if has_broadband else 0.9
