"""
Frontend Configuration Module for ContractRisk AI.
Provides API endpoints configuration, branding tokens, and visual styling constants
aligned with the Premium Dark Legal-Tech Dashboard Theme.
"""

import os
from pathlib import Path

# FastAPI Backend URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")

# Design Tokens & Color System (Premium Dark Theme)
COLOR_BACKGROUND = "#0B1020"     # Main background
COLOR_SIDEBAR = "#111827"        # Sidebar / background panels
COLOR_SURFACE = "#182235"        # Cards
COLOR_ELEVATED = "#202D42"       # Elevated cards
COLOR_PRIMARY = "#8B5CF6"        # Primary accent (purple/violet)
COLOR_PRIMARY_HOVER = "#7C3AED"  # Deeper purple hover
COLOR_TEXT_PRIMARY = "#F8FAFC"   # Primary text
COLOR_TEXT_SECONDARY = "#A1AFC2" # Secondary text
COLOR_BORDER = "#2D3A50"         # Borders

# Semantic Risk Colors
COLOR_NORMAL_RISK = "#10B981"    # Green
COLOR_LOW_RISK = "#3B82F6"       # Blue
COLOR_MEDIUM_RISK = "#F59E0B"    # Amber
COLOR_HIGH_RISK = "#EF4444"      # Red

RISK_LEVEL_COLORS = {
    "NORMAL": COLOR_NORMAL_RISK,
    "LOW": COLOR_LOW_RISK,
    "MEDIUM": COLOR_MEDIUM_RISK,
    "HIGH": COLOR_HIGH_RISK,
}

# Configurable Low-Confidence Threshold
CONFIDENCE_THRESHOLD = float(os.getenv("BERT_CONFIDENCE_THRESHOLD", "0.45"))
