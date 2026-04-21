# state.py — Централізований стан програми
# Всі модулі імпортують цей об'єкт і працюють з єдиним джерелом правди.

import time

# Головний словник стану системи
system_state = {
    "led": False,           # Поточний стан LED (True = увімкнено)
    "program_enabled": True, # Чи працює основна логіка
    "last_message": "",      # Останнє повідомлення з вебформи
    "ip": "",                # IP-адреса після підключення до Wi-Fi
    "start_time": time.time(), # Час запуску для підрахунку uptime
    "last_sensor_read": {    # Останні прочитані дані сенсорів
        "temperature": None,
        "humidity": None,
        "air_quality": None
    }
}

def get_uptime():
    """Повертає кількість секунд з моменту запуску."""
    return int(time.time() - system_state["start_time"])

def update_state(key, value):
    """Безпечне оновлення поля стану з перевіркою ключа."""
    if key in system_state:
        system_state[key] = value
    else:
        print(f"[state] Попередження: невідомий ключ '{key}'")

def update_sensor_data(temperature=None, humidity=None, air_quality=None):
    """Оновлює блок показників сенсорів."""
    system_state["last_sensor_read"] = {
        "temperature": temperature,
        "humidity": humidity,
        "air_quality": air_quality
    }

def get_full_status():
    """Повертає словник для JSON /status відповіді."""
    return {
        "led": system_state["led"],
        "program_enabled": system_state["program_enabled"],
        "ip": system_state["ip"],
        "last_message": system_state["last_message"],
        "uptime": get_uptime()
    }
