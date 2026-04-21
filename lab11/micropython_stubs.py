# micropython_stubs.py
# Підміняє MicroPython-специфічні модулі для запуску на звичайному Python 3.
# Імпортується ПЕРШИМ у run_desktop.py — до будь-якого іншого коду проєкту.

import sys
import time as _time
import random
import math

print("[stubs] Завантаження MicroPython-заглушок для desktop-режиму...")

# ─────────────────────────────────────────────────────────────────
# machine — GPIO, ADC, Pin
# ─────────────────────────────────────────────────────────────────
class _Pin:
    IN   = "IN"
    OUT  = "OUT"
    PULL_UP   = "PULL_UP"
    PULL_DOWN = "PULL_DOWN"
    IRQ_FALLING = "FALLING"
    IRQ_RISING  = "RISING"

    def __init__(self, id, mode=None, pull=None):
        self._id    = id
        self._value = 0
        self._mode  = mode

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = int(v)
        state_str = "HIGH" if self._value else "LOW"
        print(f"[stub:Pin] GP{self._id} → {state_str}")

    def irq(self, trigger=None, handler=None):
        # Просто запам'ятовуємо — кнопку у desktop-режимі можна натиснути через /toggle-system
        self._irq_handler = handler
        print(f"[stub:Pin] IRQ зареєстровано на GP{self._id} (тригер: {trigger})")

    def __repr__(self):
        return f"Pin(GP{self._id}, value={self._value})"


class _ADC:
    def __init__(self, channel):
        self._channel = channel

    def read_u16(self):
        # Симулюємо вбудований температурний сенсор: повертаємо значення для ~26°C
        # з невеликим шумом, щоб показники мінялись
        base_voltage = 0.706 + (27 - (22 + random.uniform(-2, 2))) * 0.001721
        raw = int(base_voltage / 3.3 * 65535)
        return max(0, min(65535, raw))


class _machine_module:
    Pin = _Pin
    ADC = _ADC

    @staticmethod
    def reset():
        print("[stub:machine] machine.reset() викликано — у desktop-режимі ігнорується")


sys.modules["machine"] = _machine_module()

# ─────────────────────────────────────────────────────────────────
# network — Wi-Fi
# ─────────────────────────────────────────────────────────────────
class _WLAN:
    STA_IF = "STA"
    AP_IF  = "AP"

    def __init__(self, mode):
        self._mode   = mode
        self._active = False

    def active(self, state=None):
        if state is None:
            return self._active
        self._active = bool(state)

    def connect(self, ssid, password):
        print(f"[stub:network] Симуляція підключення до '{ssid}'...")

    def isconnected(self):
        return True  # Завжди підключені у симуляторі

    def ifconfig(self):
        # Повертаємо локальний IP — сервер буде доступний на 127.0.0.1
        return ("127.0.0.1", "255.255.255.0", "127.0.0.1", "8.8.8.8")


class _network_module:
    STA_IF = "STA"
    AP_IF  = "AP"
    WLAN   = _WLAN


sys.modules["network"] = _network_module()

# ─────────────────────────────────────────────────────────────────
# ujson — просто перенаправляємо на стандартний json
# ─────────────────────────────────────────────────────────────────
import json as _json
sys.modules["ujson"] = _json

# ─────────────────────────────────────────────────────────────────
# utime — перенаправляємо на time
# ─────────────────────────────────────────────────────────────────
import time as _time_mod

class _utime_module:
    def time(self):
        return _time_mod.time()
    def sleep(self, s):
        _time_mod.sleep(s)
    def sleep_ms(self, ms):
        _time_mod.sleep(ms / 1000)
    def ticks_ms(self):
        return int(_time_mod.time() * 1000)
    def ticks_diff(self, a, b):
        return a - b

sys.modules["utime"] = _utime_module()

# ─────────────────────────────────────────────────────────────────
# Патчимо time.ticks_ms і time.ticks_diff для сумісності
# (деякий MicroPython код викликає time.ticks_ms() напряму)
# ─────────────────────────────────────────────────────────────────
_time_mod.ticks_ms   = lambda: int(_time_mod.time() * 1000)
_time_mod.ticks_diff = lambda a, b: a - b

print("[stubs] Усі заглушки встановлено ✓")
print("[stubs] machine.Pin, machine.ADC, network.WLAN, ujson — доступні")
print()
