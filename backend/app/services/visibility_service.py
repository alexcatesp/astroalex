"""
Service for calculating target visibility curves during the night
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun, get_body
import numpy as np

from app.models.session import GeoLocation, CelestialTarget


class VisibilityDataPoint:
    """Single data point in the visibility curve"""
    def __init__(self, time: datetime, altitude: float, azimuth: float, airmass: float):
        self.time = time
        self.altitude = altitude  # degrees
        self.azimuth = azimuth  # degrees
        self.airmass = airmass  # dimensionless


class VisibilityWindow:
    """Represents when a target is visible (above minimum altitude)"""
    def __init__(self, start: datetime, end: datetime, max_altitude: float, max_altitude_time: datetime):
        self.start = start
        self.end = end
        self.duration_hours = (end - start).total_seconds() / 3600
        self.max_altitude = max_altitude
        self.max_altitude_time = max_altitude_time


class VisibilityService:
    """Service for target visibility calculations"""

    # Minimum altitude for practical observation (degrees)
    MIN_ALTITUDE = 20.0

    # Sun altitude for different twilight phases (degrees)
    CIVIL_TWILIGHT = -6.0
    NAUTICAL_TWILIGHT = -12.0
    ASTRONOMICAL_TWILIGHT = -18.0

    def __init__(self):
        pass

    def calculate_visibility_curve(
        self,
        target: CelestialTarget,
        location: GeoLocation,
        date: Optional[datetime] = None,
        num_points: int = 100
    ) -> List[Dict]:
        """
        Calculate the visibility curve for a target over the night

        Args:
            target: The celestial target
            location: Observer location
            date: Date to calculate for (defaults to today)
            num_points: Number of points in the curve

        Returns:
            List of dictionaries with time, altitude, azimuth, airmass
        """
        if date is None:
            date = datetime.utcnow()

        # Create observer location
        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        # Create target coordinates
        target_coord = SkyCoord(
            ra=target.ra * u.deg,
            dec=target.dec * u.deg,
            frame='icrs'
        )

        # Calculate for the night (from noon today to noon tomorrow)
        noon_today = datetime(date.year, date.month, date.day, 12, 0, 0)
        times = Time(noon_today) + np.linspace(0, 24, num_points) * u.hour

        # Get target positions
        altaz_frame = AltAz(obstime=times, location=observer)
        target_altaz = target_coord.transform_to(altaz_frame)

        # Convert to list of dictionaries
        curve_data = []
        for i, time in enumerate(times):
            alt = target_altaz.alt[i].degree
            az = target_altaz.az[i].degree

            # Calculate airmass (approximation valid for altitudes > 10°)
            if alt > 0:
                airmass = 1.0 / np.cos(np.radians(90 - alt))
                # Clamp airmass for low altitudes
                airmass = min(airmass, 10.0)
            else:
                airmass = None

            curve_data.append({
                'time': time.datetime.isoformat(),
                'altitude': round(alt, 2),
                'azimuth': round(az, 2),
                'airmass': round(airmass, 2) if airmass else None
            })

        return curve_data

    def get_darkness_periods(
        self,
        location: GeoLocation,
        date: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Calculate when different darkness levels occur

        Returns:
            Dictionary with civil, nautical, and astronomical twilight periods
        """
        if date is None:
            date = datetime.utcnow()

        # Create observer location
        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        # Calculate for the night (from noon today to noon tomorrow)
        noon_today = datetime(date.year, date.month, date.day, 12, 0, 0)
        times = Time(noon_today) + np.linspace(0, 24, 1000) * u.hour

        # Get sun positions
        sun_altaz = get_sun(times).transform_to(AltAz(obstime=times, location=observer))
        sun_altitudes = sun_altaz.alt.degree

        # Find when sun crosses different twilight thresholds
        def find_crossing_times(altitudes, threshold):
            """Find times when altitude crosses threshold"""
            crossings = []
            for i in range(len(altitudes) - 1):
                if (altitudes[i] > threshold and altitudes[i + 1] <= threshold) or \
                   (altitudes[i] < threshold and altitudes[i + 1] >= threshold):
                    crossings.append(times[i].datetime)
            return crossings

        civil_crossings = find_crossing_times(sun_altitudes, self.CIVIL_TWILIGHT)
        nautical_crossings = find_crossing_times(sun_altitudes, self.NAUTICAL_TWILIGHT)
        astro_crossings = find_crossing_times(sun_altitudes, self.ASTRONOMICAL_TWILIGHT)

        # Find astronomical darkness period
        astro_dark_indices = np.where(sun_altitudes < self.ASTRONOMICAL_TWILIGHT)[0]

        darkness_start = None
        darkness_end = None
        if len(astro_dark_indices) > 0:
            darkness_start = times[astro_dark_indices[0]].datetime
            darkness_end = times[astro_dark_indices[-1]].datetime

        return {
            'civil_twilight': {
                'threshold': self.CIVIL_TWILIGHT,
                'times': [t.isoformat() for t in civil_crossings]
            },
            'nautical_twilight': {
                'threshold': self.NAUTICAL_TWILIGHT,
                'times': [t.isoformat() for t in nautical_crossings]
            },
            'astronomical_twilight': {
                'threshold': self.ASTRONOMICAL_TWILIGHT,
                'times': [t.isoformat() for t in astro_crossings]
            },
            'darkness_window': {
                'start': darkness_start.isoformat() if darkness_start else None,
                'end': darkness_end.isoformat() if darkness_end else None,
                'duration_hours': (darkness_end - darkness_start).total_seconds() / 3600 if darkness_start and darkness_end else 0
            }
        }

    def get_visibility_window(
        self,
        target: CelestialTarget,
        location: GeoLocation,
        date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Calculate when a target is optimally visible (above MIN_ALTITUDE during darkness)

        Returns:
            Dictionary with start, end, duration, and max altitude time
        """
        curve_data = self.calculate_visibility_curve(target, location, date, num_points=200)
        darkness = self.get_darkness_periods(location, date)

        if not darkness['darkness_window']['start']:
            return None

        darkness_start = datetime.fromisoformat(darkness['darkness_window']['start'])
        darkness_end = datetime.fromisoformat(darkness['darkness_window']['end'])

        # Filter curve to only dark hours and above minimum altitude
        visible_points = []
        for point in curve_data:
            point_time = datetime.fromisoformat(point['time'])
            if (darkness_start <= point_time <= darkness_end and
                point['altitude'] >= self.MIN_ALTITUDE):
                visible_points.append(point)

        if not visible_points:
            return None

        # Find max altitude point
        max_alt_point = max(visible_points, key=lambda p: p['altitude'])

        return {
            'start': visible_points[0]['time'],
            'end': visible_points[-1]['time'],
            'duration_hours': round(len(visible_points) * 24 / 200, 2),  # Approximate
            'max_altitude': max_alt_point['altitude'],
            'max_altitude_time': max_alt_point['time'],
            'min_airmass': max_alt_point['airmass']
        }

    def get_moon_position(
        self,
        location: GeoLocation,
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Get moon position and phase information

        Returns:
            Dictionary with altitude, azimuth, and illumination
        """
        if date is None:
            date = datetime.utcnow()

        # Create observer location
        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        time = Time(date)
        altaz_frame = AltAz(obstime=time, location=observer)

        # Get moon position
        moon = get_body('moon', time, observer)
        moon_altaz = moon.transform_to(altaz_frame)

        # Get sun position for phase calculation
        sun = get_body('sun', time, observer)

        # Calculate moon phase (0 = new, 0.5 = full)
        elongation = moon.separation(sun).degree
        phase = (1 - np.cos(np.radians(elongation))) / 2
        illumination = int(phase * 100)

        return {
            'altitude': round(moon_altaz.alt.degree, 2),
            'azimuth': round(moon_altaz.az.degree, 2),
            'illumination': illumination,
            'phase_description': self._get_moon_phase_description(illumination)
        }

    def _get_moon_phase_description(self, illumination: int) -> str:
        """Get descriptive moon phase name"""
        if illumination < 5:
            return 'New Moon'
        elif illumination < 25:
            return 'Waxing Crescent'
        elif illumination < 45:
            return 'First Quarter'
        elif illumination < 55:
            return 'Waxing Gibbous'
        elif illumination < 95:
            return 'Full Moon'
        elif illumination < 75:
            return 'Waning Gibbous'
        elif illumination < 55:
            return 'Last Quarter'
        else:
            return 'Waning Crescent'
