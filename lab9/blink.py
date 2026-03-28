from machine import Pin, I2C, SoftI2C
from OLED_1inch5 import OLED_1inch5
from SHTC3 import SHTC3
from VOC_SGP40 import SGP40
from VOC_Algorithm import VOC_Algorithm
from time import sleep

OLED_ADDR = 0x3d
SHTC3_ADDR = 0x70
VOC_ADDR = 0x59

OLED_i2c = SoftI2C(sda=Pin(6), scl=Pin(7), freq=1_000_000)
sleep(0.1)
Sensors_i2c = I2C(id=0, sda=Pin(8), scl=Pin(9), freq=100_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, OLED_i2c)
sthc3 = SHTC3(Sensors_i2c, SHTC3_ADDR)
sthc3.wakeup()
sgp = SGP40(Sensors_i2c, VOC_ADDR)
VOC = VOC_Algorithm()

while True:
    raw = sgp.measureRaw(25, 50)
    Voc = VOC.VocAlgorithm_process(raw)
    OLED.fill(0)
    OLED.text("Raw Gas = {}".format(raw),1,5,15)
    OLED.text("Voc = {}".format(Voc),1,15,15)
    OLED.show()
    sleep(0.3)
