#!/usr/bin/python

import getpass, poplib
from lcd_class import Lcd
import datetime
import time
#f=open('maildump.txt', 'w')
lcd=Lcd()
lcd.init()
mesaj_array = ['','','','','','','','','','','']
from time import strftime
msg = ""
while True:
	#msg =""
	user = 'savusfridge' 
	Mailbox = poplib.POP3_SSL('pop.googlemail.com', '995') 
	Mailbox.user(user) 
	Mailbox.pass_('frigider') 
	numMessages = len(Mailbox.list()[1])
	if numMessages != 0:
		msg=""
		todaysdate = strftime("%H:%M") 
		mesaj = "Primit la " +todaysdate + " "
		lcd.line1(mesaj)
#		for i in range(numMessages):
	        for txt in Mailbox.retr(1)[1]:
#			f.write(txt+"\n")
			msg = msg+"\n"+txt
	

		Mailbox.quit()
#		f.close()

		start = msg.find("Message-ID: ")
		n_f=msg.find("From:", start)
#		n_f=msg.find("From:")
		m_f=msg.find("<", n_f)
		mesaj = mesaj + msg[n_f:m_f]
		n_s=msg.find("Subject:")
		m_s=msg.find("\n", n_s)
		mesaj = mesaj + msg[n_s:m_s]

#n_b=msg.find("boundary=")
#m_b=msg.find("\n", n_b)
#boundary = msg[n_b+9:m_b]
#print boundary
		n_body=msg.find("Content-Type: text/plain;")
		n_body=msg.find("\n", n_body)
		n_encode=msg.find("Content-Transfer-Encoding", n_body)
		if n_encode<n_body+50:
			if n_encode>0:
			    n_body=n_encode
		n_body=msg.find("\n", n_body)
		m_body=msg.find("--", n_body)
		if m_body==-1:
			mesaj = mesaj+ " Body: " + msg[n_body:]
		else:
			mesaj = mesaj + " Body: "+  msg[n_body:m_body]
		mesaj = mesaj.replace('\n', ' ')
		mesaj = mesaj.replace ('  ', ' ')
		mesaj = mesaj.replace ('  ', ' ')
		mesaj = mesaj.replace ('  ', ' ')
		print mesaj
		l=len(mesaj)
		n=int(l/16)+1
		
		for i in range (2):
			for i in range (n-1):
				lcd.line1(mesaj[i*16:((i+1)*16)])
				lcd.line2(mesaj[(i+1)*16:((i+2)*16)])
				time.sleep(3)
		for i in range (9):
			mesaj_array[i] = mesaj_array[i+1]
		mesaj_array[9]=mesaj
	#	maildump = open('maildump', 'w')
		for i in range (9):
			maildump = open('maildump', 'w')
			maildump.write(mesaj_array[i]+"\n")
			maildump.close
