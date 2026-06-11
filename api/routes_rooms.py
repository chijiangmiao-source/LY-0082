import logging

from sqlalchemy import select, func, and_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Room, Visit

logger = logging.getLogger(__name__)


async def list_rooms(request: Request) -> JSONResponse:
    floor_id = request.query_params.get("floor_id")
    async with async_session() as session:
        stmt = select(Room)
        if floor_id:
            stmt = stmt.where(Room.floor_id == int(floor_id))
        result = await session.execute(stmt)
        rooms = result.scalars().all()

        room_data = []
        for r in rooms:
            active_result = await session.execute(
                select(func.count()).select_from(Visit).where(
                    and_(
                        Visit.room_id == r.id,
                        Visit.check_in_time.isnot(None),
                        Visit.check_out_time.is_(None),
                        Visit.release_status == "released",
                    )
                )
            )
            current_visitors = active_result.scalar() or 0
            room_data.append({
                "id": r.id,
                "room_number": r.room_number,
                "floor_id": r.floor_id,
                "room_type": r.room_type,
                "occupancy_status": r.occupancy_status,
                "max_visitors": r.max_visitors,
                "current_visitors": current_visitors,
            })

    return JSONResponse(room_data)


async def create_room(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    body = await request.json()
    async with async_session() as session:
        room = Room(
            room_number=body.get("room_number", ""),
            floor_id=body.get("floor_id"),
            room_type=body.get("room_type", "single"),
            occupancy_status=body.get("occupancy_status", "vacant"),
            max_visitors=body.get("max_visitors", 2),
        )
        session.add(room)
        await session.commit()
        await session.refresh(room)

    return JSONResponse({
        "id": room.id,
        "room_number": room.room_number,
        "floor_id": room.floor_id,
        "room_type": room.room_type,
        "occupancy_status": room.occupancy_status,
        "max_visitors": room.max_visitors,
    }, status_code=201)


async def update_room(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    room_id = int(request.path_params["id"])
    body = await request.json()

    async with async_session() as session:
        result = await session.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            return JSONResponse({"detail": "房间不存在"}, status_code=404)

        if "room_number" in body:
            room.room_number = body["room_number"]
        if "floor_id" in body:
            room.floor_id = body["floor_id"]
        if "room_type" in body:
            room.room_type = body["room_type"]
        if "occupancy_status" in body:
            room.occupancy_status = body["occupancy_status"]
        if "max_visitors" in body:
            room.max_visitors = body["max_visitors"]

        await session.commit()
        await session.refresh(room)

    return JSONResponse({
        "id": room.id,
        "room_number": room.room_number,
        "floor_id": room.floor_id,
        "room_type": room.room_type,
        "occupancy_status": room.occupancy_status,
        "max_visitors": room.max_visitors,
    })


async def delete_room(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    room_id = int(request.path_params["id"])
    async with async_session() as session:
        result = await session.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            return JSONResponse({"detail": "房间不存在"}, status_code=404)

        await session.delete(room)
        await session.commit()

    return JSONResponse({"detail": "删除成功"})


routes = [
    Route("/api/rooms", list_rooms, methods=["GET"]),
    Route("/api/rooms", create_room, methods=["POST"]),
    Route("/api/rooms/{id:int}", update_room, methods=["PUT"]),
    Route("/api/rooms/{id:int}", delete_room, methods=["DELETE"]),
]
