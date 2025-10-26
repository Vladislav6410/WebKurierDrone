import sys, importlib
_mod = importlib.import_module("engine.agents.geodesy_agent")
globals().update(_mod.__dict__)
sys.modules[__name__] = _mod