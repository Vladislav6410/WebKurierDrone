#!/usr/bin/env bash
#
# WebKurierVehicleHub — Telemetry Install Script
# Устанавливает:
#  - скрипт телеметрии в /opt/webkurier/telemetry/
#  - systemd-юнит webkurier-telemetry.service
#
# Ожидаемая структура репозитория:
#  WebKurierVehicleHub/
#    engine/telemetry/telemetry_bridge.py
#    engine/telemetry/config.yaml
#    deploy/systemd/webkurier-telemetry.service.template
#
# Использование:
#   cd /path/to/WebKurierVehicleHub
#   sudo ./deploy/install.sh
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TELEMETRY_SRC_DIR="${REPO_ROOT}/engine/telemetry"
SYSTEMD_TEMPLATE="${REPO_ROOT}/deploy/systemd/webkurier-telemetry.service.template"

TELEMETRY_DST_DIR="/opt/webkurier/telemetry"
SYSTEMD_UNIT="/etc/systemd/system/webkurier-telemetry.service"

SERVICE_NAME="webkurier-telemetry.service"

echo "=== WebKurierVehicleHub • Telemetry Installer ==="

# 1. Проверка прав
if [[ "$EUID" -ne 0 ]]; then
  echo "Ошибка: этот скрипт нужно запускать с правами root."
  echo "Пожалуйста, выполните:"
  echo "  sudo $0"
  exit 1
fi

# 2. Проверяем, что запускаемся из корня репозитория / правильного места
if [[ ! -d "${TELEMETRY_SRC_DIR}" ]]; then
  echo "Ошибка: не найдена директория ${TELEMETRY_SRC_DIR}"
  echo "Убедись, что структура:"
  echo "  engine/telemetry/telemetry_bridge.py"
  echo "  engine/telemetry/config.yaml"
  echo "существует относительно deploy/."
  exit 1
fi

if [[ ! -f "${TELEMETRY_SRC_DIR}/telemetry_bridge.py" ]]; then
  echo "Ошибка: отсутствует файл ${TELEMETRY_SRC_DIR}/telemetry_bridge.py"
  exit 1
fi

if [[ ! -f "${TELEMETRY_SRC_DIR}/config.yaml" ]]; then
  echo "Внимание: отсутствует файл ${TELEMETRY_SRC_DIR}/config.yaml"
  echo "Создай его или добавь позже. Продолжаем установку без него..."
fi

if [[ ! -f "${SYSTEMD_TEMPLATE}" ]]; then
  echo "Ошибка: отсутствует шаблон systemd-юнита:"
  echo "  ${SYSTEMD_TEMPLATE}"
  exit 1
fi

# 3. Создаём директорию /opt/webkurier/telemetry
echo "[1/4] Создаю директорию ${TELEMETRY_DST_DIR} ..."
mkdir -p "${TELEMETRY_DST_DIR}"

# 4. Копируем скрипт телеметрии и конфиг
echo "[2/4] Копирую файлы телеметрии в ${TELEMETRY_DST_DIR} ..."

cp "${TELEMETRY_SRC_DIR}/telemetry_bridge.py" "${TELEMETRY_DST_DIR}/telemetry_bridge.py"

if [[ -f "${TELEMETRY_SRC_DIR}/config.yaml" ]]; then
  cp "${TELEMETRY_SRC_DIR}/config.yaml" "${TELEMETRY_DST_DIR}/config.yaml"
fi

chmod 755 "${TELEMETRY_DST_DIR}/telemetry_bridge.py" || true

# 5. Устанавливаем systemd unit
echo "[3/4] Устанавливаю systemd-юнит в ${SYSTEMD_UNIT} ..."

cp "${SYSTEMD_TEMPLATE}" "${SYSTEMD_UNIT}"
chmod 644 "${SYSTEMD_UNIT}"

# 6. Перечитываем systemd, включаем и запускаем сервис
echo "[4/4] Перезапускаю конфигурацию systemd и включаю сервис..."

systemctl daemon-reload

# enable сервис для автозапуска
systemctl enable "${SERVICE_NAME}"

# пробуем запустить прямо сейчас
systemctl restart "${SERVICE_NAME}" || systemctl start "${SERVICE_NAME}"

echo
echo "=== Готово! ==="
echo "Сервис ${SERVICE_NAME} установлен и должен быть запущен."
echo "Проверить статус можно командой:"
echo "  systemctl status ${SERVICE_NAME}"
echo
echo "Файлы на борту:"
echo "  Скрипт телеметрии: ${TELEMETRY_DST_DIR}/telemetry_bridge.py"
echo "  Конфиг телеметрии: ${TELEMETRY_DST_DIR}/config.yaml (если был)"
echo "  systemd unit:      ${SYSTEMD_UNIT}"
echo
echo "Если нужно, добавь позже другие сервисы (например, webkurier-video.service)"
echo "по той же схеме в deploy/systemd/ и /etc/systemd/system/."