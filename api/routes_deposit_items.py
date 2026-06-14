import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_, or_, func, case
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import DepositRecord, ItemLoanRecord, Appointment, Room, Resident

logger = logging.getLogger(__name__)


def _format_dt(dt):
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def deposit_list(request: Request) -> JSONResponse:
    params = request.query_params
    status = params.get("status")
    visitor_name = params.get("visitor_name")
    appointment_id = params.get("appointment_id")

    async with async_session() as session:
        stmt = select(DepositRecord).join(
            Appointment, DepositRecord.appointment_id == Appointment.id
        )
        conditions = []
        if status:
            conditions.append(DepositRecord.status == status)
        if visitor_name:
            conditions.append(DepositRecord.visitor_name.like(f"%{visitor_name}%"))
        if appointment_id:
            conditions.append(DepositRecord.appointment_id == int(appointment_id))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(DepositRecord.collected_at.desc())

        result = await session.execute(stmt)
        records = result.scalars().all()

        apt_ids = [r.appointment_id for r in records]
        apt_info = {}
        if apt_ids:
            apt_stmt = (
                select(Appointment, Room, Resident)
                .join(Room, Appointment.resident.has(Room))
                .join(Resident, Appointment.resident_id == Resident.id)
                .where(Appointment.id.in_(apt_ids))
            )
            apt_result = await session.execute(apt_stmt)
            for apt, room, resident in apt_result.all():
                apt_info[apt.id] = {
                    "appointment_no": apt.appointment_no,
                    "room_number": room.room_number if room else None,
                    "resident_name": resident.name if resident else None,
                }

    return JSONResponse([
        {
            "id": r.id,
            "visit_id": r.visit_id,
            "appointment_id": r.appointment_id,
            "visitor_name": r.visitor_name,
            "amount": r.amount,
            "status": r.status,
            "refund_amount": r.refund_amount,
            "deduct_amount": r.deduct_amount,
            "deduct_reason": r.deduct_reason,
            "collected_at": _format_dt(r.collected_at),
            "refunded_at": _format_dt(r.refunded_at),
            "operator": r.operator,
            "appointment_no": apt_info.get(r.appointment_id, {}).get("appointment_no"),
            "room_number": apt_info.get(r.appointment_id, {}).get("room_number"),
            "resident_name": apt_info.get(r.appointment_id, {}).get("resident_name"),
        }
        for r in records
    ])


async def deposit_create(request: Request) -> JSONResponse:
    data = await request.json()
    operator = request.state.user.username if hasattr(request.state, "user") else None

    appointment_id = data.get("appointment_id")
    visit_id = data.get("visit_id")
    visitor_name = data.get("visitor_name")
    amount = float(data.get("amount", 0))

    if not appointment_id or not visitor_name or amount <= 0:
        return JSONResponse({"detail": "参数不完整"}, status_code=400)

    async with async_session() as session:
        record = DepositRecord(
            appointment_id=appointment_id,
            visit_id=visit_id,
            visitor_name=visitor_name,
            amount=amount,
            status="collected",
            operator=operator,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return JSONResponse({"id": record.id, "status": "collected"})


async def deposit_settle(request: Request) -> JSONResponse:
    deposit_id = request.path_params["id"]
    data = await request.json()
    operator = request.state.user.username if hasattr(request.state, "user") else None

    action = data.get("action")
    refund_amount = data.get("refund_amount")
    deduct_amount = data.get("deduct_amount")
    deduct_reason = data.get("deduct_reason")

    if action not in ("refund", "partial_refund", "deduct"):
        return JSONResponse({"detail": "无效的操作类型"}, status_code=400)

    async with async_session() as session:
        stmt = select(DepositRecord).where(DepositRecord.id == deposit_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return JSONResponse({"detail": "押金记录不存在"}, status_code=404)
        if record.status != "collected":
            return JSONResponse({"detail": "押金状态不允许结算"}, status_code=400)

        now = datetime.now(timezone.utc)
        if action == "refund":
            record.status = "refunded"
            record.refund_amount = record.amount
            record.deduct_amount = 0
        elif action == "partial_refund":
            if refund_amount is None:
                return JSONResponse({"detail": "请提供退款金额"}, status_code=400)
            refund_amount = float(refund_amount)
            record.status = "partial_refunded"
            record.refund_amount = refund_amount
            record.deduct_amount = record.amount - refund_amount
            record.deduct_reason = deduct_reason
        elif action == "deduct":
            if deduct_reason is None or deduct_reason.strip() == "":
                return JSONResponse({"detail": "请提供扣费原因"}, status_code=400)
            record.status = "deducted"
            record.refund_amount = 0
            record.deduct_amount = record.amount
            record.deduct_reason = deduct_reason

        record.refunded_at = now
        record.operator = operator or record.operator
        await session.commit()

    return JSONResponse({"id": record.id, "status": record.status})


async def item_list(request: Request) -> JSONResponse:
    params = request.query_params
    status = params.get("status")
    item_type = params.get("item_type")
    visitor_name = params.get("visitor_name")
    appointment_id = params.get("appointment_id")

    async with async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = select(ItemLoanRecord).join(
            Appointment, ItemLoanRecord.appointment_id == Appointment.id
        )
        conditions = []
        if status and status != "overdue_due":
            conditions.append(ItemLoanRecord.status == status)
        if item_type:
            conditions.append(ItemLoanRecord.item_type == item_type)
        if visitor_name:
            conditions.append(ItemLoanRecord.visitor_name.like(f"%{visitor_name}%"))
        if appointment_id:
            conditions.append(ItemLoanRecord.appointment_id == int(appointment_id))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(ItemLoanRecord.loaned_at.desc())

        result = await session.execute(stmt)
        records = result.scalars().all()

        updated_records = []
        for r in records:
            if (
                r.status == "loaned"
                and r.due_return_at is not None
                and now > r.due_return_at
            ):
                r.status = "overdue"
                updated_records.append(r)
        if updated_records:
            await session.commit()

        apt_ids = [r.appointment_id for r in records]
        apt_info = {}
        if apt_ids:
            apt_stmt = (
                select(Appointment, Room, Resident)
                .join(Resident, Appointment.resident_id == Resident.id)
                .outerjoin(Room, Resident.room_id == Room.id)
                .where(Appointment.id.in_(apt_ids))
            )
            apt_result = await session.execute(apt_stmt)
            for apt, room, resident in apt_result.all():
                apt_info[apt.id] = {
                    "appointment_no": apt.appointment_no,
                    "room_number": room.room_number if room else None,
                    "resident_name": resident.name if resident else None,
                }

    return JSONResponse([
        {
            "id": r.id,
            "visit_id": r.visit_id,
            "appointment_id": r.appointment_id,
            "visitor_name": r.visitor_name,
            "item_type": r.item_type,
            "item_name": r.item_name,
            "item_identifier": r.item_identifier,
            "status": r.status,
            "loaned_at": _format_dt(r.loaned_at),
            "due_return_at": _format_dt(r.due_return_at),
            "returned_at": _format_dt(r.returned_at),
            "abnormal_reason": r.abnormal_reason,
            "operator": r.operator,
            "appointment_no": apt_info.get(r.appointment_id, {}).get("appointment_no"),
            "room_number": apt_info.get(r.appointment_id, {}).get("room_number"),
            "resident_name": apt_info.get(r.appointment_id, {}).get("resident_name"),
        }
        for r in records
    ])


async def item_create(request: Request) -> JSONResponse:
    data = await request.json()
    operator = request.state.user.username if hasattr(request.state, "user") else None

    appointment_id = data.get("appointment_id")
    visit_id = data.get("visit_id")
    visitor_name = data.get("visitor_name")
    item_type = data.get("item_type")
    item_name = data.get("item_name")
    item_identifier = data.get("item_identifier")
    due_return_at = data.get("due_return_at")

    if not appointment_id or not visitor_name or not item_type or not item_name:
        return JSONResponse({"detail": "参数不完整"}, status_code=400)

    valid_types = {"temporary_id", "escort_clothes", "locker_key", "escort_bed", "other"}
    if item_type not in valid_types:
        return JSONResponse({"detail": "无效的物品类型"}, status_code=400)

    async with async_session() as session:
        due = None
        if due_return_at:
            try:
                due = datetime.fromisoformat(due_return_at.replace("Z", "+00:00"))
            except ValueError:
                pass

        record = ItemLoanRecord(
            appointment_id=appointment_id,
            visit_id=visit_id,
            visitor_name=visitor_name,
            item_type=item_type,
            item_name=item_name,
            item_identifier=item_identifier,
            status="loaned",
            due_return_at=due,
            operator=operator,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return JSONResponse({"id": record.id, "status": "loaned"})


async def item_return(request: Request) -> JSONResponse:
    item_id = request.path_params["id"]
    data = await request.json()
    operator = request.state.user.username if hasattr(request.state, "user") else None

    action = data.get("action", "return")
    abnormal_reason = data.get("abnormal_reason")

    valid_actions = {"return", "lost", "damaged"}
    if action not in valid_actions:
        return JSONResponse({"detail": "无效的操作类型"}, status_code=400)

    if action in ("lost", "damaged") and (not abnormal_reason or abnormal_reason.strip() == ""):
        return JSONResponse({"detail": "请提供异常原因"}, status_code=400)

    async with async_session() as session:
        stmt = select(ItemLoanRecord).where(ItemLoanRecord.id == item_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return JSONResponse({"detail": "领用记录不存在"}, status_code=404)
        if record.status in ("returned", "lost", "damaged"):
            return JSONResponse({"detail": "该物品已完成归还/异常处理"}, status_code=400)

        now = datetime.now(timezone.utc)
        if action == "return":
            record.status = "returned"
        elif action == "lost":
            record.status = "lost"
            record.abnormal_reason = abnormal_reason
        elif action == "damaged":
            record.status = "damaged"
            record.abnormal_reason = abnormal_reason

        record.returned_at = now
        record.operator = operator or record.operator
        await session.commit()

    return JSONResponse({"id": record.id, "status": record.status})


async def deposit_item_summary(request: Request) -> JSONResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        pending_deposit_result = await session.execute(
            select(func.count()).select_from(DepositRecord).where(
                DepositRecord.status == "collected"
            )
        )
        pending_deposit_count = pending_deposit_result.scalar()

        pending_deposit_amount_result = await session.execute(
            select(func.coalesce(func.sum(DepositRecord.amount), 0)).select_from(DepositRecord).where(
                DepositRecord.status == "collected"
            )
        )
        pending_deposit_amount = pending_deposit_amount_result.scalar() or 0

        overdue_items_result = await session.execute(
            select(func.count()).select_from(ItemLoanRecord).where(
                or_(
                    ItemLoanRecord.status == "overdue",
                    and_(
                        ItemLoanRecord.status == "loaned",
                        ItemLoanRecord.due_return_at.isnot(None),
                        ItemLoanRecord.due_return_at < now,
                    ),
                )
            )
        )
        overdue_item_count = overdue_items_result.scalar()

        abnormal_items_result = await session.execute(
            select(func.count()).select_from(ItemLoanRecord).where(
                ItemLoanRecord.status.in_(["lost", "damaged"])
            )
        )
        abnormal_item_count = abnormal_items_result.scalar()

        today_collected_result = await session.execute(
            select(func.count()).select_from(DepositRecord).where(
                DepositRecord.collected_at >= today_start
            )
        )
        today_collected_count = today_collected_result.scalar()

        today_collected_amount_result = await session.execute(
            select(func.coalesce(func.sum(DepositRecord.amount), 0)).select_from(DepositRecord).where(
                DepositRecord.collected_at >= today_start
            )
        )
        today_collected_amount = today_collected_amount_result.scalar() or 0

        item_distribution_result = await session.execute(
            select(
                ItemLoanRecord.item_type,
                func.count().label("total_count"),
                func.sum(
                    case(
                        (ItemLoanRecord.status.in_(["lost", "damaged"]), 1),
                        else_=0,
                    )
                ).label("abnormal_count"),
            )
            .group_by(ItemLoanRecord.item_type)
            .order_by(func.count().desc())
        )
        item_distribution = [
            {
                "item_type": row[0],
                "total_count": row[1],
                "abnormal_count": row[2] or 0,
            }
            for row in item_distribution_result.all()
        ]

        item_name_map = {
            "temporary_id": "临时证件",
            "escort_clothes": "陪护服",
            "locker_key": "储物柜钥匙",
            "escort_bed": "陪护床用品",
            "other": "其他物品",
        }
        for d in item_distribution:
            d["item_name"] = item_name_map.get(d["item_type"], d["item_type"])

    return JSONResponse({
        "pending_deposit_count": pending_deposit_count,
        "pending_deposit_amount": float(pending_deposit_amount),
        "overdue_item_count": overdue_item_count,
        "abnormal_item_count": abnormal_item_count,
        "today_collected_count": today_collected_count,
        "today_collected_amount": float(today_collected_amount),
        "item_distribution": item_distribution,
    })


routes = [
    Route("/api/deposits", deposit_list, methods=["GET"]),
    Route("/api/deposits", deposit_create, methods=["POST"]),
    Route("/api/deposits/{id:int}/settle", deposit_settle, methods=["POST"]),
    Route("/api/items", item_list, methods=["GET"]),
    Route("/api/items", item_create, methods=["POST"]),
    Route("/api/items/{id:int}/return", item_return, methods=["POST"]),
    Route("/api/deposit-items/summary", deposit_item_summary, methods=["GET"]),
]
