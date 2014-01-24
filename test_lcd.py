#!/usr/bin/env python
#
# $Id: test_lcd.py,v 1.5 2013/07/01 11:51:20 bob Exp $

from radio_class import Radio
from lcd_class import Lcd
import shutil
import urllib
from xml.dom import minidom
import time
from time import strftime
CITY_ID = '877873'
#ploiesti
TEMP_TYPE = 'c'
WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?w=' + CITY_ID +' &u=c'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'


def interrupt():
        return False
lcd = Lcd()
lcd.init()
lcd.setWidth(16)

while True:
    dom = minidom.parse(urllib.urlopen(WEATHER_URL))
    ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
    present = ycondition.getAttribute('text')
    temp =  ycondition.getAttribute('temp')
    forecasts = ""
    lcd.line1("Now we have "+ str(temp)+"C")
    lcd.line2(str(present))
    time.sleep(4)
#    lcd.line2(str(node.getAttribute('text')))
#    time.sleep(1)
    lcd.init()


    i=0
    while i<3:
        node = dom.getElementsByTagNameNS(WEATHER_NS, 'forecast')[i]
#        forecasts=str(node.getAttribute('date'))+'  Low  '+str(node.getAttribute('low'))+'  High  '+str(node.getAttribute('high'))+'  '+str(node.getAttribute('text'))+'  '
#        lista ='Ploiesti - '+ present+' Current Temperature: '+temp+' C' + ' Forecasts: '+forecasts
        todaysdate = strftime("%H:%M %d/%m/%Y")
#        lcd.scroll1("Prognoza Meteo"+" -- "+(str(todaysdate)), interrupt)
#        lcd.scroll2(str(lista),interrupt)
        
        lcd.line1("Meteo " +str(node.getAttribute('date')))
        lcd.line2("Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high')))
#        print "Meteo  " +str(node.getAttribute('date'))
#	print "Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high'))
        time.sleep(3)
	lcd.line2(str(node.getAttribute('text')))
        time.sleep(3)
        lcd.line1("")
        lcd.line2(str(todaysdate))
        time.sleep(3)
        i+=1

#start = time.time()
#while n>=0:
#        lcd.scroll2(str(lista),interrupt) 
#	print time.time()-start
#	start = time.time()
#	n=n-1
#lcd.init()


