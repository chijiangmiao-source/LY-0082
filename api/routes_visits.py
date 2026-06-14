import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Appointment, Blacklist, Resident, Room, Visit, VisitCode, CodeErrorLog

logger = logging.getLogger(__name__)


async def log_code_error(session, code: str, error_type: str):
    log_entry = CodeErrorLog(code=code, error_type=error_type)
    session.add(log_entry)
    await session.commit()


async def get_by_code(request: Request) -> JSONResponse:
    code = request.path_params["code"].strip().upper()

    async with async_session() as session:
        vc_result = await session.execute(
            select(VisitCode).where(VisitCode.code == code)
        )
        visit_code = vc_result.scalar_one_or_none()
        if not visit_code:
            await log_code_error(session, code, "invalid_code")
            return JSONResponse({"detail": "探视码不存在", "error_type": "invalid_code"}, status_code=404)

        apt_result = await session.execute(
            select(Appointment).where(Appointment.id == visit_code.appointment_id)
        )
        appointment = apt_result.scalar_one_or_none()
        if not appointment:
            await log_code_error(session, code, "invalid_appointment")
            return JSONResponse({"detail": "关联预约不存在", "error_type": "invalid_appointment"}, status_code=404)

        res_result = await session.execute(
            select(Resident).where(Resident.id == appointment.resident_id)
        )
        resident = res_result.scalar_one_or_none()

        room_result = await session.execute(
            select(Room).where(Room.id == resident.room_id)
        ) if resident else None
        room = room_result.scalar_one_or_none() if room_result else None

        warnings = []
        now = datetime.now(timezone.utc)

        if visit_code.is_used:
            warnings.append("该探视码已使用")
        if appointment.status in ("checked_in", "checked_out", "cancelled", "rejected"):
            warnings.append(f"预约状态为{appointment.status}，无法核验")
        if appointment.status == "pending":
            warnings.append("预约尚未审核通过")
        if now < appointment.scheduled_start or now > appointment.scheduled_end:
            warnings.append("不在预约时段内")
        if appointment.visitor_id_card:
            bl_result = await session.execute(
                select(Blacklist).where(Blacklist.visitor_id_card == appointment.visitor_id_card)
            )
            if bl_result.scalar_one_or_none():
                warnings.append("访客在黑名单中")
        if room:
            active_count_result = await session.execute(
                select(func.count()).select_from(Visit).where(
                    and_(
                        Visit.room_id == room.id,
                        Visit.check_in_time.isnot(None),
                        Visit.check_out_time.is_(None),
                        Visit.release_status == "released",
                    )
                )
            )
            if active_count_result.scalar() >= room.max_visitors:
                warnings.append("房间探视人数已满")
        if appointment.visitor_id_card:
            other_active_result = await session.execute(
                select(Visit).join(Appointment, Visit.appointment_id == Appointment.id).where(
                    and_(
                        Visit.check_in_time.isnot(None),
                        Visit.check_out_time.is_(None),
                        Visit.release_status == "released",
                        Appointment.visitor_id_card == appointment.visitor_id_card,
                    )
                )
            )
            if other_active_result.scalar_one_or_none():
                warnings.append("访客尚未离开其他房间")

    return JSONResponse({
        "id": appointment.id,
        "appointment_no": appointment.appointment_no,
        "resident_id": appointment.resident_id,
        "resident_name": resident.name if resident else "",
        "room_number": room.room_number if room else "",
        "visitor_name": appointment.visitor_name,
        "visitor_phone": appointment.visitor_phone,
        "visitor_id_card": appointment.visitor_id_card,
        "visitor_relation": appointment.visitor_relation,
        "is_whitelist_visitor": appointment.is_whitelist_visitor,
        "scheduled_start": appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
        "scheduled_end": appointment.scheduled_end.isoformat() if appointment.scheduled_end else None,
        "status": appointment.status,
        "visit_code": visit_code.code,
        "visit_code_used": visit_code.is_used,
        "warnings": warnings,
    })


async def checkin_by_code(request: Request) -> JSONResponse:
    body = await request.json()
    code = body.get("code", "").strip().upper()
    reject_reason = body.get("reject_reason", "")
    now = datetime.now(timezone.utc)

    if not code:
        return JSONResponse({"detail": "请输入探视码"}, status_code=400)

    async with async_session() as session:
        vc_result = await session.execute(
            select(VisitCode).where(VisitCode.code == code)
        )
        visit_code = vc_result.scalar_one_or_none()
        if not visit_code:
            await log_code_error(session, code, "invalid_code")
            return JSONResponse({"detail": "探视码不存在", "error_type": "invalid_code"}, status_code=400)

        if visit_code.is_used:
            await log_code_error(session, code, "code_used")
            return JSONResponse({"detail": "该探视码已使用", "error_type": "code_used"}, status_code=400)

        apt_result = await session.execute(
            select(Appointment).where(Appointment.id == visit_code.appointment_id)
        )
        appointment = apt_result.scalar_one_or_none()
        if not appointment:
            await log_code_error(session, code, "invalid_appointment")
            return JSONResponse({"detail": "关联预约不存在", "error_type": "invalid_appointment"}, status_code=400)

        if appointment.status in ("checked_in", "checked_out", "cancelled", "rejected"):
            return JSONResponse({"detail": f"预约状态为{appointment.status}，无法核验"}, status_code=400)

        if appointment.status == "pending":
            return JSONResponse({"detail": "预约尚未审核通过"}, status_code=400)

        res_result = await session.execute(
            select(Resident).where(Resident.id == appointment.resident_id)
        )
        resident = res_result.scalar_one_or_none()
        target_room_id = resident.room_id if resident else None

        visitor_id_card = appointment.visitor_id_card

        if reject_reason:
            reason_len = len(reject_reason.strip())
            if reason_len < 2 or reason_len > 200:
                return JSONResponse({"detail": "拒绝原因长度需在2-200字之间"}, status_code=400)
            visit = Visit(
                appointment_id=appointment.id,
                room_id=target_room_id,
                visit_code_id=visit_code.id,
                check_in_time=now,
                release_status="rejected",
                reject_reason=reject_reason.strip(),
            )
            session.add(visit)
            appointment.status = "rejected"
            visit_code.is_used = True
            visit_code.used_at = now
            await session.commit()
            return JSONResponse({
                "id": visit.id,
                "appointment_id": visit.appointment_id,
                "room_id": visit.room_id,
                "visit_code_id": visit.visit_code_id,
                "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
                "release_status": visit.release_status,
                "reject_reason": reject_reason.strip(),
            }, status_code=201)

        bl_result = await session.execute(select(Blacklist).where(Blacklist.visitor_id_card == visitor_id_card))
        if bl_result.scalar_one_or_none():
            visit = Visit(
                appointment_id=appointment.id,
                room_id=target_room_id,
                visit_code_id=visit_code.id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客在黑名单中",
            )
            session.add(visit)
            appointment.status = "rejected"
            visit_code.is_used = True
            visit_code.used_at = now
            await session.commit()
            return JSONResponse({"detail": "访客在黑名单中"}, status_code=400)

        if now < appointment.scheduled_start or now > appointment.scheduled_end:
            visit = Visit(
                appointment_id=appointment.id,
                room_id=target_room_id,
                visit_code_id=visit_code.id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="不在预约时段内",
            )
            session.add(visit)
            appointment.status = "rejected"
            visit_code.is_used = True
            visit_code.used_at = now
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
                appointment_id=appointment.id,
                room_id=target_room_id,
                visit_code_id=visit_code.id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="房间探视人数已满",
            )
            session.add(visit)
            appointment.status = "rejected"
            visit_code.is_used = True
            visit_code.used_at = now
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
                appointment_id=appointment.id,
                room_id=target_room_id,
                visit_code_id=visit_code.id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客尚未离开其他房间",
            )
            session.add(visit)
            appointment.status = "rejected"
            visit_code.is_used = True
            visit_code.used_at = now
            await session.commit()
            return JSONResponse({"detail": "访客尚未离开其他房间"}, status_code=400)

        visit = Visit(
            appointment_id=appointment.id,
            room_id=target_room_id,
            visit_code_id=visit_code.id,
            check_in_time=now,
            release_status="released",
        )
        session.add(visit)
        appointment.status = "checked_in"
        visit_code.is_used = True
        visit_code.used_at = now
        await session.commit()
        await session.refresh(visit)

    return JSONResponse({
        "id": visit.id,
        "appointment_id": visit.appointment_id,
        "room_id": visit.room_id,
        "visit_code_id": visit.visit_code_id,
        "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
        "release_status": visit.release_status,
    }, status_code=201)


async def checkin(request: Request) -> JSONResponse:
    body = await request.json()
    appointment_id = body.get("appointment_id")
    visitor_id_card = body.get("visitor_id_card", "")
    room_id = body.get("room_id")
    reject_reason = body.get("reject_reason", "")
    visit_code_id = body.get("visit_code_id")
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
                visit_code_id=visit_code_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason=reject_reason.strip(),
            )
            session.add(visit)
            appointment.status = "rejected"
            if visit_code_id:
                vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
                vc = vc_result.scalar_one_or_none()
                if vc:
                    vc.is_used = True
                    vc.used_at = now
            await session.commit()
            return JSONResponse({
                "id": visit.id,
                "appointment_id": visit.appointment_id,
                "room_id": visit.room_id,
                "visit_code_id": visit.visit_code_id,
                "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
                "release_status": visit.release_status,
                "reject_reason": reject_reason.strip(),
            }, status_code=201)

        bl_result = await session.execute(select(Blacklist).where(Blacklist.visitor_id_card == visitor_id_card))
        if bl_result.scalar_one_or_none():
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                visit_code_id=visit_code_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客在黑名单中",
            )
            session.add(visit)
            appointment.status = "rejected"
            if visit_code_id:
                vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
                vc = vc_result.scalar_one_or_none()
                if vc:
                    vc.is_used = True
                    vc.used_at = now
            await session.commit()
            return JSONResponse({"detail": "访客在黑名单中"}, status_code=400)

        if now < appointment.scheduled_start or now > appointment.scheduled_end:
            visit = Visit(
                appointment_id=appointment_id,
                room_id=target_room_id,
                visit_code_id=visit_code_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="不在预约时段内",
            )
            session.add(visit)
            appointment.status = "rejected"
            if visit_code_id:
                vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
                vc = vc_result.scalar_one_or_none()
                if vc:
                    vc.is_used = True
                    vc.used_at = now
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
                visit_code_id=visit_code_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="房间探视人数已满",
            )
            session.add(visit)
            appointment.status = "rejected"
            if visit_code_id:
                vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
                vc = vc_result.scalar_one_or_none()
                if vc:
                    vc.is_used = True
                    vc.used_at = now
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
                visit_code_id=visit_code_id,
                check_in_time=now,
                release_status="rejected",
                reject_reason="访客尚未离开其他房间",
            )
            session.add(visit)
            appointment.status = "rejected"
            if visit_code_id:
                vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
                vc = vc_result.scalar_one_or_none()
                if vc:
                    vc.is_used = True
                    vc.used_at = now
            await session.commit()
            return JSONResponse({"detail": "访客尚未离开其他房间"}, status_code=400)

        visit = Visit(
            appointment_id=appointment_id,
            room_id=target_room_id,
            visit_code_id=visit_code_id,
            check_in_time=now,
            release_status="released",
        )
        session.add(visit)
        appointment.status = "checked_in"
        if visit_code_id:
            vc_result = await session.execute(select(VisitCode).where(VisitCode.id == visit_code_id))
            vc = vc_result.scalar_one_or_none()
            if vc:
                vc.is_used = True
                vc.used_at = now
        await session.commit()
        await session.refresh(visit)

    return JSONResponse({
        "id": visit.id,
        "appointment_id": visit.appointment_id,
        "room_id": visit.room_id,
        "visit_code_id": visit.visit_code_id,
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
    Route("/api/visits/checkin/code", checkin_by_code, methods=["POST"]),
    Route("/api/visits/code/{code}", get_by_code, methods=["GET"]),
    Route("/api/visits/checkout", checkout, methods=["POST"]),
    Route("/api/visits/active", list_active, methods=["GET"]),
]
