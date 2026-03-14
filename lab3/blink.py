# Потенціометр

from machine import Pin, PWM, ADC
import time

potetiometer = ADC(27)
led = PWM(Pin(10))
led.freq(1000)

while True:
    digital_value = potetiometer.read_u16()
    led.duty_u16(digital_value)
    time.sleep_ms(10)


# Кнопка 

# from machine import Pin, PWM
# import time

# led = PWM(Pin(10))
# led.freq(1000)
# button = Pin(3, Pin.IN, Pin.PULL_UP)

# brightness_level = [0, 8192, 32768, 65535]
# counter = 0
# last_state = 0
# debounce_time = 0
# interrupt_flag = 0

# def callback(pin):

#     global interrupt_flag, debounce_time

#     if(time.ticks_diff(time.ticks_ms(), debounce_time)) > 150:

#         interrupt_flag = 1

#         debounce_time = time.ticks_ms()

# button.irq(trigger=Pin.IRQ_FALLING, handler=callback)

# while True:
#     if (interrupt_flag == 1):

#         interrupt_flag = 0
#         counter = (counter + 1) % len(brightness_level)
#         new_duty = brightness_level[counter]

#         led.duty_u16(new_duty)
#         time.sleep_ms(10)






# Фоторезистор

# from machine import Pin, PWM, ADC
# import time

# led = PWM(Pin(10))
# led.freq(1000)
# photoresistor = ADC(26)


# while True:
#     digital_value = photoresistor.read_u16()
#     new_duty = 65535 - digital_value
#     led.duty_u16(new_duty)
#     time.sleep_ms(10)