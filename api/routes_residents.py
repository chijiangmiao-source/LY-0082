import logging

from sqlalchemy import select, or_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Resident, Room

logger = logging.getLogger(__name__)


async def list_residents(request: Request) -> JSONResponse:
    search = request.query_params.get("search")
    async with async_session() as session:
        stmt = select(Resident)
        if search:
            stmt = stmt.where(Resident.name.like(f"%{search}%"))
        result = await session.execute(stmt)
        residents = result.scalars().all()

        room_ids = list(set(r.room_id for r in residents))
        rooms_map = {}
        if room_ids:
            rooms_result = await session.execute(select(Room).where(Room.id.in_(room_ids)))
            for rm in rooms_result.scalars().all():
                rooms_map[rm.id] = rm.room_number

    return JSONResponse([
        {
            "id": r.id,
            "name": r.name,
            "phone": r.phone,
            "room_id": r.room_id,
            "room_number": rooms_map.get(r.room_id, ""),
            "check_in_date": r.check_in_date.isoformat() if r.check_in_date else None,
            "expected_check_out_date": r.expected_check_out_date.isoformat() if r.expected_check_out_date else None,
        }
        for r in residents
    ])


async def create_resident(request: Request) -> JSONResponse:
    body = await request.json()
    async with async_session() as session:
        resident = Resident(
            name=body.get("name", ""),
            phone=body.get("phone"),
            room_id=body.get("room_id"),
            check_in_date=body.get("check_in_date"),
            expected_check_out_date=body.get("expected_check_out_date"),
        )
        session.add(resident)
        await session.commit()
        await session.refresh(resident)

    return JSONResponse({
        "id": resident.id,
        "name": resident.name,
        "phone": resident.phone,
        "room_id": resident.room_id,
        "check_in_date": resident.check_in_date.isoformat() if resident.check_in_date else None,
        "expected_check_out_date": resident.expected_check_out_date.isoformat() if resident.expected_check_out_date else None,
    }, status_code=201)


async def update_resident(request: Request) -> JSONResponse:
    resident_id = int(request.path_params["id"])
    body = await request.json()

    async with async_session() as session:
        result = await session.execute(select(Resident).where(Resident.id == resident_id))
        resident = result.scalar_one_or_none()
        if not resident:
            return JSONResponse({"detail": "住户不存在"}, status_code=404)

        if "name" in body:
            resident.name = body["name"]
        if "phone" in body:
            resident.phone = body["phone"]
        if "room_id" in body:
            resident.room_id = body["room_id"]
        if "check_in_date" in body:
            resident.check_in_date = body["check_in_date"]
        if "expected_check_out_date" in body:
            resident.expected_check_out_date = body["expected_check_out_date"]

        await session.commit()
        await session.refresh(resident)

    return JSONResponse({
        "id": resident.id,
        "name": resident.name,
        "phone": resident.phone,
        "room_id": resident.room_id,
        "check_in_date": resident.check_in_date.isoformat() if resident.check_in_date else None,
        "expected_check_out_date": resident.expected_check_out_date.isoformat() if resident.expected_check_out_date else None,
    })


async def delete_resident(request: Request) -> JSONResponse:
    resident_id = int(request.path_params["id"])
    async with async_session() as session:
        result = await session.execute(select(Resident).where(Resident.id == resident_id))
        resident = result.scalar_one_or_none()
        if not resident:
            return JSONResponse({"detail": "住户不存在"}, status_code=404)

        await session.delete(resident)
        await session.commit()

    return JSONResponse({"detail": "删除成功"})


routes = [
    Route("/api/residents", list_residents, methods=["GET"]),
    Route("/api/residents", create_resident, methods=["POST"]),
    Route("/api/residents/{id:int}", update_resident, methods=["PUT"]),
    Route("/api/residents/{id:int}", delete_resident, methods=["DELETE"]),
]
