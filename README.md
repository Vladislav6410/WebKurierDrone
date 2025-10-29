<p align="center">
  <img src="docs/banner_drone_ai.svg?v=2" width="880" alt="WebKurierDrone Banner" style="border-radius:12px;box-shadow:0 0 25px rgba(0,255,255,0.15);"/>
</p>

<h1 align="center">🚁 WebKurierDrone v1.2 — Геодезия • 3D-моделирование • AI</h1>

<p align="center">
  <b>Интеллектуальная система автономного управления дронами нового поколения</b><br>
  <sub>Core • Drone • Chain • Bot — единая экосистема WebKurier</sub>
</p>
 **WebKurierDrone v1.1 — Геодезия, 3D-моделирование и AI**

Интеллектуальная система управления автономными дронами для:
- 🌍 Геодезии, картографии, аэрофотосъёмки
- 📦 Доставки и мониторинга
- 🔥 Пожарного и экологического анализа
- 🗣 Голосового управления
- 💬 Интеграции с Telegram / WhatsApp
- 🤖 AI-модулей для 3D и гиперспектрального анализа

---

## ⚙️ Архитектура проекта

WebKurierDrone/
├── core/                 # Ядро системы
├── agents/
│   ├── autopilot_ai/     # Автопилот и ИИ
│   ├── geodesy_agent/    # Геодезия и фотограмметрия
│   ├── synthetic_data/   # Генерация синтетических данных (Stable Diffusion)
│   └── fire_monitor/     # Мониторинг пожаров
├── bots/
│   ├── telegram_bot/     # Telegram бот
│   └── whatsapp_bot/     # WhatsApp бот
├── radio_control/        # MAVLink управление
├── config/               # Конфигурации сенсоров и зон
├── ui/                   # Веб-интерфейс
├── utils/                # Логи, парсеры, инструменты
├── scripts/helm/         # Kubernetes Helm Chart
└── tests/                # Тесты агентов и ботов

---

## 🧩 Основные функции

| Модуль | Назначение | Технологии |
|--------|-------------|------------|
| `geodesy_agent` | Геодезия, гиперспектральная обработка | GDAL, Spectral |
| `synthetic_data` | Диффузионные модели местности | Stable Diffusion |
| `autopilot_ai` | Автономный полёт, MAVLink | Python, PX4/ArduPilot |
| `bots/telegram_bot` | Управление миссиями | Telegram API |
| `scripts/helm/` | Масштабирование | Kubernetes, Kafka |

---

## 🛰 Поддерживаемые сенсоры

📄 `config/telemetry_config.json`
```json
{
  "sensors": {
    "hyperspectral": {
      "type": "Headwall_Nano",
      "bands": 270,
      "format": "ENVI"
    },
    "rtk_gnss": {
      "type": "Emlid_Reach_RX",
      "accuracy_cm": 0.006
    }
  }
}


⸻

🧠 AI и 3D-моделирование

Геодезия и фотограмметрия

📄 agents/geodesy_agent/geodesy.py

from subprocess import run

def process_photogrammetry(images_dir, output_dir):
    run(["odm", "--project-path", output_dir, images_dir])
    return f"{output_dir}/odm_orthophoto/odm_orthophoto.tif"

Гиперспектральная обработка

import spectral as sp, numpy as np, gdal

def process_hyperspectral(path):
    img = sp.open_image(path)
    data = img.load()
    mineral_map = np.argmax(data[:, :, 10:50], axis=2)
    driver = gdal.GetDriverByName("GTiff")
    out = driver.Create("mineral_map.tiff", mineral_map.shape[1], mineral_map.shape[0], 1, gdal.GDT_Float32)
    out.GetRasterBand(1).WriteArray(mineral_map)
    out.FlushCache()
    return "mineral_map.tiff"


⸻

🌄 Пример миссии (Photogrammetry)

📄 exchange/missions_in/mission_photogrammetry.json

{
  "schema_version": "1.0",
  "id": "msn-001",
  "type": "photogrammetry_scan",
  "params": {
    "alt_m": 80,
    "speed_mps": 10,
    "overlap_percent": 80,
    "sidelap_percent": 70
  },
  "waypoints": [
    {"lat": 52.52, "lon": 13.40, "alt": 80}
  ],
  "geofence": {
    "type": "Polygon",
    "coordinates": [[[13.4, 52.5], [13.5, 52.5], [13.5, 52.6], [13.4, 52.6], [13.4, 52.5]]]
  }
}


⸻

☁️ Масштабируемость (Kubernetes)

📄 scripts/helm/webkurier-drone/Chart.yaml

apiVersion: v2
name: webkurier-drone
version: 1.0.0
dependencies:
  - name: kafka
    version: 0.1.0

📄 scripts/helm/webkurier-drone/templates/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: webkurier-drone
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: photogrammetry
          image: webkurier/drone-odm:latest
          command: ["python", "agents/geodesy_agent/geodesy.py"]

Развертывание:

helm install webkurier ./scripts/helm/webkurier-drone


⸻

🔗 Интеграция с Telegram

📄 bots/telegram_bot/handlers.py

async def upload_mission(update, context):
    mission = await update.message.document.get_file()
    await mission.download_to_drive("exchange/missions_in/mission.json")
    await update.message.reply_text("✅ Миссия загружена / Mission uploaded")


⸻

🧪 Тестирование

📄 tests/test_geodesy.py

def test_hyperspectral_processing():
    from agents.geodesy_agent.geodesy import process_hyperspectral
    result = process_hyperspectral("test_data/sample.hdr")
    assert result.endswith(".tiff")


⸻

📋 Требования / Requirements

Компонент	Версия
Python	3.11
torch	≥ 2.0.1
diffusers	≥ 0.21.0
transformers	≥ 4.31.0
spectral	≥ 0.23
gdal	≥ 3.6
Docker	≥ 24
Kubernetes (опционально)	≥ 1.30


⸻

🧾 Лицензия

Проект распространяется под лицензией MIT.
Некоторые компоненты (AI, фотограмметрия, автопилот) доступны по запросу лицензии:
📩 webkurier@license.io или через Telegram @WebKurierBot

⸻

🛰 Автор и поддержка

WebKurier DroneAI Team
📅 Версия: v1.1 • Обновлено: 2025-10-26

⸻

🚀 Совместимость:
WebKurierCore • WebKurierChain • WebKurierSecurity • TelegramBot • Dropbox

