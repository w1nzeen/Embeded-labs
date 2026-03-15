import asyncio
from machine import Pin, ADC, SoftI2C
from OLED_1inch5 import OLED_1inch5
from time import sleep


i2c = SoftI2C(scl=Pin(7), sda=Pin(6), freq=1_000_000)
sleep(0.1)
OLED = OLED_1inch5(0x3d, i2c)

photoresistor = ADC(Pin(26))   
potentiometer = ADC(Pin(27))   
button        = Pin(15, Pin.IN, Pin.PULL_UP)  

state = {
    "display_on": True,
    "photo_val":  0,
    "pot_val":    0,
}

async def task_button():
    prev = 1   
    while True:
        cur = button.value()
        if prev == 1 and cur == 0:          
            state["display_on"] = not state["display_on"]
            if not state["display_on"]:
                OLED.fill(0)
                OLED.show()
        prev = cur
        await asyncio.sleep_ms(50)

async def task_adc():
    while True:
        state["photo_val"] = photoresistor.read_u16()
        state["pot_val"]   = potentiometer.read_u16()
        await asyncio.sleep_ms(100)

async def task_display():
    while True:
        if state["display_on"]:
            photo_pct = state["photo_val"] / 65535 * 100
            pot_pct   = state["pot_val"]   / 65535 * 100
            photo_bar = 1 + int(photo_pct * 125 / 100)
            pot_bar   = 1 + int(pot_pct   * 125 / 100)

            OLED.fill(0)

            OLED.text("GP26 Photo", 1, 2, 15)
            OLED.text("{:.1f}%".format(photo_pct), 80, 2, 10)
            OLED.rect(0, 14, 127, 16, 15)
            OLED.rect(1, 15, photo_bar, 14, 8, True)

            OLED.text("GP27 Pot  ", 1, 36, 15)
            OLED.text("{:.1f}%".format(pot_pct), 80, 36, 10)
            OLED.rect(0, 48, 127, 16, 15)
            OLED.rect(1, 49, pot_bar, 14, 12, True)

            OLED.hline(0, 72, 128, 5)
            status = "ON " if state["display_on"] else "OFF"
            OLED.text("Display: " + status, 1, 78, 6)
            OLED.text("BTN GP15", 1, 92, 4)

            OLED.show()

        await asyncio.sleep_ms(50)

async def main():
    await asyncio.gather(
        task_button(),
        task_adc(),
        task_display(),
    )

asyncio.run(main())