"""
Pipeline orchestration service
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from app.models.pipeline import ProcessingPipeline, ProcessingStep
from app.services.processing.calibrator import ScienceFrameCalibrator
from app.services.processing.quality_analyzer import QualityAnalyzer
from app.services.processing.registrar import ImageRegistrar
from app.services.processing.stacker import ImageStacker

logger = logging.getLogger(__name__)


class PipelineService:
    """Service for managing and executing processing pipelines"""

    def __init__(self, project_path: str):
        """
        Initialize the pipeline service.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.pipelines_dir = self.project_path / "02_processed_data"
        self.metadata_file = self.pipelines_dir / ".pipelines.json"
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        """Ensure the pipelines metadata file exists"""
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            self.metadata_file.write_text(json.dumps({"pipelines": []}, indent=2))

    def _read_metadata(self) -> dict:
        """Read pipelines metadata from file"""
        try:
            return json.loads(self.metadata_file.read_text())
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return {"pipelines": []}

    def _write_metadata(self, data: dict):
        """Write pipelines metadata to file"""
        try:
            self.metadata_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            raise

    def create_pipeline(
        self,
        object_name: str,
        filters: List[str],
        panels: Optional[List[str]] = None,
    ) -> ProcessingPipeline:
        """
        Create a new processing pipeline.

        Args:
            object_name: Astronomical object being processed
            filters: List of filters to process
            panels: Optional mosaic panel names

        Returns:
            Created ProcessingPipeline
        """
        pipeline_id = str(uuid.uuid4())

        pipeline = ProcessingPipeline(
            id=pipeline_id,
            project_id="",  # Set by caller
            object_name=object_name,
            filters=filters,
            panels=panels,
            steps=[],
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        metadata = self._read_metadata()
        metadata["pipelines"].append(pipeline.model_dump())
        self._write_metadata(metadata)

        logger.info(f"Created pipeline: {object_name} (ID: {pipeline_id})")
        return pipeline

    def get_pipelines(self) -> List[ProcessingPipeline]:
        """Get all pipelines"""
        metadata = self._read_metadata()
        return [ProcessingPipeline(**p) for p in metadata["pipelines"]]

    def get_pipeline(self, pipeline_id: str) -> Optional[ProcessingPipeline]:
        """Get a pipeline by ID"""
        metadata = self._read_metadata()
        for p in metadata["pipelines"]:
            if p["id"] == pipeline_id:
                return ProcessingPipeline(**p)
        return None

    def _update_pipeline(self, pipeline: ProcessingPipeline):
        """Update pipeline in metadata"""
        pipeline.updated_at = datetime.now()
        metadata = self._read_metadata()

        for i, p in enumerate(metadata["pipelines"]):
            if p["id"] == pipeline.id:
                metadata["pipelines"][i] = pipeline.model_dump()
                break

        self._write_metadata(metadata)

    def execute_calibration(
        self,
        pipeline_id: str,
        science_paths: List[str],
        master_bias_path: Optional[str] = None,
        master_dark_path: Optional[str] = None,
        master_flat_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute calibration step.

        Args:
            pipeline_id: Pipeline ID
            science_paths: Science frame paths
            master_bias_path: Master bias path
            master_dark_path: Master dark path
            master_flat_path: Master flat path

        Returns:
            Results dictionary
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Output directory
        output_dir = self.project_path / "02_processed_data" / "science" / pipeline.object_name / "calibrated"

        logger.info(f"Executing calibration for {len(science_paths)} frames")

        # Execute calibration
        results = ScienceFrameCalibrator.calibrate_batch(
            science_paths=science_paths,
            output_dir=str(output_dir),
            master_bias_path=master_bias_path,
            master_dark_path=master_dark_path,
            master_flat_path=master_flat_path,
        )

        # Update pipeline
        pipeline.status = "running"
        self._update_pipeline(pipeline)

        successful = sum(1 for r in results if r.get("success"))

        return {
            "total": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results,
        }

    def execute_quality_analysis(
        self,
        pipeline_id: str,
        file_paths: List[str],
    ) -> Dict[str, Any]:
        """
        Execute quality analysis step.

        Args:
            pipeline_id: Pipeline ID
            file_paths: Frame paths to analyze

        Returns:
            Results dictionary
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        logger.info(f"Executing quality analysis for {len(file_paths)} frames")

        # Execute analysis
        metrics = QualityAnalyzer.analyze_batch(file_paths)

        # Update pipeline
        pipeline.status = "running"
        self._update_pipeline(pipeline)

        return {
            "total": len(metrics),
            "metrics": metrics,
        }

    def execute_registration(
        self,
        pipeline_id: str,
        source_paths: List[str],
        reference_path: Optional[str] = None,
        quality_metrics: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Execute registration/alignment step.

        Args:
            pipeline_id: Pipeline ID
            source_paths: Paths to images to align
            reference_path: Optional reference image (auto-selected if None)
            quality_metrics: Optional quality metrics for reference selection

        Returns:
            Results dictionary
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Select reference if not provided
        if not reference_path:
            reference_path = ImageRegistrar.select_reference(source_paths, quality_metrics)

        # Output directory
        output_dir = self.project_path / "02_processed_data" / "science" / pipeline.object_name / "registered"

        logger.info(f"Executing registration for {len(source_paths)} frames")

        # Execute registration
        results = ImageRegistrar.register_batch(
            source_paths=source_paths,
            reference_path=reference_path,
            output_dir=str(output_dir),
        )

        # Update pipeline
        pipeline.status = "running"
        self._update_pipeline(pipeline)

        successful = sum(1 for r in results if r.get("success"))

        return {
            "total": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "reference": reference_path,
            "results": results,
        }

    def execute_stacking(
        self,
        pipeline_id: str,
        file_paths: List[str],
        method: Literal["median", "average", "sum"] = "median",
        rejection: Optional[Literal["sigma_clip", "minmax"]] = "sigma_clip",
    ) -> Dict[str, Any]:
        """
        Execute stacking/integration step.

        Args:
            pipeline_id: Pipeline ID
            file_paths: Paths to registered images
            method: Stacking method
            rejection: Rejection method

        Returns:
            Results dictionary
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Output directory
        output_dir = self.project_path / "02_processed_data" / "science" / pipeline.object_name / "stacked"

        logger.info(f"Executing stacking for {len(file_paths)} frames")

        # Stack by filter
        results = ImageStacker.stack_by_filter(
            file_paths=file_paths,
            output_dir=str(output_dir),
            method=method,
            rejection=rejection,
        )

        # Update pipeline
        pipeline.status = "completed"
        self._update_pipeline(pipeline)

        successful_filters = sum(1 for r in results.values() if r.get("success"))

        return {
            "total_filters": len(results),
            "successful": successful_filters,
            "failed": len(results) - successful_filters,
            "results": results,
        }

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """
        Delete a pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            True if deleted, False if not found
        """
        metadata = self._read_metadata()

        for i, p in enumerate(metadata["pipelines"]):
            if p["id"] == pipeline_id:
                metadata["pipelines"].pop(i)
                self._write_metadata(metadata)
                logger.info(f"Deleted pipeline: {pipeline_id}")
                return True

        return False
