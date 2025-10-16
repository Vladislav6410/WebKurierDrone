# WebKurierDrone

  <p align="center">
  <img src="docs/hero_webkurierdrone.jpg?raw=true" alt="WebKurierDrone" width="640">
</p>

# 🚁 WebKurierDrone
Интеллектуальная система управления автономными дронами...

## 🚀 WebKurierDrone v1.0

Интеллектуальная система управления автономными дронами для задач:

- 🛰 Геодезии и картографии  
- 📦 Доставки  
- 🔥 Пожарного и градиентного мониторинга  
- 🎙 Голосового управления  
- 💬 Интеграции с Telegram и WhatsApp  
- ⚙️ Подключения к ядру **WebKurierCore** и **WebKurierChain**

---

## 🔧 Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Vladislav6410/WebKurierDrone.git
cd WebKurierDrone

# 2. Собрать Docker-образ
docker build -t webkurier .

# 3. Запустить контейнер
docker run -p 5000:5000 webkurier
[![Tests](https://github.com/Vladislav6410/WebKurierDrone/actions/workflows/tests.yml/badge.svg)](https://github.com/Vladislav6410/WebKurierDrone/actions/workflows/tests.yml)
Интеллектуальная система управления автономными дронами для задач:

- Геодезии и картографии  
- Доставки  
- Пожарного и градиентного мониторинга  
- Голосового управления  
- Интеграции с Telegram и WhatsApp  
- Подключения к ядру WebKurierCore и WebKurierChain

## Лицензия

🔒 Некоторые компоненты проекта (ИИ, управление миссией, автопилот) не опубликованы в этом репозитории.  
Для получения полной версии — [запросите лицензию](mailto:webkurier@license.io) или обратитесь через Telegram: [@WebKurierBot](https://t.me/WebKurierBot)

├── README.md
├── .gitignore
├── requirements.txt
├── Dockerfile
├── LICENSE
├── config/
│   ├── settings.yaml
│   ├── telemetry_config.json
│   └── voice_commands.json
├── core/
│   ├── __init__.py
│   └── main.py
├── agents/
│   ├──Drone с учpy
│   ├── autopilot_ai/
│   │   ├── autopilot.py
│   │   └── index.html
│   ├── geodesy_agent/
│   │   └── geodesy.py
│   ├── fire_monitor/
│   │   └── detector.py
│   └── delivery_agent/
│       └── route_planner.py
├── bots/
│   ├── telegram_bot/
│   │   ├── bot.py
│   │   ├── handlers.py
│   │   └── lang/
│   │       ├── ru.json
│   │       ├── en.json
│   │       └── de.json
│   └── whatsapp_bot/
│       └── bot.py
├── radio_control/
│   └── mavlink_radio.py
├── voice_control/
│   └── recognizer.py
├── ui/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── utils/
│   ├── logger.py
│   └── telemetry_parser.py
├── docs/
│   ├── WebKurierDrone_Overview.pdf
│   ├── Architecture_Scheme.png
│   ├── Getting_Started.md
│   ├── Dev_Guide_Engineer.md
│   ├── Dev_Guide_Programmer.md
│   └── TechSpec.md
├── tests/
│   ├── test_core.py
│   ├── test_autopilot.py
│   └── test_bot.py
└── scripts/
    ├── start.sh
    └── deploy.sh# WebKurierDrone v1.0

Интеллектуальная система управления автономными дронами для задач:
- Геодезии и картографии
- Доставки
- Пожарного и градиентного мониторинга
- Голосового управления
- Интеграции с Telegram и WhatsApp

## Запуск
```bash
docker build -t webkurier .
docker run -p 5000:5000 webkurier

Структура

📁 core/ – ядро WebKurierCore
📁 agents/ – агенты дрона
📁 bots/ – Telegram и WhatsApp боты
📁 radio_control/ – связь через MAVLink
📁 voice_control/ – голосовое управление
📁 ui/ – интерфейс управления
📁 utils/ – логи, парсеры, инструменты
📁 docs/ – PDF и технические описания
📁 tests/ – юнит-тесты### 1. Клонируйте репозиторий
```
git clone https://github.com/your-org/webkurierdrone.git
cd webkurierdrone
```
```
