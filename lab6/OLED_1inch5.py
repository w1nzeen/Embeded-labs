# MicroPython SSD1327 OLED driver, I2C interface

import framebuf
import time

class OLED_1inch5(framebuf.FrameBuffer):
    def __init__(self, olde_addr, i2c):
        
        self.width  = 128
        self.height = 128
        
        self.rotate = 180 #only 0 and 180

        self.olde_addr = olde_addr

        self.i2c = i2c
        
        self.temp = bytearray(2)
        self.buffer = bytearray(self.height * self.width//2)

        super().__init__(self.buffer, self.width, self.height, framebuf.GS4_HMSB)
        self.init_display()
        
        self.white =   0xf
        self.balck =   0x0000
        
    def write_cmd(self, cmd):
        self.temp[0] = 0x00 
        self.temp[1] = cmd
        self.i2c.writeto(self.olde_addr, self.temp)

    def write_data(self, buf):
        self.i2c.writeto(self.olde_addr, b'\x40'+buf)
        
    def init_display(self):
        """Initialize dispaly"""  
        
        self.write_cmd(0xae)     #--turn off oled panel

        self.write_cmd(0x15)     #  set column address
        self.write_cmd(0x00)     #  start column   0
        self.write_cmd(0x7f)     #  end column   127

        self.write_cmd(0x75)     #   set row address
        self.write_cmd(0x00)     #  start row   0
        self.write_cmd(0x7f)     #  end row   127

        self.write_cmd(0x81)     # set contrast control
        self.write_cmd(0x80) 

        self.write_cmd(0xa0)     # gment remap
        self.write_cmd(0x51)     #51

        self.write_cmd(0xa1)     # start line
        self.write_cmd(0x00) 

        self.write_cmd(0xa2)     # display offset
        self.write_cmd(0x00) 

        self.write_cmd(0xa4)     # rmal display
        self.write_cmd(0xa8)     # set multiplex ratio
        self.write_cmd(0x7f) 

        self.write_cmd(0xb1)     # set phase leghth
        self.write_cmd(0xf1) 

        self.write_cmd(0xb3)     # set dclk
        self.write_cmd(0x00)     #80Hz:0xc1 90Hz:0xe1   100Hz:0x00   110Hz:0x30 120Hz:0x50   130Hz:0x70     01
 
        self.write_cmd(0xab)     #
        self.write_cmd(0x01)     #

        self.write_cmd(0xb6)     # set phase leghth
        self.write_cmd(0x0f) 

        self.write_cmd(0xbe) 
        self.write_cmd(0x0f) 

        self.write_cmd(0xbc) 
        self.write_cmd(0x08) 

        self.write_cmd(0xd5) 
        self.write_cmd(0x62) 

        self.write_cmd(0xfd) 
        self.write_cmd(0x12) 

        time.sleep(0.1)
        self.write_cmd(0xAF)    #--turn on oled panel
        
    def setwindows(self, Xstart, Ystart, Xend, Yend):
        if((Xstart > self.width) or (Ystart > self.height) or (Xend > self.width) or (Yend > self.height)):
            return
        self.write_cmd(0x15)
        self.write_cmd(Xstart//2)
        self.write_cmd(Xend//2 - 1)

        self.write_cmd(0x75)
        self.write_cmd(Ystart)
        self.write_cmd(Yend - 1)
        
    def show(self):
        self.setwindows(0, 0, 128, 128)
        self.write_data(self.buffer)
        # for i in range(0, self.height):
        #     for j in range(0, self.width//2):
        #             self.write_data(self.buffer[j+self.width//2*i])
        return
