# -*- coding: utf-8 -*-
"""
MAVLink-адаптер для Autopilot:
- Преобразует команды Autopilot.update(...) (thrust 0..1, pitch/roll/yaw -1..1) в PWM/SET_ATTITUDE_TARGET.
- Может работать в dry-run режиме (без реального модема).
Зависимости: pymavlink (см. requirements.txt).
"""

from typing import Dict, Optional

try:
    from pymavlink import mavutil
except Exception:  # если pymavlink недоступен
    mavutil = None


def _scale_unit_to_pwm(u: float, lo: int = 1000, hi: int = 2000) -> int:
    """u in [0..1] -> PWM [1000..2000]."""
    u = max(0.0, min(1.0, float(u)))
    return int(lo + (hi - lo) * u)


def _scale_bipolar_to_pwm(x: float, lo: int = 1000, hi: int = 2000) -> int:
    """x in [-1..1] -> PWM [1000..2000], 0 -> 1500."""
    x = max(-1.0, min(1.0, float(x)))
    mid = (lo + hi) // 2
    span = (hi - lo) // 2
    return int(mid + span * x)


class MavlinkRadio:
    """
    Упрощённый MAVLink-линк:
      - UDP/Serial подключение
      - Heartbeat, arm/disarm
      - Отправка RC_OVERRIDE (для тестов) и скелет SET_ATTITUDE_TARGET
    """

    def __init__(self, conn_str: str = "udpout:127.0.0.1:14550", baud: int = 57600, dry_run: bool = False):
        self.conn_str = conn_str
        self.baud = baud
        self.dry_run = dry_run or (mavutil is None)
        self._mav: Optional["mavutil.mavlink_connection"] = None

    # --- lifecycle ---
    def connect(self) -> None:
        if self.dry_run:
            print(f"[MAVLINK] DRY-RUN. No physical connection: {self.conn_str}")
            return
        if self.conn_str.startswith(("udp:", "udpout:", "udpin:", "tcp:", "tcpout:", "tcpin:")):
            self._mav = mavutil.mavlink_connection(self.conn_str)
        else:
            self._mav = mavutil.mavlink_connection(self.conn_str, baud=self.baud)
        print(f"[MAVLINK] Connected: {self.conn_str}")

    def wait_heartbeat(self, timeout: int = 10) -> None:
        if self.dry_run or not self._mav:
            print("[MAVLINK] DRY heartbeat ok")
            return
        self._mav.wait_heartbeat(timeout=timeout)
        print(f"[MAVLINK] Heartbeat (sysid={self._mav.target_system}, compid={self._mav.target_component})")

    def arm(self) -> None:
        if self.dry_run or not self._mav:
            print("[MAVLINK] DRY arm")
            return
        self._mav.arducopter_arm()
        self._mav.motors_armed_wait()
        print("[MAVLINK] ARMED")

    def disarm(self) -> None:
        if self.dry_run or not self._mav:
            print("[MAVLINK] DRY disarm")
            return
        self._mav.arducopter_disarm()
        self._mav.motors_disarmed_wait()
        print("[MAVLINK] DISARMED")

    # --- commands ---
    def send_rc_override(self, thrust_u: float, pitch_x: float, roll_x: float, yaw_x: float) -> None:
        """
        RC_OVERRIDE каналов (MODE2):
          CH3: THR (0..1) → PWM
          CH2: ELE (pitch -1..1) → PWM
          CH1: AIL (roll  -1..1) → PWM
          CH4: RUD (yaw   -1..1) → PWM
        """
        ch1 = _scale_bipolar_to_pwm(roll_x)     # AIL
        ch2 = _scale_bipolar_to_pwm(pitch_x)    # ELE
        ch3 = _scale_unit_to_pwm(thrust_u)      # THR
        ch4 = _scale_bipolar_to_pwm(yaw_x)      # RUD

        if self.dry_run or not self._mav:
            print(f"[MAVLINK] RC_OVERRIDE: AIL={ch1}, ELE={ch2}, THR={ch3}, RUD={ch4}")
            return

        self._mav.mav.rc_channels_override_send(
            self._mav.target_system,
            self._mav.target_component,
            ch1, ch2, ch3, ch4, 0, 0, 0, 0
        )

    def send_attitude_target(self, pitch_x: float, roll_x: float, yaw_rate: float = 0.0, thrust_u: float = 0.5) -> None:
        """
        Заготовка для SET_ATTITUDE_TARGET.
        TODO: добавить кватернион из pitch/roll/yaw для полного MAVLink-управления.
        """
        if self.dry_run or not self._mav:
            print(f"[MAVLINK] SET_ATTITUDE_TARGET pitch={pitch_x:.2f}, roll={roll_x:.2f}, yaw_rate={yaw_rate:.2f}, thrust={thrust_u:.2f}")
            return
        # Здесь можно добавить mavlink_msg_set_attitude_target_send(...)

    # --- high-level bridge ---
    def apply_autopilot_cmd(self, cmd: Dict[str, float]) -> None:
        """
        Принимает словарь из Autopilot.update(...):
          {"thrust":0..1, "pitch":-1..1, "roll":-1..1, "yaw":-1..1, "failsafe":bool, ...}
        и мапит в RC_OVERRIDE.
        """
        thrust = float(cmd.get("thrust", 0.0))
        pitch = float(cmd.get("pitch", 0.0))
        roll = float(cmd.get("roll", 0.0))
        yaw = float(cmd.get("yaw", 0.0))

        if cmd.get("failsafe", False):
            thrust = min(thrust, 0.3)
            pitch, roll, yaw = 0.1, 0.0, 0.0

        self.send_rc_override(thrust_u=thrust, pitch_x=pitch, roll_x=roll, yaw_x=yaw)
