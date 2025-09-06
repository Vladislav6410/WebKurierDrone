# -*- coding: utf-8 -*-
"""
Тесты базовой логики полётного контроллера.
Используются мок-датчики из tests/mocks/hardware_mock.py
"""

import unittest
from tests.mocks.hardware_mock import MockGPS, MockIMU, MockBarometer, MockBattery, MockLink


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
        Заготовка для теста PID-регулятора.
        Здесь можно будет подставлять ошибку (setpoint - current)
        и проверять корректность управляющего сигнала.
        """
        error = 5.0
        # TODO: подключить реальный PID-алгоритм
        control_output = error * 0.1  # условный коэффициент
        self.assertAlmostEqual(control_output, 0.5)

    def test_sensor_data_validation(self):
        """
        Проверка целостности данных с датчиков.
        """
        lat, lon, alt = self.gps.get_position()
        attitude = self.imu.get_attitude()
        baro = self.baro.read()
        batt = self.batt.status()

        self.assertIsInstance(lat, float)
        self.assertIn("roll", attitude)
        self.assertGreater(baro["pressure_hpa"], 800)
        self.assertGreater(batt["voltage_v"], 0)

    def test_emergency_landing(self):
        """
        Заготовка для теста аварийной посадки.
        Критерий: низкий заряд батареи → команда "LAND".
        """
        self.batt.voltage_v = 18.0  # просадка для 6S (≈3.0В/ячейку)
        status = self.batt.status()
        command = "LAND" if status["voltage_v"] < 19.2 else "FLY"
        self.assertEqual(command, "LAND")

    def test_link_send_receive(self):
        """
        Проверка работы канала связи MockLink.
        """
        msg_out = {"cmd": "status"}
        self.link.send(msg_out)
        self.link.inject({"resp": "ok"})
        msg_in = self.link.recv()

        self.assertEqual(self.link.sent[0]["cmd"], "status")
        self.assertEqual(msg_in["resp"], "ok")


if __name__ == "__main__":
    unittest.main()