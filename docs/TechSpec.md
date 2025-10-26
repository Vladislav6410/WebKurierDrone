# Технические характеристики

## Compatibility & Core
- Совместимость: Python 3.9+, Linux/Mac/Win, Docker 20+
- Коммуникация: MAVLink, TCP/UDP, Web Interface
- Поддержка голосовых языков: ru, en, de, pl
- Поддержка управления через: Telegram, WhatsApp, голос
- Интеграция: REST API + WebSocket для внешних модулей
- Мониторинг: системный лог, телеметрия, уведомления по webhook

## Accuracy (Mapping, RTK/PPK + GCP)
- Плановая точность (RGB photogrammetry, 80/70 overlap, RTK Fix + 6–10 GCP):
  - Horizontal (XY): 2–3 cm
  - Vertical (Z): 4–5 cm
- Заявления вроде "<0.01 cm" не используются — физически некорректно для практических сценариев
- GNSS поддержка: GPS, GLONASS, Galileo, BeiDou
- Коррекция данных: RTK real-time или PPK post-process, выбор автоматически
- Поддержка экспорта точек привязки в форматы CSV, GeoTIFF, LAS

## Compliance
- Проверка UAS Geographical Zones локально (GeoJSON/GeoPackage)
- Remote ID — включаем для классов C1+ (по стране)
- Страхование: min €1M (уточняется по юрисдикции и типу операций)
- Соответствие требованиям EASA и §21h LuftVO (для операций в Германии)
- Журнал полетных миссий ведётся локально и безопасно шифруется (AES-256)

## Security & Data Policy
- Шифрование всех журналов и миссий: AES-256 при хранении, TLS 1.3 при передаче
- Хранение данных локально с возможностью облачного зеркалирования (опционально)
- Контроль доступа токенами (JWT) и ротация ключей каждые 72 часа
- Автоматическое создание резервных копий с CRC-проверкой целостности
- Серверная аутентификация на основе сертификатов X.509
- Соблюдение норм GDPR/DSGVO: данные пользователей не передаются третьим лицам
- Функция безопасного удаления (crypto-shred) по запросу оператора

## System Integration Schema

| Модуль | Протокол/Технология | Функция | Связь с другими модулями |
|--------|---------------------|---------|--------------------------|
| **Flight Controller** | MAVLink (TCP/UDP) | Управление БПЛА, телеметрия | → RTK Module, Mission Planner, Safety Monitor |
| **RTK/PPK Module** | RTCM3, UBX | Коррекция GNSS | → Flight Controller, Data Logger |
| **Voice Interface** | Speech-to-Text (ru/en/de/pl) | Голосовые команды | → Command Parser, Telegram/WhatsApp Bot |
| **Telegram/WhatsApp Bot** | Bot API, WebSocket | Удалённое управление | → Mission Planner, Status Monitor |
| **REST API** | HTTPS/TLS 1.3, JWT | Внешняя интеграция | → все модули (unified access) |
| **Data Logger** | AES-256, CRC32 | Журнал миссий, backup | → Cloud Mirror (optional), Crypto-Shred |
| **Geo-Zone Checker** | GeoJSON/GeoPackage | Проверка запретных зон | → Mission Planner, Safety Monitor |
| **Web Interface** | WebSocket, HTTPS | Визуализация, контроль | → Flight Controller, Mission Planner, Telemetry |
| **Safety Monitor** | Event-driven | Аварийные протоколы | → Flight Controller, Notification System |
| **Notification System** | Webhook, Email, Push | Алерты оператору | → все критические модули |

### Поток данных (пример миссии):
1. **Планирование**: Web Interface → Mission Planner → Geo-Zone Checker
2. **Запуск**: Mission Planner → Flight Controller + RTK Module
3. **Полёт**: Flight Controller ↔ RTK Module → Data Logger + Telemetry
4. **Мониторинг**: Safety Monitor → Notification System (при событиях)
5. **Завершение**: Data Logger → Backup + Cloud Mirror (optional)
