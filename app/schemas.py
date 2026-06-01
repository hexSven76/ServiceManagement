from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .models import BookingStatusEnum, PaymentStatusEnum, RoleEnum, ServiceStatusEnum, SlotStatusEnum, NotificationTypeEnum


@dataclass
class UserCreate:
    username: str
    email: str
    password: str
    role: RoleEnum
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    image_path: str | None = None


@dataclass
class LoginRequest:
    identifier: str
    password: str


@dataclass
class ServiceCreate:
    provider_id: int
    title: str
    description: str | None
    category: str | None
    duration_minutes: int
    price: float
    image_path: str | None = None
    status: ServiceStatusEnum = ServiceStatusEnum.ACTIVE


@dataclass
class ServiceUpdate:
    title: str | None = None
    description: str | None = None
    category: str | None = None
    duration_minutes: int | None = None
    price: float | None = None
    image_path: str | None = None
    status: ServiceStatusEnum | None = None


@dataclass
class SlotCreate:
    service_id: int
    start_time: datetime
    end_time: datetime
    status: SlotStatusEnum = SlotStatusEnum.ACTIVE


@dataclass
class BookingCreate:
    slot_id: int


@dataclass
class PaymentCreate:
    booking_id: int
    payment_reference: str | None = None


@dataclass
class ReviewCreate:
    booking_id: int
    rating: int
    comment: str | None = None
