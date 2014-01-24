#!/usr/bin/env python
import socket
from thread import *#nu stiu exact ce face, cred ca un fel de multitasking
#mai grav e ca nu stiu unde e folosita si de ce e aici
import os#pentru accesarea shellului
import RPi.GPIO as GPIO
import signal#nici asta nu stiu la ce ajuta, pare a fi ceva cu exceptiile, timere si alarme cred ca nu folosit
import subprocess#cred ca tot pentru shell
import sys#acceseaza variabile de sistem, pentru handling de erori, nu il folosesc efectiv, desi apare in cod
import time
import string
import datetime
from time import strftime
from radio_class import Radio
from lcd_class import Lcd
import shutil#acceseaz fisiere etc. nu e folosita
import urllib#deschide url-uri, pentru forecast
from lcd_class import Lcd
from xml.dom import minidom#acceseaza xml-uri, tot forecast
import getpass, poplib#pentru mail
import datetime
import logging#pentru log, debug, temporar
logging.basicConfig(filename='mihai.log',filemode='w',format='%(asctime)s %(message)s', level=logging.DEBUG)
from rss_class import Rss#de la smecherul cu radioul cu mpd/mpc
rss = Rss()#rss-ul, of course
rss_content=""
rss_time=time.time()#ca sa reincarce stirile dupa 15 min
mesaj_array = [' ',' ',' ',' ',' ',' ',' ',' ',' ',' ']#arhiva de mailuri
msg =""#mesajul curent? - sau o variabila temporara pentru spargerea mesajului curent in string-uri
CITY_ID = '877873' #codul pentru Ploiesti
TEMP_TYPE = 'c' #adica in grade celsius
WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?w=' + CITY_ID +' &u=c'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'
MENU_SWITCH = 25 #definitia butoanelor
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 18
DOWN_SWITCH = 17
METEO=0#definitia starilor
RADIO=1
AUTO="AUTO"#starea centralei
onoff=0#daca a mai fost un switch intre on-ul fortat si off-ul urmator
tick=0#intarziere la trecerea din radio in mail
but_nr=0#de cate ori e apasat butonul centralei
#CENTRALA=2
MAIL=2
RSS=3#coduri de stare
STATE=METEO #starea initiala in care e sistemul
METEO_time = time.time()#cand intra in starea meteo
meteo_mesaj = ""#ce afiseaza ca meteo	
meteo_content=""#ptr http
radio_lcd=""#analog, radio
MERGE=0#daca merge radioul devine 1
FLAG=""#asta e mesajul curent care se afiseaza pe lcd
durata_mesaj= []#cat timp e afisat mesajul curent	
split_mesaj=[]#fragmentul de mesaj afisat (sirul de fragmente etc.)
time_change = 0#cand trebuie sa se schimbe mesajul afisat
i_index=0#index de?
nr_iteratii=0#daca sirul de afisat s-a terminat, incepe o noua iteratie sau nu
first = 0#pentru debounce
nr_new_msg = 0#numarul de mesaje noi
mail_index=9#mesajul afisat curent
str_mail_http=""#ultimul mesaj primit, va fi afisat in browser
#merge radioul
toggle_new=0
toggle_old=0
lcd = Lcd() #defineste lcd-ul
lcd.init()
GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers
GPIO.setup(MENU_SWITCH, GPIO.IN)
GPIO.setup(UP_SWITCH, GPIO.IN)
GPIO.setup(DOWN_SWITCH, GPIO.IN)
GPIO.setup(LEFT_SWITCH, GPIO.IN)
GPIO.setup(RIGHT_SWITCH, GPIO.IN)
radiolist = open('radiolist', 'r')#lista de radiouri curente
line = radiolist.readline()
radio =[]#lista interna de radiouri, temporar
RADIO_time=time.time()#ar trebui sa tina radioul activ 2 min, dar n-am gasit codul care face asta
settle_time = 0#timpul cat radioul e activ
mail_time_on=time.time()#timpul cat mailul e activ
while line:#revenim la lista de radiouri
	temp = line.split('&')
	radio.append((temp[0], temp[1].strip('\n')))
	line = radiolist.readline()
#aici reconstituie lista de radiouri disponibile
schedule=open('schedule', 'r')#programul centralei
orar=schedule.read()
orar_start=0
host =""#lista de radiouri, initial goala
for i in range (0,len(radio)):
	host = host + " "+str(radio[i][0])
#aici scot playlistul si descrierea posturilor
station = open('station','r')
current = int(station.readline())
#aici incarc statia curenta
warp = len(radio)#cate radiouri sunt
radiolist.close()
station.close()
p=os.popen('gpio read 12')
status_cent= int(p.readline())#verfica statusul curent al centralei, citind pinul de cda
maildump=open('maildump','r')#arhiva de mailuri de pe card
nxt = 0#indecsi afisare 
prv = 0
str_mail = maildump.read()
for i in range(10):
    nxt = str_mail.find("***", prv)
#    print next	
    mesaj_array[i]=str_mail[prv:nxt-2]
    prv = nxt+5
    #print prv	
    #print mesaj_array[i]
maildump.close#aici am incarcat mailurile vechi pentru a putea fi consultate

rss_txt=""

volum = open('volume','r')
vol = int(volum.readline())
volum.close()
#aici incarc setarea de volum
init_cmd=""#pentru validarea comenzii de pe http
init_time=time.time()#pentru comenzile de pe http, sa nu se repete comenzile automat la refresh
cmd_ok=0#variabila care arata ca am primit o cda valida

time_stamp = time.time()#nici asta nu mai e folosita
time_now = time_stamp#nu cred ca mai e folosita in versiunea curenta
logging.debug('a trecut de initializari')
def no_interrupt():
	logging.debug('call no interrupt')
	return False#nu stiu ce face asta, probabil ca intrerupe afisarea pe lcd

def exec_cmd(cmd):
	p = os.popen(cmd)
	result = ""
	while p.readline():
	        result = result + p.readline()
    #.rstrip('\n')
	logging.debug ('call exec_cmd')
	return result#alias pentru executia comenzilor de bash

exec_cmd('pkill -9 -f vlc')#omoara orice alt vlc activ
exec_cmd ('gpio mode 12 out')#seteaza pinul care controleaza centrala
exec_cmd('gpio mode 14 out')#pregateste pentru semnalizarea mailurilor noi

def switch_event_menu(p):#main event, am apasat butonul de meniu
    logging.debug('call switch event %s', p)
    global STATE
    global radio, time_stamp
    global host, RADIO_time
    global current, warp, tick
    global vol, MERGE, mesaj_array, mail_time_on
    global radio_lcd, FLAG, settle_time, nr_new_msg#unele cred ca nu-mi mai trebuie
    debounce = time.time()#timp pentru ?
    if STATE ==METEO:#daca vine din meteo
        STATE=RADIO#trece in radio
        settle_time = time.time()#porneste cronometrul
	tick = time.time()#asemenea, sa asteptam 1 sec pentru apasare lunga
	if MERGE==1:#daca radioul merge, afiseaza info curenta
                 index = 4+warp-current#al catelea in lista de radiouri
                 text_line2=(str(radio[index-1][1]))#incarcam descriera, cf indexului
                 radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")	
		 FLAG=radio_lcd#ia niste informatii si le afiseaza
    elif (time.time()-tick<1) and STATE==RADIO:#daca apasam mai repede decat 1 sec
        STATE=MAIL#pe butonul de meniu, starea devine mail
        mail_time_on=time.time()#porneste cronometrul
        FLAG=mesaj_array[9]#incarca ultimul mesaj
    elif STATE==RADIO:	#daca e radio si n-am apasat imediat inca o data
			
	    if MERGE ==0:#daca radioul nu merge
		 exec_cmd('sudo pkill -9 -f vlc')
           	 exec_cmd('su - pi -c "vlc '+host+' -I rc --rc-host 127.0.0.1:4222 --novideo -d && ls"')
            #porneste radioul cu lista de statii
           	 MERGE = 1#radioul e pornit
           	 time.sleep(1)#nu stiu sigur daca mai e util, dadea eroare fara in versiunile anterioare
           	     #asteptam initializarea vlc-ului
           	 string = ('echo "gotoitem '+ str(current)+'" | netcat 127.0.0.1 4222 ')
           	 exec_cmd(string)#incarca statia curenta
           	 string2 = ('echo "volume ' + str(vol)+ '" |netcat 127.0.0.1 4222 ')
                # volumul curent
           	 exec_cmd(string2)
           	 index = 4+warp-current#incarca descrierea statiei  - asta e indexul de unde ia descrierea
           	 text_line2=(str(radio[index-1][1]))
           	 radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")#mesajul de afisat
		
           	 FLAG = radio_lcd#il afiseaza
#		print FLAG
	   	 RADIO_time=time.time()	#cronometru?
		#aici incarca descrierea statiei
                #lcd.line2(text_line2)            
		# print "2"#test ca trece
            elif MERGE==1:#daca radioul e pornit si apasam iar meniul
                 while GPIO.input(p):#daca e apasat mai mult
                     time.sleep(.1)#de 1 sec, omoara radioul
                     if time.time()>debounce+1:
                      	string =  ('echo "shutdown" | netcat 127.0.0.1 4222 ')
                       	exec_cmd(string)
                       	time.sleep(1)
                       	MERGE=0#si intra in starea meteo
		        STATE=METEO
            	       	FLAG=get_forecast()#afiseaza
		        #print "3"	    #test

	   	        break
                 if time.time()<debounce+1:#daca nu apas 1 sec
	         	STATE=MAIL#se uce la mail
                 	mail_time_on=time.time()#incepe cronometrul (dupa 2 min revine la meteo)
	         	FLAG=mesaj_array[9]#afiseaza ultimul mesaj
            		#print "4"  #test
    elif STATE==MAIL:#daca suntem in starea mail
            while GPIO.input(p):#daca tinem apasat peste o sec
                  time.sleep(.1)#decrementeaza numarul de mesaje necitite
                  if time.time()>debounce+1:
			nr_new_msg -=1#daca nu ami sunt mesaje necitite, trece in meteo
			if nr_new_msg ==0:
				STATE= METEO
				FLAG=get_forecast()#forteaza afisarea meteo
                        return#ca sa nu treaca prin comenzile de mai jos
			#nu stiu daca chiar asa face, s-ar putea sa fie nevoie de comenzi in plus
			#ca mai sus
	
           # print "5"#test
            STATE=RSS#daca apasam scurt
            nr_iteratii=1#trece in rss si forteaza afisarea stirilor
    else:
	    STATE=METEO#din rss trece in meteo
	    FLAG=get_forecast()    #afisarea
    return


def switch_event_up(p):#vol-up
    logging.debug('up call')
    global current, warp
    global STATE, vol
    global time_stamp, radio_lcd, FLAG, RADIO_time, settle_time
#    settle_time = time.time()+1
    if (STATE ==RADIO or STATE==METEO) and MERGE==1:#daca nu e rss sau mail
        while GPIO.input(p):
            exec_cmd ('echo "volume +10"|netcat 127.0.0.1 4222')#creste volumul atat timp cat e apasat
            #incrementeaza continuu volumul
            vol = vol +10 #cand termina actualizeaza valoare, o afiseaza si o scrie in fisierul "volume"
 	#    lcd.line2("Volum "+str(vol))
	    time.sleep(0.2)
            index = 4+warp-current#actualizeaza informatiile afisate - trebuie sa fac ceva cu lcd-ul, nu merge ok
            text_line2=(str(radio[index-1][1]))
	    radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")#aicipb
	#print radio_lcd
	    FLAG = radio_lcd
#	    text_stack(FLAG)	
#	    lcd.line2("Volum "+str(vol))
        RADIO_time=time.time()

        volum = open('volume','w')
        volum.write(str(vol))
        volum.close()#actualizeaza volumul pe card, pentru restaurarea viitoare


    return
#volume up =10 (cat timp e apasat butonul)


def switch_event_down(p):
    logging.debug('down call')
    global current, warp
    global STATE, vol, nr_iteratii
    global time_stamp, radio_lcd, FLAG, RADIO_time, settle_time
 #   settle_time = time.time()+1
    if (STATE ==RADIO or STATE==METEO)and MERGE==1:#daca merge radioul, daca nu, apasarea te duce in rss
        while GPIO.input(p):
            exec_cmd ('echo "volume -10"|netcat 127.0.0.1 4222')
            vol = vol -10
	  #  lcd.line2("Volum "+str(vol))
            time.sleep(0.2)
            index = 4+warp-current
            text_line2=(str(radio[index-1][1]))
            radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")
           # print radio_lcd
       	    FLAG = radio_lcd
        RADIO_time=time.time()
        volum = open('volume','w')
        volum.write(str(vol))
        volum.close()
    elif STATE==RSS:#pana aici e similar, aici, din rss trece in meteo, iar mai jos invers
	STATE=METEO
	FLAG=get_forecast()
    else:
	STATE=RSS
	nr_iteratii=1#forteaza afisarea stirilor

    return
#volume down -10 (cat timp e apasat butonul)

def switch_event_next(z):#urmatoarea statie de radio
    logging.debug('next call')
    global current, warp, AUTO, onoff, but_nr
    global STATE, mesaj_array, mail_index
    global time_stamp, radio_lcd, FLAG, RADIO_time, settle_time

    #settle_time = time.time()+5
    t_down=0
    next_radio=0	
    debounce=time.time()	
    while time.time()-debounce<1:
   	while GPIO.input(z):
           	time.sleep(.1)
		t_down=t_down+1
		debounce=time.time()
	   #print t_dow
	if t_down>=10:
		but_nr+=1
		t_down=0
		next_radio=1
		if but_nr==5:
			but_nr=0
   	if but_nr==0:
		AUTO="AUTO"
		time.sleep(.3)
    	if but_nr==1:
		AUTO="ON"
		time.sleep(.3)
    	if but_nr==2:
		AUTO="OFF"
		time.sleep(.3)
    	if but_nr==3:
		AUTO="FON"
		time.sleep(.3)
    	if but_nr==4:
		AUTO="FOFF"
		time.sleep(.3)


    p=os.popen('gpio read 12')
    status_cent=int(p.readline())
#    m=(m+1)%2#toggle pinul 12 - trebuie altul, asta e pentru cen$

#    print m, but_nr
    if AUTO=="ON":
#	if m==0:
       	    exec_cmd('gpio write 12 1')
            onoff=0			
    if AUTO=="OFF":
#	if m==1:
            exec_cmd('gpio write 12 0')
	    onoff=0


    if AUTO=="FON":
        exec_cmd('gpio write 12 1')
    if AUTO=="FOFF":
        exec_cmd('gpio write 12 0')



    if STATE ==RADIO:#cand e radio, schimba postul
	if next_radio==0:#mai putin decat apasarea lunga de mai sus
        	exec_cmd ('echo "next"|netcat 127.0.0.1 4222')
        	temp = current -5
        	current = (temp%warp)+4
        	index = 4+warp-current#schmekerii ca sa gasim descrierea corecta, playlistul e intr-o ordine aiurea
        	text_line2=(str(radio[index-1][1]))
        	radio_lcd=(text_line2+"\n"+"1&"+"Volum "+str(vol)+"\n"+"1&")
#         print radio_lcd
             
        	FLAG = radio_lcd            #actualizeaza afisarea
        	RADIO_time=time.time()#cronometrul de 2 min
#                      aici e descrierea statiei
        	station = open('station','w')#actualizeaza fisierul statii pentru o noua pornire
        	station.write(str(current))
        	station.close()#scrie denumirea statiei in fisierul "station"
    if STATE==MAIL:
	if next_radio==0:
		if mail_index<9:
			mail_index +=1
		else:
			mail_index=9
		FLAG=mesaj_array[mail_index]

    return
#next station (cat timp e apasat butonul)

def switch_event_prev(p):
    logging.debug('previous called')
    global current, warp
    global STATE, radio, mesaj_array, mail_index
    global time_stamp, radio_lcd, FLAG, RADIO_time, settle_time
    #settle_time = time.time()+5
    debounce = time.time()

#    while GPIO.input(p):
#           time.sleep(.1)
#           if time.time()>debounce+1:
#                   exec_cmd('gpio write 12 1')
#                   time.sleep(1)
#                   break


    if STATE ==RADIO:
        exec_cmd ('echo "prev"|netcat 127.0.0.1 4222')
        temp = current -3
        current = (temp%warp)+4
        index = 4+warp-current
        text_line2=(str(radio[index-1][1]))
       	radio_lcd=(text_line2+"\n"+"1&"+"Volum "+str(vol)+"\n"+"1&")
        FLAG = radio_lcd
        RADIO_time=time.time()
        station = open('station','w')
        station.write(str(current))
        station.close()
    if STATE==MAIL:
                if mail_index>0:
                        mail_index -=1
		else:
			mail_index=0
                FLAG=mesaj_array[mail_index]
	

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
#	print next
   	next=mesaj.find("\n", prev)
        split_mesaj.append(mesaj[prev:next])
#	print split_mesaj
        prev=mesaj.find("&", next)
#	print prev
        durata_mesaj.append(mesaj[next+1:prev])
	prev +=1
    	next=mesaj.find("\n", prev)
#    print split_mesaj
#    print durata_mesaj
    for i in range(len(split_mesaj)-1):
	lcd.line1(split_mesaj[i])
	lcd.line2(split_mesaj[i+1])
    	for n in range(20):	
		if FLAG:
		    lcd.line1("")
		    lcd.line2("")
		    break
		else:
		    time.sleep(float(durata_mesaj[i])/20)
		    n+=1	
	
    return


def execute_cmd(cmd):
	logging.debug('execute command  %s', cmd)
	global MERGE, AUTO, STATE, vol, warp, current, FLAG, RADIO_time, onoff, settle_time, str_mail_http
	global mesaj_array, nr_iteratii
#	print cmd
	if cmd =="v_up" and MERGE==1:
	    exec_cmd ('echo "volume +10"|netcat 127.0.0.1 4222')#creste volumul at$
            #incrementeaza continuu volumul
            vol = vol +10 #cand termina actualizeaza valoare, o afiseaza si o scri$
        #    lcd.line2("Volum "+str(vol))
            time.sleep(0.2)
            index = 4+warp-current#actualizeaza informatiile afisate - trebuie sa $
            text_line2=(str(radio[index-1][1]))
            radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")
        #print radio_lcd
            FLAG = radio_lcd
#           text_stack(FLAG)    
#           lcd.line2("Volum "+str(vol))
            RADIO_time=time.time()

            volum = open('volume','w')
            volum.write(str(vol))
            volum.close()
		
	if cmd=="v_down" and MERGE==1:
            exec_cmd ('echo "volume -10"|netcat 127.0.0.1 4222')#creste volumul at$
            #incrementeaza continuu volumul
            vol = vol -10 #cand termina actualizeaza valoare, o afiseaza si o scri$
        #    lcd.line2("Volum "+str(vol))
            time.sleep(0.2)
            index = 4+warp-current#actualizeaza informatiile afisate - trebuie sa $
            text_line2=(str(radio[index-1][1]))
            radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")
        #print radio_lcd
            FLAG = radio_lcd
#           text_stack(FLAG)    
#           lcd.line2("Volum "+str(vol))
            RADIO_time=time.time()

            volum = open('volume','w')
            volum.write(str(vol))
            volum.close()

	if cmd=="prog_up" and MERGE==1:
		exec_cmd ('echo "next"|netcat 127.0.0.1 4222')
                temp = current -5
                current = (temp%warp)+4
                index = 4+warp-current#schmekerii ca sa gasim descrierea corecta, $
                text_line2=(str(radio[index-1][1]))
                radio_lcd=(text_line2+"\n"+"1&"+"Volum "+str(vol)+"\n1&")
#         print radio_lcd

                FLAG = radio_lcd            #actualizeaza afisarea
                RADIO_time=time.time()#cronometrul de 2 min
#                      aici e descrierea statiei
                station = open('station','w')#actualizeaza fisierul statii pentru $
                station.write(str(current))
                station.close()#

	if cmd=="prog_down" and MERGE==1:
		exec_cmd ('echo "prev"|netcat 127.0.0.1 4222')
                temp = current -3
                current = (temp%warp)+4
                index = 4+warp-current#schmekerii ca sa gasim descrierea corecta, $
                text_line2=(str(radio[index-1][1]))
                radio_lcd=(text_line2+"\n"+"1&"+"Volum "+str(vol)+"\n1&")
#         print radio_lcd

                FLAG = radio_lcd            #actualizeaza afisarea
                RADIO_time=time.time()#cronometrul de 2 min
#                      aici e descrierea statiei
                station = open('station','w')#actualizeaza fisierul statii pentru $
                station.write(str(current))
                station.close()#
	if cmd=="radio_on_off" and MERGE==0:
		 settle_time=time.time()
		 exec_cmd('sudo pkill -9 -f vlc')
		 exec_cmd('su - pi -c "vlc '+host+' -I rc --rc-host 127.0.0.1:4222 --novideo -d && ls"')
            #porneste radioul cu lista de statii
                 MERGE = 1#radioul e pornit
		 STATE=RADIO		
                 time.sleep(1)#nu stiu sigur daca mai e util, dadea eroare fara in versiunile anterioare
                     #asteptam initializarea vlc-ului
                 string = ('echo "gotoitem '+ str(current)+'" | netcat 127.0.0.1 4222 ')
                 exec_cmd(string)#incarca statia curenta
                 string2 = ('echo "volume ' + str(vol)+ '" |netcat 127.0.0.1 4222 ')
                # volumul curent
                 exec_cmd(string2)
                 index = 4+warp-current#incarca descrierea statiei  - asta e indexul de unde ia descrierea
                 text_line2=(str(radio[index-1][1]))
                 radio_lcd=("Volum "+str(vol)+"\n"+"1&"+text_line2+"\n"+"1&")#mesajul de afisat

                 FLAG = radio_lcd#il afiseaza
#               print FLAG
                 RADIO_time=time.time() #cronometru?


		 return
	if cmd=="radio_on_off" and MERGE==1:
		 string =  ('echo "shutdown" | netcat 127.0.0.1 4222 ')
                 exec_cmd(string)
                 time.sleep(1)
                 MERGE=0#si intra in starea meteo
                 STATE=METEO
                 FLAG=get_forecast()




		 return
	p=os.popen('gpio read 12')
        status_cent=int(p.readline())

	if cmd=="c_on":
		AUTO="ON"
            	exec_cmd('gpio write 12 1')
            	onoff=0
	if cmd=="c_off":
		AUTO="OFF"
            	exec_cmd('gpio write 12 0')
            	onoff=0
	if cmd=="c_f_on":
		AUTO="FON"
        	exec_cmd('gpio write 12 1')
	if cmd=="c_f_off":
		AUTO="FOFF"
        	exec_cmd('gpio write 12 0')
	if cmd=="auto":
		AUTO="AUTO"

	if cmd=="rss":
		STATE=RSS
		nr_iteratii=1
	if cmd=="meteo":
		STATE=METEO
		FLAG=get_forecast()
	if cmd=="mail":
		STATE=MAIL
		mail_time_on=time.time()
                maildump=open('maildump','r')

                nxttt = 0
                prvvv = 0
                str_mail=maildump.read()
                for i in range(10):
                       nxttt = str_mail.find("***", prvvv)
                       mesaj_array[i]=str_mail[prvvv:nxttt-2]
                       prvvv = nxttt+5
                       #print mesaj_array[i]
                maildump.close
		FLAG=mesaj_array[9]
		str_mail_http=mesaj_array[9].replace("1&", "")
#		last =str_mail_http.rfind("***", -4)
#		last=len(str_mail_http)-last
#		str_mail_http=str_mail_http[last+2:-4]


	return

def get_forecast():
	global meteo_content
	try:
    		dom = minidom.parse(urllib.urlopen(WEATHER_URL))
    		ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
    		present = ycondition.getAttribute('text')
    		temp =  ycondition.getAttribute('temp')
    		forecasts = ""
    		meteo_mesaj = "Now we have "+ str(temp)+"C" +"\n"+"1&"+ str(present)+"\n"+"1&"
		meteo_content="Now we have "+ str(temp)+"C" + "\n"+str(present)
    # \n forteaza sfarsitul afisarii pe linia curenta si 2 e durata de afisare in secunde
    		i=0
    		meteo_mesaj2="" 
		meteo_content2=""
    		while i<3:
        		node = dom.getElementsByTagNameNS(WEATHER_NS, 'forecast')[i]

        		meteo_mesaj2 =meteo_mesaj2+"Meteo " +str(node.getAttribute('date'))+"\n"+"1&" + "Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high'))+"\n"+"1&"+str(node.getAttribute('text'))+"\n"+"1&"
			meteo_content2=meteo_content2+"Meteo "+str(node.getAttribute('date')) +"\n"+ "Low "+str(node.getAttribute('low'))+" High " +str(node.getAttribute('high'))+ " "+str(node.getAttribute('text'))+"\n"
        		i+=1
    		meteo_mesaj=meteo_mesaj+meteo_mesaj2+"\n"+"1&"
		meteo_content=meteo_content+"\n"+meteo_content2
#    print todaysdate
    	except:
		meteo_mesaj="No connection"
	logging.debug('forecast %s', meteo_mesaj)
	return meteo_mesaj
def text_stack(txt):
	logging.debug('text stack called %s', txt)
	global time_change
	time_change = time.time()
	#print time_change
        global split_mesaj
        global durata_mesaj
	global i_index
	split_mesaj_old = split_mesaj
	durata_mesaj_old = durata_mesaj
	split_mesaj=[]
	durata_mesaj =[]
        n=1
        next =0
        prev=0
        while (next != -1):
#           print next
            next=txt.find("\n", prev)
	    temp_str=txt[prev:next]	

#            split_mesaj.append(txt[prev:next])
#           print split_mesaj
            prev=txt.find("&", next)
#           print prev
	    durata_tmp=txt[next+1:prev]
#            durata_mesaj.append(txt[next+1:prev])
	    space_st=0
	    space_fin=0
	    while True:
     	    	if len(temp_str[space_st:])>16:
			tmp=temp_str[space_st:space_st+16]
			#print tmp
			last_space=tmp.rfind(" ", 0, 16)
			if last_space== -1:
				last_space=16
			space_fin=space_st+last_space
#			print space_fin
#			print space_st
			split_mesaj.append(temp_str[space_st:space_fin])
#			print tmp[space_st:space_fin]
			durata_mesaj.append(durata_tmp)
			space_st=space_fin+1
	    	else:
			split_mesaj.append(temp_str[space_st:])
			durata_mesaj.append(durata_tmp)
			break

            prev +=1
            next=txt.find("\n", prev)
#        print split_mesaj
#        print durata_mesaj
#    for i in range(len(split_mesaj)-1):
#        lcd.line1(split_mesaj[i])
#        lcd.line2(split_mesaj[i+1])
#        for n in range(20):
#                if FLAG:
#                    lcd.line1("")
#                    lcd.line2("")
#                    break
#                else:
#                    time.sleep(float(durata_mesaj[i])/20)
#                    n+=1
	i_index=0

	return

def text_change(clock1):
	global time_change, split_mesaj, durata_mesaj, settle_time, i_index, nr_iteratii, vol
	logging.debug ('text change called')
#	print split_mesaj, i_index
	if i_index < len(split_mesaj):
                if len(split_mesaj[i_index])>16:
                        lcd.scroll2(split_mesaj[i_index], no_interrupt)
#                               print split_mesaj[i_index]
                else:
                	lcd.line2(split_mesaj[i_index])
#                               print split_mesaj[i_index]
		try:
			time_float=float(durata_mesaj[i_index])
		except:
			time_float=1
		if (clock1-time_change) >= time_float:
			time_change = clock1
			i_index +=1
			if i_index == len(split_mesaj):
				nr_iteratii +=1
				i_index=0
#	lcd.line2("Volum "+str(vol))
	return


def switch_event(switch):#debounce-ul general si selectia butoanelor
	logging.debug('switch event called')
	global first
	debounce = time.time()
	if first == 0:#pentru oscilatiile contactelor, sa nu ia in seama decat prima apasare si apoi se uita dupa .15s daca mai e apasat
		first=1
		while GPIO.input(switch):
			time.sleep(.1)
			if time.time()>debounce+0.15:
				if switch == MENU_SWITCH:
					switch_event_menu(switch)

				if switch == DOWN_SWITCH:
					switch_event_down(switch)

				if switch == UP_SWITCH:
					switch_event_up(switch)

				if switch ==LEFT_SWITCH:
                                        switch_event_next(switch)

                                if switch == RIGHT_SWITCH:
                                        switch_event_prev(switch)

				first=0
				return 1
		
		first =0
		return -1
	else:
		return -1

def centrala():#incarca programul din schedule, verifica in ce interval ne aflam si seteaza centrala accordingly
#	return#temporar, scoate diezul de la return-ul de mai jos
	logging.debug('centrala called')
	global orar, orar_start, AUTO, onoff, status_cent
	ziua=strftime("%A")
	start=orar.find(ziua)
	fin=orar.find("***", start)
	orar_today=orar[start:fin]
#	print orar_today	
	ora=int(strftime("%H"))
	minut=int(strftime("%M"))
	interval1=orar_today.find("\n")
	interval2=orar_today.find("\n", interval1)
	while interval2 != -1:
		H_old= orar_today[interval1+1:interval1+3]
		M_old = orar_today[interval1+4:interval1+6]

#		print H_old, M_old
#		print int(H_old), int(M_old)
		if (ora<int(H_old)) or (ora==int(H_old) and minut< int(M_old)):
	#		end_action=orar_today.rfind(" ",0, interval1)
#			print end_action
#			print interval1
	#		p=os.popen('gpio read 12')
	 #               m= int(p.readline())
	 #               action = orar_today[end_action+1:interval1]
#			print action
	  #              if action=="OFF" and m==1:
           #    		        exec_cmd('gpio write 12 0')
      	#	        if action =="ON" and m==0:
         #      			exec_cmd('gpio write 12 1')

			break
#				print action
		interval1=interval2

		interval2=orar_today.find("\n", interval2+1)
#	print interval1
        end_action=orar_today.rfind(" ",0, interval1)	
	action=orar_today[end_action+1:interval1]



        p=os.popen('gpio read 12')
        status_cent= int(p.readline())

	if AUTO=="AUTO":
		if status_cent==1 and action=="OFF":
			exec_cmd('gpio write 12 0')
                if status_cent==0 and action=="ON":
                        exec_cmd('gpio write 12 1')


	if AUTO=="ON":#daca trece in on, o porneste si apoi o opreste la primul off din schedule
		if action=="ON":
			onoff=1
		if onoff==1 and status_cent==1 and action=="OFF":
                        exec_cmd('gpio write 12 0')
			onoff=0
			AUTO="AUTO"
	if AUTO=="OFF":
		if action =="OFF":
			onoff=1
		if onoff==1 and status_cent==0 and action=="ON":
                        exec_cmd('gpio write 12 1')	
			onoff=0
			AUTO="AUTO"


	return	#de aici scoate diezul


def validate(cmd):#verifica comenzile de la browser, sa nu se repete din cauza refresh-ului
	logging.debug('validate called %s', cmd)
	global init_cmd, init_time, cmd_ok
#	print init_cmd, cmd
	if cmd==init_cmd:#daca se repeta comanda anterioara, verifica - daca e peste 15 sec e refresh, daca nu mai execut-o o data
		if (time.time()-init_time)>15:# and (time.time()-init_time)<37:
			init_time=time.time()
			cmd_ok=0
			return
		else:
			cmd_ok=1
			init_cmd=cmd
			print "time"+init_cmd
#			print time.time()-init_time
			init_time=time.time()
			return
	else:
		cmd_ok=1
		init_cmd=cmd
		init_time=time.time()
		print "inegal"+init_cmd
		return

	return


def get_mail():#copiata si adaptata
	logging.debug('get mail called')
	global FLAG, STATE, mesaj_array, nr_new_msg, mail_index, msg_blink
#	FLAG=0
	try:
        	user = 'savusfridge'
        	Mailbox = poplib.POP3_SSL('pop.googlemail.com', '995')
        	Mailbox.user(user)
        	Mailbox.pass_('frigider')
		numMessages = len(Mailbox.list()[1])

        except:
		print "inca o eroare de mail", sys.exc_info()[0], sys.exc_info()[2]#aici crapa, nu stiu de ce
		numMessages=0
        if numMessages != 0:
		nr_new_msg +=1
		msg_blink=time.time()#blinkane pe pinul 14
		mail_index = 9
		STATE=MAIL
                msg=""
                todaysdate = strftime("%b %d %H:%M")
                mesaj = todaysdate + "\n1&"
#               for i in range(numMessages):
                for txt in Mailbox.retr(1)[1]:
#                       f.write(txt+"\n")
                        msg = msg+"\n"+txt


#               f.close()

                start = msg.find("Message-ID: ")#aici incerc sa il impart in chestii utile, dar mai am erori in 
						#functie de clientul de mail expeditor
                n_f=msg.find("From:", start)
#               n_f=msg.find("From:")
                m_f=msg.find("<", n_f)
                mesaj = mesaj + msg[n_f:m_f]+"\n1&"
                n_s=msg.find("Subject:")
                m_s=msg.find("\n", n_s)
                mesaj = mesaj + msg[n_s:m_s]+"\n1&"

                n_body=msg.find("Content-Type: text/plain;")
                n_body=msg.find("\n", n_body)
                n_encode=msg.find("Content-Transfer-Encoding", n_body)
                if n_encode<n_body+50:
                        if n_encode>0:
                            n_body=n_encode
                n_body=msg.find("\n", n_body)
                m_body=msg.find("--", n_body)
                if m_body==-1:
			ms = msg[n_body:].replace('\n', ' ')
                	ms = ms.replace ('  ', ' ')#sterg spatiile goale
                	ms = ms.replace ('  ', ' ')
                	ms = ms.replace ('  ', ' ')
                        mesaj = mesaj+ "Body: " + ms+"\n1&"
                else:
                        ms = msg[n_body:m_body].replace('\n', ' ')
                        ms = ms.replace ('  ', ' ')
                        ms = ms.replace ('  ', ' ')
                        ms = ms.replace ('  ', ' ')
                        mesaj = mesaj+ "Body: " + ms+"\n1&"

#		FLAG=str(nr_new_msg) +" mesaj(e)\n1&"
                FLAG= mesaj
		#print mesaj
                for i in range (9):#mutam mesajele anterioare sa-i facem loc celui nou
                        mesaj_array[i] = mesaj_array[i+1]
                mesaj_array[9]=mesaj
                maildump = open('maildump', 'w')#scriem treaba, formatata ca sa poata fi si citita ulterior
                for i in range (10):
         #               maildump = open('maildump', 'w')
                        maildump.write(mesaj_array[i]+"\n *** \n")
                maildump.close

	try:
        	Mailbox.quit()
	except:
		print "no mailboxes to quit"
	if STATE==MAIL:#aici incarca in memorie mesajele vechi, pentru a putea fi afisate la cerere, actualizand cu asta primit acum

	        maildump=open('maildump','r')
	        nxtt = 0
	        prvv = 0
	        str_mail=maildump.read()
	        for i in range(10):
	               nxtt = str_mail.find("***", prvv)
	               mesaj_array[i]=str_mail[prvv:nxtt-2]
	               prvv = nxtt+5
	               #print mesaj_array[i]
	        maildump.close
#		maildump=open('maildump','r')
#		next = 0
#		prev = 0
#		for i in range(10):
#			next = maildump.read().find("***", prev)
#			mesaj_array[i]=maildump.read()[prev:next]
#			prev = next+3
#			print mesaj_array[i]
#		maildump.close
	return

def get_rss():#ia rss-ul, ii schimba diacriticele si il imparte in siruri mai mici de 16 caractere
	logging.debug('rss called')
	global rss_content
	try:
		FLAG_RSS=""
		rss_content=""
		rss_1=rss.getFeed()
		rss_1=rss.getFeed()
		rss_next=rss.getFeed()
		#print rss_1
		#print rss_next
		while rss_next!= rss_1:
                	rss_next.decode('ascii','ignore')
#                       print rss_line
                	rss_next=rss_next.replace("\\t", "t")
                	rss_next=rss_next.replace("\\sf", "s")
                	rss_next=rss_next.replace("\\xe2", "a")
                	rss_next=rss_next.replace("\\u0102", "A")
                	rss_next=rss_next.replace("\\a", "a")
                	rss_next=rss_next.replace("\\se", "S")
                	rss_next=rss_next.replace("\\u0219", "s")
                	rss_next=rss_next.replace("\\u021b", "t")
        #       	rss_line=rss_line.replace("\\", "")
                	rss_next=rss_next.replace("\\u0162", "T")
                	rss_next=rss_next.replace("\\xc3xae", "i")
                	rss_next=rss_next.replace("\\xce", "I")
                	rss_next=rss_next.replace("\\xc2", "A")
                	rss_next=rss_next.replace("\\u0218", "S")
                	rss_next=rss_next.replace("\\u021a", "T")
                	rss_next=rss_next.replace(chr(238), "i")
                	rss_next=rss_next.replace(chr(140), "i")
        		rss_content=rss_content+rss_next+"\n"
	#print rss_txt
                        space_st=0
                        space_fin=0
                        while space_fin != -1:
                                if len(rss_next[space_st:])>16:
                                        temp_str=rss_next[space_st:space_st+16]
#                                       print temp_str
                                        last_space=temp_str.rfind(" ", 0, 16)
                                        if last_space==-1:
                                                last_space=16
#                                       print last_space
                                        space_fin = space_st+last_space
                                        FLAG_RSS=FLAG_RSS+rss_next[space_st:space_fin]+"\n0.5&"
                                        space_st=space_fin+1
                                else:
                                        FLAG_RSS=FLAG_RSS+rss_next[space_st:]+"\n0.5&"
                                        break

			rss_next=rss.getFeed()
	except:

		FLAG_RSS="Eroare RSS"
#	print rss_content
#	print "\n\n"+FLAG_RSS
	return FLAG_RSS 

#GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event_menu, bouncetime=500)
#GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event_down, bouncetime=500)
#GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event_up, bouncetime=500)
#GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event_next, bouncetime=500)
#GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event_prev, bouncetime=500)

GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event)
GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event)
GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event)
GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event)
GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event)




#definirea butoanelor si a intreruperilor generate de ele


#main loop

#initializarile
FLAG=get_forecast()
METEO_time=time.time()
get_mail()
MAIL_time = time.time()
#print get_forecast()
#lcd_split(meteo_lcd)
lcd.init()
lcd_time=0
FLAG_RSS=get_rss()
logging.debug('ready for main loop')
while True:
    inceput = time.time()#ca sa stim ce actualiza,
    if STATE==RADIO:
	if inceput-settle_time>=120:
	    STATE=METEO
	    FLAG=get_forecast()	
    if FLAG != "":#aici cheama treaba de afisare - mai trebuie lucrat, blocheaza din cand in cand
	#print FLAG
	text_stack(FLAG) #updateaza textul de afisat

	FLAG=""

    logging.debug('flag %s', FLAG)
    text_change(inceput)#testeaza daca e cazul sa se schime ce-i afisat
    index = 4+warp-current#incarca descrierea statiei  - asta e indexul de unde ia descrierea
    print "loop "+strftime("%H:%M")#temporar, sa vad daca se blocheaza inainte	
    mesaj_socket="AN "+ str(STATE)+"&"+str(vol)+"&"+str(MERGE)+"&"+(str(radio[index-1][1]))+"&"+AUTO+"&"+str(status_cent)+"&"
    logging.debug('mesajul de trimis la socket %s', mesaj_socket)
    if STATE==3:
	    mesaj_socket=mesaj_socket+"\n"+rss_content+"&"
    if STATE==0:
	    mesaj_socket=mesaj_socket+"\n"+meteo_content+"&"    
    if STATE==MAIL:
	    mesaj_socket=mesaj_socket+"\n"+"MAIL\n"+str_mail_http+"&"
    try:#comunicarea cu browserul, socket-uri
	    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
	    print 'Failed to create socket'
#    sys.exit()

#    print 'Socket Created'

    host_srv = '';
    port = 9000;

    try:
	        skt.connect((host_srv, port))

    except:
	        print "no socket conection"

    try :
    #Set the whole string
	    logging.debug('incercam transmisia la socket')
	    skt.sendall(mesaj_socket)
#	    print (str(STATE)+str(vol)+str(MERGE)+(str(radio[index-1][1])))
#	    print 'Message send successfully'
	
    except socket.error:
    #Send failed
	    print 'Send failed'
	    #sys.exit()
	

#Now receive data
    try:
	    logging.debug('incercam receptia de la socket')
	    reply = skt.recv(1024)
	    logging.debug('mesajul primit de la browser %s', reply)
	    str_cmd= reply.find ("browser/hello.py?")
	    end_cmd=reply.find("=", str_cmd)
	    tog_st=reply.find("***")
#	    print "Tog new "+reply[tog_st-3:tog_st+14]
	    try:
	    	toggle_new=int(reply[tog_st+3:tog_st+4])
	    except:
		toggle_new=toggle_old
	    if toggle_new!=toggle_old:
		    if str_cmd !=-1 and end_cmd!=-1:
		    	cmd_test=reply[str_cmd+17:end_cmd]
	#		print cmd_test	
		    	validate(cmd_test)
			if cmd_ok==1:
				execute_cmd(cmd_test)
				cmd_ok=0
		    toggle_old=toggle_new
	    skt.close()	
    except:
	    print "no socket to receive from"
#    print cmd_ok	
#    print "reply "+reply

 #   except:
#	print "no reply"



#    print str(todaysdate)
#    print str(STATE)
#    if (inceput-lcd_time)>=0.5:
#	print "hit"
#	if inceput >= settle_time:
    time_string = strftime("%H:%M")
    if STATE == 0:
		alt_state="METEO"
    if STATE==1:
		alt_state = "RADIO"
    if STATE==2:

		alt_state = "MAIL"

    if STATE==3:
		alt_state="NEWS"

    altele = alt_state+" "+AUTO
    if nr_new_msg!=0:
		altele=" M"+str(nr_new_msg)
    lcd.line1(time_string+" "+altele)#ce afisam pe prima linie a lcd-ului
#	time.sleep(.1)
#    lcd_time=inceput

#    if STATE==METEO:
    if (inceput - METEO_time)>=900:#actualizari
        FLAG=get_forecast()
        METEO_time=time.time()
	logging.debug('meteo updated')

    if (inceput - rss_time)>=900:
        FLAG_RSS=get_rss()
        rss_time=time.time()
	logging.debug('rss updated')


    if (inceput - MAIL_time)>=67:#sa incercam un numar prim
        get_mail()
        MAIL_time=time.time()
	logging.debug('mail_get') 

    if (inceput-orar_start)>=30:
	centrala()#verifica daca e cazul sa faca ceva la centrala
	orar_start=time.time()

    if nr_new_msg !=0:
#	exec_cmd('gpio write 14 1')
	STATE=MAIL
	if inceput-msg_blink<0.4:
		exec_cmd('gpio write 14 1')
	if (inceput-msg_blink<0.8) and (inceput-msg_blink>0.4):
		exec_cmd('gpio write 14 0')
	if inceput-msg_blink>0.8:
		msg_blink=inceput
    else:
	exec_cmd('gpio write 14 0')

#    if nr_new_msg==0:
#	if STATE==MAIL:
#		if inceput-mail_time_on>120:
#			STATE=METEO
#			FLAG=get_forecast()

    if STATE==RSS:
	if nr_iteratii!=0:
		nr_iteratii=0
		FLAG=FLAG_RSS
	
#   if STATE==MAIL:
	
#    print radio_lcd
#    if STATE==RADIO:
#        lcd_split(radio_lcd)
#    print STATE	
#    if (inceput-RADIO_time) >=60:
#       if (inceput - METEO_time)>=60:
#               meteo_lcd=get_forecast()
#               METEO_time=time.time()
#       radio_lcd = radio_lcd+meteo_lcd
