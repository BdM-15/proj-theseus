"""
Core module for GovCon Capture Vibe.

Provides centralized configuration and shared utilities.
"""

from src.core.config import get_settings, reset_settings, Settings

__all__ = ["get_settings", "reset_settings", "Settings"]
