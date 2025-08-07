"""
Класс базового Агент-Дрона.
"""
class Drone:
    def __init__(self, drone_id, model):
        self.id = drone_id
        self.model = model

    def get_status(self):
        return {"id": self.id, "model": self.model, "status": "ready"}

    def execute_mission(self, mission):
        print(f"Дрон {self.id} выполняет миссию: {mission}")
