#!/usr/bin/env python3

# Copyright 2023 Leigh L. Klotz, Jr. https://github.com/wa5znu
# This project is licensed under the MIT License - see the LICENSE file for details.
# 
# This MicroPython script is for the rp2040-lcd-1.28 and SymRFT60 or similar WWVB receiver.
# This script will draw a circle around the center of the display,
# with each 6-degree segment colored white. The segments that are 1 or 2
# in the samples array will be drawn closer to the center, while the
# segments that are 0 will be drawn at the edge. Invalid samples are drawn
# at 4, closest to the center.

import micropython
micropython.alloc_emergency_exception_buf(100)

from micropython import const
import random
import time
from machine import Pin, SPI
import gc9a01
import math

import vga1_bold_16x32 as FONT

class SymRFT60:
    output_min = const(1)
    output_max = const(3)
    n_samples = const(1000)
    guard = const(100)

    def __init__(self, pin):      
        self.pin = pin
        self.buffer = bytearray(60)

    def get_next_sample(self):
        # Simulate a 1kHz sample rate as best we can
        # this takes 1000ms so the rest better run quickly!
        total = 0.0
        for i in range(n_samples):
            sensor_value = (1-self.pin.value())
            total += sensor_value
            time.sleep(0.001)
        # Bin the value into 0, 1, 2, or error (4)
        # by using ideal +/- guard and discarding outside those ranges
        # error can be due to noise or due to phase misalignment
        # how can we detect and so we can lock onto phase?
        if   (200 - guard) <= total <= (200 + guard):
            r = 0
        elif (500 - guard) <= total <= (500 + guard):
            r = 1
        elif (800 - guard) <= total <= (800 + guard):
            r = 2
        else:
            r = 4 # error
        print(f"{total=} {r=}")
        return r

class Sampler:
    def __init__(self):
        self.samples = SAMPLES
        self.minutes = 0
        self.seconds = 0

    def get_next_sample(self):
        sample = self.samples[self.minutes][1][self.seconds]
        self.seconds += 1
        if (self.seconds == 60):
            self.minutes = (self.minutes + 1) % len(self.samples)
            self.seconds = 0
        return sample

class ClockDisplay:
    def __init__(self, rx, spi, width, height, reset_pin, cs_pin, dc_pin, backlight_pin, rotation=0):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset_pin = reset_pin
        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.backlight_pin = backlight_pin
        self.rotation = rotation
        self.init_display()
        self.rx = rx

    def init_display(self):
        print("init_display")
        self.tft = gc9a01.GC9A01(
            self.spi,
            self.width,
            self.height,
            reset=Pin(self.reset_pin, Pin.OUT),
            cs=Pin(self.cs_pin, Pin.OUT),
            dc=Pin(self.dc_pin, Pin.OUT),
            backlight=Pin(self.backlight_pin, Pin.OUT),
            rotation=self.rotation)
        
        print("tft.init")
        self.tft.init()
        self.center_x = self.tft.width() // 2
        self.center_y = self.tft.height() // 2
        self.radius = self.center_x
        self.tft.fill(0)
        self.last_x2 = None
        self.last_y2 = None
        self.last_color = None
        self.previous_time = [-1] * 6
        print("init_display done")

    def draw_time(self, current_time):
        time_string = "{:02}:{:02}:{:02}".format(current_time[3], current_time[4], current_time[5])
        print(f"{time_string}")
        slen = len(time_string) * 16
        center_x = (self.tft.width() - slen) // 2
        center_y = self.tft.height() // 2 - 16
        self.tft.text(FONT, time_string, center_x, center_y, gc9a01.RED)

    def draw_sample(self, s):
        bit_string = str(s)
        slen = len(bit_string) * 16
        center_x = (self.tft.width() - slen) // 2
        center_y = self.tft.height() // 2 - 40
        self.tft.text(FONT, bit_string, center_x, center_y, gc9a01.RED)

    def calculate_arc_segment(self, secs, r):
        angle1 = math.radians((secs * 6) - 90)
        angle2 = math.radians(((secs + 1) * 6) - 90)
        # Calculate the x and y coordinates
        x1 = self.center_x + int(math.cos(angle1) * r)
        y1 = self.center_y + int(math.sin(angle1) * r)
        x2 = self.center_x + int(math.cos(angle2) * r)
        y2 = self.center_y + int(math.sin(angle2) * r)
        return (x1, y1, x2, y2)

    def calculate_r(self, s):
        return (self.radius - 1 - 16*int(s))

    def calculate_color(self, s, secs):
        if secs % 2 == 0:
            return gc9a01.GREEN
        else:
            return gc9a01.RED

    def update_display(self):
        while True:
            # Get the current time
            current_time = time.localtime()

            if current_time[5] != self.previous_time[5]:
                secs = current_time[5]
                mins = current_time[4]

                if secs == 0:
                    self.tft.fill(0)

                self.draw_time(current_time)
                self.previous_time = current_time

                # Get the WWVB Sample
                s = int(self.rx.get_next_sample())
                self.draw_sample(s)
                print(f"{s=}")
                
                # Calculate the arc segments and lines
                r = self.calculate_r(s)
                color = self.calculate_color(s, secs)
                (x1, y1, x2, y2) = self.calculate_arc_segment(secs, r)
                # Draw the radial line segment from the last point end to this point start
                if self.last_color:
                    self.tft.line(self.last_x2, self.last_y2, x1, y1, self.last_color)
                # Draw the circular arc segment approximation
                self.tft.line(x1, y1, x2, y2, color)
                #print(f"circular arc_segment {secs=} {r=} => {x1=} {y1=} {x2=} {y2=}\n")

                # Update last
                self.last_x2 = x2
                self.last_y2 = y2
                self.last_color = color

def main():
    print("Clockish - WA5ZNU github/wa5znu")
    # Initialize the Sym-RFT-60 WWVB Receiver input pin
    # not all GPIO pins support ADC:
    # - GPIO26-28 are available to use with ADC.
    # - GPIO29 is half battery voltage, for testing
    rx = SymRFT60(pin=Pin(26, Pin.IN))
    #sampler = Sampler()
    # Initialize the SPI and the GC9A01 display
    spi = SPI(1, baudrate=6000000, sck=Pin(10, Pin.IN), mosi=Pin(11))
    clock_display = ClockDisplay(rx, spi, 240, 240, 12, 9, 8, 25)
    clock_display.update_display()

main()
