# -*- coding: utf-8 -*-
"""
Mock-аппаратура для юнит-тестов автопилота/полётов.
Используется в тестах (например, tests/test_flight_controller.py).
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class MockGPS:
    lat: float = 55.7558   # Москва
    lon: float = 37.6176
    alt: float = 200.0

    def get_position(self) -> Tuple[float, float, float]:
        """Возвращает кортеж (lat, lon, alt)."""
        return (self.lat, self.lon, self.alt)


@dataclass
class MockIMU:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def get_attitude(self) -> Dict[str, float]:
        """Текущее пространственное положение."""
        return {"roll": self.roll, "pitch": self.pitch, "yaw": self.yaw}


@dataclass
class MockBarometer:
    pressure_hpa: float = 1013.25
    temp_c: float = 20.0

    def read(self) -> Dict[str, float]:
        return {"pressure_hpa": self.pressure_hpa, "temp_c": self.temp_c}


@dataclass
class MockBattery:
    voltage_v: float = 23.1   # для 6S ~ 3.85В/ячейку
    current_a: float = 8.5
    capacity_mah: int = 10000

    def status(self) -> Dict[str, float]:
        return {
            "voltage_v": self.voltage_v,
            "current_a": self.current_a,
            "capacity_mah": self.capacity_mah,
        }


class MockLink:
    """Эмуляция телеметрической связи (канал/модем)."""

    def __init__(self):
        self.sent = []
        self.received = []

    def send(self, msg: Dict) -> None:
        self.sent.append(msg)

    def recv(self) -> Dict:
        return self.received.pop(0) if self.received else {}

    def inject(self, msg: Dict) -> None:
        """Инжект входящего сообщения в очередь приёма (для тестов)."""
        self.received.append(msg)