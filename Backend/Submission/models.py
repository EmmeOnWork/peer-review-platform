from datetime import datetime, timezone
from typing import Optional, List # Ensure List is imported
from uuid import uuid4 # uuid4 is not directly used in Submission but good to keep if related utilities use it

class Submission:
    def __init__(
        self,
        assignment_id: str,
        student_serial_number: str,
        text: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        submitted_at: Optional[datetime] = None,
        student_name: Optional[str] = None,
        student_surname: Optional[str] = None
    ):
        self.assignment_id = assignment_id
        self.student_serial_number = student_serial_number
        self.text = text
        self.attachments = attachments if attachments is not None else []
        # Ensure submitted_at is timezone-aware (UTC)
        if submitted_at:
            if submitted_at.tzinfo is None:
                self.submitted_at = submitted_at.replace(tzinfo=timezone.utc)
            else:
                self.submitted_at = submitted_at.astimezone(timezone.utc)
        else:
            self.submitted_at = datetime.now(timezone.utc)
            
        self.student_name = student_name
        self.student_surname = student_surname

    def to_dict(self):
        # Ensure submitted_at is in a consistent state for dictionary conversion
        submitted_at_val = self.submitted_at
        if submitted_at_val.tzinfo is None:
            submitted_at_val = submitted_at_val.replace(tzinfo=timezone.utc)
        else:
            submitted_at_val = submitted_at_val.astimezone(timezone.utc)

        return {
            'assignmentId': self.assignment_id,
            'studentSerialNumber': self.student_serial_number,
            'text': self.text,
            'attachments': self.attachments,
            'submittedAt': submitted_at_val, # Store as datetime object, format to string in handler
            'studentName': self.student_name,
            'studentSurname': self.student_surname
        }

    @staticmethod
    def from_dict(data):
        submitted_at_data = data.get('submittedAt')
        parsed_submitted_at = None
        if isinstance(submitted_at_data, str):
            try:
                if submitted_at_data.endswith('Z'):
                    parsed_submitted_at = datetime.fromisoformat(submitted_at_data[:-1] + '+00:00')
                else:
                    parsed_submitted_at = datetime.fromisoformat(submitted_at_data)
            except ValueError:
                # Handle cases where parsing might fail or use a default
                parsed_submitted_at = datetime.now(timezone.utc) # Or None, or raise error
        elif isinstance(submitted_at_data, datetime):
            parsed_submitted_at = submitted_at_data
        
        # Ensure parsed_submitted_at is timezone-aware
        if parsed_submitted_at:
            if parsed_submitted_at.tzinfo is None:
                parsed_submitted_at = parsed_submitted_at.replace(tzinfo=timezone.utc)
            else:
                parsed_submitted_at = parsed_submitted_at.astimezone(timezone.utc)
        else: # Default if not provided or unparseable
             parsed_submitted_at = datetime.now(timezone.utc)


        return Submission(
            assignment_id=data.get('assignmentId'),
            student_serial_number=data.get('studentSerialNumber'),
            text=data.get('text'),
            attachments=data.get('attachments'),
            submitted_at=parsed_submitted_at,
            student_name=data.get('studentName'),
            student_surname=data.get('studentSurname')
        )