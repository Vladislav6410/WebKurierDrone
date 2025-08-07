"""
Пожарный мониторинг и обнаружение очагов.
"""
class FireMonitor:
    def scan_area(self, coordinates):
        print(f"Мониторинг пожароопасности в точках: {coordinates}")
        return {"coordinates": coordinates, "fire_detected": False}
