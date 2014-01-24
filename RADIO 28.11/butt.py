#!/usr/bin/env python
import os 
import RPi.GPIO as GPIO 
import signal 
import subprocess 
import sys 
import time 
import string 
import datetime 
from time import strftime 
from radio_class import Radio
from lcd_class import Lcd
import shutil
import urllib
from xml.dom import minidom
from time import strftime
CITY_ID = '877873'

TEMP_TYPE = 'c'
WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?w=' + CITY_ID +' &u=c'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'

def interrupt():
        return False

MENU_SWITCH = 25 
LEFT_SWITCH = 14 
RIGHT_SWITCH = 15 
UP_SWITCH = 18 
DOWN_SWITCH = 17 
MERGE=0
#merge radioul
UP = 0 
DOWN = 1 
from lcd_class import Lcd 
lcd = Lcd() 
GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers 
GPIO.setup(MENU_SWITCH, GPIO.IN) 
GPIO.setup(UP_SWITCH, GPIO.IN) 
GPIO.setup(DOWN_SWITCH, GPIO.IN) 
GPIO.setup(LEFT_SWITCH, GPIO.IN) 
GPIO.setup(RIGHT_SWITCH, GPIO.IN) 

radiolist = open('radiolist', 'r')
line = radiolist.readline()
radio =[]
text_line1 = ""
text_line2 = ""
text_line1_old = ""
text_line2_old=""
while line:
	temp = line.split('&')
		
	radio.append((temp[0], temp[1].strip('\n')))
#	key +=1
	line = radiolist.readline()
host =""
for i in range (0,len(radio)):
	host = host + " "+str(radio[i][0]) 
#print host
#aici scot playlistul si descrierea posturilor
station = open('station','r')
current = int(station.readline())
warp = len(radio)
print current
print warp
radiolist.close()
station.close()


volum = open('volume','r')
vol = int(volum.readline())
volum.close()
print vol
#aici incarc ultimele setari

time_stamp = time.time()
time_now = time_stamp
def exec_cmd(cmd): 
	p = os.popen(cmd)
	result = ""
	while p.readline():
	        result = result + p.readline()
#.rstrip('\n')
        return result

number = 0
lcd.init() 
todaysdate = strftime("%H:%M %d/%m/%Y") 
ipaddr = exec_cmd('hostname -I') 
text_line1= str(todaysdate)
lcd.line1(text_line1)
text_line2 = ipaddr 
lcd.line2(text_line2) 


def switch_event_menu(p):
#	time.sleep(0.4)
        GPIO.remove_event_detect(p)
	global MERGE
	global radio, time_stamp
	global host
	global current, warp
	global vol
	global text_line1, text_line2, text_line1_old, text_line2_old
        time_now = time.time()
#        print time_now-time_stamp
        if (time_now - time_stamp) >= 0.8:
		if GPIO.input(MENU_SWITCH):

			if MERGE == 0:
				exec_cmd('su - pi -c "vlc '+host+' -I rc --rc-host 127.0.0.1:4222 --novideo -d && ls"')
#porneste radioul cu lista de statii
				MERGE = 1
				time.sleep(1)
				string = ('echo "gotoitem '+ str(current)+'" | netcat 127.0.0.1 4222 ')
#			print string
				exec_cmd(string)
				string2 = ('echo "volume ' + str(vol)+ '" |netcat 127.0.0.1 4222 ')
				print string2
				exec_cmd(string2)
				index = 4+warp-current
                	        text_line2=(str(radio[index-1][1]))				
				lcd.line2(text_line2)
			else:
				print "else"
				string =  ('echo "shutdown" | netcat 127.0.0.1 4222 ')
				print string
				exec_cmd(string)
				time.sleep(1)
				MERGE=0
				lcd.init()
#				sys.exit(0)
		#	return 
#oprire, return to os
        time_stamp = time_now+0.3
	GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
	return 
def switch_event_up(p):
        GPIO.remove_event_detect(p)
       # print "unu"
        global text_line1, text_line2, text_line1_old, text_line2_old
        global current, warp
        global MERGE, vol
        global time_stamp
        time_now = time.time()
#        print time_now-time_stamp
        if (time_now - time_stamp) >= 0.8:
                if MERGE ==1:
                        while GPIO.input(p):                        
                	        exec_cmd ('echo "volume +10"|netcat 127.0.0.1 4222')
	
	        	        vol = vol +10
				lcd.line2("Volume "+str(vol))
                	        time.sleep(0.2)
                        volum = open('volume','w')
                        volum.write(str(vol))
                        volum.close() 

        time_stamp = time_now+0.3
        GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_up, bouncetime=500)
        return
#volume up =10 (cat timp e apasat butonul)


def switch_event_down(p):
        GPIO.remove_event_detect(p)
#        print "unu"
        global text_line1, text_line2, text_line1_old, text_line2_old
        global current, warp
        global MERGE, vol
        global time_stamp
        time_now = time.time()
#        print time_now-time_stamp
        if (time_now - time_stamp) >= 0.8:
                if MERGE ==1:
			while GPIO.input(p):                        
				exec_cmd ('echo "volume -10"|netcat 127.0.0.1 4222')
	        	        vol = vol -10
				lcd.line2("Volume "+str(vol))
				time.sleep(0.2)
			volum = open('volume','w')
		        volum.write(str(vol))
		        volum.close()                

#	print vol
        time_stamp = time_now+0.3
        GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_down, bouncetime=500)
        return
#volume down -10 (cat timp e apasat butonul)

def switch_event_next(p):
        GPIO.remove_event_detect(p)

#        print "unu"
        global text_line1, text_line2, text_line1_old, text_line2_old
        global current, warp
        global MERGE
        global time_stamp
        time_now = time.time()
#        print time_now-time_stamp
        if (time_now - time_stamp) >= 0.8:
                if MERGE ==1:
                        exec_cmd ('echo "next"|netcat 127.0.0.1 4222')
        #               print current
                        temp = current -5
                        current = (temp%warp)+4
                        index = 4+warp-current
#                       print index
                        lcd.line2(str(radio[index-1][1])) 
       #               print current
                        station = open('station','w')
                        station.write(str(current))
                        station.close()

        time_stamp = time_now+0.3
        GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_next, bouncetime=500)
        return
#next station (cat timp e apasat butonul)

def switch_event_prev(p):
	GPIO.remove_event_detect(p)
#	print "unu"
        global text_line1, text_line2, text_line1_old, text_line2_old
	global current, warp
        global MERGE, radio
	global time_stamp
	time_now = time.time()
#	print time_now-time_stamp
	if (time_now - time_stamp) >= 0.8: 
	        if MERGE ==1:
      		        exec_cmd ('echo "prev"|netcat 127.0.0.1 4222')
	#		print current
		        temp = current -3
		        current = (temp%warp)+4
			index = 4+warp-current
			text_line2=str(radio[index-1][1])
			lcd.line2(text_line2)
	#	        print current
		        station = open('station','w')
		        station.write(str(current))
		        station.close()

	time_stamp = time_now+0.3	
	GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_prev, bouncetime=500)
        return
#previous station (cat timp e apasat butonul)


GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event_down, bouncetime=500) 
GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event_up, bouncetime=500)
GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event_next, bouncetime=500)
GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event_prev, bouncetime=500)

while True:
#	todaysdate = strftime("%H:%M")
#	time_now = time.time()
#       print time_now-time_stamp
#        if (time_now - time_stamp) >= 5:
#		text_line2 = text_line2_old
#		lcd.line2(text_line2)
#		time_stamp=time_now





#	lcd.line1(str(todaysdate))
#	number +=1
#	time.sleep (1)
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
#       print "Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high'))
        time.sleep(3)
        lcd.line2(str(node.getAttribute('text')))
        time.sleep(3)
        lcd.line1("")
        lcd.line2(str(todaysdate))
        time.sleep(3)
        i+=1
