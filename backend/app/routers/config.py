"""
Configuration Router
API endpoints for app configuration and user state management
"""
from fastapi import APIRouter, HTTPException
from app.models.config import AppConfig, UserState, StorageConfig
from app.services.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["config"])
config_service = ConfigService()


@router.get("/", response_model=AppConfig)
async def get_config():
    """
    Get complete application configuration

    Returns user state, storage config, and all settings.
    """
    return config_service.get_config()


@router.get("/user-state", response_model=UserState)
async def get_user_state():
    """
    Get current user state

    Returns onboarding status, preferences, and active equipment profile.
    """
    return config_service.get_user_state()


@router.patch("/user-state", response_model=UserState)
async def update_user_state(updates: dict):
    """
    Update user state

    Updates user preferences and onboarding flags.
    """
    return config_service.update_user_state(**updates)


@router.get("/storage", response_model=StorageConfig)
async def get_storage_config():
    """
    Get storage configuration

    Returns paths for raw data, processed data, projects, and cache.
    """
    storage = config_service.get_storage_config()
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not configured")
    return storage


@router.put("/storage", response_model=StorageConfig)
async def set_storage_config(storage_config: StorageConfig):
    """
    Set storage configuration

    Configures paths for data storage. Validates that paths exist or can be created.
    """
    # Validate paths
    validation_results = storage_config.validate_paths()
    invalid_paths = [
        path for path, result in validation_results.items()
        if not result["valid"]
    ]

    if invalid_paths:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Some paths are invalid",
                "invalid_paths": invalid_paths,
                "validation_results": validation_results
            }
        )

    return config_service.set_storage_config(storage_config)


@router.post("/onboarding/complete")
async def complete_onboarding():
    """
    Mark onboarding as completed

    Sets onboarding_completed and first_time flags.
    """
    config_service.complete_onboarding()
    return {"message": "Onboarding completed"}
