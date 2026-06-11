import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import JWT_SECRET, JWT_EXPIRATION_HOURS


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def create_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/") or path == "/api/auth/login":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if not auth_header.startswith("Bearer "):
            response = JSONResponse({"detail": "未提供认证令牌"}, status_code=401)
            await response(scope, receive, send)
            return

        token = auth_header[7:]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            response = JSONResponse({"detail": "认证令牌已过期"}, status_code=401)
            await response(scope, receive, send)
            return
        except jwt.InvalidTokenError:
            response = JSONResponse({"detail": "无效的认证令牌"}, status_code=401)
            await response(scope, receive, send)
            return

        scope["state"] = {"user": payload}

        async def modified_receive():
            return await receive()

        await self.app(scope, modified_receive, send)
