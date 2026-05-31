from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole
    student_id: Optional[str] = None
    moral_score: float = 0
    is_active: bool = True
    must_change_password: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    student_id: Optional[str] = None
    moral_score: Optional[float] = None
    is_active: Optional[bool] = None
    must_change_password: Optional[bool] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: UserRole
    student_id: Optional[str]
    moral_score: float
    is_active: bool
    must_change_password: bool


class StudentScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: Optional[str]
    full_name: str
    moral_score: float
    is_active: bool
