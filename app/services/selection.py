from __future__ import annotations

import random
from collections import deque

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import (
    ClassroomLayout,
    InviteStatus,
    QueueStatus,
    RoundQueueItem,
    RoundStatus,
    Seat,
    SeatRound,
    SeatSelection,
    SeatStatus,
    SelectionPhase,
    SiteSetting,
    SpecialSeatRequest,
    SpecialRequestStatus,
    SwapRequest,
    SwapStatus,
    TeamInvite,
    TieBreakMode,
    User,
    UserRole,
)


def get_or_create_settings(db: Session) -> SiteSetting:
    settings = db.query(SiteSetting).filter(SiteSetting.id == 1).first()
    if settings:
        return settings
    settings = SiteSetting(id=1)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def seat_code_for(row_index: int, col_index: int) -> str:
    value = row_index
    letters: list[str] = []
    while value >= 0:
        value, remainder = divmod(value, 26)
        letters.append(chr(ord("A") + remainder))
        value -= 1
    return "".join(reversed(letters)) + str(col_index + 1)


def generate_layout_seats(db: Session, layout: ClassroomLayout) -> list[Seat]:
    seats: list[Seat] = []
    for row in range(layout.rows):
        for col in range(layout.cols):
            seats.append(
                Seat(
                    layout_id=layout.id,
                    row_index=row,
                    col_index=col,
                    seat_code=seat_code_for(row, col),
                    status=SeatStatus.available,
                    tags=["normal"],
                )
            )
    db.add_all(seats)
    db.commit()
    for seat in seats:
        db.refresh(seat)
    return seats


def get_active_layout(db: Session) -> ClassroomLayout:
    layout = (
        db.query(ClassroomLayout)
        .filter(ClassroomLayout.is_active.is_(True))
        .order_by(ClassroomLayout.id.desc())
        .first()
    )
    if not layout:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active classroom layout is required")
    return layout


def get_round_or_404(db: Session, round_id: int) -> SeatRound:
    round_obj = db.query(SeatRound).filter(SeatRound.id == round_id).first()
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    return round_obj


def get_student_by_student_id(db: Session, student_id: str) -> User:
    student = db.query(User).filter(User.student_id == student_id, User.role == UserRole.student).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def get_layout_or_404(db: Session, layout_id: int) -> ClassroomLayout:
    layout = db.query(ClassroomLayout).filter(ClassroomLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout not found")
    return layout


def get_seat_or_404(db: Session, seat_id: int) -> Seat:
    seat = db.query(Seat).filter(Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return seat


def _sorted_students(db: Session, tie_break_mode: TieBreakMode) -> list[User]:
    students = db.query(User).filter(User.role == UserRole.student, User.is_active.is_(True)).all()
    if tie_break_mode == TieBreakMode.random:
        seed_map = {student.id: random.random() for student in students}
        return sorted(students, key=lambda item: (-item.moral_score, seed_map[item.id]))
    return sorted(students, key=lambda item: (-item.moral_score, item.student_id or "", item.username))


def prepare_round(db: Session, round_obj: SeatRound) -> list[RoundQueueItem]:
    layout = get_active_layout(db)
    seats = db.query(Seat).filter(Seat.layout_id == layout.id).order_by(Seat.row_index, Seat.col_index).all()
    if not seats:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Layout has no seats")

    db.query(SeatSelection).filter(SeatSelection.round_id == round_obj.id).delete(synchronize_session=False)
    db.query(RoundQueueItem).filter(RoundQueueItem.round_id == round_obj.id).delete(synchronize_session=False)

    locked_map: dict[int, Seat] = {}
    for seat in seats:
        if seat.locked_student_id:
            seat.status = SeatStatus.locked
            seat.selected_student_id = seat.locked_student_id
            locked_map[seat.locked_student_id] = seat
        else:
            seat.status = SeatStatus.available
            seat.selected_student_id = None

    queue_items: list[RoundQueueItem] = []
    students = _sorted_students(db, round_obj.ranking_tiebreak)
    for index, student in enumerate(students, start=1):
        if student.id in locked_map:
            queue_items.append(
                RoundQueueItem(
                    round_id=round_obj.id,
                    student_id=student.id,
                    rank_order=index,
                    phase=SelectionPhase.closed,
                    status=QueueStatus.locked,
                )
            )
            db.add(
                SeatSelection(
                    round_id=round_obj.id,
                    seat_id=locked_map[student.id].id,
                    student_id=student.id,
                    assignment_type="locked",
                )
            )
        else:
            queue_items.append(
                RoundQueueItem(
                    round_id=round_obj.id,
                    student_id=student.id,
                    rank_order=index,
                    phase=SelectionPhase.normal,
                    status=QueueStatus.pending,
                )
            )

    round_obj.status = RoundStatus.selecting
    round_obj.site_open = False
    round_obj.selection_phase = SelectionPhase.normal
    db.add_all(queue_items)
    db.commit()
    return queue_items


def activate_next_batch(db: Session, round_obj: SeatRound) -> list[RoundQueueItem]:
    current_items = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.status == QueueStatus.current)
        .all()
    )
    if current_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current batch is still active")

    next_items = (
        db.query(RoundQueueItem)
        .filter(
            RoundQueueItem.round_id == round_obj.id,
            RoundQueueItem.phase == round_obj.selection_phase,
            RoundQueueItem.status == QueueStatus.pending,
        )
        .order_by(RoundQueueItem.rank_order)
        .limit(round_obj.allowed_selection_count)
        .all()
    )
    for item in next_items:
        item.status = QueueStatus.current
    db.commit()
    return next_items


def skip_current_batch(db: Session, round_obj: SeatRound) -> list[RoundQueueItem]:
    current_items = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.status == QueueStatus.current)
        .order_by(RoundQueueItem.rank_order)
        .all()
    )
    if not current_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No current students to skip")
    for item in current_items:
        item.status = QueueStatus.skipped
    db.commit()
    return current_items


def start_makeup_phase(db: Session, round_obj: SeatRound) -> int:
    unfinished_normal = (
        db.query(RoundQueueItem)
        .filter(
            RoundQueueItem.round_id == round_obj.id,
            RoundQueueItem.phase == SelectionPhase.normal,
            RoundQueueItem.status.in_([QueueStatus.pending, QueueStatus.current]),
        )
        .count()
    )
    if unfinished_normal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Normal queue is not finished")

    skipped_items = (
        db.query(RoundQueueItem)
        .filter(
            RoundQueueItem.round_id == round_obj.id,
            RoundQueueItem.phase == SelectionPhase.normal,
            RoundQueueItem.status == QueueStatus.skipped,
        )
        .order_by(RoundQueueItem.rank_order)
        .all()
    )
    for item in skipped_items:
        item.phase = SelectionPhase.makeup
        item.status = QueueStatus.pending
    round_obj.selection_phase = SelectionPhase.makeup
    db.commit()
    return len(skipped_items)


def finish_round(db: Session, round_obj: SeatRound) -> None:
    round_obj.status = RoundStatus.finished
    round_obj.site_open = False
    round_obj.selection_phase = SelectionPhase.closed
    db.commit()


def _build_adjacency_graph(seats: list[Seat], max_distance: int) -> dict[int, list[int]]:
    graph = {seat.id: [] for seat in seats}
    for current in seats:
        for other in seats:
            if current.id == other.id:
                continue
            distance = abs(current.row_index - other.row_index) + abs(current.col_index - other.col_index)
            if distance <= max_distance:
                graph[current.id].append(other.id)
    return graph


def validate_connected_seats(seats: list[Seat], max_distance: int) -> bool:
    if len(seats) <= 1:
        return True
    graph = _build_adjacency_graph(seats, max_distance)
    visited = set()
    queue = deque([seats[0].id])
    while queue:
        seat_id = queue.popleft()
        if seat_id in visited:
            continue
        visited.add(seat_id)
        queue.extend(graph[seat_id])
    return len(visited) == len(seats)


def get_current_student_ids(db: Session, round_id: int) -> list[str]:
    items = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_id, RoundQueueItem.status == QueueStatus.current)
        .order_by(RoundQueueItem.rank_order)
        .all()
    )
    return [item.student.student_id or item.student.username for item in items]


def _get_team_member_ids(db: Session, round_id: int, selector: User, settings: SiteSetting) -> list[int]:
    if not settings.team_enabled:
        return [selector.id]

    invites = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.round_id == round_id,
            TeamInvite.inviter_id == selector.id,
            TeamInvite.status == InviteStatus.accepted,
        )
        .order_by(TeamInvite.id)
        .limit(settings.team_max_carry)
        .all()
    )
    member_ids = [selector.id] + [invite.invitee_id for invite in invites]
    if len(member_ids) == 1:
        return member_ids

    ranks = {
        item.student_id: item.rank_order
        for item in db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_id, RoundQueueItem.student_id.in_(member_ids))
        .all()
    }
    selector_rank = ranks.get(selector.id)
    if selector_rank is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selector is missing from round queue")
    for member_id in member_ids[1:]:
        if ranks.get(member_id, 10**9) < selector_rank:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team leader must have the highest rank")
    return member_ids


def choose_seats(db: Session, round_obj: SeatRound, selector: User, seat_ids: list[int]) -> list[User]:
    settings = get_or_create_settings(db)
    queue_item = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.student_id == selector.id)
        .first()
    )
    if not queue_item or queue_item.status != QueueStatus.current:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="It is not your turn to choose seats")
    if not round_obj.site_open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat selection site is closed")
    if round_obj.status != RoundStatus.selecting:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Round is not open for selection")

    member_ids = _get_team_member_ids(db, round_obj.id, selector, settings)
    if len(seat_ids) != len(member_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(member_ids)} seat(s) for current selection",
        )

    seats = db.query(Seat).filter(Seat.id.in_(seat_ids)).all()
    seat_map = {seat.id: seat for seat in seats}
    if len(seat_map) != len(seat_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    selected_seats = [seat_map[seat_id] for seat_id in seat_ids]
    for seat in selected_seats:
        if seat.status != SeatStatus.available or seat.selected_student_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Seat {seat.seat_code} is unavailable")

    if settings.team_enabled and len(selected_seats) > 1 and settings.team_adjacent_required:
        if not validate_connected_seats(selected_seats, settings.team_adjacent_distance):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected seats are not adjacent enough")

    queue_items = {
        item.student_id: item
        for item in db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.student_id.in_(member_ids))
        .all()
    }
    ordered_member_ids = sorted(member_ids, key=lambda student_id: queue_items[student_id].rank_order)
    members = db.query(User).filter(User.id.in_(ordered_member_ids)).all()
    member_map = {member.id: member for member in members}

    for seat, member_id in zip(selected_seats, ordered_member_ids):
        existing = (
            db.query(SeatSelection)
            .filter(SeatSelection.round_id == round_obj.id, SeatSelection.student_id == member_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team contains a student with existing seat")
        db.add(
            SeatSelection(
                round_id=round_obj.id,
                seat_id=seat.id,
                student_id=member_id,
                assignment_type="free",
            )
        )
        seat.status = SeatStatus.selected
        seat.selected_student_id = member_id
        queue_items[member_id].status = QueueStatus.completed

    db.commit()
    return [member_map[member_id] for member_id in ordered_member_ids]


def apply_lock_to_student(db: Session, round_obj: SeatRound | None, student: User, seat: Seat) -> None:
    if seat.selected_student_id and seat.selected_student_id != student.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat already belongs to another student")

    existing_locked = db.query(Seat).filter(Seat.locked_student_id == student.id).all()
    for item in existing_locked:
        if item.id != seat.id:
            item.locked_student_id = None
            if item.selected_student_id == student.id:
                item.selected_student_id = None
                item.status = SeatStatus.available

    if round_obj:
        existing_selection = (
            db.query(SeatSelection)
            .filter(SeatSelection.round_id == round_obj.id, SeatSelection.student_id == student.id)
            .first()
        )
        if existing_selection and existing_selection.seat_id != seat.id:
            old_seat = db.query(Seat).filter(Seat.id == existing_selection.seat_id).first()
            if old_seat and old_seat.locked_student_id != student.id:
                old_seat.selected_student_id = None
                old_seat.status = SeatStatus.available
            db.delete(existing_selection)

    seat.locked_student_id = student.id
    seat.selected_student_id = student.id
    seat.status = SeatStatus.locked

    if round_obj:
        db.add(
            SeatSelection(
                round_id=round_obj.id,
                seat_id=seat.id,
                student_id=student.id,
                assignment_type="locked",
            )
        )
        queue_item = (
            db.query(RoundQueueItem)
            .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.student_id == student.id)
            .first()
        )
        if queue_item:
            queue_item.phase = SelectionPhase.closed
            queue_item.status = QueueStatus.locked

    db.commit()


def swap_students_in_round(
    db: Session,
    round_id: int,
    first_student_id: int,
    second_student_id: int,
    increment_counter: bool = True,
) -> None:
    first_selection = (
        db.query(SeatSelection)
        .filter(SeatSelection.round_id == round_id, SeatSelection.student_id == first_student_id)
        .first()
    )
    second_selection = (
        db.query(SeatSelection)
        .filter(SeatSelection.round_id == round_id, SeatSelection.student_id == second_student_id)
        .first()
    )
    if not first_selection or not second_selection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both students must already have seats")

    first_seat = db.query(Seat).filter(Seat.id == first_selection.seat_id).first()
    second_seat = db.query(Seat).filter(Seat.id == second_selection.seat_id).first()
    if (first_seat and first_seat.locked_student_id) or (second_seat and second_seat.locked_student_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Locked seats cannot be swapped")

    first_selection.seat_id, second_selection.seat_id = second_selection.seat_id, first_selection.seat_id
    if first_seat:
        first_seat.selected_student_id = second_student_id
        first_seat.status = SeatStatus.selected
    if second_seat:
        second_seat.selected_student_id = first_student_id
        second_seat.status = SeatStatus.selected

    if increment_counter:
        queue_items = (
            db.query(RoundQueueItem)
            .filter(RoundQueueItem.round_id == round_id, RoundQueueItem.student_id.in_([first_student_id, second_student_id]))
            .all()
        )
        for item in queue_items:
            item.swap_count += 1
    db.commit()


def build_student_status(db: Session, round_obj: SeatRound, student: User) -> dict:
    layout = get_active_layout(db)
    seats = db.query(Seat).filter(Seat.layout_id == layout.id).order_by(Seat.row_index, Seat.col_index).all()
    queue_item = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.student_id == student.id)
        .first()
    )
    settings = get_or_create_settings(db)
    return {
        "round_id": round_obj.id,
        "round_status": round_obj.status.value,
        "selection_phase": round_obj.selection_phase.value,
        "site_open": round_obj.site_open,
        "queue_status": queue_item.status if queue_item else None,
        "queue_rank": queue_item.rank_order if queue_item else None,
        "current_student_ids": get_current_student_ids(db, round_obj.id),
        "can_select": bool(queue_item and queue_item.status == QueueStatus.current and round_obj.site_open),
        "team_enabled": settings.team_enabled,
        "default_orientation": settings.default_orientation,
        "seats": [
            {
                "id": seat.id,
                "seat_code": seat.seat_code,
                "row_index": seat.row_index,
                "col_index": seat.col_index,
                "status": seat.status,
                "tags": seat.tags,
                "selected_student_id": seat.selected_student_id,
                "locked_student_id": seat.locked_student_id,
            }
            for seat in seats
        ],
    }


def create_swap_request(db: Session, round_obj: SeatRound, requester: User, target: User, reason: str | None) -> SwapRequest:
    settings = get_or_create_settings(db)
    if round_obj.status != RoundStatus.finished:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat swap is only allowed after round finish")
    if settings.swap_reason_required and not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Swap reason is required")

    requester_item = (
        db.query(RoundQueueItem)
        .filter(RoundQueueItem.round_id == round_obj.id, RoundQueueItem.student_id == requester.id)
        .first()
    )
    if requester_item and requester_item.swap_count >= settings.max_swap_count:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Swap limit reached for this round")

    if requester.id == target.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create swap request with yourself")

    if not db.query(SeatSelection).filter(SeatSelection.round_id == round_obj.id, SeatSelection.student_id == requester.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requester has no seat")
    if not db.query(SeatSelection).filter(SeatSelection.round_id == round_obj.id, SeatSelection.student_id == target.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target has no seat")

    request = SwapRequest(
        round_id=round_obj.id,
        requester_id=requester.id,
        target_id=target.id,
        reason=reason,
        status=SwapStatus.pending_target,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def create_special_request(
    db: Session,
    round_obj: SeatRound,
    student: User,
    requested_seat_id: int | None,
    requested_tag: str | None,
    reason: str | None,
) -> SpecialSeatRequest:
    settings = get_or_create_settings(db)
    if not settings.special_request_open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Special request entry is closed")
    request = SpecialSeatRequest(
        round_id=round_obj.id,
        student_id=student.id,
        requested_seat_id=requested_seat_id,
        requested_tag=requested_tag,
        reason=reason,
        status=SpecialRequestStatus.pending,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request
