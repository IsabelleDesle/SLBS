# LIBRARIES 
######################################


import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)

# to get the text from the linux command 
import subprocess

# to create I2C objects 
import smbus

# for the bluetooth connection
import sys
import dbus, dbus.mainloop.glib
#import bluetooth_uart_server
import threading
import queue

class LCD:
        def __init__(self, LCD_WIDTH =  16, 
                     LCD_CHR = 1, 
                     LCD_CMD = 0, 
                     LCD_LINE_1 = 0x80 | 0x0, # 0b10000000 | 0b00000000
                     LCD_LINE_2 = 0x80 | 0x40, # 0b10000000 | 0b01000000
                     LCD_BACKLIGHT = 0x08, #0b0000_1000
                     ENABLE_HIGH = 0x4, #0b0000_0100
                     ENABLE_LOW = 0xfb, #0b1111_1011,
                     E_PULSE = 0.0002,
                     E_DELAY = 0.0002,
                     i2c_LCD = smbus.SMBus(1),
                     i2C_address_LCD = 0x27): #0x27 is the address of the LCD, check with i2cdetect -y 1

                self.LCD_WIDTH = LCD_WIDTH
                self.LCD_CHR = LCD_CHR
                self.LCD_CMD= LCD_CMD
                self.LCD_LINE_1 = LCD_LINE_1
                self.LCD_LINE_2 = LCD_LINE_2
                self.LCD_BACKLIGHT = LCD_BACKLIGHT
                self.ENABLE_HIGH = ENABLE_HIGH
                self.ENABLE_LOW = ENABLE_LOW
                self.E_PULSE = E_PULSE
                self.E_DELAY = E_DELAY
                self.i2c_LCD = i2c_LCD
                self.i2C_address_LCD = i2C_address_LCD  
                
        def lcd_init(self):
                self.send_byte_with_e_toggle(0b0011_0000) # 8 bit mode
                self.send_byte_with_e_toggle(0b0011_0000) # again to set it on 8 bit if it was on 4 bit already 
                self.send_byte_with_e_toggle(0b0010_0000) # now set in 4 bit 

                self.send_instruction(0x06) #000110 cursor move direction
                self.send_instruction(0x0C) #001100 display on, cursor off, blink off
                self.send_instruction(0x28) #101000 data length, number of lines, font size
                self.clear()
                sleep(self.E_DELAY)

        def clear(self):
                self.send_instruction(0x01) # 000001 clear display
                sleep(self.E_DELAY)

    # toggling on and off will be needed to send bits to the LCD
        def send_byte_with_e_toggle(self,bits):
                sleep(self.E_DELAY)
                # write data to i2c with E bit HIGH - toggle enable on
                self.i2c_LCD.write_byte(self.i2C_address_LCD, (bits | self.ENABLE_HIGH))
                sleep(self.E_PULSE)
                # write data to i2c with E bit LOW ) tobble enable off
                self.i2c_LCD.write_byte(self.i2C_address_LCD , (bits | self.ENABLE_LOW))
                sleep(self.E_DELAY)

    # add mode and backlight parameters to send 
        def set_data_bits(self,bits, mode): # mode: char of cmd
                bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
                bits_low = mode | ((bits<<4) & 0xF0) | self.LCD_BACKLIGHT
                self.send_byte_with_e_toggle(bits_high)
                self.send_byte_with_e_toggle(bits_low)

        # a function to send commands : mode command  
        def send_instruction(self,byte):
                self.set_data_bits(byte, self.LCD_CMD)
                sleep(0.01)

        # another function to send data : mode character
        def send_character(self,byte):
                self.set_data_bits(byte, self.LCD_CHR)
                sleep(0.01)
  
    # send string to LCD in 3 steps :
    #1/ add empty spaces to the string
    #2/ send command concerning the position on LCD 
    #3/ send string bit by bit in ascii format
        def send_string(self, string, line):
                
                string = str(string)
                string = string.ljust(self.LCD_WIDTH, " ")
                self.send_instruction(line)
                for i in range(self.LCD_WIDTH):
                        # set_data_bits(ord(string[i]), LCD_CHR)
                        # sleep(0.01)
                        self.send_character(ord(string[i])) #function send_character instead of set_data_bits. 

        
        #to split messages in 2 lines and send to lcd
        def split_and_send_lines(self, message):
                if len(message) > 16:
                        text01 = message[0:16]
                        text02 = message[16:]
                else:
                        text01 = message[0:16]
                        text02 = ""

                self.send_string(text01, self.LCD_LINE_1)
                self.send_string(text02, self.LCD_LINE_2)
                sleep(0.5)


        # 4/ GATT UART 
        #to split messages in 2 lines and send to lcd
        def send_uart_message(self, message):
                if len(message) > 16:
                        text05_01 = message[0:16]
                        text05_02 = message[16:]
                else:
                        text05_01 = message[0:16]
                        text05_02 = ""

                self.send_string(text05_01, self.LCD_LINE_1)
                self.send_string(text05_02, self.LCD_LINE_2)
                sleep(0.5)