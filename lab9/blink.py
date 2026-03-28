import uasyncio as asyncio  # type: ignore
from machine import Pin, SoftI2C, I2C  # type: ignore
from OLED_1inch5 import OLED_1inch5 # type: ignore
from SHTC3 import SHTC3 # type: ignore
from VOC_SGP40 import SGP40
from VOC_Algorithm import VOC_Algorithm

OLED_ADDR  = 0x3d
SHTC3_ADDR = 0x70
VOC_ADDR   = 0x59

OLED_i2c    = SoftI2C(sda=Pin(6), scl=Pin(7), freq=1_000_000)
Sensors_i2c = I2C(id=0, sda=Pin(8), scl=Pin(9), freq=100_000)

OLED  = OLED_1inch5(OLED_ADDR, OLED_i2c)
shtc3 = SHTC3(Sensors_i2c, SHTC3_ADDR)
shtc3.wakeup()
sgp = SGP40(Sensors_i2c, VOC_ADDR)
VOC = VOC_Algorithm()

button = Pin(3, Pin.IN, Pin.PULL_UP)

VOC_SECTORS = [
    (100, "Excellent",    3),
    (200, "Good",         6),
    (300, "Light poll.",  9),
    (400, "Mod. poll.", 12),
    (500, "Heavy poll.", 15),
]

state = {
    "running": True,
    "T":   0.0,
    "RH":  0.0,
    "raw": 0,
    "voc": 0,
}

WIDTH      = 128
WHITE      = 15
BAR_X      = 4
BAR_Y      = 60
BAR_W      = WIDTH - 8    
BAR_H      = 28
SECTOR_W   = BAR_W // 5  
SECTOR_GAP = 1

def voc_label(voc):
    for max_v, label, _ in VOC_SECTORS:
        if voc <= max_v:
            return label
    return VOC_SECTORS[-1][1]

def draw_screen():
    voc = state["voc"]
    OLED.fill(0)

    OLED.text("T={:.1f}C RH={:.1f}%".format(state["T"], state["RH"]), 0,  2, WHITE)
    OLED.text("Raw: {}".format(state["raw"]),                          0, 14, WHITE)
    OLED.text("VOC: {}".format(voc),                                   0, 26, WHITE)
    OLED.text(voc_label(voc),                                          0, 38, WHITE)

    for x in range(WIDTH):
        OLED.pixel(x, 52, WHITE)

    filled_sectors = min(voc // 100, 5)       
    partial_frac   = (voc % 100) / 100.0      

    for s, (_, _, shade) in enumerate(VOC_SECTORS):
        gap = SECTOR_GAP if s > 0 else 0
        x0  = BAR_X + s * SECTOR_W + gap
        w   = SECTOR_W - gap

        OLED.rect(x0, BAR_Y, w, BAR_H, 4)

        if s < filled_sectors:
            fill_w = w
        elif s == filled_sectors:
            fill_w = max(1, int(w * partial_frac)) if partial_frac > 0 else 0
        else:
            fill_w = 0

        if fill_w > 0:
            OLED.fill_rect(x0, BAR_Y, fill_w, BAR_H, shade)

    for i, lbl in enumerate(["0", "100", "200", "300", "400", "500"]):
        tx = BAR_X + i * SECTOR_W - (2 if i > 0 else 0)
        OLED.text(lbl, max(0, tx), BAR_Y + BAR_H + 4, WHITE)

    OLED.show()

def draw_paused():
    OLED.fill(0)
    OLED.text("  PAUSED", 20, 56, WHITE)
    OLED.show()


async def task_sensor():
    """Read SHTC3 + SGP40 every 300 ms using real T & RH for compensation."""
    while state["running"] != "exit":
        if state["running"]:
            T, RH = shtc3.measurement(0, 0, 0)
            raw   = sgp.measureRaw(T, RH)
            voc   = VOC.VocAlgorithm_process(raw)
            state["T"]   = T
            state["RH"]  = RH
            state["raw"] = raw
            state["voc"] = voc
        await asyncio.sleep_ms(300)

async def task_display():
    """Refresh OLED every 350 ms."""
    while state["running"] != "exit":
        if state["running"]:
            draw_screen()
        else:
            draw_paused()
        await asyncio.sleep_ms(350)

    OLED.fill(0)
    OLED.text("Goodbye!", 28, 56, WHITE)
    OLED.show()

async def task_button():
    """
    Poll button every 10 ms with software debounce.
      Short press  (<1.5 s) → toggle pause / resume
      Long press   (≥1.5 s) → exit program
    """
    DEBOUNCE_MS   = 50
    LONG_PRESS_MS = 1500
    prev = button.value()

    while state["running"] != "exit":
        cur = button.value()

        if prev == 1 and cur == 0:              
            await asyncio.sleep_ms(DEBOUNCE_MS)
            if button.value() != 0:              
                prev = button.value()
                await asyncio.sleep_ms(10)
                continue

            hold = 0
            while button.value() == 0:
                await asyncio.sleep_ms(10)
                hold += 10

            if hold >= LONG_PRESS_MS:
                state["running"] = "exit"       
            else:
                state["running"] = not state["running"]

        prev = cur
        await asyncio.sleep_ms(10)

async def main():
    await asyncio.gather(
        task_sensor(),
        task_display(),
        task_button(),
    )

asyncio.run(main())