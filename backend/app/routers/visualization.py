"""
Visualization and export API endpoints
"""
from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.visualization import MosaicAssembler, ColorCombiner, ImageExporter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visualization", tags=["visualization"])


# Request models
class MosaicRequest(BaseModel):
    panel_paths: List[str]
    output_path: str
    background_match: bool = True


class LRGBRequest(BaseModel):
    l_path: Optional[str] = None
    r_path: str
    g_path: str
    b_path: str
    output_path: str
    l_weight: float = 1.0


class NarrowbandRequest(BaseModel):
    channel_1_path: str
    channel_2_path: str
    channel_3_path: str
    output_path: str
    mapping: Literal["SHO", "HOO", "Custom"] = "SHO"


class ExportRequest(BaseModel):
    fits_path: str
    output_path: str
    format: Literal["fits", "tiff", "jpg", "png"] = "tiff"
    bit_depth: Literal[8, 16] = 16
    stretch: bool = True
    stretch_method: str = "asinh"


@router.post("/mosaic")
async def assemble_mosaic(request: MosaicRequest):
    """Assemble mosaic from multiple panels."""
    try:
        result = MosaicAssembler.assemble_mosaic(
            panel_paths=request.panel_paths,
            output_path=request.output_path,
            background_match=request.background_match,
        )
        return result
    except Exception as e:
        logger.error(f"Error assembling mosaic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/color/lrgb")
async def combine_lrgb(request: LRGBRequest):
    """Combine LRGB images."""
    try:
        result = ColorCombiner.combine_lrgb(
            l_path=request.l_path,
            r_path=request.r_path,
            g_path=request.g_path,
            b_path=request.b_path,
            output_path=request.output_path,
            l_weight=request.l_weight,
        )
        return result
    except Exception as e:
        logger.error(f"Error combining LRGB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/color/narrowband")
async def combine_narrowband(request: NarrowbandRequest):
    """Combine narrowband images (SHO, HOO, etc.)."""
    try:
        result = ColorCombiner.combine_narrowband(
            channel_1_path=request.channel_1_path,
            channel_2_path=request.channel_2_path,
            channel_3_path=request.channel_3_path,
            output_path=request.output_path,
            mapping=request.mapping,
        )
        return result
    except Exception as e:
        logger.error(f"Error combining narrowband: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_image(request: ExportRequest):
    """Export FITS image to various formats."""
    try:
        result = ImageExporter.export(
            fits_path=request.fits_path,
            output_path=request.output_path,
            format=request.format,
            bit_depth=request.bit_depth,
            stretch=request.stretch,
            stretch_method=request.stretch_method,
        )
        return result
    except Exception as e:
        logger.error(f"Error exporting image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
