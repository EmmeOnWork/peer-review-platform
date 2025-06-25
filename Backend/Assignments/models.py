from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import re

class RubricItem(BaseModel):
    criterion: str
    maxScore: int = Field(..., ge=0, description="Maximum score for the criterion")

class Assignment(BaseModel):
    title: str
    description: str
    deadline: datetime
    rubric: List[RubricItem]
    students: List[str]
    teacherSerialNumber: Optional[str]
    teacherName: Optional[str] = None
    teacherSurname: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    @field_validator('students')
    @classmethod
    def check_students(cls, v):
        if not v:
            raise ValueError("At least one student must be assigned")
        for student in v:
            if not re.fullmatch(r'\d{10}', student):
                raise ValueError('Each student serial number must be exactly 10 digits')
        return v

    @field_validator('teacherSerialNumber')
    @classmethod
    def check_teacher_serial(cls, v):
        if not re.fullmatch(r'\d{10}', v):
            raise ValueError('Teacher serial number must be exactly 10 digits')
        return v

    @field_validator('teacherName')
    @classmethod
    def check_teacher_name(cls, v):
        # No specific regex validation for teacherName, as it's a string
        if not v:
            raise ValueError('Teacher name cannot be empty')
        return v

    @field_validator('teacherSurname')
    @classmethod
    def check_teacher_surname(cls, v):
        # No specific regex validation for teacherSurname, as it's a string
        if not v:
            raise ValueError('Teacher surname cannot be empty')
        return v

    