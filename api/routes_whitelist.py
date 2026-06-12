import logging

from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import VisitorWhitelist, Resident

logger = logging.getLogger(__name__)


async def list_whitelist(request: Request) -> JSONResponse:
    resident_id = request.query_params.get("resident_id")

    async with async_session() as session:
        stmt = select(VisitorWhitelist).order_by(VisitorWhitelist.created_at.desc())
        if resident_id:
            stmt = stmt.where(VisitorWhitelist.resident_id == int(resident_id))
        result = await session.execute(stmt)
        entries = result.scalars().all()

        resident_ids = list(set(e.resident_id for e in entries))
        residents_map = {}
        if resident_ids:
            res_result = await session.execute(select(Resident).where(Resident.id.in_(resident_ids)))
            for r in res_result.scalars().all():
                residents_map[r.id] = {"name": r.name, "room_id": r.room_id}

        room_ids = [v["room_id"] for v in residents_map.values()]
        rooms_map = {}
        if room_ids:
            from models import Room
            room_result = await session.execute(select(Room).where(Room.id.in_(room_ids)))
            for rm in room_result.scalars().all():
                rooms_map[rm.id] = rm.room_number

    return JSONResponse([
        {
            "id": e.id,
            "resident_id": e.resident_id,
            "resident_name": residents_map.get(e.resident_id, {}).get("name", ""),
            "room_number": rooms_map.get(residents_map.get(e.resident_id, {}).get("room_id"), ""),
            "visitor_name": e.visitor_name,
            "visitor_phone": e.visitor_phone,
            "visitor_id_card": e.visitor_id_card,
            "visitor_relation": e.visitor_relation,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ])


async def add_whitelist(request: Request) -> JSONResponse:
    body = await request.json()
    resident_id = body.get("resident_id")
    visitor_name = body.get("visitor_name", "").strip()

    if not resident_id:
        return JSONResponse({"detail": "请选择住户"}, status_code=400)
    if not visitor_name:
        return JSONResponse({"detail": "请输入访客姓名"}, status_code=400)

    async with async_session() as session:
        res_result = await session.execute(select(Resident).where(Resident.id == resident_id))
        if not res_result.scalar_one_or_none():
            return JSONResponse({"detail": "住户不存在"}, status_code=400)

        visitor_id_card = body.get("visitor_id_card", "").strip()
        if visitor_id_card:
            existing = await session.execute(
                select(VisitorWhitelist).where(
                    VisitorWhitelist.resident_id == resident_id,
                    VisitorWhitelist.visitor_id_card == visitor_id_card,
                )
            )
            if existing.scalar_one_or_none():
                return JSONResponse({"detail": "该访客已在住户的白名单中"}, status_code=400)

        entry = VisitorWhitelist(
            resident_id=resident_id,
            visitor_name=visitor_name,
            visitor_phone=body.get("visitor_phone"),
            visitor_id_card=visitor_id_card or None,
            visitor_relation=body.get("visitor_relation"),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)

    return JSONResponse({
        "id": entry.id,
        "resident_id": entry.resident_id,
        "visitor_name": entry.visitor_name,
        "visitor_phone": entry.visitor_phone,
        "visitor_id_card": entry.visitor_id_card,
        "visitor_relation": entry.visitor_relation,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }, status_code=201)


async def update_whitelist(request: Request) -> JSONResponse:
    entry_id = int(request.path_params["id"])
    body = await request.json()

    async with async_session() as session:
        result = await session.execute(select(VisitorWhitelist).where(VisitorWhitelist.id == entry_id))
        entry = result.scalar_one_or_none()
        if not entry:
            return JSONResponse({"detail": "白名单记录不存在"}, status_code=404)

        if "visitor_name" in body:
            entry.visitor_name = body["visitor_name"]
        if "visitor_phone" in body:
            entry.visitor_phone = body["visitor_phone"]
        if "visitor_id_card" in body:
            entry.visitor_id_card = body["visitor_id_card"]
        if "visitor_relation" in body:
            entry.visitor_relation = body["visitor_relation"]

        await session.commit()
        await session.refresh(entry)

    return JSONResponse({
        "id": entry.id,
        "resident_id": entry.resident_id,
        "visitor_name": entry.visitor_name,
        "visitor_phone": entry.visitor_phone,
        "visitor_id_card": entry.visitor_id_card,
        "visitor_relation": entry.visitor_relation,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    })


async def remove_whitelist(request: Request) -> JSONResponse:
    entry_id = int(request.path_params["id"])
    async with async_session() as session:
        result = await session.execute(select(VisitorWhitelist).where(VisitorWhitelist.id == entry_id))
        entry = result.scalar_one_or_none()
        if not entry:
            return JSONResponse({"detail": "白名单记录不存在"}, status_code=404)

        await session.delete(entry)
        await session.commit()

    return JSONResponse({"detail": "已从白名单移除"})


async def get_by_resident(request: Request) -> JSONResponse:
    resident_id = int(request.path_params["resident_id"])

    async with async_session() as session:
        result = await session.execute(
            select(VisitorWhitelist).where(VisitorWhitelist.resident_id == resident_id)
            .order_by(VisitorWhitelist.created_at.desc())
        )
        entries = result.scalars().all()

    return JSONResponse([
        {
            "id": e.id,
            "resident_id": e.resident_id,
            "visitor_name": e.visitor_name,
            "visitor_phone": e.visitor_phone,
            "visitor_id_card": e.visitor_id_card,
            "visitor_relation": e.visitor_relation,
        }
        for e in entries
    ])


routes = [
    Route("/api/whitelist", list_whitelist, methods=["GET"]),
    Route("/api/whitelist", add_whitelist, methods=["POST"]),
    Route("/api/whitelist/{id:int}", update_whitelist, methods=["PUT"]),
    Route("/api/whitelist/{id:int}", remove_whitelist, methods=["DELETE"]),
    Route("/api/whitelist/resident/{resident_id:int}", get_by_resident, methods=["GET"]),
]
