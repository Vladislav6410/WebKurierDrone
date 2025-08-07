"""
Планирование маршрута доставки.
"""
class RoutePlanner:
    def plan(self, from_point, to_point):
        print(f"Прокладка маршрута: {from_point} -> {to_point}")
        return {"route": [from_point, to_point]}
