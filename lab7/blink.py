from machine import Pin, ADC, SoftI2C, Timer, PWM
from OLED_1inch5 import OLED_1inch5
from time import sleep
import utime

i2c_num = 1
sda_pin = Pin(6)
scl_pin = Pin(7)

WIDTH = 128
HEIGHT = 128
OLED_ADDR = 0x3d

sound_sensor = ADC(Pin(28))
i2c = SoftI2C(scl = scl_pin, sda = sda_pin, freq=1_000_000)
sleep(0.1)
buzzer = PWM(Pin(15))
button = Pin(14, Pin.IN, Pin.PULL_UP)

OLED = OLED_1inch5(OLED_ADDR, i2c)
column_hights =[]  
sound_value   = 0    
running       = True 
btn_pressed   = False

def button_irq(pin):
    """Лише встановлює прапорець — вся логіка в головному циклі."""
    global btn_pressed
    btn_pressed = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_irq)

def read_sensor(timer):
    """Зчитує сенсор звуку по перериванню таймера (10 Гц)."""
    global sound_value
    vol         = sound_sensor.read_u16()
    sound_value = vol / 65535 * 100

sensor_timer = Timer()
sensor_timer.init(freq=10, mode=Timer.PERIODIC, callback=read_sensor)

melody_str = "Melody:b=116,o=4,d=4:e,8b,8p,8b,8a,8b,e,8b,8p,8b,8p,8a,b,d5,8c5,8p,8c5,8b,8c5,e,8c5,8p,8c5,8p,8b,c5,d5"

NOTES = {
    'c': 261.63, 'c#': 277.18, 'd': 293.66, 'd#': 311.13, 'e': 329.63,
    'f': 349.23, 'f#': 369.99, 'g': 392.00, 'g#': 415.30, 'a': 440.00,
    'a#': 466.16, 'b': 493.88, 'p': 0
}

def parse_rtttl(rtttl_str):
    parts = rtttl_str.split(':')
    header = parts[1].split(',')
    notes_data = parts[2].split(',')
    bpm = 116
    default_duration = 4
    default_octave = 4
    for h in header:
        if h.startswith('b='): bpm = int(h[2:])
        if h.startswith('d='): default_duration = int(h[2:])
        if h.startswith('o='): default_octave = int(h[2:])
    wholenote = (60 * 1000 / bpm) * 4
    parsed_notes = []
    for n in notes_data:
        n = n.strip()
        if not n: continue
        i = 0
        duration = ""
        while i < len(n) and n[i].isdigit():
            duration += n[i]
            i += 1
        note_duration = int(duration) if duration else default_duration
        note_name = ""
        while i < len(n) and not n[i].isdigit():
            note_name += n[i]
            i += 1
        octave = int(n[i:]) if i < len(n) else default_octave
        freq = 0
        if note_name in NOTES:
            freq = NOTES[note_name]
            if freq > 0:
                freq *= (2 ** (octave - 4))
        ms_duration = wholenote / note_duration
        parsed_notes.append((freq, ms_duration))
    return parsed_notes

melody_notes = parse_rtttl(melody_str)

def play_melody():
    """Програє мелодію через зумер (RTTTL)."""
    for freq, ms_duration in melody_notes:
        active_ms = int(ms_duration * 0.9)
        pause_ms  = int(ms_duration * 0.1)
        if freq > 0:
            buzzer.freq(int(freq))
            buzzer.duty_u16(30000)
        else:
            buzzer.duty_u16(0)
        utime.sleep_ms(active_ms)
        buzzer.duty_u16(0)
        utime.sleep_ms(pause_ms)
    buzzer.duty_u16(0)

# ─── 8. Малювання прямокутників замість ліній (завдання 9) ──────────────────
def draw_histogram():
    """Малює гістограму у вигляді залитих прямокутників (2 пікселі завширшки)."""
    i = 0
    for ch in column_hights:
        if ch > 0:
            OLED.fill_rect(i, 127 - ch, 2, ch, 15)
        i += 2

# ─── 9. Головний цикл ───────────────────────────────────────────────────────
play_melody()   # грає при запуску (завдання 12)

while True:
    # Обробка прапорця кнопки (завдання 10)
    if btn_pressed:
        btn_pressed = False
        running = not running
        if not running:
            buzzer.duty_u16(0)
            column_hights.clear()
            OLED.fill(0)
            OLED.text("  PAUSED  ", 14, 56, 15)
            OLED.show()

    if not running:
        sleep(0.05)
        continue

    # Поточне значення вже оновлене таймером (завдання 11)
    sound = sound_value

    column_hight = int(sound)
    column_hights.append(column_hight)
    if len(column_hights) > 64:
        del column_hights[0]

    OLED.fill(0)
    OLED.text("Sound={0:.1f}%".format(sound), 1, 5, 15)
    draw_histogram()
    OLED.show()

    sleep(0.1)