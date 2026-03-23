from machine import Pin, ADC, SoftI2C
from time import sleep

from OLED_1inch5 import OLED_1inch5

i2c_num = 1
sda_pin = Pin(6)
scl_pin = Pin(7)

WIDTH = 128
HEIGHT = 128
OLED_ADDR = 0x3d

sound_sensor = ADC(Pin(28))
i2c = SoftI2C(scl = scl_pin, sda = sda_pin, freq=1_000_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, i2c)
column_hights =[]

while True:
    vol = sound_sensor.read_u16()
    sound = vol/65535*100

    column_hight =int(sound)
    column_hights.append(column_hight)
    if len(column_hights)>64:
        del column_hights[0]

    OLED.fill(0)
    OLED.text("Sound = {0:.2f} %".format(sound),1,5,15)
    i=0
    for ch in column_hights:
        OLED.line(i,127,i,127-ch,15)
        OLED.line(i+1,127,i+1,127-ch,1)
        i=i+2
    OLED.show()
    sleep(0.1)