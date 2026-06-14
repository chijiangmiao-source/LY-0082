import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from database import async_session
from models import (
    Appointment,
    Visit,
    Room,
    Resident,
    DepositRecord,
    ItemLoanRecord,
    VisitorBill,
    BillChargeItem,
    ElectronicSignature,
)

logger = logging.getLogger(__name__)


def generate_bill_no() -> str:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    import random
    suffix = "".join([str(random.randint(0, 9)) for _ in range(4)])
    return f"VB{timestamp}{suffix}"


async def calculate_overtime_fee(visit: Visit, appointment: Appointment) -> tuple[float, str]:
    if not visit.check_in_time or not visit.check_out_time or not appointment.scheduled_end:
        return 0, ""

    scheduled_end = appointment.scheduled_end
    actual_end = visit.check_out_time

    if actual_end <= scheduled_end:
        return 0, ""

    overtime_minutes = (actual_end - scheduled_end).total_seconds() / 60
    overtime_minutes = max(0, overtime_minutes)

    if overtime_minutes < 15:
        return 0, ""

    overtime_hours = (overtime_minutes + 59) // 60
    fee_rate = 50
    fee = overtime_hours * fee_rate

    description = f"超时{int(overtime_minutes)}分钟，按{int(overtime_hours)}小时计算，每小时{fee_rate}元"
    return fee, description


async def generate_bill(request: Request) -> JSONResponse:
    body = await request.json()
    visit_id = body.get("visit_id")
    operator = body.get("operator", "")

    if not visit_id:
        return JSONResponse({"detail": "请提供visit_id"}, status_code=400)

    async with async_session() as session:
        visit_result = await session.execute(
            select(Visit, Appointment, Room, Resident)
            .join(Appointment, Visit.appointment_id == Appointment.id)
            .join(Room, Visit.room_id == Room.id)
            .join(Resident, Appointment.resident_id == Resident.id)
            .where(Visit.id == visit_id)
        )
        row = visit_result.first()
        if not row:
            return JSONResponse({"detail": "未找到探视记录"}, status_code=404)

        visit = row.Visit
        appointment = row.Appointment
        room = row.Room
        resident = row.Resident

        existing_bill_result = await session.execute(
            select(VisitorBill).where(VisitorBill.visit_id == visit_id)
        )
        if existing_bill_result.scalar_one_or_none():
            return JSONResponse({"detail": "该探视已生成账单"}, status_code=400)

        deposit_result = await session.execute(
            select(DepositRecord).where(
                and_(
                    DepositRecord.appointment_id == appointment.id,
                    DepositRecord.status.in_(["collected", "refunded", "partial_refunded", "deducted"]),
                )
            )
        )
        deposits = deposit_result.scalars().all()

        items_result = await session.execute(
            select(ItemLoanRecord).where(
                and_(
                    ItemLoanRecord.appointment_id == appointment.id,
                    ItemLoanRecord.status.in_(["returned", "lost", "damaged"]),
                )
            )
        )
        items = items_result.scalars().all()

        deposit_amount = 0
        deposit_refund_amount = 0
        item_damage_fee = 0
        item_lost_fee = 0
        other_fee = 0

        charge_items = []

        for dep in deposits:
            deposit_amount += dep.amount
            if dep.status == "refunded":
                refund = dep.refund_amount if dep.refund_amount is not None else dep.amount
                deposit_refund_amount += refund
                charge_items.append({
                    "charge_type": "deposit_refund",
                    "item_name": "押金退还",
                    "description": f"押金全额退还",
                    "amount": -refund,
                    "related_record_id": dep.id,
                })
            elif dep.status == "partial_refunded":
                refund = dep.refund_amount if dep.refund_amount is not None else 0
                deduct = dep.deduct_amount if dep.deduct_amount is not None else (dep.amount - refund)
                deposit_refund_amount += refund
                other_fee += deduct
                charge_items.append({
                    "charge_type": "deposit_refund",
                    "item_name": "押金退还",
                    "description": f"押金部分退还",
                    "amount": -refund,
                    "related_record_id": dep.id,
                })
                charge_items.append({
                    "charge_type": "other",
                    "item_name": "扣费",
                    "description": dep.deduct_reason or "扣费",
                    "amount": deduct,
                    "related_record_id": dep.id,
                })
            elif dep.status == "deducted":
                deduct = dep.deduct_amount if dep.deduct_amount is not None else dep.amount
                other_fee += deduct
                charge_items.append({
                    "charge_type": "other",
                    "item_name": "押金全额扣费",
                    "description": dep.deduct_reason or "扣费",
                    "amount": deduct,
                    "related_record_id": dep.id,
                })

            if dep.status == "collected":
                charge_items.append({
                    "charge_type": "deposit_collect",
                    "item_name": "押金收取",
                    "description": f"押金收取",
                    "amount": dep.amount,
                    "related_record_id": dep.id,
                })

        for item in items:
            if item.status == "damaged":
                fee = 0
                if item.item_type == "temporary_id":
                    fee = 50
                elif item.item_type == "escort_clothes":
                    fee = 100
                elif item.item_type == "locker_key":
                    fee = 80
                elif item.item_type == "escort_bed":
                    fee = 200
                else:
                    fee = 50

                item_damage_fee += fee
                charge_items.append({
                    "charge_type": "item_damage",
                    "item_name": f"{item.item_name}损坏",
                    "description": item.abnormal_reason or "物品损坏",
                    "amount": fee,
                    "related_record_id": item.id,
                })
            elif item.status == "lost":
                fee = 0
                if item.item_type == "temporary_id":
                    fee = 100
                elif item.item_type == "escort_clothes":
                    fee = 200
                elif item.item_type == "locker_key":
                    fee = 150
                elif item.item_type == "escort_bed":
                    fee = 500
                else:
                    fee = 100

                item_lost_fee += fee
                charge_items.append({
                    "charge_type": "item_lost",
                    "item_name": f"{item.item_name}丢失",
                    "description": item.abnormal_reason or "物品丢失",
                    "amount": fee,
                    "related_record_id": item.id,
                })

        overtime_fee, overtime_desc = await calculate_overtime_fee(visit, appointment)
        if overtime_fee > 0:
            charge_items.append({
                "charge_type": "overtime",
                "item_name": "超时占用附加费",
                "description": overtime_desc,
                "amount": overtime_fee,
                "related_record_id": None,
            })

        total_charge = sum(ci["amount"] for ci in charge_items if ci["amount"] > 0)
        total_refund = sum(-ci["amount"] for ci in charge_items if ci["amount"] < 0)
        total_amount = total_charge - total_refund

        if not visit.check_out_time:
            visit.check_out_time = datetime.now(timezone.utc)
            appointment.status = "checked_out"

        bill = VisitorBill(
            bill_no=generate_bill_no(),
            visit_id=visit.id,
            appointment_id=appointment.id,
            visitor_name=appointment.visitor_name,
            room_number=room.room_number,
            resident_name=resident.name,
            deposit_amount=deposit_amount,
            deposit_refund_amount=deposit_refund_amount,
            item_damage_fee=item_damage_fee,
            item_lost_fee=item_lost_fee,
            overtime_fee=overtime_fee,
            other_fee=other_fee,
            total_amount=max(0, total_amount),
            actual_paid=0,
            payment_status="pending",
            signature_status="unsigned",
            operator=operator,
        )
        session.add(bill)
        await session.flush()

        for ci in charge_items:
            bill_charge_item = BillChargeItem(
                bill_id=bill.id,
                charge_type=ci["charge_type"],
                item_name=ci["item_name"],
                description=ci["description"],
                amount=ci["amount"],
                related_record_id=ci["related_record_id"],
            )
            session.add(bill_charge_item)

        await session.commit()
        await session.refresh(bill)

    return await get_bill_detail_internal(bill.id, session)


async def get_bill_detail_internal(bill_id: int, session) -> JSONResponse:
    bill_result = await session.execute(
        select(VisitorBill).where(VisitorBill.id == bill_id)
    )
    bill = bill_result.scalar_one_or_none()
    if not bill:
        return JSONResponse({"detail": "账单不存在"}, status_code=404)

    items_result = await session.execute(
        select(BillChargeItem).where(BillChargeItem.bill_id == bill_id).order_by(BillChargeItem.created_at)
    )
    charge_items = items_result.scalars().all()

    signature_result = await session.execute(
        select(ElectronicSignature).where(ElectronicSignature.bill_id == bill_id)
    )
    signature = signature_result.scalar_one_or_none()

    visit_result = await session.execute(
        select(Visit).where(Visit.id == bill.visit_id)
    )
    visit = visit_result.scalar_one_or_none()

    return JSONResponse({
        "id": bill.id,
        "bill_no": bill.bill_no,
        "visit_id": bill.visit_id,
        "appointment_id": bill.appointment_id,
        "visitor_name": bill.visitor_name,
        "room_number": bill.room_number,
        "resident_name": bill.resident_name,
        "deposit_amount": float(bill.deposit_amount),
        "deposit_refund_amount": float(bill.deposit_refund_amount),
        "item_damage_fee": float(bill.item_damage_fee),
        "item_lost_fee": float(bill.item_lost_fee),
        "overtime_fee": float(bill.overtime_fee),
        "other_fee": float(bill.other_fee),
        "total_amount": float(bill.total_amount),
        "actual_paid": float(bill.actual_paid),
        "payment_status": bill.payment_status,
        "signature_status": bill.signature_status,
        "generated_at": bill.generated_at.isoformat() if bill.generated_at else None,
        "paid_at": bill.paid_at.isoformat() if bill.paid_at else None,
        "remarks": bill.remarks,
        "operator": bill.operator,
        "check_in_time": visit.check_in_time.isoformat() if visit and visit.check_in_time else None,
        "check_out_time": visit.check_out_time.isoformat() if visit and visit.check_out_time else None,
        "charge_items": [
            {
                "id": ci.id,
                "charge_type": ci.charge_type,
                "item_name": ci.item_name,
                "description": ci.description,
                "amount": float(ci.amount),
                "created_at": ci.created_at.isoformat() if ci.created_at else None,
            }
            for ci in charge_items
        ],
        "signature": {
            "signer_name": signature.signer_name if signature else None,
            "signature_data": signature.signature_data if signature else None,
            "signed_at": signature.signed_at.isoformat() if signature and signature.signed_at else None,
            "sign_device": signature.sign_device if signature else None,
        } if signature else None,
    })


async def get_bill_detail(request: Request) -> JSONResponse:
    bill_id = int(request.path_params["id"])

    async with async_session() as session:
        return await get_bill_detail_internal(bill_id, session)


async def get_bill_by_visit(request: Request) -> JSONResponse:
    visit_id = int(request.path_params["visit_id"])

    async with async_session() as session:
        bill_result = await session.execute(
            select(VisitorBill).where(VisitorBill.visit_id == visit_id)
        )
        bill = bill_result.scalar_one_or_none()
        if not bill:
            return JSONResponse({"detail": "未找到账单"}, status_code=404)

        return await get_bill_detail_internal(bill.id, session)


async def list_bills(request: Request) -> JSONResponse:
    params = request.query_params
    visitor_name = params.get("visitor_name", "").strip()
    payment_status = params.get("payment_status", "").strip()
    signature_status = params.get("signature_status", "").strip()
    bill_no = params.get("bill_no", "").strip()
    start_date = params.get("start_date", "").strip()
    end_date = params.get("end_date", "").strip()

    async with async_session() as session:
        query = select(VisitorBill).order_by(VisitorBill.generated_at.desc())

        if visitor_name:
            query = query.where(VisitorBill.visitor_name.contains(visitor_name))
        if payment_status:
            query = query.where(VisitorBill.payment_status == payment_status)
        if signature_status:
            query = query.where(VisitorBill.signature_status == signature_status)
        if bill_no:
            query = query.where(VisitorBill.bill_no.contains(bill_no))
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.where(VisitorBill.generated_at >= start_dt)
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.where(VisitorBill.generated_at < end_dt)
            except:
                pass

        result = await session.execute(query)
        bills = result.scalars().all()

        return JSONResponse([
            {
                "id": bill.id,
                "bill_no": bill.bill_no,
                "visit_id": bill.visit_id,
                "visitor_name": bill.visitor_name,
                "room_number": bill.room_number,
                "resident_name": bill.resident_name,
                "total_amount": float(bill.total_amount),
                "actual_paid": float(bill.actual_paid),
                "payment_status": bill.payment_status,
                "signature_status": bill.signature_status,
                "generated_at": bill.generated_at.isoformat() if bill.generated_at else None,
            }
            for bill in bills
        ])


async def confirm_payment(request: Request) -> JSONResponse:
    bill_id = int(request.path_params["id"])
    body = await request.json()
    actual_paid = body.get("actual_paid")
    remarks = body.get("remarks", "")
    operator = body.get("operator", "")

    if actual_paid is None:
        return JSONResponse({"detail": "请提供实际支付金额"}, status_code=400)

    async with async_session() as session:
        bill_result = await session.execute(
            select(VisitorBill).where(VisitorBill.id == bill_id)
        )
        bill = bill_result.scalar_one_or_none()
        if not bill:
            return JSONResponse({"detail": "账单不存在"}, status_code=404)

        actual_paid = float(actual_paid)
        bill.actual_paid = actual_paid
        bill.paid_at = datetime.now(timezone.utc)
        bill.remarks = remarks or bill.remarks
        bill.operator = operator or bill.operator

        if actual_paid >= bill.total_amount:
            bill.payment_status = "paid"
        elif actual_paid > 0:
            bill.payment_status = "partial_paid"
        else:
            bill.payment_status = "waived"

        await session.commit()
        await session.refresh(bill)

        return await get_bill_detail_internal(bill.id, session)


async def sign_bill(request: Request) -> JSONResponse:
    bill_id = int(request.path_params["id"])
    body = await request.json()
    signer_name = body.get("signer_name", "").strip()
    signature_data = body.get("signature_data", "").strip()
    sign_device = body.get("sign_device", "")

    if not signer_name:
        return JSONResponse({"detail": "请提供签收人姓名"}, status_code=400)
    if not signature_data:
        return JSONResponse({"detail": "请提供签名数据"}, status_code=400)

    async with async_session() as session:
        bill_result = await session.execute(
            select(VisitorBill).where(VisitorBill.id == bill_id)
        )
        bill = bill_result.scalar_one_or_none()
        if not bill:
            return JSONResponse({"detail": "账单不存在"}, status_code=404)

        if bill.signature_status == "signed":
            return JSONResponse({"detail": "该账单已签名"}, status_code=400)

        signature = ElectronicSignature(
            bill_id=bill.id,
            signer_name=signer_name,
            signature_data=signature_data,
            sign_device=sign_device,
            sign_ip=request.client.host if request.client else None,
        )
        session.add(signature)

        bill.signature_status = "signed"
        await session.commit()

        return await get_bill_detail_internal(bill.id, session)


async def get_bill_statistics(request: Request) -> JSONResponse:
    params = request.query_params
    days = int(params.get("days", "30"))
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    async with async_session() as session:
        total_bills_result = await session.execute(
            select(func.count()).select_from(VisitorBill).where(
                VisitorBill.generated_at >= start_date
            )
        )
        total_bills = total_bills_result.scalar() or 0

        paid_bills_result = await session.execute(
            select(func.count()).select_from(VisitorBill).where(
                and_(
                    VisitorBill.generated_at >= start_date,
                    VisitorBill.payment_status == "paid",
                )
            )
        )
        paid_bills = paid_bills_result.scalar() or 0

        settlement_rate = round((paid_bills / total_bills) * 100, 1) if total_bills > 0 else 0

        deduct_items_result = await session.execute(
            select(BillChargeItem).where(
                and_(
                    BillChargeItem.amount > 0,
                    BillChargeItem.charge_type.in_(["item_damage", "item_lost", "overtime", "other"]),
                    BillChargeItem.created_at >= start_date,
                )
            )
        )
        deduct_items = deduct_items_result.scalars().all()

        total_deduct_amount = sum(item.amount for item in deduct_items)
        deduct_count = len(deduct_items)
        avg_deduct_amount = round(total_deduct_amount / deduct_count, 2) if deduct_count > 0 else 0

        reason_stats = {}
        for item in deduct_items:
            reason = item.item_name
            if reason not in reason_stats:
                reason_stats[reason] = {"count": 0, "total_amount": 0}
            reason_stats[reason]["count"] += 1
            reason_stats[reason]["total_amount"] += item.amount

        deduct_reason_distribution = sorted(
            [
                {
                    "reason": k,
                    "count": v["count"],
                    "total_amount": round(v["total_amount"], 2),
                }
                for k, v in reason_stats.items()
            ],
            key=lambda x: x["count"],
            reverse=True,
        )

        return JSONResponse({
            "total_bills": total_bills,
            "paid_bills": paid_bills,
            "settlement_rate": settlement_rate,
            "deduct_count": deduct_count,
            "total_deduct_amount": round(total_deduct_amount, 2),
            "avg_deduct_amount": avg_deduct_amount,
            "deduct_reason_distribution": deduct_reason_distribution,
        })


routes = [
    Route("/api/bills/generate", generate_bill, methods=["POST"]),
    Route("/api/bills/{id:int}", get_bill_detail, methods=["GET"]),
    Route("/api/bills/visit/{visit_id:int}", get_bill_by_visit, methods=["GET"]),
    Route("/api/bills", list_bills, methods=["GET"]),
    Route("/api/bills/{id:int}/pay", confirm_payment, methods=["POST"]),
    Route("/api/bills/{id:int}/sign", sign_bill, methods=["POST"]),
    Route("/api/bills/statistics", get_bill_statistics, methods=["GET"]),
]
