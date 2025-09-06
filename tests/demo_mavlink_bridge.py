# -*- coding: utf-8 -*-
"""
Демо-связка: Autopilot → MavlinkRadio (dry-run).
- Симулируем CRUISE-режим автопилота
- Передаём команды в MAVLink-адаптер (печать PWM)
- Логируем в tests/out/mavlink_bridge_log.csv
Запуск:
    python tests/demo_mavlink_bridge.py
"""

import os
from engine.agents.autopilot_ai.autopilot import Autopilot, _simulate_step
from radio_control.mavlink_radio import MavlinkRadio


def main():
    # 1) Автопилот
    ap = Autopilot()
    ap.set_mode("CRUISE", target_alt_m=40.0, target_airspeed_ms=18.0)

    # 2) MAVLink-радио (dry-run: True — безопасно без модема/pymavlink)
    link = MavlinkRadio(conn_str="udpout:127.0.0.1:14550", dry_run=True)
    link.connect()
    link.wait_heartbeat()
    link.arm()

    # 3) Симуляция + передача команд
    dt = 0.1
    steps = 200  # 20 сек
    state = {"alt_m": 0.0, "airspeed": 0.0}

    # лог
    os.makedirs(os.path.join("tests", "out"), exist_ok=True)
    log_path = os.path.join("tests", "out", "mavlink_bridge_log.csv")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("t,alt_m,airspeed,thrust,pitch,roll,yaw,failsafe\n")

        for i in range(steps):
            t = i * dt
            sensors = {"baro_alt_m": state["alt_m"], "airspeed": state["airspeed"]}
            sys = {"dt": dt, "battery_v": 23.6, "link_ok": True}

            cmd = ap.update(sensors, sys)
            link.apply_autopilot_cmd(cmd)  # → печать PWM в консоль (dry-run)

            # лог
            f.write("{:.2f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{}\n".format(
                t, state["alt_m"], state["airspeed"],
                cmd["thrust"], cmd["pitch"], cmd.get("roll", 0.0), cmd.get("yaw", 0.0),
                int(cmd["failsafe"])
            ))

            # простая динамика
            state = _simulate_step(state, cmd, dt)

    link.disarm()
    print(f"\n📁 Лог сохранён: {log_path}")
    print("✅ Демо завершено (dry-run). Для реального модема установи pymavlink и отключи dry_run.")


if __name__ == "__main__":
    main()