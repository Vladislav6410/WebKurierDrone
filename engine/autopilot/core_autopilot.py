from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # WebKurierDrone/

def load_autopilot_config():
    cfg_path = PROJECT_ROOT / "config" / "autopilot.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class CoreAutopilot:
    def __init__(self):
        self.config = load_autopilot_config()
        # дальше передаём части конфига в подмодули:
        # self.motor_matrix = MotorMatrix(self.config["motor_system"])