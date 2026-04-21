# main.py — Точка входу програми
#
# Порядок запуску:
#   1. Налаштування кнопки (IRQ)
#   2. Підключення до Wi-Fi
#   3. Початкове зчитування сенсорів
#   4. Запуск HTTP-сервера
#
# Автоматичний запуск:
#   MicroPython виконує main.py автоматично після boot.py.
#   Якщо цей файл є на Pico W — програма стартує сама при подачі живлення.

import time
import machine
from machine import Pin

from state import system_state
from wifi_manager import connect_wifi
from sensors import get_sensor_data
from server import run_server

# ── Налаштування ──────────────────────────────────────────────────────
WIFI_SSID     = "YOUR_WIFI_SSID"      # <<< Змініть на вашу мережу
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"  # <<< Змініть на ваш пароль
WIFI_TIMEOUT  = 20                    # Секунд на підключення

BUTTON_PIN    = 15  # GP15 — апаратна кнопка (підключити між GP15 і GND)

# ── Апаратна кнопка і переривання ────────────────────────────────────

# Зберігаємо час останнього спрацювання для debounce
_last_button_press = 0

def _button_irq_handler(pin):
    """
    IRQ-обробник кнопки.

    ВАЖЛИВО: У interrupt handler ЗАБОРОНЕНО:
        - Виділяти пам'ять (список, dict, str конкатенація)
        - Викликати print() — нестабільно в ISR
        - Виконувати складні обчислення
        - Звертатись до мережі або файлової системи

    Ми лише:
        1. Перевіряємо debounce (мінімальний інтервал між натисканнями)
        2. Перемикаємо прапорець program_enabled

    Основний цикл (в run_server) вже реагує на цей прапорець.
    """
    global _last_button_press
    now = time.ticks_ms()

    # Debounce: ігноруємо натискання частіше ніж раз на 300мс
    if time.ticks_diff(now, _last_button_press) < 300:
        return

    _last_button_press = now
    # Атомарна операція — безпечна в ISR
    system_state["program_enabled"] = not system_state["program_enabled"]

def setup_button():
    """
    Налаштовує кнопку на GP15 з підтягуючим резистором (PULL_UP).

    Схема підключення:
        GP15 ──── кнопка ──── GND
        (при натисканні на піні буде LOW → FALLING)

    Тригер IRQ_FALLING: спрацьовує при відпусканні кнопки
    (більш стабільне спрацювання, ніж RISING при PULL_UP).
    """
    btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    btn.irq(trigger=Pin.IRQ_FALLING, handler=_button_irq_handler)
    print(f"[main] Кнопка налаштована на GP{BUTTON_PIN}")
    return btn  # Зберігаємо посилання, щоб GC не прибрав об'єкт

# ── Запуск ────────────────────────────────────────────────────────────

def main():
    print("=" * 40)
    print("  Pico W Backend — Старт")
    print("=" * 40)

    # 1. Апаратна кнопка
    button = setup_button()

    # 2. Підключення до Wi-Fi
    try:
        ip = connect_wifi(WIFI_SSID, WIFI_PASSWORD, timeout=WIFI_TIMEOUT)
        print(f"[main] Відкрийте браузер: http://{ip}")
    except RuntimeError as e:
        print(f"[main] КРИТИЧНА ПОМИЛКА Wi-Fi: {e}")
        print("[main] Перезавантаження через 5 секунд...")
        time.sleep(5)
        machine.reset()  # Перезавантажуємо плату — часто допомагає при Wi-Fi глюках

    # 3. Початкове зчитування сенсорів (заповнює last_sensor_read у стані)
    try:
        get_sensor_data()
        print("[main] Сенсори ініціалізовано")
    except Exception as e:
        print(f"[main] Попередження: помилка ініціалізації сенсорів: {e}")
        # Не зупиняємо програму — сенсори повернуть None

    # 4. Запуск HTTP-сервера (блокуючий нескінченний цикл)
    try:
        run_server(host="0.0.0.0", port=80)
    except KeyboardInterrupt:
        print("\n[main] Зупинено користувачем (Ctrl+C)")
    except Exception as e:
        print(f"[main] КРИТИЧНА ПОМИЛКА сервера: {e}")
        print("[main] Перезавантаження через 3 секунди...")
        time.sleep(3)
        machine.reset()

# Виконуємо тільки якщо запущено напряму (не при імпорті)
if __name__ == "__main__":
    main()
