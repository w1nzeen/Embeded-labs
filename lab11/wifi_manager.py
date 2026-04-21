# wifi_manager.py — Модуль підключення до Wi-Fi мережі
# Відповідає виключно за встановлення з'єднання і повернення IP.

import network
import time
from state import system_state

def connect_wifi(ssid, password, timeout=15):
    """
    Підключається до Wi-Fi мережі в режимі STA (Station).

    Параметри:
        ssid     — назва мережі
        password — пароль
        timeout  — максимальний час очікування у секундах (за замовчуванням 15)

    Повертає:
        str — IP-адреса пристрою при успішному підключенні

    Викидає:
        RuntimeError — якщо підключення не відбулося за відведений час

    Якщо підключення не вдалося:
        - у консоль виводиться повідомлення про помилку
        - RuntimeError передається вгору — main.py вирішує, чи перезавантажити плату
    """
    print(f"[wifi] Підключення до мережі '{ssid}'...")

    # Ініціалізуємо інтерфейс Wi-Fi в режимі клієнта (Station)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Якщо вже підключено — повертаємо поточний IP без повторного handshake
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"[wifi] Вже підключено. IP: {ip}")
        system_state["ip"] = ip
        return ip

    wlan.connect(ssid, password)

    # Очікуємо підключення з таймаутом
    start = time.time()
    while not wlan.isconnected():
        elapsed = time.time() - start
        if elapsed >= timeout:
            wlan.active(False)  # Деактивуємо інтерфейс перед помилкою
            raise RuntimeError(
                f"[wifi] Помилка: не вдалося підключитися до '{ssid}' за {timeout}с"
            )
        print(f"[wifi] Очікування... ({int(elapsed)}с)")
        time.sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"[wifi] Успішно підключено! IP: {ip}")

    # Зберігаємо IP у глобальному стані
    system_state["ip"] = ip
    return ip
