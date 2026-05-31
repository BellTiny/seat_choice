from pydantic import BaseModel, ConfigDict, Field

from app.models.models import InviteStatus, QueueStatus, SeatStatus, SpecialRequestStatus, SwapStatus


class ScoreImportResult(BaseModel):
    updated_count: int
    ignored_count: int
    ignored_student_ids: list[str]
    created_students: list["ImportedStudentCredential"] = Field(default_factory=list)


class ImportedStudentCredential(BaseModel):
    student_id: str
    username: str
    temporary_password: str


class SeatLockRequest(BaseModel):
    student_id: str | None = None
    seat_id: int


class QueueActionResponse(BaseModel):
    message: str
    current_student_ids: list[str] = []


class SeatChoiceRequest(BaseModel):
    seat_ids: list[int] = Field(min_length=1)


class SeatStatusView(BaseModel):
    id: int
    seat_code: str
    row_index: int
    col_index: int
    status: SeatStatus
    tags: list[str]
    selected_student_id: int | None
    locked_student_id: int | None


class StudentSelectionStatus(BaseModel):
    round_id: int
    round_status: str
    selection_phase: str
    site_open: bool
    queue_status: QueueStatus | None
    queue_rank: int | None
    current_student_ids: list[str]
    can_select: bool
    team_enabled: bool
    default_orientation: int
    seats: list[SeatStatusView]


class TeamInviteCreate(BaseModel):
    invitee_student_id: str


class TeamInviteRespond(BaseModel):
    accept: bool


class TeamInviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    inviter_id: int
    invitee_id: int
    status: InviteStatus


class SwapRequestCreate(BaseModel):
    target_student_id: str
    reason: str | None = None


class SwapRespondRequest(BaseModel):
    accept: bool


class SwapReviewRequest(BaseModel):
    approve: bool
    review_comment: str | None = None


class ForceSwapRequest(BaseModel):
    first_student_id: str
    second_student_id: str


class SwapRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    requester_id: int
    target_id: int
    reason: str | None
    status: SwapStatus
    review_comment: str | None


class SpecialRequestCreate(BaseModel):
    requested_seat_id: int | None = None
    requested_tag: str | None = None
    reason: str | None = None


class SpecialRequestReview(BaseModel):
    approve: bool
    review_comment: str | None = None
    seat_id: int | None = None


class SpecialRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    student_id: int
    requested_seat_id: int | None
    requested_tag: str | None
    reason: str | None
    status: SpecialRequestStatus
    reviewer_id: int | None
    review_comment: str | None
