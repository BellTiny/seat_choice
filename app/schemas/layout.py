from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import SeatStatus


class LayoutCreate(BaseModel):
    name: str
    rows: int = Field(ge=1)
    cols: int = Field(ge=1)
    is_active: bool = True


class LayoutUpdate(BaseModel):
    name: Optional[str] = None
    rows: Optional[int] = Field(default=None, ge=1)
    cols: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class SeatAdminUpdate(BaseModel):
    tags: list[str] | None = None


class SeatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    layout_id: int
    row_index: int
    col_index: int
    seat_code: str
    status: SeatStatus
    tags: list[str]
    locked_student_id: int | None
    selected_student_id: int | None


class LayoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rows: int
    cols: int
    is_active: bool
    seats: list[SeatOut] = []
