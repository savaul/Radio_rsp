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
from lcd_class import Lcd
from xml.dom import minidom
CITY_ID = '877873' #codul pentru Ploiesti
TEMP_TYPE = 'c' #adica in grade celsius
WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?w=' + CITY_ID +' &u=c'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'
MENU_SWITCH = 25 #definitia butoanelor
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 18
DOWN_SWITCH = 17
METEO=0
RADIO=1
CENTRALA=2
MAIL=3
STATE=METEO #starea in care e sistemul
METEO_time = time.time()
meteo_mesaj = ""
radio_lcd=""
#merge radioul
FLAG=0
lcd = Lcd() #defineste lcd-ul
lcd.init()
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
	line = radiolist.readline()
#aici reconstituie lista de radiouri disponibile

host =""
for i in range (0,len(radio)):
	host = host + " "+str(radio[i][0])
#aici scot playlistul si descrierea posturilor
station = open('station','r')
current = int(station.readline())
#aici incarc statia curenta
warp = len(radio)
radiolist.close()
station.close()


volum = open('volume','r')
vol = int(volum.readline())
volum.close()
#aici incarc setarea de volum

time_stamp = time.time()
time_now = time_stamp
#momentul de start
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = ""
	while p.readline():
        result = result + p.readline()
        #.rstrip('\n')
    return result


def switch_event_menu(p):
    GPIO.remove_event_detect(p)
    global STATE
    global radio, time_stamp
    global host
    global current, warp
    global vol, radio_lcd, FLAG
    time_now = time.time()
    #        debounce
    if (time_now - time_stamp) >= 0.8:
        if GPIO.input(MENU_SWITCH):
            if STATE ==METEO:
                STATE=RADIO
                exec_cmd('su - pi -c "vlc '+host+' -I rc --rc-host 127.0.0.1:4222 --novideo -d && ls"')
                #porneste radioul cu lista de statii
                STATE = 1
                time.sleep(1)
                #asteptam initializarea vlc-ului
                string = ('echo "gotoitem '+ str(current)+'" | netcat 127.0.0.1 4222 ')
                #			incarca statia curenta
                exec_cmd(string)
                string2 = ('echo "volume ' + str(vol)+ '" |netcat 127.0.0.1 4222 ')
                # volumul curent
                exec_cmd(string2)
                index = 4+warp-current
                text_line2=(str(radio[index-1][1]))
                radio_lcd=("Statia "+text_line2+"\n"+"2&"+"Volum "+str(vol)+"\n"+"2&")
                #aici incarca descrierea statiei
                #lcd.line2(text_line2)
            
            elif STATE==RADIO:
                time.sleep(2)
                timp = time.time()
                if (timp-time_now)>1.5:
                    if GPIO.input(MENU_SWITCH):
                        string =  ('echo "shutdown" | netcat 127.0.0.1 4222 ')
                        exec_cmd(string)
                        time.sleep(1)
                        STATE=METEO
                    else:
                        STATE=CENTRALA
            elif STATE==CENTRALA:
                time_now = time.time()
                    #        debounce
                if (time_now - time_stamp) >= 0.8:
                    if GPIO.input(MENU_SWITCH):
                        STATE=MAIL
            elif STATE==MAIL:
                time_now = time.time()
    #        debounce
                if (time_now - time_stamp) >= 0.8:
                    if GPIO.input(MENU_SWITCH):
                        STATE=METEO
                
    time_stamp = time_now+0.3
    GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
    #reporneste detectarea butoanelor
    return


def switch_event_up(p):
    GPIO.remove_event_detect(p)
    #global text_line1, text_line2, text_line1_old, text_line2_old
    global current, warp
    global STATE, vol
    global time_stamp
    time_now = time.time()
    #       debounce
    if (time_now - time_stamp) >= 0.8:
        if STATE ==RADIO:
            while GPIO.input(p):
                exec_cmd ('echo "volume +10"|netcat 127.0.0.1 4222')
                #incrementeaza continuu volumul
                vol = vol +10 #cand termina actualizeaza valoare, o afiseaza si o scrie in fisierul "volume"
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
    #global text_line1, text_line2, text_line1_old, text_line2_old
    global current, warp
    global STATE, vol
    global time_stamp
    time_now = time.time()
    #        debounce
    if (time_now - time_stamp) >= 0.8:
        if STATE ==RADIO:
            while GPIO.input(p):
                exec_cmd ('echo "volume -10"|netcat 127.0.0.1 4222')
                vol = vol -10
                time.sleep(0.2)
            volum = open('volume','w')
            volum.write(str(vol))
            volum.close()
    time_stamp = time_now+0.3
    GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_down, bouncetime=500)
    return
#volume down -10 (cat timp e apasat butonul)

def switch_event_next(p):
    GPIO.remove_event_detect(p)
    #global text_line1, text_line2, text_line1_old, text_line2_old
    global current, warp
    global STATE
    global time_stamp
    time_now = time.time()
    #        print time_now-time_stamp
    if (time_now - time_stamp) >= 0.8:
        if STATE ==RADIO:
            exec_cmd ('echo "next"|netcat 127.0.0.1 4222')
            temp = current -5
            current = (temp%warp)+4
            index = 4+warp-current
            #                      aici e descrierea statiei
            station = open('station','w')
            station.write(str(current))
            station.close()#scrie denumirea statiei in fisierul "station"


    time_stamp = time_now+0.3
    GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_next, bouncetime=500)
    return
#next station (cat timp e apasat butonul)

def switch_event_prev(p):
	GPIO.remove_event_detect(p)
    #    global text_line1, text_line2, text_line1_old, text_line2_old
    global current, warp
    global STATE, radio
    global time_stamp
    time_now = time.time()
    if (time_now - time_stamp) >= 0.8:
        if STATE ==RADIO:
            exec_cmd ('echo "prev"|netcat 127.0.0.1 4222')
            temp = current -3
            current = (temp%warp)+4
            index = 4+warp-current
            station = open('station','w')
            station.write(str(current))
            station.close()

    time_stamp = time_now+0.3
    GPIO.add_event_detect(p, GPIO.RISING, callback=switch_event_prev, bouncetime=500)
    return
#previous station (cat timp e apasat butonul)

def lcd_split (mesaj):
    global FLAG
    FLAG=0
    split_mesaj=[]
    durata_mesaj= []
    n=1
    next =0
    prev=0
    while (next != -1):
        next=mesaj.find("\n", prev)
        split_mesaj.append(mesaj[prev:next])
        prev=mesaj.find("&", next)
        durata_mesaj.append(mesaj[next+1:prev])
        prev +=1
        next=mesaj.find("\n", prev)
    for i in range(len(split_mesaj)-1):
        lcd.line1(split_mesaj[i])
        lcd.line2(split_mesaj[i+1])
        if FLAG:
            break
        else:
            time.sleep(float(durata_mesaj[i]))
    

    return
def get_forecast():
    dom = minidom.parse(urllib.urlopen(WEATHER_URL))
    ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
    present = ycondition.getAttribute('text')
    temp =  ycondition.getAttribute('temp')
    forecasts = ""
    meteo_mesaj = "Now we have "+ str(temp)+"C" +"\n"+"2&"+ str(present)+"\n"+"2&"
    # \n forteaza sfarsitul afisarii pe linia curenta si 2 e durata de afisare in secunde
    i=0
    meteo_mesaj2=""
    while i<3:
        node = dom.getElementsByTagNameNS(WEATHER_NS, 'forecast')[i]
        todaysdate = strftime("%H:%M %d/%m/%Y")

        meteo_mesaj2 =meteo_mesaj2+"Meteo " +str(node.getAttribute('date'))+"\n"+"2&" + "Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high'))+"\n"+"2&"+str(node.getAttribute('text'))+"\n"+"2&"

        i+=1
    meteo_mesaj=meteo_mesaj+meteo_mesaj2+str(todaysdate)+"\n"+"2&"
    return meteo_mesaj


GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event_down, bouncetime=500)
GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event_up, bouncetime=500)
GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event_next, bouncetime=500)
GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event_prev, bouncetime=500)
#definirea butoanelor si a intreruperilor generate de ele
meteo_lcd=get_forecast()
print meteo_lcd
while True:
    inceput = time.time()
    if STATE==METEO:
        if (inceput - METEO_time)>=900:
            get_forecast()
        lcd_split(meteo_lcd)
    if STATE==RADIO:
        lcd_split(radio_lcd)






