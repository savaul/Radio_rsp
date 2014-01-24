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
MENU_SWITCH = 25 
LEFT_SWITCH = 14 
RIGHT_SWITCH = 15 
UP_SWITCH = 17 
DOWN_SWITCH = 18 
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
lcd.line1(str(todaysdate)) 
lcd.line2(ipaddr) 


def switch_event_menu(p):
	time.sleep(0.4)

	global MERGE
	global radio
	global host
	global current
	global vol
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

		else:
			print "else"
			string =  ('echo "shutdown" | netcat 127.0.0.1 4222 ')
			print string
			exec_cmd(string)
			time.sleep(1)
			MERGE=0
			sys.exit(0)
		return 
#oprire, return to os
	return 

def switch_event_up(p):
	global vol
        time.sleep(0.4)

        global MERGE
	if MERGE ==1:
		while GPIO.input(UP_SWITCH):
			exec_cmd ('echo "volume +10"|netcat 127.0.0.1 4222')
			vol = vol+10
			time.sleep(0.2)
	volum = open('volume','w')
	volum.write(str(vol))
	volum.close()
	return
#volume up =10 (cat timp e apasat butonul)
def switch_event_down(p):
	global vol        
        time.sleep(0.4)

        global MERGE
	if MERGE ==1:
		while GPIO.input(DOWN_SWITCH):
                        exec_cmd ('echo "volume -10"|netcat 127.0.0.1 4222')
			vol = vol -10
                        time.sleep(0.2)
	volum = open('volume','w')
        volum.write(str(vol))
        volum.close()
	return
#volume down -10 (cat timp e apasat butonul)

def switch_event_next(p):
	global current, warp
        time.sleep(0.4)

        global MERGE
        if MERGE ==1:
                while GPIO.input(LEFT_SWITCH):
                        exec_cmd ('echo "next"|netcat 127.0.0.1 4222')
			current = ((current-3)%warp)+4 
                        time.sleep(1)
	station = open('station','w')
        station.write(str(current))
        station.close()
        return
#next station (cat timp e apasat butonul)

def switch_event_prev(p):
	print "unu"
	global current, warp
        global MERGE
	global time_stamp
	time_now = time.time()
	print time_now-time_stamp
	if (time_now - time_stamp) >= 1.8: 
#	        if MERGE ==1:
      	        exec_cmd ('echo "prev"|netcat 127.0.0.1 4222')

	        print current
	        temp = current -3
	        current = (temp%warp)+4
	        print current
	        station = open('station','w')
	        station.write(str(current))
	        station.close()

	time_stamp = time_now+0.3	
        return
#previous station (cat timp e apasat butonul)


GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event_down, bouncetime=500) 
GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event_up, bouncetime=500)
GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event_next, bouncetime=200)
GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event_prev, bouncetime=200)

while True:
	lcd.line2(str(number))
	number +=1
	time.sleep (1)
