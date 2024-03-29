#!/usr/bin/env python
# -*- coding: latin-1 -*-
# Test program for the Adafruit Plate
# $Id: test_ada_lcd.py,v 1.3 2013/07/01 12:04:11 bob Exp $
#

import atexit
from time import sleep
from ada_lcd_class import Adafruit_lcd

lcd = Adafruit_lcd()

def interrupt():
	return False

def finish():
	lcd.clear()
	lcd.line1("Finished") 

atexit.register(finish)
lcd.setWidth(16)
lcd.line1("Test Adafruit")
lcd.scroll2("Line 2: abcdefghijklmnopqrstuvwxyz 0123456789",interrupt) 
lcd.line1("Try buttons")

while True:
	if lcd.buttonPressed(lcd.MENU):
		print("Menu button")
		lcd.line2("Menu button")
	elif lcd.buttonPressed(lcd.LEFT):
		print("Left button")
		lcd.line2("Left button")
	elif lcd.buttonPressed(lcd.RIGHT):
		print("Right button")
		lcd.line2("Right button")
	elif lcd.buttonPressed(lcd.UP):
		print("Up button")
		lcd.line2("Up button")
	elif lcd.buttonPressed(lcd.DOWN):
		print("Down button")
		lcd.line2("Down button")
	
