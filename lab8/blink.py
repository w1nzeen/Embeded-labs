from machine import Pin, SoftI2C, I2C # type: ignore
from OLED_1inch5 import OLED_1inch5
from shtc3 import SHTC3
from time import sleep

WIDTH = 128
HEIGHT = 128

OLED_ADDR =0x3d
SHTC3_ADDR = 0x70

OLED_i2c = SoftI2C(sda = Pin(6), scl = Pin(7), freq = 1_000_000)
sleep(0.1)
SHTC3_i2c = I2C(id = 0, sda = Pin(8), scl = Pin(9), freq = 100_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, OLED_i2c)
shtc3 = SHTC3(SHTC3_i2c, SHTC3_ADDR)
shtc3.wakeup()

while True:
    T,RH = shtc3.measurement(0,0,0)
    OLED.fill(0)
    OLED.text("T = {:.2f}C".format(T),1,5,15)
    OLED.text("RH = {:.2f}%".format(RH),1,15,15)
    OLED.show()
    sleep(0.5)
