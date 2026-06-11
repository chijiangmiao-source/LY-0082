import logging

from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Blacklist

logger = logging.getLogger(__name__)


async def list_blacklist(request: Request) -> JSONResponse:
    async with async_session() as session:
        result = await session.execute(select(Blacklist).order_by(Blacklist.created_at.desc()))
        entries = result.scalars().all()

    return JSONResponse([
        {
            "id": b.id,
            "visitor_name": b.visitor_name,
            "visitor_id_card": b.visitor_id_card,
            "reason": b.reason,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in entries
    ])


async def add_blacklist(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    body = await request.json()
    async with async_session() as session:
        existing = await session.execute(
            select(Blacklist).where(Blacklist.visitor_id_card == body.get("visitor_id_card", ""))
        )
        if existing.scalar_one_or_none():
            return JSONResponse({"detail": "该身份证号已在黑名单中"}, status_code=400)

        entry = Blacklist(
            visitor_name=body.get("visitor_name", ""),
            visitor_id_card=body.get("visitor_id_card", ""),
            reason=body.get("reason"),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)

    return JSONResponse({
        "id": entry.id,
        "visitor_name": entry.visitor_name,
        "visitor_id_card": entry.visitor_id_card,
        "reason": entry.reason,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }, status_code=201)


async def remove_blacklist(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    entry_id = int(request.path_params["id"])
    async with async_session() as session:
        result = await session.execute(select(Blacklist).where(Blacklist.id == entry_id))
        entry = result.scalar_one_or_none()
        if not entry:
            return JSONResponse({"detail": "黑名单记录不存在"}, status_code=404)

        await session.delete(entry)
        await session.commit()

    return JSONResponse({"detail": "已从黑名单移除"})


routes = [
    Route("/api/blacklist", list_blacklist, methods=["GET"]),
    Route("/api/blacklist", add_blacklist, methods=["POST"]),
    Route("/api/blacklist/{id:int}", remove_blacklist, methods=["DELETE"]),
]
