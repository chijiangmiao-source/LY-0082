import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, distinct
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Appointment, Room, Visit, Floor, VisitCode

logger = logging.getLogger(__name__)


async def dashboard(request: Request) -> JSONResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        visit_count_result = await session.execute(
            select(func.count()).select_from(Visit).where(
                and_(
                    Visit.check_in_time >= today_start,
                    Visit.release_status == "released",
                )
            )
        )
        visit_count = visit_count_result.scalar()

        active_visitors_result = await session.execute(
            select(func.count()).select_from(Visit).where(
                and_(
                    Visit.check_in_time.isnot(None),
                    Visit.check_out_time.is_(None),
                    Visit.release_status == "released",
                )
            )
        )
        active_visitors = active_visitors_result.scalar()

        interception_count_result = await session.execute(
            select(func.count()).select_from(Visit).where(
                and_(
                    Visit.release_status == "rejected",
                    Visit.check_in_time >= today_start,
                )
            )
        )
        interception_count = interception_count_result.scalar()

        rooms_result = await session.execute(select(Room))
        rooms = rooms_result.scalars().all()
        overcapacity_count = 0
        for room in rooms:
            active_result = await session.execute(
                select(func.count()).select_from(Visit).where(
                    and_(
                        Visit.room_id == room.id,
                        Visit.check_in_time.isnot(None),
                        Visit.check_out_time.is_(None),
                        Visit.release_status == "released",
                    )
                )
            )
            if active_result.scalar() >= room.max_visitors:
                overcapacity_count += 1

        whitelist_visit_count = 0
        if visit_count > 0:
            whitelist_visit_result = await session.execute(
                select(func.count()).select_from(Visit)
                .join(Appointment, Visit.appointment_id == Appointment.id)
                .where(
                    and_(
                        Visit.check_in_time >= today_start,
                        Visit.release_status == "released",
                        Appointment.is_whitelist_visitor == True,
                    )
                )
            )
            whitelist_visit_count = whitelist_visit_result.scalar()
        whitelist_ratio = round((whitelist_visit_count / visit_count) * 100, 1) if visit_count > 0 else 0

        visit_code_released_result = await session.execute(
            select(func.count()).select_from(Visit).where(
                and_(
                    Visit.check_in_time >= today_start,
                    Visit.release_status == "released",
                    Visit.visit_code_id.isnot(None),
                )
            )
        )
        visit_code_released_count = visit_code_released_result.scalar()

        visit_code_rejected_result = await session.execute(
            select(func.count()).select_from(CodeErrorLog).where(
                CodeErrorLog.created_at >= today_start,
            )
        )
        visit_code_rejected_count = visit_code_rejected_result.scalar()

    return JSONResponse({
        "today_visits": visit_count,
        "active_visitors": active_visitors,
        "interception_count": interception_count,
        "overcapacity_count": overcapacity_count,
        "whitelist_visit_count": whitelist_visit_count,
        "whitelist_ratio": whitelist_ratio,
        "visit_code_released_count": visit_code_released_count,
        "visit_code_rejected_count": visit_code_rejected_count,
    })


async def room_heat(request: Request) -> JSONResponse:
    now = datetime.now(timezone.utc)
    days = int(request.query_params.get("days", "30"))
    start_date = now - timedelta(days=days)

    async with async_session() as session:
        result = await session.execute(
            select(Visit.room_id, func.count().label("visit_count"))
            .where(
                and_(
                    Visit.check_in_time >= start_date,
                    Visit.release_status == "released",
                )
            )
            .group_by(Visit.room_id)
        )
        rows = result.all()

        room_ids = [r[0] for r in rows]
        rooms_map = {}
        if room_ids:
            rooms_result = await session.execute(select(Room).where(Room.id.in_(room_ids)))
            for room in rooms_result.scalars().all():
                rooms_map[room.id] = room.room_number

    return JSONResponse([
        {
            "room_id": r[0],
            "room_number": rooms_map.get(r[0], ""),
            "visit_count": r[1],
        }
        for r in rows
    ])


async def interception(request: Request) -> JSONResponse:
    now = datetime.now(timezone.utc)
    days = int(request.query_params.get("days", "30"))
    start_date = now - timedelta(days=days)

    async with async_session() as session:
        result = await session.execute(
            select(Visit.reject_reason, func.count().label("count"))
            .where(
                and_(
                    Visit.release_status == "rejected",
                    Visit.check_in_time >= start_date,
                )
            )
            .group_by(Visit.reject_reason)
        )
        rows = result.all()

    return JSONResponse([
        {"reason": r[0], "count": r[1]}
        for r in rows
    ])


async def overcapacity(request: Request) -> JSONResponse:
    now = datetime.now(timezone.utc)
    days = int(request.query_params.get("days", "7"))
    start_date = now - timedelta(days=days)

    async with async_session() as session:
        rejected_rooms_result = await session.execute(
            select(Visit.room_id, func.count().label("reject_count"))
            .where(
                and_(
                    Visit.release_status == "rejected",
                    Visit.reject_reason == "房间探视人数已满",
                    Visit.check_in_time >= start_date,
                )
            )
            .group_by(Visit.room_id)
        )
        rejected_rooms = rejected_rooms_result.all()

        result_list = []
        for room_id, reject_count in rejected_rooms:
            room_result = await session.execute(select(Room).where(Room.id == room_id))
            room = room_result.scalar_one_or_none()
            if room:
                result_list.append({
                    "room_id": room.id,
                    "room_number": room.room_number,
                    "max_visitors": room.max_visitors,
                    "overcapacity_count": reject_count,
                })

    return JSONResponse(result_list)


routes = [
    Route("/api/statistics/dashboard", dashboard, methods=["GET"]),
    Route("/api/statistics/room-heat", room_heat, methods=["GET"]),
    Route("/api/statistics/interception", interception, methods=["GET"]),
    Route("/api/statistics/overcapacity", overcapacity, methods=["GET"]),
]
