"""
Configuration Service
Manages application configuration and user state
"""
import json
from pathlib import Path
from typing import Optional

from app.models.config import AppConfig, UserState, StorageConfig


class ConfigService:
    """Service for managing application configuration"""

    def __init__(self, config_file: str = "./data/config/app_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with default config if file doesn't exist
        if not self.config_file.exists():
            default_config = AppConfig()
            self._save_config(default_config)

    def _load_config(self) -> AppConfig:
        """Load configuration from file"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return AppConfig()

    def _save_config(self, config: AppConfig):
        """Save configuration to file"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, default=str)

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self._load_config()

    def get_user_state(self) -> UserState:
        """Get current user state"""
        config = self._load_config()
        return config.user_state

    def update_user_state(self, **updates) -> UserState:
        """Update user state with provided fields"""
        config = self._load_config()

        for key, value in updates.items():
            if hasattr(config.user_state, key):
                setattr(config.user_state, key, value)

        self._save_config(config)
        return config.user_state

    def get_storage_config(self) -> Optional[StorageConfig]:
        """Get storage configuration"""
        config = self._load_config()
        return config.storage

    def set_storage_config(self, storage_config: StorageConfig) -> StorageConfig:
        """Set storage configuration"""
        config = self._load_config()
        config.storage = storage_config
        config.user_state.storage_configured = True
        self._save_config(config)
        return storage_config

    def complete_onboarding(self):
        """Mark onboarding as completed"""
        self.update_user_state(onboarding_completed=True, first_time=False)

    def set_active_equipment_profile(self, profile_id: str):
        """Set the active equipment profile"""
        self.update_user_state(
            active_equipment_profile_id=profile_id,
            has_equipment_profile=True
        )

    def mark_camera_characterized(self):
        """Mark that camera has been characterized"""
        self.update_user_state(has_characterized_camera=True)
