from machine import Pin, SoftI2C
from OLED_1inch5 import OLED_1inch5
from time import sleep

i2c_num = 1
sda_num = Pin(6)
scl_num = Pin(7)

'''' УВАГА! Не змінювати стандартні налаштування дисплею 128x128'''

WIDTH = 128
HEIGHT = 128


OLED_ADDR = 0x3d  ###Aдреса дисплею на I2C шині


i2c = SoftI2C(scl =scl_num, sda = sda_num, freq = 1_000_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, i2c)

def task1():
    OLED.fill(0)
    OLED.text("SMARAHDOVE NEBO",1,5,OLED.white)
    OLED.show()
    sleep(1)
    OLED.text("CHEKAYE NA ZAVTRA",1,20,OLED.white)
    OLED.show()
    sleep(2)
    OLED.text("YA IDU DO TEBE",1,35,OLED.white)
    OLED.show()
    sleep(1)
    OLED.text("YA IDU NAZAD",1,50,OLED.white)
    OLED.show()
    sleep(3)


# OLED.pixel(100,100,15)

# OLED.line(0,0,127,0,1)
# OLED.hline(0,64,128,1)
# OLED.vline(64,0,128,1)

# OLED.rect(0, 80,127,90, 8)
# OLED.rect(0, 90,127,100, 10, True)

# OLED.show()

while True:
    task1()