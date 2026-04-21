from machine import Pin, ADC, SoftI2C, Timer
from OLED_1inch5 import OLED_1inch5
from time import sleep

i2c_num = 1
sda_pin = Pin(6)
scl_pin = Pin(7)

WIDTH     = 128
HEIGHT    = 128
OLED_ADDR = 0x3d

photoresistor = ADC(Pin(26))
potentiometer = ADC(Pin(27))  

i2c = SoftI2C(scl=scl_pin, sda=sda_pin, freq=1_000_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, i2c)

display_on = True
vol_photo  = 0
vol_pot    = 0

button = Pin(3, Pin.IN, Pin.PULL_UP)

def button_handler(pin):
    global display_on
    display_on = not display_on
    if not display_on:
        OLED.fill(0)
        OLED.show()

button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

def timer_handler(timer):
    global vol_photo, vol_pot
    vol_photo = photoresistor.read_u16()
    vol_pot   = potentiometer.read_u16()

timer = Timer()
timer.init(mode=Timer.PERIODIC, period=100, callback=timer_handler)

def tasks():
    if not display_on:
        sleep(0.1)
        return

    brightness     = vol_photo / 65535 * 100
    brightness_pot = vol_pot   / 65535 * 100
    width_bar      = 1 + int(brightness     * 125 / 100)
    width_bar_pot  = 1 + int(brightness_pot * 125 / 100)

    OLED.fill(0)

    OLED.text("Brightness", 1, 5, 15)
    OLED.text("{0:.2f} %".format(brightness), 1, 20, 15)
    OLED.rect(0, 50, 127, 30, 15)
    OLED.rect(1, 51, width_bar, 28, 6, True)

    OLED.text("Pot", 1, 88, 15)
    OLED.text("{0:.2f} %".format(brightness_pot), 1, 100, 15)
    OLED.rect(0, 112, 127, 14, 15)
    OLED.rect(1, 113, width_bar_pot, 12, 6, True)

    OLED.show()
    sleep(0.1)

while True:
    tasks()