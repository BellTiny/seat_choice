from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import QueueStatus, RoundStatus, SelectionPhase, TieBreakMode


class SemesterCreate(BaseModel):
    name: str
    is_active: bool = True


class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class SemesterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class RoundCreate(BaseModel):
    semester_id: int
    name: str
    status: RoundStatus = RoundStatus.not_started
    ranking_tiebreak: TieBreakMode = TieBreakMode.student_id_asc
    allowed_selection_count: int = Field(default=1, ge=1)


class RoundUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[RoundStatus] = None
    ranking_tiebreak: Optional[TieBreakMode] = None
    allowed_selection_count: Optional[int] = Field(default=None, ge=1)
    site_open: Optional[bool] = None


class RoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    semester_id: int
    name: str
    status: RoundStatus
    ranking_tiebreak: TieBreakMode
    site_open: bool
    selection_phase: SelectionPhase
    allowed_selection_count: int


class QueueItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    student_id: int
    student_code: str | None = None
    student_name: str | None = None
    rank_order: int
    phase: SelectionPhase
    status: QueueStatus
    swap_count: int
