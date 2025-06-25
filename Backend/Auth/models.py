from sqlalchemy import Column, String, Date, DateTime
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict 
import re
from db import Base

class User(Base):
    __tablename__ = "users"

    serial_number = Column(String(10), primary_key=True, index=True)
    name = Column(String, nullable=False)  
    surname = Column(String, nullable=False) 
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    fiscal_code = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    residence = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic schemas for request/responses

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str 
    surname: str 
    email: EmailStr
    password: str
    role: str = Field(..., pattern="^(student|teacher)$")
    fiscalCode: str
    birthDate: date
    residence: str

    @field_validator('fiscalCode')
    @classmethod
    def check_fiscal_code(cls, v):
        if not re.fullmatch(r"[A-Z0-9]{16}", v):
            raise ValueError('Invalid fiscal code format')
        return v

class UpdateOwnProfileRequest(BaseModel):
    residence: str | None = None
    password: str | None = None
    old_password: str | None = None

class UserProfileFull(BaseModel):
    name: str 
    surname: str 
    serialNumber: str = Field(..., pattern=r"^\d{10}$")
    email: EmailStr
    role: str = Field(..., pattern="^(student|teacher)$")
    fiscalCode: str
    birthDate: date
    residence: str

class UserProfileNoId(BaseModel):
    name: str 
    surname: str
    email: EmailStr
    role: str = Field(..., pattern="^(student|teacher)$")

class StudentDetails(BaseModel):
    name: str
    surname: str
    serialNumber: str = Field(..., pattern=r"^\d{10}$")
    email: EmailStr
    role: str = Field(default="student", pattern="^student$") 

#  MODELLI PER LA RICERCA
class StudentPublicProfile(BaseModel):
    name: str
    surname: str
    email: EmailStr
    role: str = Field(default="student", pattern="^student$")

class StudentTeacherView(BaseModel):
    name: str
    surname: str
    serialNumber: str = Field(..., pattern=r"^\d{10}$")
    email: EmailStr
    role: str = Field(default="student", pattern="^student$")

class TeacherPublicProfile(BaseModel):
    name: str
    surname: str
    email: EmailStr
    role: str 

    model_config = ConfigDict(from_attributes=True)