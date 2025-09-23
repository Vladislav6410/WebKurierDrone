# Валидный пример MAVSDK: загрузка грид-миссии (без вымышленного drone.utm.*)
# Требуется: pip install mavsdk
import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from typing import List
from .mission_grid import Waypoint

async def upload_and_start(waypoints: List[Waypoint], speed_ms: float = 6.0):
    drone = System()
    await drone.connect(system_address="udp://:14540")

    async for state in drone.core.connection_state():
        if state.is_connected:
            break

    mission_items = []
    for wp in waypoints:
        mission_items.append(
            MissionItem(
                latitude_deg=wp.lat,
                longitude_deg=wp.lon,
                relative_altitude_m=wp.rel_alt,
                speed_m_s=speed_ms,
                is_fly_through=False,
                gimbal_pitch_deg=wp.gimbal_pitch,
                gimbal_yaw_deg=None,
                camera_action=MissionItem.CameraAction.TAKE_PHOTO if wp.take_photo else MissionItem.CameraAction.NONE,
                loiter_time_s=0,
                camera_photo_interval_s=0
            )
        )

    await drone.action.set_maximum_speed(speed_ms)
    await drone.mission.upload_mission(MissionPlan(mission_items))
    await drone.action.arm()
    await drone.mission.start_mission()

if __name__ == "__main__":
    # демо: маленький прямоугольник над Берлином (НЕ ЛЕТАТЬ БЕЗ РАЗРЕШЕНИЯ)
    from .mission_grid import generate_grid, GridParams
    bbox = (52.5205, 13.4040, 52.5210, 13.4060)
    wps = generate_grid(bbox, GridParams())
    asyncio.run(upload_and_start(wps, speed_ms=5.0))