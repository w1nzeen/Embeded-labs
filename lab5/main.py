from machine import Pin, SoftI2C
from OLED_1inch5 import OLED_1inch5
from time import sleep

from pixel_font import draw_text, text_width, CHAR_H, SCALE # КАСТОМНА БІБЛІОТЕКА, якщо не використовуєте піксельні шрифти видаліть


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
    OLED.hline(19, 11, 93, 15) # Формат x, y, weight, colour
    OLED.show()
    sleep(1)
    OLED.vline(111, 12, 51, 15) # Формат x, y, height, colour
    OLED.show()
    sleep(1)
    OLED.line(111, 62, 19, 12, 15) # Формат x, y, x2, y2, colour
    OLED.show()
    sleep(1)
    OLED.rect(21, 45, 44, 15, 15) # Формат x, y, weight, height, colour, True/False= Filled not Filled
    OLED.show()
    sleep(1)
    OLED.rect(21, 65, 44, 13, 15, True) # Формат x, y, weight, height, colour, True/False= Filled not Filled
    OLED.show()
    sleep(3)



'''Третя таска "Анімація" '''
def task3():
    pass 

    MESSAGE    = "Smarahdove Nebo Chekaye Na Zavtra! "
    SPEED      = 3       # пікселів за кадр
    DELAY      = 0.01    # затримка між кадрами
 
    text_w     = text_width(MESSAGE)
    full_cycle = 128 + text_w
    y0         = (128 - CHAR_H * SCALE) // 2
 
    offset = 0
    while True:
        OLED.fill(0)
        draw_text(OLED, MESSAGE, x=128 - offset, y=y0)
        OLED.show()
        offset = (offset + SPEED) % full_cycle
        sleep(DELAY)
 
'''Основний цикл (Щоб показати якусь одну таску коментуйте інші(ctrl + / або command + /), або робіть маніпуляції через кнопку)'''
while True:
    task1()
    task2()
    task3()