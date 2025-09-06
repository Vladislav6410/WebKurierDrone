# -*- coding: utf-8 -*-
"""
Тесты базовой логики полётного контроллера.
Используются мок-датчики из tests/mocks/hardware_mock.py
и реальный PID-контроллер из utils/pid.py
"""

import unittest
from tests.mocks.hardware_mock import MockGPS, MockIMU, MockBarometer, MockBattery, MockLink
from utils.pid import PID


class TestFlightController(unittest.TestCase):
    def setUp(self):
        # Инициализация мок-объектов перед каждым тестом
        self.gps = MockGPS()
        self.imu = MockIMU()
        self.baro = MockBarometer()
        self.batt = MockBattery()
        self.link = MockLink()

    def test_pid_controller(self):
        """
        Проверка, что PID уменьшает ошибку на простой модели 1-го порядка:
        x_{k+1} = x_k + alpha * u_k
        """
        pid = PID(
            kp=0.6, ki=0.2, kd=0.05,
            setpoint=10.0,
            output_limits=(-100, 100),
            integral_limits=(-50, 50)
        )

        x = 0.0     # текущее значение (например, высота)
        dt = 0.1
        alpha = 0.05  # коэффициент влияния управления

        initial_error = abs(pid.setpoint - x)

        for _ in range(100):  # моделируем 10 секунд
            u = pid.update(x, dt)
            x += alpha * u

        final_error = abs(pid.setpoint - x)

        # ошибка должна снизиться хотя бы на 70%
        self.assertLess(final_error, initial_error * 0.3)

    def test_sensor_data_validation(self):
        lat, lon, alt = self.gps.get_position()
        attitude = self.imu.get_attitude()
        baro = self.baro.read()
        batt = self.batt.status()

        self.assertIsInstance(lat, float)
        self.assertIn("roll", attitude)
        self.assertGreater(baro["pressure_hpa"], 800)
        self.assertGreater(batt["voltage_v"], 0)

    def test_emergency_landing(self):
        self.batt.voltage_v = 18.0  # просадка для 6S (~3.0В/ячейку)
        status = self.batt.status()
        command = "LAND" if status["voltage_v"] < 19.2 else "FLY"
        self.assertEqual(command, "LAND")

    def test_link_send_receive(self):
        msg_out = {"cmd": "status"}
        self.link.send(msg_out)
        self.link.inject({"resp": "ok"})
        msg_in = self.link.recv()

        self.assertEqual(self.link.sent[0]["cmd"], "status")
        self.assertEqual(msg_in["resp"], "ok")


if __name__ == "__main__":
    unittest.main()