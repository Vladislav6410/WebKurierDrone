# -*- coding: utf-8 -*-
"""
Autopilot AI — пакет агрегатор.

Реэкспорт удобных сущностей для использования:
    from engine.agents.autopilot_ai import SPECS, print_table, best_by
"""

from .fixar_specs import (
    SPECS,
    FIELDS,
    get,
    all_models,
    to_rows,
    to_csv,
    print_table,
    best_by,
)

__all__ = [
    "SPECS",
    "FIELDS",
    "get",
    "all_models",
    "to_rows",
    "to_csv",
    "print_table",
    "best_by",
]

__version__ = "1.0.0"