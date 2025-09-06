# -*- coding: utf-8 -*-
"""
Юнит-тесты для engine/agents/autopilot_ai (FIXAR & benchmarks).
Запуск:
  python -m unittest tests.test_autopilot_specs
"""

import unittest

from engine.agents.autopilot_ai import (
    SPECS, get, best_by, all_models, FIELDS
)

class TestFixarSpecs(unittest.TestCase):
    def test_models_present(self):
        self.assertIn("FIXAR 007 NG", SPECS)
        self.assertIn("FIXAR 025", SPECS)
        self.assertIn("WingtraOne GEN II", SPECS)
        self.assertIn("Trinity F90+", SPECS)
        self.assertIn("DJI M300 RTK", SPECS)

    def test_fields_shape(self):
        # каждая запись должна содержать все ключи из FIELDS
        for name, spec in SPECS.items():
            for key in FIELDS:
                self.assertIn(key, spec, msg=f"'{key}' отсутствует в '{name}'")

    def test_payload_values(self):
        self.assertEqual(SPECS["FIXAR 007 NG"]["payload_kg"], 2.0)
        self.assertGreaterEqual(SPECS["FIXAR 025"]["payload_kg"], 10.0)

    def test_best_by_metrics(self):
        self.assertEqual(best_by("range_km", True)["name"], "FIXAR 025")
        self.assertIn(best_by("payload_kg", True)["name"], {"FIXAR 025", "DJI M300 RTK"})  # 10.0 vs 2.7
        self.assertEqual(best_by("endurance_min", True)["name"], "FIXAR 025")

    def test_get_helper(self):
        self.assertIsNotNone(get("Trinity F90+"))
        self.assertIsNone(get("NonExistingModel"))

    def test_all_models(self):
        models = set(all_models())
        self.assertTrue({"FIXAR 025", "DJI M300 RTK"}.issubset(models))

if __name__ == "__main__":
    unittest.main()