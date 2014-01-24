#!/usr/bin/python
#asta e dispecerul aplicatiei - ia mesajele de la radio si le trimite browserului
#si invers, plus testeaza daca radioul mai trimite mesaje, adica daca mai merge
#daca nu, il reseteaza
import socket
import sys, os
from thread import *
import time
radio_msg=""#ce trimite radioul si apoi se forwardeaza browserului
brow_msg=""#invers 
HOST = ''   # Symbolic name meaning all available interfaces
PORT = 9000 # Arbitrary non-privileged port
n=0#nr de depasiri ale intervalui de 5 sec. 
toggle=0#ca se refresheze poza
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.settimeout(15)
print 'Socket created'
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
     
print 'Socket bind complete'
 
#Start listening on socket
s.listen(10)#10 cred ca e numarul max de conexiuni simultane
print 'Socket now listening'
start_time=time.time() #cand incepe radioul, respectiv cand a trimis ultimul mesaj
def exec_cmd(cmd):#ca sa execute comenzi de shell
        p = os.popen(cmd)
        result = ""
        while p.readline():
                result = result + p.readline()
    #.rstrip('\n')
        return result
#Function for handling connections. This will be used to create threads
def clientthread(conn):#mi-e neclar - la fiecare conexiune, e chemata aceasta functie
#care proceseaza mesajele primite - cand nu mai avem "data" iese
    global radio_msg, brow_msg, start_time, n, toggle
    #Sending message to connected client
#    conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
     
    #infinite loop so that function do not terminate and thread do not end.
    while True:
        #Receiving from client
        data = conn.recv(4096)
#	print data
	if data[:3]=="AN ":#un prefix pentru identificarea expeditorului - aici radioul
		radio_msg = "from radio"+data#ia mesajul de la radio
		time.sleep(0.2)
		reply=brow_msg+"empty"#raspunde radioului cu mesajul browserului
		start_time=time.time()#reseteaza clock-ul radioului, merge
#		print data
	elif data=="ignore":#mesajul ping-ului, just checking ca radioul merge
#		print "ignore"
		reply="ignore"#trebuie? un raspuns
		interval = time.time()-start_time
		if interval > 5:
			n+=1
			print interval, n
		if interval>120:#test de cand n-am mai auzit nimic de la radio
			print "reset"#pentru debug
			print radio_msg
			print time.strftime("%H:%M")
			print (time.time()-start_time)
			exec_cmd('sudo pkill -9 -f socket_radio.py')
	                time.sleep(5)
        	        exec_cmd('sudo python socket_radio.py')
                	start_time=time.time()#resetam treaba, sa nu mai auzim de reset un timp
		
	elif data[:7] == "browser":
		brow_msg = data#daca nu,inseamna ca-i de la browser
		time.sleep(0.2)
		toggle=(toggle+1)%2
		brow_msg=brow_msg+"***"+str(toggle)
		reply =radio_msg#trimit mesajul de la radio
#       print time.time()-start_time
#        reply = time.strftime("%H.%M:%S")
        if not data:
#		time.sleep(2)
#                exec_cmd('sudo pkill -9 -f socket_radio.py')
#                time.sleep(.5)
#                exec_cmd('sudo python socket_radio.py')
#                start_time=time.time()
#		print "no more data"
        	break
#	print reply
        conn.sendall(reply)#trimite raspunsul cui trebuie
    #came out of loop
    conn.close()#sanatate
 
#now keep talking with the client
while 1:#adica mereu - programul asta doar sta sa asculte socketul
    	conn, addr = s.accept()
#    	print 'Connected with ' + addr[0] + ':' + str(addr[1])
     
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.

	start_new_thread(clientthread ,(conn,))#cheama functia de mai sus
 
s.close()
