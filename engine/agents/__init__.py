# compatibility shim: redirect 'agents' → 'engine.agents'
import sys, importlib
_real = importlib.import_module("engine.agents")
sys.modules[__name__] = _real  # теперь import agents == import engine.agents