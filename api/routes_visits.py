import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Appointment, Blacklist, Resident, Room, Visit

logger = logging.getLogger(__name__)


async def checkin(request: Request) -> JSONResponse:
    body = await request.json()
    appointment_id = body.get("appointment_id")
    visitor_id_card = body.get("visitor_id_card", "")
    room_id = body.get("room_id")
    reject_reason = body.get("reject_reason", "")
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        appt_result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = appt_result.scalar_one_or_none()
        if not appointment:
            return JSONResponse({"detail": "预约不存在"}, status_code=404)

        if appointment.status in ("checked_in", "checked_out", "cancelled", "rejected"):
            return JSONResponse({"detail": f"预约状态为{appointment.status}，无法进行核验"}, status_code=400)

        if not visitor_id_card:
            visitor_id_card = appointment.visitor_id_card

        target_room_id = room_id
        if not target_room_id:
            res_result = await session.execute(select(Resident).where(Resident.id == appointment.resident_id))
            resident = res_result.scalar_one_or_none()
            if resident:
                target_room_id = resident.room_id

        if reject_reason:
            reason_len = len(reject_reason.strip())
            if reason_len < 2 or reason_len > 200:
                return JSONResponse({"detail": "拒绝原因长度需在2-200字之间"}, status_code=400)
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason=reject_reason.strip(),
            )
            session.add(visit)
            appointment.status = "rejected"
            await session.commit()
            return JSONResponse({
                "id": visit.id,
                "appointment_id": visit.appointment_id,
                "room_id": visit.room_id,
                "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
                "release_status": visit.release_status,
                "reject_reason": reject_reason.strip(),
            }, status_code=201)

        bl_result = await session.execute(select(Blacklist).where(Blacklist.visitor_id_card == visitor_id_card))
        if bl_result.scalar_one_or_none():
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客在黑名单中",
            )
            session.add(visit)
            appointment.status = "rejected"
            await session.commit()
            return JSONResponse({"detail": "访客在黑名单中"}, status_code=400)

        if now < appointment.scheduled_start or now > appointment.scheduled_end:
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="不在预约时段内",
            )
            session.add(visit)
            appointment.status = "rejected"
            await session.commit()
            return JSONResponse({"detail": "不在预约时段内"}, status_code=400)

        room_result = await session.execute(select(Room).where(Room.id == target_room_id))
        room = room_result.scalar_one_or_none()

        active_count_result = await session.execute(
            select(func.count()).select_from(Visit).where(
                and_(
                    Visit.room_id == target_room_id,
                    Visit.check_in_time.isnot(None),
                    Visit.check_out_time.is_(None),
                    Visit.release_status == "released",
                )
            )
        )
        active_count = active_count_result.scalar()

        if room and active_count >= room.max_visitors:
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="房间探视人数已满",
            )
            session.add(visit)
            appointment.status = "rejected"
            await session.commit()
            return JSONResponse({"detail": "房间探视人数已满"}, status_code=400)

        other_active_result = await session.execute(
            select(Visit).join(Appointment, Visit.appointment_id == Appointment.id).where(
                and_(
                    Visit.check_in_time.isnot(None),
                    Visit.check_out_time.is_(None),
                    Visit.release_status == "released",
                    Visit.room_id != target_room_id,
                    Appointment.visitor_id_card == visitor_id_card,
                )
            )
        )
        other_visit = other_active_result.scalar_one_or_none()
        if other_visit:
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客尚未离开其他房间",
            )
            session.add(visit)
            appointment.status = "rejected"
            await session.commit()
            return JSONResponse({"detail": "访客尚未离开其他房间"}, status_code=400)

        visit = Visit(
            appointment_id=appointment_id,
            room_id=target_room_id,
            check_in_time=now,
            release_status="released",
        )
        session.add(visit)
        appointment.status = "checked_in"
        await session.commit()
        await session.refresh(visit)

    return JSONResponse({
        "id": visit.id,
        "appointment_id": visit.appointment_id,
        "room_id": visit.room_id,
        "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
        "release_status": visit.release_status,
    }, status_code=201)


async def checkout(request: Request) -> JSONResponse:
    body = await request.json()
    visit_id = body.get("visit_id")
    appointment_id = body.get("appointment_id")
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        if visit_id:
            visit_result = await session.execute(select(Visit).where(Visit.id == visit_id))
            visit = visit_result.scalar_one_or_none()
        elif appointment_id:
            visit_result = await session.execute(
                select(Visit).where(
                    and_(
                        Visit.appointment_id == appointment_id,
                        Visit.check_in_time.isnot(None),
                        Visit.check_out_time.is_(None),
                        Visit.release_status == "released",
                    )
                )
            )
            visit = visit_result.scalar_one_or_none()
        else:
            return JSONResponse({"detail": "请提供visit_id或appointment_id"}, status_code=400)

        if not visit:
            return JSONResponse({"detail": "未找到活跃的探视记录"}, status_code=404)

        visit.check_out_time = now

        appt_result = await session.execute(select(Appointment).where(Appointment.id == visit.appointment_id))
        appointment = appt_result.scalar_one_or_none()
        if appointment:
            appointment.status = "checked_out"

        await session.commit()
        await session.refresh(visit)

    return JSONResponse({
        "id": visit.id,
        "appointment_id": visit.appointment_id,
        "room_id": visit.room_id,
        "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
        "check_out_time": visit.check_out_time.isoformat() if visit.check_out_time else None,
        "release_status": visit.release_status,
    })


async def list_active(request: Request) -> JSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(Visit, Appointment, Room, Resident)
            .join(Appointment, Visit.appointment_id == Appointment.id)
            .join(Room, Visit.room_id == Room.id)
            .join(Resident, Appointment.resident_id == Resident.id)
            .where(
                and_(
                    Visit.check_in_time.isnot(None),
                    Visit.check_out_time.is_(None),
                    Visit.release_status == "released",
                )
            )
        )
        rows = result.all()

    return JSONResponse([
        {
            "id": row.Visit.id,
            "visitor_name": row.Appointment.visitor_name,
            "room_number": row.Room.room_number,
            "resident_name": row.Resident.name,
            "check_in_time": row.Visit.check_in_time.isoformat() if row.Visit.check_in_time else None,
            "appointment_id": row.Visit.appointment_id,
        }
        for row in rows
    ])


routes = [
    Route("/api/visits/checkin", checkin, methods=["POST"]),
    Route("/api/visits/checkout", checkout, methods=["POST"]),
    Route("/api/visits/active", list_active, methods=["GET"]),
]
