from __future__ import annotations
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'service_booking.db').as_posix()}"

DEFAULT_PROFILE_IMAGE = "assets/default_profile.png"
DEFAULT_SERVICE_IMAGE = "assets/default_service.png"

CURRENCY_LABEL = "IRR"
CANCEL_WINDOW_HOURS = 2

PDF_OUTPUT_DIR = BASE_DIR / "reports"
PDF_OUTPUT_DIR.mkdir(exist_ok=True)
