import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.api.models import TelegramLink, Student, IdentityState

log = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def resolve_identity(self, telegram_id: int, telegram_username: str | None) -> IdentityState:
        """
        Calculates the explicit IdentityState for the incoming user interaction.
        """
        link = self.db.query(TelegramLink).filter_by(telegram_id=str(telegram_id)).first()
        
        # Scenario 1: First time user (No link exists)
        if not link:
            # Auto-upsert ghost record
            new_link = TelegramLink(
                telegram_id=str(telegram_id),
                telegram_username=telegram_username,
                student_id=None,
                is_conflicted=False
            )
            self.db.add(new_link)
            self.db.commit()
            return IdentityState.GUEST
            
        # Scenario 2: Administrative Quarantined
        if link.is_conflicted:
            return IdentityState.CONFLICTED
            
        # Scenario 3: Missing Institution Binding
        if not link.student_id:
            return IdentityState.GUEST
            
        # Scenario 4: Fully Verified
        return IdentityState.VERIFIED

    def bind_student_id(self, telegram_id: int, telegram_username: str | None, student_id: str) -> IdentityState:
        """
        Attempts to soft-bind the executing Telegram profile to a Student ID record.
        """
        student_id = student_id.strip()
        student = self.db.query(Student).filter_by(id=student_id).first()
        
        if not student:
            # Invalid/Unrecognized Institute ID
            return IdentityState.GUEST
            
        link = self.db.query(TelegramLink).filter_by(telegram_id=str(telegram_id)).first()
        if not link:
            link = TelegramLink(telegram_id=str(telegram_id), telegram_username=telegram_username)
            self.db.add(link)
            
        # Check if the Student ID is already bound to ANOTHER Telegram ID
        existing_binding = self.db.query(TelegramLink).filter(
            TelegramLink.student_id == student_id,
            TelegramLink.telegram_id != str(telegram_id)
        ).first()
        
        if existing_binding:
            # Conflict Detected! User A trying to claim User B's student_id
            link.is_conflicted = True
            self.db.commit()
            return IdentityState.CONFLICTED
            
        # Safe to bind
        link.student_id = student_id
        link.is_conflicted = False
        self.db.commit()
        return IdentityState.VERIFIED
