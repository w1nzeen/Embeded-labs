import uasyncio as asyncio  # type: ignore
from machine import Pin, SoftI2C, I2C  # type: ignore
from OLED_1inch5 import OLED_1inch5
from qmi8658 import QMI8658

OLED_ADDR    = 0x3d
QMI8658_ADDR = 0x6b

OLED_i2c    = SoftI2C(sda=Pin(6), scl=Pin(7), freq=1_000_000)
Sensors_i2c = I2C(id=0, sda=Pin(8), scl=Pin(9), freq=100_000)

OLED     = OLED_1inch5(OLED_ADDR, OLED_i2c)
qmi8658  = QMI8658(Sensors_i2c, QMI8658_ADDR)

button = Pin(3, Pin.IN, Pin.PULL_UP)

WIDTH   = 128
HEIGHT  = 128
WHITE   = 15
CX      = WIDTH  // 2   # screen centre X
CY      = HEIGHT // 2   # screen centre Y
RADIUS  = 8             # ball radius in pixels
MARGIN  = RADIUS + 2    # keeps the ball fully on screen

SENS = 7

state = {
    "running": True,
    "xyz": [0.0] * 6,   # [ax, ay, az, gx, gy, gz]
}

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def draw_circle(cx, cy, r, col):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        OLED.hline(cx - dx, cy + dy, 2 * dx + 1, col)

def draw_screen():
    xyz = state["xyz"]
    ax, ay = xyz[0], xyz[1]

    bx = clamp(int(CX + ax * SENS), MARGIN, WIDTH  - MARGIN)
    by = clamp(int(CY - ay * SENS), MARGIN, HEIGHT - MARGIN)

    OLED.fill(0)

    OLED.hline(CX - 4, CY, 9, 4)
    OLED.vline(CX, CY - 4, 9, 4)

    draw_circle(bx, by, RADIUS, WHITE)

    OLED.fill_rect(0, HEIGHT - 40, WIDTH, 40, 0)   # clear text area
    OLED.text("Ax={:+.2f} Ay={:+.2f}".format(ax, ay),        0, HEIGHT - 38, WHITE)
    OLED.text("Az={:+.2f}".format(xyz[2]),                    0, HEIGHT - 28, WHITE)
    OLED.text("Gx={:+.0f} Gy={:+.0f}".format(xyz[3], xyz[4]),0, HEIGHT - 18, WHITE)
    OLED.text("Gz={:+.0f}".format(xyz[5]),                    0, HEIGHT -  8, WHITE)

    OLED.show()

def draw_paused():
    OLED.fill(0)
    OLED.text("  PAUSED", 20, 56, WHITE)
    OLED.show()


async def task_sensor():
    while state["running"] != "exit":
        if state["running"]:
            state["xyz"] = qmi8658.Read_XYZ()
            xyz = state["xyz"]
            print("ACC  X={:+.2f}  Y={:+.2f}  Z={:+.2f}".format(*xyz[:3]))
            print("GYR  X={:+.0f}  Y={:+.0f}  Z={:+.0f}\n".format(*xyz[3:]))
        await asyncio.sleep_ms(50)

async def task_display():
    while state["running"] != "exit":
        if state["running"]:
            draw_screen()
        else:
            draw_paused()
        await asyncio.sleep_ms(60)

    OLED.fill(0)
    OLED.text("Goodbye!", 28, 56, WHITE)
    OLED.show()

async def task_button():
    DEBOUNCE_MS   = 50
    LONG_PRESS_MS = 1500
    prev = button.value()

    while state["running"] != "exit":
        cur = button.value()

        if prev == 1 and cur == 0:               # falling edge → button down
            await asyncio.sleep_ms(DEBOUNCE_MS)
            if button.value() != 0:              # bounce → skip
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