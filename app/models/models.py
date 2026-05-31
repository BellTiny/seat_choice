from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    student = "student"


class RoundStatus(str, enum.Enum):
    not_started = "not_started"
    selecting = "selecting"
    finished = "finished"


class SelectionPhase(str, enum.Enum):
    normal = "normal"
    makeup = "makeup"
    closed = "closed"


class TieBreakMode(str, enum.Enum):
    student_id_asc = "student_id_asc"
    random = "random"


class SeatStatus(str, enum.Enum):
    available = "available"
    locked = "locked"
    selected = "selected"


class QueueStatus(str, enum.Enum):
    pending = "pending"
    current = "current"
    completed = "completed"
    skipped = "skipped"
    locked = "locked"


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class SwapStatus(str, enum.Enum):
    pending_target = "pending_target"
    pending_admin = "pending_admin"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class SpecialRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    student_id = Column(String(50), unique=True, nullable=True, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    hashed_password = Column(String(255), nullable=False)
    moral_score = Column(Float, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False)


class SiteSetting(Base, TimestampMixin):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, default=1)
    round_interval_days = Column(Integer, nullable=False, default=14)
    max_swap_count = Column(Integer, nullable=False, default=1)
    swap_reason_required = Column(Boolean, nullable=False, default=True)
    team_enabled = Column(Boolean, nullable=False, default=False)
    team_max_carry = Column(Integer, nullable=False, default=1)
    team_adjacent_required = Column(Boolean, nullable=False, default=True)
    team_adjacent_distance = Column(Integer, nullable=False, default=1)
    special_request_open = Column(Boolean, nullable=False, default=False)
    default_orientation = Column(Integer, nullable=False, default=0)
    webhook_url = Column(String(500), nullable=True)
    jwt_expire_minutes = Column(Integer, nullable=False, default=720)


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class SeatRound(Base, TimestampMixin):
    __tablename__ = "seat_rounds"

    id = Column(Integer, primary_key=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(Enum(RoundStatus), nullable=False, default=RoundStatus.not_started)
    ranking_tiebreak = Column(Enum(TieBreakMode), nullable=False, default=TieBreakMode.student_id_asc)
    site_open = Column(Boolean, nullable=False, default=False)
    selection_phase = Column(Enum(SelectionPhase), nullable=False, default=SelectionPhase.normal)
    allowed_selection_count = Column(Integer, nullable=False, default=1)

    semester = relationship("Semester")


class ClassroomLayout(Base, TimestampMixin):
    __tablename__ = "classroom_layouts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class Seat(Base, TimestampMixin):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("layout_id", "seat_code", name="uq_layout_seat_code"),
        UniqueConstraint("layout_id", "row_index", "col_index", name="uq_layout_position"),
    )

    id = Column(Integer, primary_key=True, index=True)
    layout_id = Column(Integer, ForeignKey("classroom_layouts.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    col_index = Column(Integer, nullable=False)
    seat_code = Column(String(20), nullable=False)
    status = Column(Enum(SeatStatus), nullable=False, default=SeatStatus.available)
    tags = Column(JSON, nullable=False, default=list)
    locked_student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    selected_student_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    layout = relationship("ClassroomLayout")
    locked_student = relationship("User", foreign_keys=[locked_student_id])
    selected_student = relationship("User", foreign_keys=[selected_student_id])


class SeatSelection(Base, TimestampMixin):
    __tablename__ = "seat_selections"
    __table_args__ = (UniqueConstraint("round_id", "student_id", name="uq_round_student_selection"),)

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("seat_rounds.id"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assignment_type = Column(String(20), nullable=False, default="free")

    seat = relationship("Seat")
    student = relationship("User")
    round = relationship("SeatRound")


class RoundQueueItem(Base, TimestampMixin):
    __tablename__ = "round_queue_items"
    __table_args__ = (UniqueConstraint("round_id", "student_id", name="uq_round_student_queue"),)

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("seat_rounds.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rank_order = Column(Integer, nullable=False)
    phase = Column(Enum(SelectionPhase), nullable=False, default=SelectionPhase.normal)
    status = Column(Enum(QueueStatus), nullable=False, default=QueueStatus.pending)
    swap_count = Column(Integer, nullable=False, default=0)

    round = relationship("SeatRound")
    student = relationship("User")


class TeamInvite(Base, TimestampMixin):
    __tablename__ = "team_invites"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("seat_rounds.id"), nullable=False, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(InviteStatus), nullable=False, default=InviteStatus.pending)

    round = relationship("SeatRound")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])


class SwapRequest(Base, TimestampMixin):
    __tablename__ = "swap_requests"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("seat_rounds.id"), nullable=False, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(SwapStatus), nullable=False, default=SwapStatus.pending_target)
    review_comment = Column(Text, nullable=True)

    round = relationship("SeatRound")
    requester = relationship("User", foreign_keys=[requester_id])
    target = relationship("User", foreign_keys=[target_id])


class SpecialSeatRequest(Base, TimestampMixin):
    __tablename__ = "special_seat_requests"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("seat_rounds.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    requested_tag = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(Enum(SpecialRequestStatus), nullable=False, default=SpecialRequestStatus.pending)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)

    round = relationship("SeatRound")
    student = relationship("User", foreign_keys=[student_id])
    requested_seat = relationship("Seat", foreign_keys=[requested_seat_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
