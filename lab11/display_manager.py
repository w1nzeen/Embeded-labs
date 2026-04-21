# display_manager.py — Адаптер дисплея
#
# Архітектура: цей модуль є єдиним місцем у проєкті, де взаємодіємо з дисплеєм.
# Всі інші модулі викликають лише display_message(text).
# Де підключити реальний дисплей — позначено ">>> РЕАЛЬНИЙ ДИСПЛЕЙ <<<".

# ──────────────────────────────────────────────────────────────────
# >>> РЕАЛЬНИЙ ДИСПЛЕЙ <<<
# Розкоментуйте і адаптуйте один з варіантів нижче:
#
# Варіант 1: SSD1306 OLED 128x64 через I2C
#   from machine import I2C, Pin
#   from ssd1306 import SSD1306_I2C
#   i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
#   _display = SSD1306_I2C(128, 64, i2c)
#
# Варіант 2: SSD1306 через SPI
#   from machine import SPI, Pin
#   from ssd1306 import SSD1306_SPI
#   spi = SPI(0, baudrate=1000000)
#   _display = SSD1306_SPI(128, 64, spi, dc=Pin(8), res=Pin(9), cs=Pin(10))
#
# Варіант 3: LCD 16x2 через I2C (бібліотека lcd_api або I2C_LCD)
#   from machine import I2C, Pin
#   from lcd_api import LcdApi
#   from i2c_lcd import I2cLcd
#   i2c = I2C(0, scl=Pin(1), sda=Pin(0))
#   _display = I2cLcd(i2c, 0x27, 2, 16)
# ──────────────────────────────────────────────────────────────────

# Поки дисплей не підключено — зберігаємо повідомлення і виводимо в консоль
_display = None
_last_display_text = ""

def _init_display():
    """
    Ініціалізує дисплей.
    Викликається один раз при старті.
    Якщо дисплея немає — працює в режимі консоль-заглушки.
    """
    global _display
    # >>> РЕАЛЬНИЙ ДИСПЛЕЙ <<<
    # Перемістіть ініціалізацію з коментарів вище сюди.
    # Приклад для SSD1306:
    #   from machine import I2C, Pin
    #   from ssd1306 import SSD1306_I2C
    #   try:
    #       i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
    #       _display = SSD1306_I2C(128, 64, i2c)
    #       print("[display] SSD1306 ініціалізовано")
    #   except Exception as e:
    #       print(f"[display] Помилка ініціалізації: {e}")
    #       _display = None

    if _display is None:
        print("[display] Режим заглушки (реальний дисплей не підключено)")

def display_message(text):
    """
    Головна публічна функція — виводить текст на дисплей.

    Параметри:
        text — рядок для відображення (до 64 символів рекомендовано)

    Алгоритм:
        1. Зберігає текст у буфері
        2. Намагається вивести на реальний дисплей
        3. Якщо дисплея немає — виводить у консоль
        4. При помилці — не падає, логує проблему
    """
    global _last_display_text
    _last_display_text = str(text)[:64]  # Обмежуємо довжину

    print(f"[display] Повідомлення: {_last_display_text}")

    if _display is None:
        # Заглушка: нічого більше не робимо, повідомлення вже в консолі
        return

    try:
        # >>> РЕАЛЬНИЙ ДИСПЛЕЙ <<<
        # Розкоментуйте потрібний блок:

        # ── SSD1306 OLED ──────────────────────────────────
        # _display.fill(0)
        # _display.text("Pico W", 0, 0)
        # # Розбиваємо на рядки по 16 символів
        # words = _last_display_text
        # _display.text(words[:16], 0, 16)
        # if len(words) > 16:
        #     _display.text(words[16:32], 0, 26)
        # if len(words) > 32:
        #     _display.text(words[32:48], 0, 36)
        # _display.show()

        # ── LCD 16x2 ──────────────────────────────────────
        # _display.clear()
        # _display.putstr(_last_display_text[:16])
        # if len(_last_display_text) > 16:
        #     _display.move_to(0, 1)
        #     _display.putstr(_last_display_text[16:32])

        pass  # Видаліть цей рядок після розкоментування реального коду

    except Exception as e:
        print(f"[display] Помилка виводу на дисплей: {e}")

def get_last_display_text():
    """Повертає останній текст, що був на дисплеї."""
    return _last_display_text

# Ініціалізуємо при імпорті модуля
_init_display()
