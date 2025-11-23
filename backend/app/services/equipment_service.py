"""
Equipment Profile Service
Manages CRUD operations for equipment profiles
"""
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.models.equipment import (
    EquipmentProfile,
    EquipmentCreate,
    EquipmentUpdate
)


class EquipmentService:
    """Service for managing equipment profiles"""

    def __init__(self, base_dir: str = "./data/equipment"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.base_dir / "profiles.json"

        # Initialize file if it doesn't exist
        if not self.profiles_file.exists():
            self._save_profiles([])

    def _load_profiles(self) -> List[EquipmentProfile]:
        """Load all profiles from file"""
        try:
            with open(self.profiles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [EquipmentProfile(**profile) for profile in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_profiles(self, profiles: List[EquipmentProfile]):
        """Save all profiles to file"""
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(
                [profile.model_dump() for profile in profiles],
                f,
                indent=2,
                default=str
            )

    def create_profile(self, profile_data: EquipmentCreate) -> EquipmentProfile:
        """Create a new equipment profile"""
        profiles = self._load_profiles()

        # Check if this is the first profile
        is_first = len(profiles) == 0

        # Create new profile
        profile = EquipmentProfile(
            id=str(uuid.uuid4()),
            name=profile_data.name,
            description=profile_data.description,
            camera=profile_data.camera,
            telescope=profile_data.telescope,
            mount=profile_data.mount,
            filters=profile_data.filters,
            default_location=profile_data.default_location,
            is_active=is_first,  # Auto-activate if first profile
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        profiles.append(profile)
        self._save_profiles(profiles)

        return profile

    def list_profiles(self) -> List[EquipmentProfile]:
        """List all equipment profiles"""
        return self._load_profiles()

    def get_profile(self, profile_id: str) -> Optional[EquipmentProfile]:
        """Get a specific equipment profile by ID"""
        profiles = self._load_profiles()
        for profile in profiles:
            if profile.id == profile_id:
                return profile
        return None

    def get_active_profile(self) -> Optional[EquipmentProfile]:
        """Get the currently active equipment profile"""
        profiles = self._load_profiles()
        for profile in profiles:
            if profile.is_active:
                return profile
        return None

    def update_profile(
        self,
        profile_id: str,
        update_data: EquipmentUpdate
    ) -> Optional[EquipmentProfile]:
        """Update an equipment profile"""
        profiles = self._load_profiles()

        for i, profile in enumerate(profiles):
            if profile.id == profile_id:
                # Update only provided fields
                update_dict = update_data.model_dump(exclude_unset=True)

                # If setting this profile as active, deactivate others
                if update_dict.get("is_active"):
                    for other_profile in profiles:
                        if other_profile.id != profile_id:
                            other_profile.is_active = False

                # Apply updates
                for key, value in update_dict.items():
                    setattr(profile, key, value)

                profile.updated_at = datetime.now()
                profiles[i] = profile
                self._save_profiles(profiles)
                return profile

        return None

    def delete_profile(self, profile_id: str) -> bool:
        """Delete an equipment profile"""
        profiles = self._load_profiles()
        initial_count = len(profiles)

        # Filter out the profile to delete
        profiles = [p for p in profiles if p.id != profile_id]

        if len(profiles) < initial_count:
            # If we deleted the active profile and there are others, activate the first one
            if len(profiles) > 0 and not any(p.is_active for p in profiles):
                profiles[0].is_active = True

            self._save_profiles(profiles)
            return True

        return False

    def set_active_profile(self, profile_id: str) -> Optional[EquipmentProfile]:
        """Set a profile as active"""
        update_data = EquipmentUpdate(is_active=True)
        return self.update_profile(profile_id, update_data)
