"""
Frontend Adapters

Platform adapters for different chat/messaging platforms.
"""

from .base_adapter import BaseAdapter
from .telegram_adapter import TelegramAdapter

__all__ = [
    'BaseAdapter',
    'TelegramAdapter'
]
