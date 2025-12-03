import asyncio
from datetime import datetime, timezone
import httpx

CORE_API_BASE = "http://127.0.0.1:8081"  # адрес Core-API изнутри сервера
HEARTBEAT_INTERVAL_SEC = 15  # как часто слать heartbeat


async def send_heartbeat_loop():
    while True:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                payload = {
                    "service": "webkurier-telemetry",
                    "status": "ok",
                    "details": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        # сюда можно добавить метрики: fps, queue_size, errors и т.п.
                    },
                }
                await client.post(
                    f"{CORE_API_BASE}/api/telemetry/heartbeat",
                    json=payload,
                )
        except Exception as e:
            # можно залогировать локально
            print(f"[heartbeat] failed: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)


async def run_telemetry_main():
    """
    Твой основной цикл телеметрии:
    чтение датчиков, упаковка пакетов, отправка и т.п.
    """
    while True:
        # TODO: твоя логика телеметрии
        await asyncio.sleep(1.0)


async def main():
    # Запускаем два параллельных таска:
    # 1) собственно телеметрия
    # 2) фоновый heartbeat в Core-API
    telemetry_task = asyncio.create_task(run_telemetry_main())
    heartbeat_task = asyncio.create_task(send_heartbeat_loop())

    await asyncio.gather(telemetry_task, heartbeat_task)


if __name__ == "__main__":
    asyncio.run(main())