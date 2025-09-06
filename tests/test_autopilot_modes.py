# -*- coding: utf-8 -*-
"""
Юнит-тесты режимов Autopilot (MANUAL/HOLD_ALT/CRUISE) и failsafe.
Зависит от: engine/agents/autopilot_ai/autopilot.py, utils/pid.py
"""

import unittest

from engine.agents.autopilot_ai.autopilot import (
    Autopilot,
    _simulate_step,  # внутренний симулятор для тестов
)


class TestAutopilotModes(unittest.TestCase):
    def test_manual_passthrough(self):
        ap = Autopilot()
        ap.set_mode("MANUAL")

        sensors = {"baro_alt_m": 10.0, "airspeed": 5.0}
        sys = {"dt": 0.1, "battery_v": 23.5, "link_ok": True}
        manual = {"thrust": 0.77, "pitch": -0.12, "roll": 0.25, "yaw": -0.33}

        out = ap.update(sensors, sys, manual_cmd=manual)
        self.assertFalse(out["failsafe"])
        self.assertEqual(out["mode"], "MANUAL")
        self.assertAlmostEqual(out["thrust"], manual["thrust"], places=5)
        self.assertAlmostEqual(out["pitch"], manual["pitch"], places=5)
        self.assertAlmostEqual(out["roll"], manual["roll"], places=5)
        self.assertAlmostEqual(out["yaw"], manual["yaw"], places=5)

    def test_hold_alt_converges(self):
        ap = Autopilot()
        target_alt = 50.0
        ap.set_mode("HOLD_ALT", target_alt_m=target_alt)

        dt = 0.1
        state = {"alt_m": 0.0, "airspeed": 0.0}
        for _ in range(250):  # 25 сек
            sensors = {"baro_alt_m": state["alt_m"], "airspeed": state["airspeed"]}
            sys = {"dt": dt, "battery_v": 23.5, "link_ok": True}
            cmd = ap.update(sensors, sys)
            state = _simulate_step(state, cmd, dt)

        self.assertFalse(cmd["failsafe"])
        self.assertEqual(cmd["mode"], "HOLD_ALT")
        self.assertLess(abs(state["alt_m"] - target_alt), 5.0)  # допуск 5 м

    def test_cruise_converges(self):
        ap = Autopilot()
        target_alt, target_ms = 40.0, 18.0
        ap.set_mode("CRUISE", target_alt_m=target_alt, target_airspeed_ms=target_ms)

        dt = 0.1
        state = {"alt_m": 0.0, "airspeed": 0.0}
        for _ in range(300):  # 30 сек
            sensors = {"baro_alt_m": state["alt_m"], "airspeed": state["airspeed"]}
            sys = {"dt": dt, "battery_v": 23.5, "link_ok": True}
            cmd = ap.update(sensors, sys)
            state = _simulate_step(state, cmd, dt)

        self.assertFalse(cmd["failsafe"])
        self.assertEqual(cmd["mode"], "CRUISE")
        self.assertLess(abs(state["alt_m"] - target_alt), 6.0)  # допуски
        self.assertLess(abs(state["airspeed"] - target_ms), 3.0)

    def test_failsafe_low_battery(self):
        ap = Autopilot()
        ap.set_mode("HOLD_ALT", target_alt_m=20.0)

        sensors = {"baro_alt_m": 10.0, "airspeed": 0.0}
        sys = {"dt": 0.1, "battery_v": 18.0, "link_ok": True}  # ниже порога
        out = ap.update(sensors, sys)

        self.assertTrue(out["failsafe"])
        self.assertEqual(out["failsafe_reason"], "LOW_BATTERY")
        self.assertAlmostEqual(out["thrust"], 0.3, places=3)

    def test_failsafe_link_loss(self):
        ap = Autopilot()
        ap.set_mode("HOLD_ALT", target_alt_m=20.0)

        dt = 0.1
        sensors = {"baro_alt_m": 10.0, "airspeed": 0.0}
        # несколько шагов подряд без связи, чтобы превысить таймаут
        out = None
        for _ in range(30):  # 3 сек > 2.0s timeout
            sys = {"dt": dt, "battery_v": 23.0, "link_ok": False}
            out = ap.update(sensors, sys)

        self.assertIsNotNone(out)
        self.assertTrue(out["failsafe"])
        self.assertEqual(out["failsafe_reason"], "LINK_LOSS")

    def test_failsafe_baro_fault(self):
        ap = Autopilot()
        ap.set_mode("HOLD_ALT", target_alt_m=20.0)

        # baro_alt_m отсутствует/невалиден
        sensors = {"airspeed": 0.0}
        sys = {"dt": 0.1, "battery_v": 23.0, "link_ok": True}
        out = ap.update(sensors, sys)

        self.assertTrue(out["failsafe"])
        self.assertEqual(out["failsafe_reason"], "BARO_FAULT")


if __name__ == "__main__":
    unittest.main()