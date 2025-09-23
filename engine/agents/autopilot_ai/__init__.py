"""
Фасад к реальному модулю в корне: agents/autopilot_ai
Импортируй всегда так:
    from engine.agents.autopilot_ai import generate_grid, upload_and_start
"""
from agents.autopilot_ai.mavsdk_mission import upload_and_start
from agents.autopilot_ai.mission_grid import GridParams, Waypoint, generate_grid
from agents.autopilot_ai.utm_adapter import USpaceAdapter
from agents.autopilot_ai.hyperspectral_ndvi import compute_ndvi

__all__ = [
    "upload_and_start",
    "GridParams", "Waypoint", "generate_grid",
    "USpaceAdapter",
    "compute_ndvi",
]