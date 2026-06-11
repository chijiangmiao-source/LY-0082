import logging
import random
import time
from datetime import datetime, timezone

from sqlalchemy import select, and_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Appointment, Blacklist, Resident

logger = logging.getLogger(__name__)


def generate_appointment_no() -> str:
    ts = int(time.time())
    rand = random.randint(0, 9999)
    return f"VT{ts}{rand:04d}"


async def list_appointments(request: Request) -> JSONResponse:
    status = request.query_params.get("status")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    resident_id = request.query_params.get("resident_id")

    async with async_session() as session:
        stmt = select(Appointment).order_by(Appointment.scheduled_start.desc())
        if status:
            stmt = stmt.where(Appointment.status == status)
        if resident_id:
            stmt = stmt.where(Appointment.resident_id == int(resident_id))
        if date_from:
            stmt = stmt.where(Appointment.scheduled_start >= datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc))
        if date_to:
            stmt = stmt.where(Appointment.scheduled_end <= datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc))

        result = await session.execute(stmt)
        appointments = result.scalars().all()

        resident_ids = list(set(a.resident_id for a in appointments))
        residents_map = {}
        if resident_ids:
            res_result = await session.execute(select(Resident).where(Resident.id.in_(resident_ids)))
            for r in res_result.scalars().all():
                residents_map[r.id] = r.name

    return JSONResponse([
        {
            "id": a.id,
            "appointment_no": a.appointment_no,
            "resident_id": a.resident_id,
            "resident_name": residents_map.get(a.resident_id, ""),
            "visitor_name": a.visitor_name,
            "visitor_phone": a.visitor_phone,
            "visitor_id_card": a.visitor_id_card,
            "visitor_relation": a.visitor_relation,
            "scheduled_start": a.scheduled_start.isoformat() if a.scheduled_start else None,
            "scheduled_end": a.scheduled_end.isoformat() if a.scheduled_end else None,
            "status": a.status,
        }
        for a in appointments
    ])


async def create_appointment(request: Request) -> JSONResponse:
    body = await request.json()
    visitor_id_card = body.get("visitor_id_card", "")

    async with async_session() as session:
        bl_result = await session.execute(select(Blacklist).where(Blacklist.visitor_id_card == visitor_id_card))
        if bl_result.scalar_one_or_none():
            return JSONResponse({"detail": "访客在黑名单中，无法预约"}, status_code=400)

        appointment = Appointment(
            appointment_no=generate_appointment_no(),
            resident_id=body.get("resident_id"),
            visitor_name=body.get("visitor_name", ""),
            visitor_phone=body.get("visitor_phone"),
            visitor_id_card=visitor_id_card,
            visitor_relation=body.get("visitor_relation"),
            scheduled_start=body.get("scheduled_start"),
            scheduled_end=body.get("scheduled_end"),
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)

    return JSONResponse({
        "id": appointment.id,
        "appointment_no": appointment.appointment_no,
        "resident_id": appointment.resident_id,
        "visitor_name": appointment.visitor_name,
        "visitor_phone": appointment.visitor_phone,
        "visitor_id_card": appointment.visitor_id_card,
        "visitor_relation": appointment.visitor_relation,
        "scheduled_start": appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
        "scheduled_end": appointment.scheduled_end.isoformat() if appointment.scheduled_end else None,
        "status": appointment.status,
    }, status_code=201)


async def update_appointment(request: Request) -> JSONResponse:
    appointment_id = int(request.path_params["id"])
    body = await request.json()

    async with async_session() as session:
        result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalar_one_or_none()
        if not appointment:
            return JSONResponse({"detail": "预约不存在"}, status_code=404)

        if "visitor_name" in body:
            appointment.visitor_name = body["visitor_name"]
        if "visitor_phone" in body:
            appointment.visitor_phone = body["visitor_phone"]
        if "visitor_id_card" in body:
            appointment.visitor_id_card = body["visitor_id_card"]
        if "visitor_relation" in body:
            appointment.visitor_relation = body["visitor_relation"]
        if "scheduled_start" in body:
            appointment.scheduled_start = body["scheduled_start"]
        if "scheduled_end" in body:
            appointment.scheduled_end = body["scheduled_end"]
        if "status" in body:
            appointment.status = body["status"]

        await session.commit()
        await session.refresh(appointment)

    return JSONResponse({
        "id": appointment.id,
        "appointment_no": appointment.appointment_no,
        "resident_id": appointment.resident_id,
        "visitor_name": appointment.visitor_name,
        "visitor_phone": appointment.visitor_phone,
        "visitor_id_card": appointment.visitor_id_card,
        "visitor_relation": appointment.visitor_relation,
        "scheduled_start": appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
        "scheduled_end": appointment.scheduled_end.isoformat() if appointment.scheduled_end else None,
        "status": appointment.status,
    })


async def cancel_appointment(request: Request) -> JSONResponse:
    appointment_id = int(request.path_params["id"])

    async with async_session() as session:
        result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalar_one_or_none()
        if not appointment:
            return JSONResponse({"detail": "预约不存在"}, status_code=404)

        appointment.status = "cancelled"
        await session.commit()

    return JSONResponse({"detail": "预约已取消"})


async def search_appointments(request: Request) -> JSONResponse:
    appointment_no = request.query_params.get("appointment_no", "")
    visitor_name = request.query_params.get("visitor_name", "")

    async with async_session() as session:
        stmt = select(Appointment)
        conditions = []
        if appointment_no:
            conditions.append(Appointment.appointment_no.like(f"%{appointment_no}%"))
        if visitor_name:
            conditions.append(Appointment.visitor_name.like(f"%{visitor_name}%"))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await session.execute(stmt)
        appointments = result.scalars().all()

        resident_ids = list(set(a.resident_id for a in appointments))
        residents_map = {}
        if resident_ids:
            res_result = await session.execute(select(Resident).where(Resident.id.in_(resident_ids)))
            for r in res_result.scalars().all():
                residents_map[r.id] = r.name

    return JSONResponse([
        {
            "id": a.id,
            "appointment_no": a.appointment_no,
            "resident_id": a.resident_id,
            "resident_name": residents_map.get(a.resident_id, ""),
            "visitor_name": a.visitor_name,
            "visitor_phone": a.visitor_phone,
            "visitor_id_card": a.visitor_id_card,
            "visitor_relation": a.visitor_relation,
            "scheduled_start": a.scheduled_start.isoformat() if a.scheduled_start else None,
            "scheduled_end": a.scheduled_end.isoformat() if a.scheduled_end else None,
            "status": a.status,
        }
        for a in appointments
    ])


routes = [
    Route("/api/appointments/search", search_appointments, methods=["GET"]),
    Route("/api/appointments", list_appointments, methods=["GET"]),
    Route("/api/appointments", create_appointment, methods=["POST"]),
    Route("/api/appointments/{id:int}", update_appointment, methods=["PUT"]),
    Route("/api/appointments/{id:int}", cancel_appointment, methods=["DELETE"]),
]
