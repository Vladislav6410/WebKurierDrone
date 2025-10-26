# -*- coding: utf-8 -*-
"""
Гибрид: переключение между миссией проекта (basic) и высшим пилотажем (aerobatics).
"""
from typing import Dict, Any, Optional
from .autopilot_basic import Autopilot as BasicAP, check_mission_zones
from .autopilot_aerobatics import AerobaticsAutopilot as AeroAP

class HybridAutopilot:
    def __init__(self):
        self.basic = BasicAP()
        self.aero = AeroAP()
        self.use_aero: bool = False

    def switch(self, aerobatics: bool):
        self.use_aero = bool(aerobatics)

    def set_mode(self, *args, **kwargs):
        (self.aero if self.use_aero else self.basic).set_mode(*args, **kwargs)

    def set_targets(self, *args, **kwargs):
        (self.aero if self.use_aero else self.basic).set_targets(*args, **kwargs)

    def set_home(self, *args, **kwargs):
        self.basic.set_home(*args, **kwargs); self.aero.set_home(*args, **kwargs)

    def set_geofence(self, *args, **kwargs):
        self.basic.set_geofence(*args, **kwargs); self.aero.set_geofence(*args, **kwargs)

    def update(self, sensors: Dict[str,Any], sys: Dict[str,Any], manual_cmd: Optional[Dict[str,float]]=None):
        ap = self.aero if self.use_aero else self.basic
        return ap.update(sensors, sys, manual_cmd)

    # проверка зон — на этапе планирования миссии (для basic)
    @staticmethod
    def ensure_mission_safe(poly_coords_latlon, zone_files):
        check_mission_zones(poly_coords_latlon, zone_files)