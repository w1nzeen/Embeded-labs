# sensors.py — Читання показників сенсорів
#
# Де підключити реальні сенсори — позначено коментарями ">>> РЕАЛЬНИЙ СЕНСОР <<<".
# Температура читається з вбудованого ADC(4) на Pico W.
# Вологість і якість повітря — заглушки з чітким інтерфейсом.

from machine import ADC
from state import update_sensor_data

# ──────────────────────────────────────────────
# Вбудований температурний сенсор Pico W (ADC channel 4)
# ──────────────────────────────────────────────
_temp_sensor = ADC(4)

def read_temperature():
    """
    Читає температуру з вбудованого сенсора ADC(4).

    Повертає:
        float — температура в °C, або None при помилці

    Примітка:
        Вбудований сенсор дає наближену температуру чіпа (~±2°C).
        >>> РЕАЛЬНИЙ СЕНСОР <<<
        Щоб підключити DHT22 або DS18B20:
            import dht
            sensor = dht.DHT22(Pin(X))
            sensor.measure()
            return sensor.temperature()
    """
    try:
        raw = _temp_sensor.read_u16()
        # Перетворення за формулою з документації RP2040
        voltage = raw * 3.3 / 65535
        temperature = 27 - (voltage - 0.706) / 0.001721
        return round(temperature, 1)
    except Exception as e:
        print(f"[sensors] Помилка читання температури: {e}")
        return None

def read_humidity():
    """
    Повертає відносну вологість у відсотках.

    Повертає:
        float або None

    >>> РЕАЛЬНИЙ СЕНСОР <<<
    Підключення DHT22 до Pin(GP15):
        import dht
        from machine import Pin
        sensor = dht.DHT22(Pin(15))
        sensor.measure()
        return sensor.humidity()

    Підключення SHT31 через I2C:
        from sht31 import SHT31
        sensor = SHT31(i2c)
        return sensor.humidity
    """
    # Заглушка — повертає None поки немає реального сенсора
    return None

def read_air_quality():
    """
    Повертає індекс якості повітря (AQI або ppm CO2/VOC).

    Повертає:
        int або None

    >>> РЕАЛЬНИЙ СЕНСОР <<<
    Підключення MQ-135 через ADC:
        from machine import ADC, Pin
        adc = ADC(Pin(26))  # GP26 = ADC0
        raw = adc.read_u16()
        # Конвертація в ppm залежить від калібрування
        return int(raw * 500 / 65535)

    Підключення SGP30 через I2C:
        from sgp30 import SGP30
        sensor = SGP30(i2c)
        return sensor.iaq_measure().co2eq
    """
    # Заглушка — повертає None поки немає реального сенсора
    return None

def get_sensor_data():
    """
    Зчитує всі сенсори і повертає словник.

    Повертає:
        dict з полями:
            "temperature" — °C (float або None)
            "humidity"    — % (float або None)
            "air_quality" — AQI/ppm (int або None)

    Також оновлює last_sensor_read у system_state через update_sensor_data().
    При помилці поле = None — фронтенд має відображати "N/A".
    """
    temperature = read_temperature()
    humidity    = read_humidity()
    air_quality = read_air_quality()

    # Зберігаємо у глобальному стані
    update_sensor_data(temperature, humidity, air_quality)

    return {
        "temperature": temperature,
        "humidity":    humidity,
        "air_quality": air_quality
    }
