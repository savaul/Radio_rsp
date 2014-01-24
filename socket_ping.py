#! /usr/bin/env python
#asta trimite mesaje periodic pentru a activa socketul ce la randul sau verifica 
#daca a primit recent vreun mesaj de la radio
#daca nu, reseteaza radioul
import socket, sys, time, os
import logging
logging.basicConfig(filename='ping.log',filemode='w',format='%(asctime)s %(message)s', level=logging.WARNING)
logging.debug('initialize, %s', time.strftime("%H:%M:%S"))
def exec_cmd(cmd):
        p = os.popen(cmd)
        result = ""
        while p.readline():
                result = result + p.readline()
    #.rstrip('\n')
        return result
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    sys.exit()


host = '';#localhost
port = 9000;#se conecteaza cu socketul existent
s.connect((host, port))
message = "ignore"#trebuie sa trimita un mesaj, neimportant in cazul asta
while True:
	try :
    #Set the whole string
    		s.sendall(message)
		message = "ignore"+time.strftime("%H:%M:%S")
		logging.debug("am trimis mesajul %s ", message)
		time.sleep(7)
#		try:
#			exec_cmd("fswebcam -r 320x240 -d /dev/video0 /var/www/poza.jpg &>/dev/null")
#			logging.debug("inca o poza")
#		except:
#			print "eroare camera"
#			logging.debug ("eroare camera")
	except socket.error:
    #Send failed
    		sys.exit()
		break
s.close()#sanatate
