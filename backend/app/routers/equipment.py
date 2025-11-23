"""
Equipment Profile Router
API endpoints for equipment profile management
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.equipment import (
    EquipmentProfile,
    EquipmentCreate,
    EquipmentUpdate
)
from app.services.equipment_service import EquipmentService
from app.services.config_service import ConfigService

router = APIRouter(prefix="/equipment", tags=["equipment"])
equipment_service = EquipmentService()
config_service = ConfigService()


@router.post("/profiles/", response_model=EquipmentProfile)
async def create_profile(profile_data: EquipmentCreate):
    """
    Create a new equipment profile

    Creates a profile with camera, telescope, mount, and filters.
    If this is the first profile, it will be set as active automatically.
    """
    profile = equipment_service.create_profile(profile_data)

    # Update user state if this is the first profile
    if profile.is_active:
        config_service.set_active_equipment_profile(profile.id)

    return profile


@router.get("/profiles/", response_model=List[EquipmentProfile])
async def list_profiles():
    """
    List all equipment profiles

    Returns all saved equipment profiles, with active profile marked.
    """
    return equipment_service.list_profiles()


@router.get("/profiles/active", response_model=EquipmentProfile)
async def get_active_profile():
    """
    Get the currently active equipment profile

    Returns the profile currently set as active, or 404 if none exists.
    """
    profile = equipment_service.get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No active equipment profile found")
    return profile


@router.get("/profiles/{profile_id}", response_model=EquipmentProfile)
async def get_profile(profile_id: str):
    """
    Get a specific equipment profile by ID
    """
    profile = equipment_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Equipment profile not found")
    return profile


@router.put("/profiles/{profile_id}", response_model=EquipmentProfile)
async def update_profile(profile_id: str, update_data: EquipmentUpdate):
    """
    Update an equipment profile

    Updates the specified profile. If setting as active, all other profiles
    will be automatically deactivated.
    """
    profile = equipment_service.update_profile(profile_id, update_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Equipment profile not found")

    # Update user state if changing active profile
    if update_data.is_active:
        config_service.set_active_equipment_profile(profile.id)

    return profile


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """
    Delete an equipment profile

    Deletes the profile. If deleting the active profile and other profiles exist,
    the first remaining profile will be set as active.
    """
    success = equipment_service.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment profile not found")

    return {"message": "Equipment profile deleted successfully"}


@router.post("/profiles/{profile_id}/activate", response_model=EquipmentProfile)
async def activate_profile(profile_id: str):
    """
    Set a profile as the active one

    Convenience endpoint to activate a profile. All other profiles will be deactivated.
    """
    profile = equipment_service.set_active_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Equipment profile not found")

    config_service.set_active_equipment_profile(profile.id)
    return profile
