"""
Service for environmental context: weather APIs and astronomical calculations
"""
from datetime import datetime, timedelta
from typing import Optional, List
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun, SkyCoord, get_body
import numpy as np

from app.models.session import GeoLocation, SkyConditions, Ephemeris, AssistantMessage


class EnvironmentalService:
    """Service for environmental context and ephemeris calculations"""

    def __init__(self):
        pass

    def calculate_ephemeris(self, location: GeoLocation, date: Optional[datetime] = None) -> Ephemeris:
        """
        Calculate astronomical ephemeris for a given location and date

        Args:
            location: Observer location
            date: Date to calculate for (defaults to today)

        Returns:
            Ephemeris object with all astronomical data
        """
        if date is None:
            date = datetime.utcnow()

        # Create observer location
        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        # Calculate for the evening (start from noon today)
        noon_today = datetime(date.year, date.month, date.day, 12, 0, 0)
        times = Time(noon_today) + np.linspace(0, 24, 1000) * u.hour

        # Get sun positions
        sun_altaz = get_sun(times).transform_to(AltAz(obstime=times, location=observer))

        # Find sunset (when sun goes below horizon)
        sunset_idx = np.where(np.diff(sun_altaz.alt.deg < 0))[0]
        if len(sunset_idx) > 0:
            sunset_time = times[sunset_idx[0]].datetime
        else:
            sunset_time = noon_today  # Fallback

        # Find sunrise (when sun rises above horizon after sunset)
        sunrise_idx = np.where(np.diff(sun_altaz.alt.deg > 0))[0]
        sunrise_idx = sunrise_idx[sunrise_idx > sunset_idx[0]] if len(sunset_idx) > 0 else sunrise_idx
        if len(sunrise_idx) > 0:
            sunrise_time = times[sunrise_idx[0]].datetime
        else:
            sunrise_time = noon_today + timedelta(hours=12)  # Fallback

        # Astronomical twilight: sun altitude < -18 degrees
        astro_twilight_evening_idx = np.where(np.diff(sun_altaz.alt.deg < -18))[0]
        if len(astro_twilight_evening_idx) > 0:
            astro_twilight_evening = times[astro_twilight_evening_idx[0]].datetime
        else:
            astro_twilight_evening = sunset_time + timedelta(hours=1)

        astro_twilight_morning_idx = np.where(np.diff(sun_altaz.alt.deg > -18))[0]
        astro_twilight_morning_idx = astro_twilight_morning_idx[astro_twilight_morning_idx > astro_twilight_evening_idx[0]] if len(astro_twilight_evening_idx) > 0 else astro_twilight_morning_idx
        if len(astro_twilight_morning_idx) > 0:
            astro_twilight_morning = times[astro_twilight_morning_idx[0]].datetime
        else:
            astro_twilight_morning = sunrise_time - timedelta(hours=1)

        # Calculate darkness duration
        darkness_duration = (astro_twilight_morning - astro_twilight_evening).total_seconds() / 3600

        # Get moon data
        moon_time = Time(date)
        moon = get_body('moon', moon_time)
        sun = get_sun(moon_time)

        # Calculate moon phase (elongation from sun)
        elongation = sun.separation(moon).deg
        moon_phase = (1 - np.cos(np.radians(elongation))) / 2  # 0 = new moon, 1 = full moon
        moon_illumination = int(moon_phase * 100)

        return Ephemeris(
            darkness_start=astro_twilight_evening,
            darkness_end=astro_twilight_morning,
            darkness_duration=darkness_duration,
            moon_phase=moon_phase,
            moon_illumination=moon_illumination,
            sun_set=sunset_time,
            sun_rise=sunrise_time,
            astronomical_twilight_start=astro_twilight_evening,
            astronomical_twilight_end=astro_twilight_morning
        )

    def get_sky_conditions(self, location: GeoLocation) -> SkyConditions:
        """
        Get current sky conditions from weather API

        For now, returns placeholder data. In production, this would:
        - Query Meteoblue or OpenMeteo API
        - Parse seeing, clouds, jet stream data
        - Handle API fallback and caching

        Args:
            location: Observer location

        Returns:
            SkyConditions object
        """
        # TODO: Implement actual API calls to Meteoblue/OpenMeteo
        # For now, return placeholder data
        return SkyConditions(
            seeing=2.5,  # arcseconds
            clouds=30,   # percentage
            jet_stream=25.0,  # m/s
            transparency=75,
            humidity=60,
            wind_speed=5.0,
            temperature=15.0,
            source="placeholder"
        )

    def generate_recommendations(self, conditions: SkyConditions, ephemeris: Ephemeris) -> AssistantMessage:
        """
        Generate intelligent observing recommendations based on conditions

        Args:
            conditions: Current sky conditions
            ephemeris: Astronomical ephemeris

        Returns:
            AssistantMessage with recommendations
        """
        recommendations = []

        # Darkness duration
        hours = int(ephemeris.darkness_duration)
        minutes = int((ephemeris.darkness_duration - hours) * 60)
        darkness_msg = f"Tienes **{hours}h {minutes}m** de oscuridad astronómica ({ephemeris.darkness_start.strftime('%H:%M')} - {ephemeris.darkness_end.strftime('%H:%M')})."
        recommendations.append(darkness_msg)

        # Seeing recommendations
        if conditions.seeing < 2.0:
            seeing_msg = f"El Seeing es excelente ({conditions.seeing}\"), perfecto para trabajo planetario o alta resolución."
        elif conditions.seeing < 3.0:
            seeing_msg = f"El Seeing es moderado ({conditions.seeing}\"), adecuado para cielo profundo. Considera Binning 2x2 si usas focales largas."
        else:
            seeing_msg = f"El Seeing es pobre ({conditions.seeing}\"), te recomiendo evitar focales extremas o usar Binning 2x2."
        recommendations.append(seeing_msg)

        # Moon recommendations
        if ephemeris.moon_illumination > 70:
            moon_msg = f"Luna al {ephemeris.moon_illumination}%, te sugiero trabajar en **Banda Estrecha (H-alfa, OIII, SII)**."
        elif ephemeris.moon_illumination > 40:
            moon_msg = f"Luna al {ephemeris.moon_illumination}%, buena noche para banda estrecha o objetos brillantes."
        else:
            moon_msg = f"Luna al {ephemeris.moon_illumination}%, excelente para objetos débiles en banda ancha (LRGB)."
        recommendations.append(moon_msg)

        # Clouds
        if conditions.clouds > 70:
            cloud_msg = f"⚠️ Nubes al {conditions.clouds}%, la sesión podría verse interrumpida."
            recommendations.append(cloud_msg)
        elif conditions.clouds > 40:
            recommendations.append(f"Nubes al {conditions.clouds}%, monitorea el cielo durante la sesión.")

        # Build final message
        greeting_hour = ephemeris.darkness_start.hour
        if greeting_hour < 12:
            greeting = "Buenos días"
        elif greeting_hour < 20:
            greeting = "Buenas tardes"
        else:
            greeting = "Buenas noches"

        message = f"{greeting}. " + " ".join(recommendations)

        return AssistantMessage(
            step="context",
            message=message,
            data={
                "seeing": conditions.seeing,
                "clouds": conditions.clouds,
                "moon_illumination": ephemeris.moon_illumination,
                "darkness_hours": ephemeris.darkness_duration
            }
        )

    def calculate_target_visibility(
        self,
        target_ra: float,
        target_dec: float,
        location: GeoLocation,
        date: Optional[datetime] = None
    ) -> dict:
        """
        Calculate when a target is visible and at what altitude

        Args:
            target_ra: Right ascension in degrees
            target_dec: Declination in degrees
            location: Observer location
            date: Date to calculate for

        Returns:
            Dict with visibility information
        """
        if date is None:
            date = datetime.utcnow()

        observer = EarthLocation(
            lat=location.latitude * u.deg,
            lon=location.longitude * u.deg,
            height=(location.elevation or 0) * u.m
        )

        target = SkyCoord(ra=target_ra * u.deg, dec=target_dec * u.deg, frame='icrs')

        # Calculate altitude throughout the night
        ephemeris = self.calculate_ephemeris(location, date)
        start_time = Time(ephemeris.darkness_start)
        end_time = Time(ephemeris.darkness_end)

        times = start_time + np.linspace(0, (end_time - start_time).to(u.hour).value, 100) * u.hour
        altaz = target.transform_to(AltAz(obstime=times, location=observer))

        max_alt = np.max(altaz.alt.deg)
        max_alt_time = times[np.argmax(altaz.alt.deg)].datetime

        # Check if target is above 30 degrees (good observing altitude)
        good_altitude = altaz.alt.deg > 30
        good_time_indices = np.where(good_altitude)[0]

        if len(good_time_indices) > 0:
            best_start = times[good_time_indices[0]].datetime
            best_end = times[good_time_indices[-1]].datetime
            optimal_hours = (best_end - best_start).total_seconds() / 3600
        else:
            best_start = None
            best_end = None
            optimal_hours = 0

        return {
            "max_altitude": float(max_alt),
            "max_altitude_time": max_alt_time,
            "optimal_window_start": best_start,
            "optimal_window_end": best_end,
            "optimal_hours": optimal_hours,
            "is_observable": max_alt > 30,
            "recommendation": "Excelente" if max_alt > 60 else "Buena" if max_alt > 40 else "Baja" if max_alt > 20 else "No observable"
        }
