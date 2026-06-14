from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("admin", "receptionist", name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    rooms: Mapped[list["Room"]] = relationship(back_populates="floor")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor_id: Mapped[int] = mapped_column(Integer, ForeignKey("floors.id"), nullable=False)
    room_type: Mapped[str] = mapped_column(Enum("single", "double", "suite", "vip", name="room_type"), nullable=False)
    occupancy_status: Mapped[str] = mapped_column(
        Enum("vacant", "occupied", "maintenance", name="occupancy_status"), default="vacant"
    )
    max_visitors: Mapped[int] = mapped_column(Integer, default=2)

    floor: Mapped["Floor"] = relationship(back_populates="rooms")
    residents: Mapped[list["Resident"]] = relationship(back_populates="room")


class Resident(Base):
    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_check_out_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    room: Mapped["Room"] = relationship(back_populates="residents")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="resident")


class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visitor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    visitor_id_card: Mapped[str] = mapped_column(String(18), unique=True, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VisitorWhitelist(Base):
    __tablename__ = "visitor_whitelist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resident_id: Mapped[int] = mapped_column(Integer, ForeignKey("residents.id"), nullable=False)
    visitor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    visitor_id_card: Mapped[str] = mapped_column(String(18), nullable=False)
    visitor_relation: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    resident: Mapped["Resident"] = relationship()


class VisitCode(Base):
    __tablename__ = "visit_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id"), nullable=False)
    is_used: Mapped[bool] = mapped_column(default=False)
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    appointment: Mapped["Appointment"] = relationship(back_populates="visit_code")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    resident_id: Mapped[int] = mapped_column(Integer, ForeignKey("residents.id"), nullable=False)
    visitor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    visitor_id_card: Mapped[str] = mapped_column(String(18), nullable=False)
    visitor_relation: Mapped[str] = mapped_column(String(20), nullable=True)
    is_whitelist_visitor: Mapped[bool] = mapped_column(default=False)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "checked_in", "checked_out", "cancelled", "rejected", name="appointment_status"),
        default="pending",
    )

    resident: Mapped["Resident"] = relationship(back_populates="appointments")
    visits: Mapped[list["Visit"]] = relationship(back_populates="appointment")
    visit_code: Mapped["VisitCode"] = relationship(back_populates="appointment", uselist=False)


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False)
    visit_code_id: Mapped[int] = mapped_column(Integer, ForeignKey("visit_codes.id"), nullable=True)
    check_in_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    check_out_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    release_status: Mapped[str] = mapped_column(Enum("released", "rejected", name="release_status"), nullable=False)
    reject_reason: Mapped[str] = mapped_column(String(255), nullable=True)

    appointment: Mapped["Appointment"] = relationship(back_populates="visits")
    room: Mapped["Room"] = relationship()
    visit_code: Mapped["VisitCode"] = relationship()


class CodeErrorLog(Base):
    __tablename__ = "code_error_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    error_type: Mapped[str] = mapped_column(
        Enum("invalid_code", "code_used", "invalid_appointment", name="code_error_type"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
