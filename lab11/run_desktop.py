#!/usr/bin/env python3
# run_desktop.py — Запуск бекенду Pico W на звичайному комп'ютері
#
# Використання:
#   python run_desktop.py
#
# Потім відкрийте браузер: http://127.0.0.1:8080
#
# ВАЖЛИВО: цей файл має лежати поруч з main.py, server.py тощо.

import sys
import os

# ── 1. Додаємо поточну папку до шляху пошуку модулів ─────────────
# Щоб Python знайшов state.py, server.py тощо без встановлення
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 2. Завантажуємо заглушки МicroPython ДО будь-якого імпорту ───
# Важливо: цей рядок — ПЕРШИМ, бо далі server.py вже імпортує machine
import micropython_stubs  # noqa: F401  (встановлює sys.modules["machine"] тощо)

# ── 3. Тепер безпечно імпортуємо модулі проєкту ──────────────────
from state   import system_state
from sensors import get_sensor_data
from server  import run_server, led_on, led_off

# ── 4. Налаштування для desktop-режиму ───────────────────────────
DESKTOP_PORT = 8080   # 80-й порт потребує sudo; 8080 — без привілеїв
DESKTOP_HOST = "127.0.0.1"

# ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Pico W Backend — DESKTOP СИМУЛЯТОР")
    print("=" * 50)
    print()
    print("  Режим: звичайний Python 3 (не MicroPython)")
    print("  Заглушки: machine, network, ujson — активні")
    print()

    # Імітуємо успішне Wi-Fi підключення
    system_state["ip"] = DESKTOP_HOST
    print(f"[sim] Wi-Fi симульовано. IP: {DESKTOP_HOST}")

    # Початкове зчитування сенсорів
    data = get_sensor_data()
    print(f"[sim] Сенсори: {data}")
    print()
    print(f"  ✓ Відкрийте браузер: http://{DESKTOP_HOST}:{DESKTOP_PORT}")
    print(f"  ✓ JSON статус:       http://{DESKTOP_HOST}:{DESKTOP_PORT}/status")
    print(f"  ✓ JSON сенсори:      http://{DESKTOP_HOST}:{DESKTOP_PORT}/sensors")
    print()
    print("  Ctrl+C — зупинити сервер")
    print("-" * 50)

    try:
        run_server(host=DESKTOP_HOST, port=DESKTOP_PORT)
    except KeyboardInterrupt:
        print("\n[sim] Зупинено. До побачення!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n[sim] Помилка: порт {DESKTOP_PORT} вже зайнятий.")
            print(f"[sim] Змініть DESKTOP_PORT у run_desktop.py або зупиніть інший процес.")
        else:
            raise

if __name__ == "__main__":
    main()
