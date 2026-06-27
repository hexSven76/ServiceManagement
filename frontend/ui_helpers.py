from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st


UPLOAD_ROOT = Path("assets/uploads")


def enum_to_text(value: Any, default: str = "-") -> str:
    """
    Convert enum/string/None into clean frontend text.
    """
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    text = str(value).split(".")[-1].strip()

    if not text:
        return default

    return text.upper()


def format_datetime(value: Any, default: str = "-") -> str:
    """
    Format datetime values consistently for tables/cards.
    """
    if value is None:
        return default

    if isinstance(value, str):
        return value

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value)


def format_date(value: Any, default: str = "-") -> str:
    if value is None:
        return default

    if isinstance(value, str):
        return value

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    return str(value)


def format_price_irr(value: Any, default: str = "-") -> str:
    """
    Format prices as IRR without crashing on bad values.
    """
    if value is None:
        return default

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return default

    return f"{amount:,.0f} IRR"


def format_duration_minutes(value: Any, default: str = "-") -> str:
    if value is None:
        return default

    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return default

    if minutes < 60:
        return f"{minutes} min"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} h"

    return f"{hours} h {remaining_minutes} min"


def render_status_badge(status: Any):
    """
    Display common status values using consistent Streamlit badges.
    """
    text = enum_to_text(status)

    success_statuses = {
        "ACTIVE",
        "CONFIRMED",
        "APPROVED",
        "PAID",
        "COMPLETED",
    }

    warning_statuses = {
        "PENDING",
        "UNPAID",
        "INACTIVE",
    }

    error_statuses = {
        "REJECTED",
        "CANCELED",
        "CANCELLED",
        "FAILED",
        "EXPIRED",
    }

    if text in success_statuses:
        st.success(text)
    elif text in warning_statuses:
        st.warning(text)
    elif text in error_statuses:
        st.error(text)
    else:
        st.info(text)


def status_to_table_text(status: Any) -> str:
    return enum_to_text(status)


def render_empty_state(message: str, help_text: str | None = None):
    """
    Standard empty-state message for pages with no data.
    """
    st.info(message)

    if help_text:
        st.caption(help_text)


def show_action_error(error: Exception, debug: bool = False):
    """
    Show backend/user-facing errors cleanly.

    Use debug=True temporarily only while developing.
    """
    message = str(error).strip() or "Something went wrong."

    st.error(message)

    if debug:
        st.exception(error)


def safe_uploaded_filename(original_name: str) -> str:
    """
    Generate a safe unique filename while keeping the original extension.
    """
    suffix = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def validate_uploaded_image(uploaded_file, max_size_mb: int = 5) -> tuple[bool, str]:
    """
    Validate image uploads.
    """
    if uploaded_file is None:
        return True, ""

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix not in allowed_extensions:
        return False, "Only JPG, JPEG, PNG, and WEBP images are allowed."

    max_size_bytes = max_size_mb * 1024 * 1024

    if uploaded_file.size > max_size_bytes:
        return False, f"Image size must be under {max_size_mb} MB."

    return True, ""


def save_uploaded_file(
    uploaded_file,
    subfolder: str,
    max_size_mb: int = 5,
) -> str | None:
    """
    Save uploaded file under assets/uploads/<subfolder>/.

    Returns a relative path string suitable for storing in DB.
    """
    if uploaded_file is None:
        return None

    is_valid, error_message = validate_uploaded_image(
        uploaded_file=uploaded_file,
        max_size_mb=max_size_mb,
    )

    if not is_valid:
        raise ValueError(error_message)

    upload_dir = UPLOAD_ROOT / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_uploaded_filename(uploaded_file.name)
    file_path = upload_dir / filename

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(file_path).replace(os.sep, "/")


def get_display_image_path(
    image_path: str | None,
    default_path: str,
) -> str:
    """
    Return uploaded image path when available, otherwise a default path.
    """
    if image_path:
        return image_path

    return default_path