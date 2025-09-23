from flask import Flask, jsonify, request
import os, asyncio
from mavsdk import System

app = Flask(__name__)

# где искать MAVSDK (контейнер autopilot)
AUTOPILOT_GRPC = os.getenv("AUTOPILOT_GRPC", "autopilot:50051")


@app.get("/health")
def health():
    """Проверка, что web работает и видит autopilot"""
    return jsonify(ok=True, service="webkurier-web", autopilot_grpc=AUTOPILOT_GRPC)


# ===== Вспомогательная функция для асинхронных вызовов =====
def _sync(coro):
    try:
        result = asyncio.run(coro)
        return jsonify(result)
    except Exception as e:
        return jsonify(error=str(e)), 500


# ===== Эндпоинты управления дроном =====

@app.post("/api/arm")
def api_arm():
    """Включить дрон"""
    return _sync(async_arm())


async def async_arm():
    drone = System(mavsdk_server_address=AUTOPILOT_GRPC.split(":")[0],
                   port=int(AUTOPILOT_GRPC.split(":")[1]))
    await drone.connect()
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    await drone.action.arm()
    return {"status": "armed"}


@app.post("/api/takeoff")
def api_takeoff():
    """Взлететь на заданную высоту"""
    alt = float(request.json.get("alt", 10))
    return _sync(async_takeoff(alt))


async def async_takeoff(alt_m: float):
    drone = System(mavsdk_server_address=AUTOPILOT_GRPC.split(":")[0],
                   port=int(AUTOPILOT_GRPC.split(":")[1]))
    await drone.connect()
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(5)
    return {"status": "airborne", "target_alt": alt_m}


@app.post("/api/land")
def api_land():
    """Посадить дрон"""
    return _sync(async_land())


async def async_land():
    drone = System(mavsdk_server_address=AUTOPILOT_GRPC.split(":")[0],
                   port=int(AUTOPILOT_GRPC.split(":")[1]))
    await drone.connect()
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    await drone.action.land()
    return {"status": "landing"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)