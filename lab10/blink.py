from machine import Pin, I2C, SoftI2C
from OLED_1inch5 import OLED_1inch5
from QMI8658 import QMI8658
from time import sleep

OLED_ADDR = 0x3d
QMI8658_ADDR = 0x6b

OLED_i2c = SoftI2C(sda=Pin(6), scl=Pin(7), freq=1_000_000)
sleep(0.1)
Sensors_i2c = I2C(id=0, sda=Pin(8), scl=Pin(9), freq=100_000)
sleep(0.1)

OLED = OLED_1inch5(OLED_ADDR, OLED_i2c)
qmi8658 = QMI8658(Sensors_i2c, QMI8658_ADDR)

while True:
    xyz = qmi8658.Read_XYZ()
    OLED.fill(0)
    OLED.text("ACC_X={:+.2f}".format(xyz[0]),1, 5,15)
    OLED.text("ACC_Y={:+.2f}".format(xyz[1]),1,15,15)
    OLED.text("ACC_Z={:+.2f}".format(xyz[2]),1,25,15)
    OLED.text("GYR_X={:+3.2f}".format(xyz[3]),1,45,15)
    OLED.text("GYR_Y={:+3.2f}".format(xyz[4]),1,55,15)
    OLED.text("GYR_Z={:+3.2f}".format(xyz[5]),1,65,15)
    OLED.show()
    print("ACC_X={:+.2f} ACC_Y={:+.2f}ACC_Z={:+.2f}".
    format(xyz[0],xyz[1],xyz[2]))
    print("GYR_X={:+3.2f} GYR_Y={:+3.2f} GYR_Z={:+3.2f} \r\n".
    format(xyz[3],xyz[4],xyz[5]))
    sleep(0.5)