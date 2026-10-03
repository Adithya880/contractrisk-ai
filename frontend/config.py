"""
Frontend Configuration Module for ContractRisk AI.
Provides API endpoints configuration, branding tokens, and visual styling constants.
"""

import os
from pathlib import Path

# FastAPI Backend URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")

# Design Tokens & Color System
COLOR_LOW_RISK = "#10B981"      # Calm Emerald Green
COLOR_MEDIUM_RISK = "#F59E0B"   # Cautionary Amber
COLOR_HIGH_RISK = "#EF4444"     # Urgent Crimson Red
COLOR_PRIMARY = "#2563EB"       # Deep Sapphire Blue
COLOR_BACKGROUND = "#0F172A"    # Dark Slate Background
COLOR_SURFACE = "#1E293B"       # Elevated Surface Slate

RISK_LEVEL_COLORS = {
    "LOW": COLOR_LOW_RISK,
    "MEDIUM": COLOR_MEDIUM_RISK,
    "HIGH": COLOR_HIGH_RISK,
}

RISK_LEVEL_BADGES = {
    "LOW": "🟢 LOW RISK",
    "MEDIUM": "🟡 MEDIUM RISK",
    "HIGH": "🔴 HIGH RISK",
}
