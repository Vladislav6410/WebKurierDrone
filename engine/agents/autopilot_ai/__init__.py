# shim: agents.autopilot_ai → engine.agents.autopilot_ai
import sys, importlib
_mod = importlib.import_module("engine.agents.autopilot_ai")
globals().update(_mod.__dict__)
sys.modules[__name__] = _mod