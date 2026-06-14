import logging

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from auth import AuthMiddleware
from database import engine, Base
from init_data import seed_data
from routes_auth import routes as auth_routes
from routes_floors import routes as floor_routes
from routes_rooms import routes as room_routes
from routes_residents import routes as resident_routes
from routes_appointments import routes as appointment_routes
from routes_visits import routes as visit_routes
from routes_blacklist import routes as blacklist_routes
from routes_statistics import routes as statistics_routes
from routes_whitelist import routes as whitelist_routes
from routes_deposit_items import routes as deposit_items_routes
from routes_visitor_bills import routes as visitor_bills_routes

logger = logging.getLogger(__name__)

all_routes = auth_routes + floor_routes + room_routes + resident_routes + appointment_routes + visit_routes + blacklist_routes + statistics_routes + whitelist_routes + deposit_items_routes + visitor_bills_routes


async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表创建完成")
    await seed_data()


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]

app = Starlette(
    routes=all_routes,
    middleware=middleware,
    on_startup=[startup],
)

app.add_middleware(AuthMiddleware)
