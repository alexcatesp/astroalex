"""
Service for generating acquisition flight plans (Step 5)
"""
import json
from typing import Dict, List
from datetime import datetime, timedelta
from pathlib import Path

from app.models.session import (
    AcquisitionPlan,
    CelestialTarget,
    PlanItem,
    Ephemeris,
    ScoutAnalysis
)


class FlightPlanGenerator:
    """
    Service for generating complete acquisition plans

    Features:
    - Calculate frame counts based on available time
    - Generate calibration frame requirements
    - Export to ASIAIR .plan format
    - Export to N.I.N.A. JSON format
    """

    def generate_plan(
        self,
        target: CelestialTarget,
        ephemeris: Ephemeris,
        scout_analysis: ScoutAnalysis,
        available_hours: float = None
    ) -> AcquisitionPlan:
        """
        Generate complete acquisition plan

        Args:
            target: Target object
            ephemeris: Astronomical ephemeris
            scout_analysis: Smart Scout analysis results
            available_hours: Override for available time (uses ephemeris if None)

        Returns:
            Complete AcquisitionPlan
        """
        if available_hours is None:
            available_hours = ephemeris.darkness_duration

        # Generate lights plan
        lights = self._generate_lights_plan(
            target,
            scout_analysis,
            available_hours
        )

        # Generate calibration requirements
        darks = self._generate_darks_plan(lights)
        flats = self._generate_flats_plan(lights)
        bias = self._generate_bias_plan()

        # Calculate totals
        total_time = sum(item.total_time for item in lights.values()) / 60  # Convert to hours
        total_frames = sum(item.count for item in lights.values())
        total_frames += sum(d.count for d in darks)
        total_frames += sum(f.count for f in flats)
        total_frames += bias.count

        # HDR strategy if needed
        hdr_strategy = None
        if scout_analysis.hdr_required:
            hdr_strategy = {
                "enabled": True,
                "short_exposure": scout_analysis.optimal_exposure.get("HDR_short", 30),
                "long_exposure": scout_analysis.optimal_exposure.get("L", 180),
                "blend_method": "HDR_auto"
            }

        return AcquisitionPlan(
            target=target,
            lights=lights,
            darks=darks,
            flats=flats,
            bias=bias,
            total_time=total_time,
            total_frames=total_frames,
            hdr_strategy=hdr_strategy
        )

    def export_asiair(self, plan: AcquisitionPlan, output_path: str):
        """
        Export plan to ASIAIR .plan format

        ASIAIR format is a JSON file with specific structure
        """
        asiair_plan = {
            "version": "1.0",
            "target": {
                "name": plan.target.name,
                "ra": plan.target.ra,
                "dec": plan.target.dec
            },
            "sequences": []
        }

        # Add light sequences
        for filter_name, item in plan.lights.items():
            asiair_plan["sequences"].append({
                "type": "LIGHT",
                "filter": filter_name,
                "exposure": item.exposure,
                "gain": item.gain or 100,
                "count": item.count
            })

        # Add darks
        for dark in plan.darks:
            asiair_plan["sequences"].append({
                "type": "DARK",
                "exposure": dark.exposure,
                "gain": dark.gain or 100,
                "count": dark.count
            })

        # Add flats
        for flat in plan.flats:
            asiair_plan["sequences"].append({
                "type": "FLAT",
                "filter": flat.filter_name,
                "count": flat.count
            })

        # Add bias
        asiair_plan["sequences"].append({
            "type": "BIAS",
            "count": plan.bias.count
        })

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asiair_plan, f, indent=2)

    def export_nina(self, plan: AcquisitionPlan, output_path: str):
        """
        Export plan to N.I.N.A. JSON format

        N.I.N.A. uses a different structure for sequences
        """
        nina_plan = {
            "$$type": "NINA.Sequencer.Container.SequentialContainer",
            "Name": f"Sequence for {plan.target.name}",
            "Items": []
        }

        # Add target
        nina_plan["Items"].append({
            "$$type": "NINA.Sequencer.SequenceItem.Targeting.SlewScopeToRaDec",
            "Coordinates": {
                "RA": plan.target.ra / 15,  # N.I.N.A. uses hours
                "Dec": plan.target.dec
            }
        })

        # Add light frames
        for filter_name, item in plan.lights.items():
            nina_plan["Items"].append({
                "$$type": "NINA.Sequencer.SequenceItem.Imaging.TakeExposure",
                "ExposureTime": item.exposure,
                "Gain": item.gain or 100,
                "ImageType": "LIGHT",
                "Filter": filter_name,
                "ExposureCount": item.count
            })

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(nina_plan, f, indent=2)

    def _generate_lights_plan(
        self,
        target: CelestialTarget,
        scout_analysis: ScoutAnalysis,
        available_hours: float
    ) -> Dict[str, PlanItem]:
        """
        Generate lights plan based on target and available time

        Strategy:
        - Allocate time based on filter priorities
        - Narrowband gets more time if moon is bright
        - RGB gets equal time distribution
        """
        lights = {}

        # Determine which filters to use
        use_narrowband = any(f in target.optimal_filters for f in ["H-alpha", "OIII", "SII"])
        use_broadband = any(f in target.optimal_filters for f in ["L", "R", "G", "B"])

        available_minutes = available_hours * 60

        if use_narrowband and use_broadband:
            # Allocate 60% to narrowband, 40% to broadband
            nb_time = available_minutes * 0.6
            bb_time = available_minutes * 0.4
        elif use_narrowband:
            nb_time = available_minutes
            bb_time = 0
        else:
            nb_time = 0
            bb_time = available_minutes

        # Narrowband allocation
        if use_narrowband and nb_time > 0:
            nb_filters = [f for f in ["H-alpha", "OIII", "SII"] if f in target.optimal_filters]
            time_per_filter = nb_time / len(nb_filters)

            for filter_name in nb_filters:
                exposure = scout_analysis.optimal_exposure.get(filter_name, 300)
                count = int(time_per_filter / (exposure / 60))

                lights[filter_name] = PlanItem(
                    frame_type="light",
                    filter_name=filter_name,
                    exposure=exposure,
                    count=count,
                    total_time=count * (exposure / 60)
                )

        # Broadband allocation
        if use_broadband and bb_time > 0:
            bb_filters = [f for f in ["L", "R", "G", "B"] if f in target.optimal_filters]
            time_per_filter = bb_time / len(bb_filters)

            for filter_name in bb_filters:
                exposure = scout_analysis.optimal_exposure.get(filter_name, 180)
                count = int(time_per_filter / (exposure / 60))

                lights[filter_name] = PlanItem(
                    frame_type="light",
                    filter_name=filter_name,
                    exposure=exposure,
                    count=count,
                    total_time=count * (exposure / 60)
                )

        return lights

    def _generate_darks_plan(self, lights: Dict[str, PlanItem]) -> List[PlanItem]:
        """
        Generate darks plan based on lights

        Rule: 20 darks per unique exposure time
        """
        darks = []
        unique_exposures = set()

        for item in lights.values():
            if item.exposure not in unique_exposures:
                unique_exposures.add(item.exposure)

                darks.append(PlanItem(
                    frame_type="dark",
                    exposure=item.exposure,
                    gain=item.gain,
                    count=20,
                    total_time=20 * (item.exposure / 60)
                ))

        return darks

    def _generate_flats_plan(self, lights: Dict[str, PlanItem]) -> List[PlanItem]:
        """
        Generate flats plan based on lights

        Rule: 20 flats per filter
        """
        flats = []
        unique_filters = set()

        for filter_name, item in lights.items():
            if filter_name not in unique_filters:
                unique_filters.add(filter_name)

                # Flats are typically 1-2s exposure
                flats.append(PlanItem(
                    frame_type="flat",
                    filter_name=filter_name,
                    exposure=1,  # Auto-exposure in practice
                    count=20,
                    total_time=20 * (1 / 60)
                ))

        return flats

    def _generate_bias_plan(self) -> PlanItem:
        """
        Generate bias plan

        Rule: 50 bias frames
        """
        return PlanItem(
            frame_type="bias",
            exposure=0,
            count=50,
            total_time=50 * (0.001 / 60)  # Minimal time
        )
