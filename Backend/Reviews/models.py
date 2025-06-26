# models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime, timezone # Aggiunto timezone
# import re # Non più necessario

# --- Helper Validation Patterns ---
OBJECT_ID_PATTERN = r'^[0-9a-fA-F]{24}$'
SERIAL_NUMBER_PATTERN = r'^\d{10}$' # Puoi provare con '^[0-9]{10}$' se \d dà problemi a Connexion

# --- Tipi Annotati ---
AnnotatedObjectIdStr = Annotated[str, Field(
    pattern=OBJECT_ID_PATTERN,
    description="MongoDB ObjectId (24-character hex string)",
    examples=["507f1f77bcf86cd799439011"] 
)]

AnnotatedSerialNumberStr = Annotated[str, Field(
    pattern=SERIAL_NUMBER_PATTERN,
    description="Serial number (10 digits)",
    examples=["1234567890"] 
)]

# --- Funzione Helper per Encoder JSON di Datetime ---
def _custom_datetime_encoder(dt: datetime) -> str:
    """Assicura che datetime sia UTC e formattato con Z."""
    if dt.tzinfo is None: # Se naive, Pydantic V2 di solito lo considera già UTC per isoformat
        # dt = dt.replace(tzinfo=timezone.utc) # Opzionale, Pydantic dovrebbe gestirlo
        pass
    else: # Se aware, converti a UTC
        dt = dt.astimezone(timezone.utc)
    # Pydantic V2 .isoformat() per datetime di default include microsecondi e Z se UTC.
    # timespec='milliseconds' per troncare a millisecondi se necessario.
    return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


# --- Modelli per Request Body ---
class EvaluationItem(BaseModel):
    criterion: str = Field(..., min_length=1, max_length=255)
    score: int = Field(..., ge=0, le=100)
    feedback: Optional[str] = Field(None, max_length=1000)
    model_config = {"extra": "forbid"}

class ManualAssignmentItem(BaseModel):
    reviewerserialNumber: AnnotatedSerialNumberStr
    submissionId: str 
    model_config = {"extra": "forbid"}

class ManualAssignmentRequestModel(BaseModel):
    assignmentId: AnnotatedObjectIdStr
    manualAssignments: List[ManualAssignmentItem] = Field(..., min_length=1, max_length=50)
    model_config = {"extra": "forbid"}

class AutoAssignmentRequestModel(BaseModel):
    assignmentId: AnnotatedObjectIdStr
    minReviews: int = Field(..., ge=1, le=10)
    model_config = {"extra": "forbid"}

class ReviewSubmission(BaseModel):
    evaluation: List[EvaluationItem] = Field(..., min_length=1, max_length=20)
    model_config = {"extra": "forbid"}

# --- Modelli per Response Body ---
class PeerReviewAssignmentWithDetails(BaseModel):
    reviewId: AnnotatedObjectIdStr = Field(..., alias="_id")
    submissionId: str 
    assignmentId: AnnotatedObjectIdStr
    reviewerserialNumber: AnnotatedSerialNumberStr
    reviewerName: Optional[str] = None
    reviewerSurname: Optional[str] = None
    authorSerialNumber: AnnotatedSerialNumberStr
    authorName: Optional[str] = None
    authorSurname: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
        "json_encoders": {
            datetime: _custom_datetime_encoder 
        }
    }

class PeerReviewResponseWithDetails(BaseModel):
    reviewId: AnnotatedObjectIdStr = Field(..., alias="_id")
    submissionId: str 
    assignmentId: AnnotatedObjectIdStr
    reviewerserialNumber: AnnotatedSerialNumberStr
    reviewerName: Optional[str] = None
    reviewerSurname: Optional[str] = None
    authorSerialNumber: AnnotatedSerialNumberStr
    authorName: Optional[str] = None
    authorSurname: Optional[str] = None
    evaluation: Optional[List[EvaluationItem]] = Field(None, max_length=20)
    createdAt: Optional[datetime] = None
    submittedAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
        "json_encoders": {
            datetime: _custom_datetime_encoder
        }
    }