"""Lightweight schema module kept for project compatibility."""
from pydantic import BaseModel


class Message(BaseModel):
    message: str
