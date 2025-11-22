"""
Project management service layer
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.utils.directory import DirectoryManager

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing astrophotography projects"""

    def __init__(self, projects_base_dir: str):
        """
        Initialize the project service.

        Args:
            projects_base_dir: Base directory where all projects are stored
        """
        self.base_dir = Path(projects_base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.base_dir / ".projects.json"
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        """Ensure the projects metadata file exists"""
        if not self.metadata_file.exists():
            self.metadata_file.write_text(json.dumps({"projects": []}, indent=2))

    def _read_metadata(self) -> dict:
        """Read projects metadata from file"""
        try:
            return json.loads(self.metadata_file.read_text())
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return {"projects": []}

    def _write_metadata(self, data: dict):
        """Write projects metadata to file"""
        try:
            self.metadata_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            raise

    def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create a new astrophotography project.

        Args:
            project_data: Project creation data

        Returns:
            Created project

        Raises:
            ValueError: If project with same name exists
            OSError: If directory creation fails
        """
        # Check if project name already exists
        existing = self.get_project_by_name(project_data.name)
        if existing:
            raise ValueError(f"Project with name '{project_data.name}' already exists")

        # Generate unique ID
        project_id = str(uuid.uuid4())

        # Create directory structure
        try:
            project_path = DirectoryManager.create_project_structure(
                str(self.base_dir), project_data.name
            )
        except FileExistsError as e:
            raise ValueError(str(e))

        # Create project object
        now = datetime.now()
        project = Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            path=project_path,
            created_at=now,
            updated_at=now,
        )

        # Save to metadata
        metadata = self._read_metadata()
        metadata["projects"].append(project.model_dump())
        self._write_metadata(metadata)

        logger.info(f"Created project: {project.name} (ID: {project_id})")
        return project

    def get_all_projects(self) -> List[Project]:
        """
        Get all projects.

        Returns:
            List of all projects
        """
        metadata = self._read_metadata()
        return [Project(**p) for p in metadata["projects"]]

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project if found, None otherwise
        """
        metadata = self._read_metadata()
        for p in metadata["projects"]:
            if p["id"] == project_id:
                return Project(**p)
        return None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Get a project by name.

        Args:
            name: Project name

        Returns:
            Project if found, None otherwise
        """
        metadata = self._read_metadata()
        for p in metadata["projects"]:
            if p["name"] == name:
                return Project(**p)
        return None

    def update_project(self, project_id: str, project_data: ProjectUpdate) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: Project identifier
            project_data: Updated project data

        Returns:
            Updated project if found, None otherwise
        """
        metadata = self._read_metadata()
        for i, p in enumerate(metadata["projects"]):
            if p["id"] == project_id:
                # Update fields
                if project_data.name is not None:
                    p["name"] = project_data.name
                if project_data.description is not None:
                    p["description"] = project_data.description
                p["updated_at"] = datetime.now().isoformat()

                # Save changes
                metadata["projects"][i] = p
                self._write_metadata(metadata)

                logger.info(f"Updated project: {p['name']} (ID: {project_id})")
                return Project(**p)

        return None

    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project identifier
            delete_files: Whether to delete project files from disk

        Returns:
            True if deleted, False if not found
        """
        metadata = self._read_metadata()
        project = None

        # Find and remove project
        for i, p in enumerate(metadata["projects"]):
            if p["id"] == project_id:
                project = p
                metadata["projects"].pop(i)
                break

        if not project:
            return False

        # Delete files if requested
        if delete_files:
            import shutil
            project_path = Path(project["path"])
            if project_path.exists():
                try:
                    shutil.rmtree(project_path)
                    logger.info(f"Deleted project files: {project_path}")
                except Exception as e:
                    logger.error(f"Error deleting project files: {e}")
                    raise

        # Save metadata
        self._write_metadata(metadata)
        logger.info(f"Deleted project: {project['name']} (ID: {project_id})")
        return True

    def validate_project(self, project_id: str) -> bool:
        """
        Validate that a project's directory structure is intact.

        Args:
            project_id: Project identifier

        Returns:
            True if structure is valid, False otherwise
        """
        project = self.get_project(project_id)
        if not project:
            return False

        return DirectoryManager.validate_project_structure(project.path)
