from datetime import datetime, timedelta
import pytest
from app.models import RoleEnum, ServiceStatusEnum, SlotStatusEnum
from app.services.auth_service import AuthService
from app.services.service_service import ServiceService
from app.services.schedule_service import ScheduleService

def test_create_service_and_slot(session):
    auth = AuthService(session)
    provider = auth.register("prov", "prov@example.com", "secret123", RoleEnum.PROVIDER)
    service_service = ServiceService(session)
    service = service_service.create_service(provider, provider.id, "Hair Cut", "desc", "Beauty", 60, 100.0)
    assert service.id is not None

    schedule = ScheduleService(session)
    start = datetime(2026, 1, 1, 10, 0)
    end = start + timedelta(minutes=60)
    slot = schedule.create_slot(provider, service.id, start, end)
    assert slot.id is not None
    assert slot.status == SlotStatusEnum.ACTIVE

def test_overlapping_slot_rejected(session):
    auth = AuthService(session)
    provider = auth.register("prov", "prov2@example.com", "secret123", RoleEnum.PROVIDER)
    service_service = ServiceService(session)
    service = service_service.create_service(provider, provider.id, "Massage", "desc", "Health", 30, 50.0)
    schedule = ScheduleService(session)
    start = datetime(2026, 1, 1, 10, 0)
    schedule.create_slot(provider, service.id, start, start + timedelta(minutes=30))
    with pytest.raises(Exception):
        schedule.create_slot(provider, service.id, start + timedelta(minutes=15), start + timedelta(minutes=45))
