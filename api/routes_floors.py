import logging

from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import Floor

logger = logging.getLogger(__name__)


async def list_floors(request: Request) -> JSONResponse:
    async with async_session() as session:
        result = await session.execute(select(Floor).order_by(Floor.sort_order))
        floors = result.scalars().all()

    return JSONResponse([
        {
            "id": f.id,
            "name": f.name,
            "sort_order": f.sort_order,
        }
        for f in floors
    ])


async def create_floor(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    body = await request.json()
    async with async_session() as session:
        floor = Floor(
            name=body.get("name", ""),
            sort_order=body.get("sort_order", 0),
        )
        session.add(floor)
        await session.commit()
        await session.refresh(floor)

    return JSONResponse({
        "id": floor.id,
        "name": floor.name,
        "sort_order": floor.sort_order,
    }, status_code=201)


async def update_floor(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    floor_id = int(request.path_params["id"])
    body = await request.json()

    async with async_session() as session:
        result = await session.execute(select(Floor).where(Floor.id == floor_id))
        floor = result.scalar_one_or_none()
        if not floor:
            return JSONResponse({"detail": "楼层不存在"}, status_code=404)

        if "name" in body:
            floor.name = body["name"]
        if "sort_order" in body:
            floor.sort_order = body["sort_order"]

        await session.commit()
        await session.refresh(floor)

    return JSONResponse({
        "id": floor.id,
        "name": floor.name,
        "sort_order": floor.sort_order,
    })


async def delete_floor(request: Request) -> JSONResponse:
    user_info = request.state.user
    if user_info["role"] != "admin":
        return JSONResponse({"detail": "权限不足"}, status_code=403)

    floor_id = int(request.path_params["id"])
    async with async_session() as session:
        result = await session.execute(select(Floor).where(Floor.id == floor_id))
        floor = result.scalar_one_or_none()
        if not floor:
            return JSONResponse({"detail": "楼层不存在"}, status_code=404)

        await session.delete(floor)
        await session.commit()

    return JSONResponse({"detail": "删除成功"})


routes = [
    Route("/api/floors", list_floors, methods=["GET"]),
    Route("/api/floors", create_floor, methods=["POST"]),
    Route("/api/floors/{id:int}", update_floor, methods=["PUT"]),
    Route("/api/floors/{id:int}", delete_floor, methods=["DELETE"]),
]
