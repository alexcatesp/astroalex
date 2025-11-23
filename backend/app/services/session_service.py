"""
Service for managing observing sessions
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from app.models.session import (
    ObservingSession,
    SessionCreate,
    SessionUpdate,
    SessionListItem,
    SessionStatus,
    AssistantMessage
)


class SessionService:
    """Service for CRUD operations on observing sessions"""

    def __init__(self, base_dir: str = "./data/sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session metadata file"""
        return self.base_dir / f"{session_id}.json"

    def create_session(self, session_data: SessionCreate) -> ObservingSession:
        """Create a new observing session"""
        session_id = str(uuid.uuid4())

        session = ObservingSession(
            id=session_id,
            name=session_data.name,
            date=session_data.date or datetime.utcnow(),
            location=session_data.location,
            equipment_profile_id=session_data.equipment_profile_id,
            status=SessionStatus.CREATED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Add welcome message
        welcome_msg = AssistantMessage(
            step="created",
            message=f"Sesión '{session_data.name}' creada. Empecemos analizando las condiciones de observación.",
        )
        session.messages.append(welcome_msg)

        # Save to disk
        self._save_session(session)

        return session

    def get_session(self, session_id: str) -> Optional[ObservingSession]:
        """Get session by ID"""
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return None

        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ObservingSession(**data)

    def list_sessions(self) -> List[SessionListItem]:
        """List all sessions"""
        sessions = []

        for session_file in self.base_dir.glob("*.json"):
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            session_item = SessionListItem(
                id=data["id"],
                name=data["name"],
                date=data["date"],
                status=data["status"],
                target_name=data.get("target", {}).get("name") if data.get("target") else None,
                location_name=data.get("location", {}).get("name") if data.get("location") else None,
                created_at=data["created_at"]
            )
            sessions.append(session_item)

        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x.created_at, reverse=True)

        return sessions

    def update_session(self, session_id: str, update_data: SessionUpdate) -> Optional[ObservingSession]:
        """Update session data"""
        session = self.get_session(session_id)

        if not session:
            return None

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if value is not None:
                setattr(session, field, value)

        session.updated_at = datetime.utcnow()

        # Save updated session
        self._save_session(session)

        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        session_file.unlink()
        return True

    def add_message(self, session_id: str, step: str, message: str, data: Optional[dict] = None) -> Optional[ObservingSession]:
        """Add an assistant message to the session"""
        session = self.get_session(session_id)

        if not session:
            return None

        assistant_msg = AssistantMessage(
            step=step,
            message=message,
            data=data
        )
        session.messages.append(assistant_msg)
        session.updated_at = datetime.utcnow()

        self._save_session(session)

        return session

    def update_status(self, session_id: str, status: SessionStatus) -> Optional[ObservingSession]:
        """Update session status"""
        session = self.get_session(session_id)

        if not session:
            return None

        session.status = status
        session.updated_at = datetime.utcnow()

        if status == SessionStatus.COMPLETED:
            session.completed_at = datetime.utcnow()

        self._save_session(session)

        return session

    def _save_session(self, session: ObservingSession):
        """Save session to disk"""
        session_file = self._get_session_file(session.id)

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.dict(), f, indent=2, default=str)
