from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PROVIDER = "PROVIDER"
    CUSTOMER = "CUSTOMER"


class ServiceStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SlotStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class BookingStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"


class PaymentStatusEnum(str, enum.Enum):
    PAID = "PAID"
    UNPAID = "UNPAID"


class NotificationTypeEnum(str, enum.Enum):
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    BOOKING_REJECTED = "BOOKING_REJECTED"
    BOOKING_CANCELED = "BOOKING_CANCELED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    SYSTEM = "SYSTEM"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    services: Mapped[list["Service"]] = relationship(back_populates="provider", cascade="all, delete-orphan")
    bookings_as_customer: Mapped[list["Booking"]] = relationship(
        back_populates="customer", foreign_keys="Booking.customer_id"
    )
    bookings_as_provider: Mapped[list["Booking"]] = relationship(
        back_populates="provider", foreign_keys="Booking.provider_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reviews_written: Mapped[list["Review"]] = relationship(
    back_populates="customer",
    foreign_keys="Review.customer_id",
    cascade="all, delete-orphan",
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        back_populates="provider",
        foreign_keys="Review.provider_id",
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[ServiceStatusEnum] = mapped_column(Enum(ServiceStatusEnum), default=ServiceStatusEnum.ACTIVE, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    provider: Mapped[User] = relationship(back_populates="services")
    slots: Mapped[list["TimeSlot"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="service", cascade="all, delete-orphan")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    status: Mapped[SlotStatusEnum] = mapped_column(
        Enum(SlotStatusEnum),
        default=SlotStatusEnum.ACTIVE,
        nullable=False,
    )

    service: Mapped["Service"] = relationship(
        back_populates="slots"
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="slot",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "service_id",
            "start_time",
            "end_time",
            name="uq_slot_service_time",
        ),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("time_slots.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    status: Mapped[BookingStatusEnum] = mapped_column(
        Enum(BookingStatusEnum),
        default=BookingStatusEnum.PENDING,
        nullable=False,
    )

    payment_status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum),
        default=PaymentStatusEnum.UNPAID,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime)

    cancel_deadline: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    customer: Mapped["User"] = relationship(
        back_populates="bookings_as_customer",
        foreign_keys=[customer_id],
    )

    provider: Mapped["User"] = relationship(
        back_populates="bookings_as_provider",
        foreign_keys=[provider_id],
    )

    service: Mapped["Service"] = relationship(
        back_populates="bookings"
    )

    slot: Mapped["TimeSlot"] = relationship(
        back_populates="booking",
        foreign_keys=[slot_id],
    )

    payment: Mapped["Payment"] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        uselist=False,
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[PaymentStatusEnum] = mapped_column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PAID, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="payment")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationTypeEnum] = mapped_column(Enum(NotificationTypeEnum), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    booking: Mapped["Booking | None"] = relationship(foreign_keys=[related_booking_id])
    user: Mapped[User] = relationship(back_populates="notifications")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="reviews")
    customer: Mapped["User"] = relationship(
    back_populates="reviews_written",
    foreign_keys=[customer_id],
    )
    provider: Mapped["User"] = relationship(
        back_populates="reviews_received",
        foreign_keys=[provider_id],
    )
    service: Mapped[Service] = relationship(back_populates="reviews")
