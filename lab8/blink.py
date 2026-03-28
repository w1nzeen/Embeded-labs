import uasyncio as asyncio  # type: ignore
from machine import Pin, SoftI2C, I2C # type: ignore
from OLED_1inch5 import OLED_1inch5
from shtc3 import SHTC3
from time import sleep, ticks_ms, ticks_diff

WIDTH = 128
HEIGHT = 128

OLED_ADDR = 0x3d
SHTC3_ADDR = 0x70

OLED_i2c = SoftI2C(sda = Pin(6), scl = Pin(7), freq = 1_000_000)
sleep(0.1)
SHTC3_i2c = I2C(id = 0, sda = Pin(8), scl = Pin(9), freq = 100_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, OLED_i2c)
shtc3 = SHTC3(SHTC3_i2c, SHTC3_ADDR)
shtc3.wakeup()

button = Pin(3, Pin.IN, Pin.PULL_UP)

MODE_T    = 0
MODE_RH   = 1
MODE_EXIT = 2

state = {
    "mode":       MODE_T,
    "running":    True,
    "T":          0.0,
    "RH":         0.0,
    "t_history":  [],
    "rh_history": [],
}

MAX_SAMPLES = 120
CHART_TOP   = 20
CHART_H     = HEIGHT - CHART_TOP - 4
BAR_COLOR   = 10
LABEL_COLOR = 15

T_MIN,  T_MAX  = -10.0, 50.0
RH_MIN, RH_MAX =   0.0, 100.0

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def append_history(buf, value):
    buf.append(value)
    if len(buf) > MAX_SAMPLES:
        buf.pop(0)

def draw_histogram(history, label, unit, val_min, val_max, current):
    OLED.fill(0)

    header = "{}: {:.1f}{}".format(label, current, unit)
    OLED.text(header, 0, 4, LABEL_COLOR)

    baseline = CHART_TOP + CHART_H
    for x in range(WIDTH):
        OLED.pixel(x, baseline + 1, LABEL_COLOR)

    n = len(history)
    if n == 0:
        OLED.show()
        return

    num_bars = min(n, MAX_SAMPLES)
    start    = n - num_bars
    x_offset = MAX_SAMPLES - num_bars

    for i, val in enumerate(history[start:]):
        bar_h = int(clamp((val - val_min) / (val_max - val_min), 0.0, 1.0) * CHART_H)
        if bar_h == 0:
            bar_h = 1
        x = x_offset + i
        y = baseline - bar_h
        OLED.vline(x, y, bar_h, BAR_COLOR)

    OLED.show()

def draw_exit_screen():
    OLED.fill(0)
    OLED.text("Button held",  10, 50, LABEL_COLOR)
    OLED.text("Exiting...",   18, 65, LABEL_COLOR)
    OLED.show()


async def task_sensor():
    while state["running"]:
        T, RH = shtc3.measurement(0, 0, 0)
        state["T"]  = T
        state["RH"] = RH
        append_history(state["t_history"],  T)
        append_history(state["rh_history"], RH)
        await asyncio.sleep_ms(500)

async def task_display():
    while state["running"]:
        mode = state["mode"]

        if mode == MODE_T:
            draw_histogram(
                state["t_history"], "Temp", "C",
                T_MIN, T_MAX, state["T"]
            )

        elif mode == MODE_RH:
            draw_histogram(
                state["rh_history"], "Hum", "%",
                RH_MIN, RH_MAX, state["RH"]
            )

        elif mode == MODE_EXIT:
            draw_exit_screen()
            await asyncio.sleep_ms(1000)
            OLED.fill(0)
            OLED.show()
            state["running"] = False
            return

        await asyncio.sleep_ms(500)

async def task_button():
    DEBOUNCE_MS = 200
    prev = button.value()   

    while state["running"]:
        cur = button.value()

        if prev == 1 and cur == 0:
            await asyncio.sleep_ms(DEBOUNCE_MS)   
            if button.value() == 0:               
                state["mode"] = (state["mode"] + 1) % 3

        prev = cur
        await asyncio.sleep_ms(10)   

async def main():
    await asyncio.gather(
        task_sensor(),
        task_display(),
        task_button(),
    )

asyncio.run(main())