import logging
from datetime import datetime, timezone

from sqlalchemy import select

from auth import hash_password
from database import async_session
from models import User, Floor, Room, Resident, Blacklist

logger = logging.getLogger(__name__)


async def seed_data():
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            return

        admin = User(username="admin", password_hash=hash_password("admin123"), role="admin")
        receptionist = User(username="receptionist", password_hash=hash_password("reception123"), role="receptionist")
        session.add_all([admin, receptionist])

        floors = [
            Floor(name="1楼", sort_order=1),
            Floor(name="2楼", sort_order=2),
            Floor(name="3楼", sort_order=3),
        ]
        session.add_all(floors)
        await session.flush()

        rooms = []
        for floor in floors:
            for i in range(1, 6):
                rooms.append(Room(
                    room_number=f"{floor.sort_order}{i:02d}",
                    floor_id=floor.id,
                    room_type=["single", "double", "suite", "vip"][(i - 1) % 4],
                    occupancy_status="vacant",
                    max_visitors=2,
                ))
        session.add_all(rooms)
        await session.flush()

        now = datetime.now(timezone.utc)
        residents = [
            Resident(name="张三", phone="13800001111", room_id=rooms[0].id, check_in_date=now, expected_check_out_date=None),
            Resident(name="李四", phone="13800002222", room_id=rooms[1].id, check_in_date=now, expected_check_out_date=None),
            Resident(name="王五", phone="13800003333", room_id=rooms[5].id, check_in_date=now, expected_check_out_date=None),
        ]
        session.add_all(residents)

        blacklist_entry = Blacklist(
            visitor_name="赵六",
            visitor_id_card="999999199901011234",
            reason="曾扰乱秩序",
        )
        session.add(blacklist_entry)

        await session.commit()

    logger.info("种子数据初始化完成")
