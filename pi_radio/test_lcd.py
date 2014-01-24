#!/usr/bin/env python
#
# $Id: test_lcd.py,v 1.5 2013/07/01 11:51:20 bob Exp $

from radio_class import Radio
from lcd_class import Lcd

lcd = Lcd()

def interrupt():
        return False

lcd.init()
lcd.setWidth(16)
lcd.line1("Bob Rathbone")

while True:
        lcd.scroll2("Line 2: abcdefghijklmnopqrstuvwxyz 0123456789",interrupt) 



