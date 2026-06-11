import logging

from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from auth import hash_password, verify_password, create_token
from database import async_session
from models import User

logger = logging.getLogger(__name__)


async def login(request: Request) -> JSONResponse:
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return JSONResponse({"detail": "用户名或密码错误"}, status_code=401)

    token = create_token(user.id, user.role)
    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    })


async def me(request: Request) -> JSONResponse:
    user_info = request.state.user
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_info["user_id"]))
        user = result.scalar_one_or_none()

    if not user:
        return JSONResponse({"detail": "用户不存在"}, status_code=404)

    return JSONResponse({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


routes = [
    Route("/api/auth/login", login, methods=["POST"]),
    Route("/api/auth/me", me, methods=["GET"]),
]
