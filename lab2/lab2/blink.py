from machine import Pin, Timer
import time

button = Pin(3, Pin.IN, Pin.PULL_UP)
led1 = Pin(10, Pin.OUT)
led2 = Pin("LED", Pin.OUT)

timer1=Timer(-1)
timer2=Timer(-1)
counter = 0
debounce_time=0
interrupt_flag=0

def callback(pin):
    global interrupt_flag, debounce_time, counter
    if(time.ticks_diff(time.ticks_ms(), debounce_time)) > 50:
        interrupt_flag = 1
        counter+=1
        debounce_time = time.ticks_ms() 

def reload():
    global counter
    if(counter>5):
        counter = 0

button.irq(trigger=Pin.IRQ_FALLING, handler=callback)

def blink_led(led_pin):
    led_pin.toggle()

while True:
    if(interrupt_flag == 1):
        interrupt_flag = 0
        
        reload()

        if (counter == 1):
           timer1.init(mode=Timer.PERIODIC, period=1000, callback=lambda t: blink_led(led1))
           timer2.init(mode=Timer.PERIODIC, period=1000, callback=lambda t: blink_led(led2))
        elif (counter == 2):
           timer1.init(mode=Timer.PERIODIC, period=300, callback=lambda t: blink_led(led1))
           timer2.init(mode=Timer.PERIODIC, period=1000, callback=lambda t: blink_led(led2))
        elif (counter == 3):
           timer1.init(mode=Timer.PERIODIC, period=2000, callback=lambda t: blink_led(led1))
           timer2.init(mode=Timer.PERIODIC, period=1000, callback=lambda t: blink_led(led2))
        elif (counter == 4):
           timer1.init(mode=Timer.PERIODIC, period=200, callback=lambda t: blink_led(led1))
           timer2.init(mode=Timer.PERIODIC, period=500, callback=lambda t: blink_led(led2))
        elif (counter == 5):
           timer1.init(mode=Timer.PERIODIC, period=3000, callback=lambda t: blink_led(led1))
           timer2.init(mode=Timer.PERIODIC, period=1000, callback=lambda t: blink_led(led2))
        elif (counter == 0):
         timer1.deinit()
         timer2.deinit()
         led1.off
         led2.value(0)