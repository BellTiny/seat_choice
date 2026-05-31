from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_student
from app.models.models import InviteStatus, RoundStatus, SeatRound, SeatSelection, SpecialSeatRequest, SwapRequest, SwapStatus, TeamInvite, User
from app.schemas.interaction import (
    SeatChoiceRequest,
    SpecialRequestCreate,
    SpecialRequestOut,
    StudentSelectionStatus,
    SwapRequestCreate,
    SwapRequestOut,
    SwapRespondRequest,
    TeamInviteCreate,
    TeamInviteOut,
    TeamInviteRespond,
)
from app.schemas.round import RoundOut
from app.schemas.user import UserOut
from app.services.selection import (
    build_student_status,
    choose_seats,
    create_special_request,
    create_swap_request,
    get_or_create_settings,
    get_round_or_404,
    get_student_by_student_id,
)
from app.services.webhook import send_webhook_if_configured

router = APIRouter(prefix="/student", tags=["student"], dependencies=[Depends(get_current_student)])


def _get_current_round(db: Session) -> SeatRound | None:
    return (
        db.query(SeatRound)
        .filter(SeatRound.status != RoundStatus.finished)
        .order_by(SeatRound.id.desc())
        .first()
    )


@router.get("/me", response_model=UserOut, summary="Get current student profile")
def get_me(student: User = Depends(get_current_student)) -> User:
    return student


@router.get("/current-round", response_model=RoundOut | None, summary="Get current active round for student side")
def get_current_round(db: Session = Depends(get_db)) -> SeatRound | None:
    return _get_current_round(db)


@router.get("/selection/status", response_model=StudentSelectionStatus, summary="Poll current round seat selection status")
def get_current_selection_status(db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    round_obj = _get_current_round(db)
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active round")
    return build_student_status(db, round_obj, student)


@router.post("/selection/choose", response_model=list[UserOut], summary="Choose seat(s) in current round")
async def choose_current_round_seats(
    payload: SeatChoiceRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    round_obj = _get_current_round(db)
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active round")
    selected_students = choose_seats(db, round_obj, student, payload.seat_ids)
    for selected_student in selected_students:
        await send_webhook_if_configured(
            db,
            {
                "event": "seat_selected",
                "round_id": round_obj.id,
                "student_id": selected_student.student_id or selected_student.username,
            },
        )
    return selected_students


@router.get("/selections/history", summary="Get seat selection history for current student")
def get_selection_history(db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    selections = (
        db.query(SeatSelection)
        .filter(SeatSelection.student_id == student.id)
        .order_by(SeatSelection.created_at.desc())
        .all()
    )
    return [
        {
            "id": selection.id,
            "assignment_type": selection.assignment_type,
            "created_at": selection.created_at,
            "seat": {
                "id": selection.seat.id,
                "seat_code": selection.seat.seat_code,
            }
            if selection.seat
            else None,
            "round": {
                "id": selection.round.id,
                "name": selection.round.name,
                "semester": {
                    "id": selection.round.semester.id,
                    "name": selection.round.semester.name,
                }
                if selection.round and selection.round.semester
                else None,
            }
            if selection.round
            else None,
        }
        for selection in selections
    ]


@router.get("/swaps", summary="List swap requests related to current student")
def list_student_swaps(db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    requests = (
        db.query(SwapRequest)
        .filter(or_(SwapRequest.requester_id == student.id, SwapRequest.target_id == student.id))
        .order_by(SwapRequest.id.desc())
        .all()
    )
    return [
        {
            "id": request.id,
            "round_id": request.round_id,
            "requester_id": request.requester_id,
            "target_id": request.target_id,
            "reason": request.reason,
            "status": request.status,
            "review_comment": request.review_comment,
            "requester": {
                "id": request.requester.id,
                "full_name": request.requester.full_name,
                "student_id": request.requester.student_id,
            }
            if request.requester
            else None,
            "target": {
                "id": request.target.id,
                "full_name": request.target.full_name,
                "student_id": request.target.student_id,
            }
            if request.target
            else None,
        }
        for request in requests
    ]


@router.post("/swaps", response_model=SwapRequestOut, summary="Create swap request in current round")
def create_current_round_swap_request(
    payload: SwapRequestCreate,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    round_obj = _get_current_round(db)
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active round")
    target = get_student_by_student_id(db, payload.target_student_id)
    return create_swap_request(db, round_obj, student, target, payload.reason)


@router.get("/rounds/{round_id}/status", response_model=StudentSelectionStatus, summary="Poll seat selection status")
def get_selection_status(round_id: int, db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    round_obj = get_round_or_404(db, round_id)
    return build_student_status(db, round_obj, student)


@router.post("/rounds/{round_id}/choose-seats", response_model=list[UserOut], summary="Choose seat(s) for current student or team")
async def choose_round_seats(
    round_id: int,
    payload: SeatChoiceRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    round_obj = get_round_or_404(db, round_id)
    selected_students = choose_seats(db, round_obj, student, payload.seat_ids)
    for selected_student in selected_students:
        await send_webhook_if_configured(
            db,
            {
                "event": "seat_selected",
                "round_id": round_id,
                "student_id": selected_student.student_id or selected_student.username,
            },
        )
    return selected_students


@router.post("/rounds/{round_id}/team-invites", response_model=TeamInviteOut, summary="Create team invite")
def create_team_invite(
    round_id: int,
    payload: TeamInviteCreate,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    settings = get_or_create_settings(db)
    if not settings.team_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team mode is disabled")
    invitee = get_student_by_student_id(db, payload.invitee_student_id)
    if invitee.id == student.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite yourself")
    existing = (
        db.query(TeamInvite)
        .filter(TeamInvite.round_id == round_id, TeamInvite.inviter_id == student.id, TeamInvite.invitee_id == invitee.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already exists")
    invite = TeamInvite(round_id=round_id, inviter_id=student.id, invitee_id=invitee.id, status=InviteStatus.pending)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/rounds/{round_id}/team-invites", response_model=list[TeamInviteOut], summary="List team invites related to current student")
def list_team_invites(round_id: int, db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    return (
        db.query(TeamInvite)
        .filter(TeamInvite.round_id == round_id)
        .filter(or_(TeamInvite.inviter_id == student.id, TeamInvite.invitee_id == student.id))
        .order_by(TeamInvite.id.desc())
        .all()
    )


@router.post("/team-invites/{invite_id}/respond", response_model=TeamInviteOut, summary="Accept or reject team invite")
def respond_team_invite(
    invite_id: int,
    payload: TeamInviteRespond,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id, TeamInvite.invitee_id == student.id).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    invite.status = InviteStatus.accepted if payload.accept else InviteStatus.rejected
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/rounds/{round_id}/swap-requests", response_model=SwapRequestOut, summary="Create seat swap request")
def create_student_swap_request(
    round_id: int,
    payload: SwapRequestCreate,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    round_obj = get_round_or_404(db, round_id)
    target = get_student_by_student_id(db, payload.target_student_id)
    return create_swap_request(db, round_obj, student, target, payload.reason)


@router.get("/rounds/{round_id}/swap-requests", response_model=list[SwapRequestOut], summary="List swap requests related to current student")
def list_student_swap_requests(round_id: int, db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    return (
        db.query(SwapRequest)
        .filter(SwapRequest.round_id == round_id)
        .filter(or_(SwapRequest.requester_id == student.id, SwapRequest.target_id == student.id))
        .order_by(SwapRequest.id.desc())
        .all()
    )


@router.post("/swap-requests/{request_id}/respond", response_model=SwapRequestOut, summary="Respond to incoming seat swap request")
def respond_swap_request(
    request_id: int,
    payload: SwapRespondRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    request_obj = db.query(SwapRequest).filter(SwapRequest.id == request_id, SwapRequest.target_id == student.id).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap request not found")
    request_obj.status = SwapStatus.pending_admin if payload.accept else SwapStatus.rejected
    db.commit()
    db.refresh(request_obj)
    return request_obj


@router.post("/rounds/{round_id}/special-requests", response_model=SpecialRequestOut, summary="Submit special seat request")
def submit_special_request(
    round_id: int,
    payload: SpecialRequestCreate,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    round_obj = get_round_or_404(db, round_id)
    return create_special_request(
        db,
        round_obj,
        student,
        payload.requested_seat_id,
        payload.requested_tag,
        payload.reason,
    )


@router.get("/rounds/{round_id}/special-requests", response_model=list[SpecialRequestOut], summary="List current student's special requests")
def list_special_requests(round_id: int, db: Session = Depends(get_db), student: User = Depends(get_current_student)):
    return (
        db.query(SpecialSeatRequest)
        .filter(SpecialSeatRequest.round_id == round_id)
        .filter(SpecialSeatRequest.student_id == student.id)
        .order_by(SpecialSeatRequest.id.desc())
        .all()
    )
