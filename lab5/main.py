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

''' Кінець налаштувань :) Далі все за вами!'''


'''Перша таска "Вивід тексту" '''
def task1():
    OLED.fill(0)
    OLED.text("SMARAHDOVE  NEBO",1,5,OLED.white)
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

'''Друга таска "Вивід лінії, фігури" '''
def task2():
    OLED.fill(0)
    OLED.hline(19, 11, 93, 15)
    OLED.show()
    sleep(1)
    OLED.vline(111, 12, 51, 15)
    OLED.show()
    sleep(1)
    OLED.line(111, 62, 19, 12, 15) # Формат x, y, x2, y2, colour
    OLED.show()
    sleep(1)
    OLED.rect(21, 45, 44, 15, 15)
    OLED.show()
    sleep(1)
    OLED.rect(21, 65, 44, 13, 15, True)
    OLED.show()
    sleep(3)



'''Третя таска "Анімація" '''
def task3():
    pass


'''Основний цикл'''
while True:
    task1()
    task2()
    task3()