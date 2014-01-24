#! /usr/bin/env python
#asta e partea de interfata cu browserul
import cgi#cica trebuie pentru a face scripturi de cgi
import cgitb; cgitb.enable()  # for troubleshooting
import socket
import os, os.path
import time, sys
#except:
socket_txt="No socket, sorry"
#from urlparse import urlparse
argument = os.environ['REQUEST_URI']+"ls"#asta ca sa stim ce buton cheama scriptul
reply="No reply, yet"#initializari
color_merge="FFFFFF"#culori pentru a marca daca radioul sau centrala merg
color_auto="FFFFFF"
radio_string=""#initializari




def exec_cmd(cmd):#ca sa execute comenzi de shell
        p = os.popen(cmd)
        result = ""
        while p.readline():
                result = result + p.readline()
    #.rstrip('\n')
        return result



#create an INET, STREAMing socket




try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    sys.exit()


host = '';#ne conectam la socketul existent
port = 9000;

#try:
#    remote_ip = socket.gethostbyname( host )

#except socket.gaierror:
    #could not resolve
#    print 'Hostname could not be resolved. Exiting'
#    sys.exit()

#Connect to remote server
s.connect((host, port))

#Send some data to remote server
message = "browser"+str(argument) #trimitem radioului mesajul de identificare
#plus ce buton a fost apasat

try :
    #Set the whole string
    s.sendall(message)
except socket.error:
    #Send failed
    sys.exit()


#Now receive data
reply_brut = s.recv(4096)#ce primim de la radio  -brut, of course
STATE= reply_brut[13:14]#recuperam starea radioului
if STATE=="0":
	STATE="METEO"
elif STATE=="1":
	STATE="RADIO"
elif STATE=="2":
	STATE= "MAIL"
else:
	STATE= "NEWS"
shi=reply_brut.find("&", 15)
vol=reply_brut[15:shi]#recuperam volumul
MERGE=reply_brut[shi+1:shi+2]#vedem daca merge radioul
if MERGE=="0":
	color_merge="#990000"
if MERGE=="1":
	color_merge="#00CC66"
shi2=reply_brut.find("&", shi+3)
STATIA=reply_brut[shi+3:shi2]#recuperam statia curenta
shi=shi2
shi2=reply_brut.find("&", shi+1)
AUTO=reply_brut[shi+1:shi2]#recuperam starea centralei si daca e auto etc.
shi=reply_brut.find("&", shi2+1)
status_cent=reply_brut[shi2+1:shi]
if status_cent=="0":
	status_cent="OPRITA"
	color_auto="#990000"
if status_cent=="1":
	status_cent="PORNITA"
	color_auto="#00CC66"
if reply_brut.find("&", shi+1) !=-1:
	rss_txt=reply_brut[shi+1:-6]#recuperam rss-ul sau meteo-ul etc
else: rss_txt=""
if MERGE=="0":
	radio_string="RADIO OFF"
if MERGE=="1":
	radio_string=STATIA+", Volum "+vol
reply= rss_txt
#reply=reply_brut
s.close()


#try:
#        if os.path.exists( "/tmp/python_unix_sockets_example" ):
#                os.remove( "/tmp/python_unix_sockets_example" )
#
#        server = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
#        server.bind("/tmp/python_unix_sockets_example")

#        socket_txt= server.recv( 1024 )
#        while not socket_txt:
#                socket_txt=server.recv( 1024 )
#                break
#                if "DONE" == socket_txt:
#                        break
#except:
#	socket_txt="bla_bla"

time_now=0#astea trei randuri cred ca nu mai conteaza
def get_time():
	time_now=time.time()

#socket_txt="text_variabil_&nbsp29 de caractere"
def html_out(variabila2, color_m, color_a, status_cent, AUTO, radio_string):
	print "Content-type: text/html"
	print
	print """
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<META HTTP-EQUIV="refresh" CONTENT="15">
	<title>Raspberry Control Panel</title>
	<style type="text/css">
	.arial {
		font-family: Arial, Helvetica, sans-serif;
		text-align: center;
		font-size: 14px;
	}
	</style>
	</head>
	<body>
	<table width="640" height="480" border="0" cellpadding="2" cellspacing="0">
	  <caption class="arial">
	  <strong>Centrala este """+status_cent+ ", in modul "+ AUTO+"<br>"+radio_string+"""
	  </strong>
	  </caption>
	  <tr>
            <td width="90" height="60" align="center" valign="middle"><form id="form1" name="form1" method="get" action="hello.py">
      	    <input name="v_up" type="submit" class="arial" id="v_upmm" value="V+" />
	    </form></td>
	    <td width="93" height="60" align="center" valign="middle"><form id="form2" name="form2" method="get" action="hello.py">
	      <input name="prog_up" type="submit" class="arial" id="prog_up"  value="P+" />
	    </form></td>
            <td width="100" height="60" align="center" valign="middle"><form id="form3" name="form3" method="get" action="hello.py">
              <input name="c_on" type="submit" class="arial" id="c_on"  value=" ON " />
            </form></td>
            <td width="91" height="60" align="center" valign="middle"><form id="form4" name="form4" method="get" action="hello.py">
              <input name="c_f_on" type="submit" class="arial" id="c_f_on"  value="FULL ON" />
            </form></td>

	    <td width="246" rowspan="2" align="center" valign="middle"><img src="poza.jpg" alt="" name="camera" width="320" height="240" id="camera" /></td>
	  </tr>
	  <tr>
            <td width="90" height="100" align="center" valign="middle"><form id="form5" name="form5" method="get" action="hello.py">
              <input name="v_down" type="submit" class="arial" id="v_down"  value="V-" />
            </form></td>
            <td width="93" height="100" align="center" valign="middle"><form id="form6" name="form6" method="get" action="hello.py">
              <input name="prog_down" type="submit" class="arial" id="prog_down"  value="P-" />
            </form></td>
            <td width="100" height="100" align="center" valign="middle"><form id="form7" name="form7" method="get" action="hello.py">
              <input name="c_off" type="submit" class="arial" id="c_off"  value="OFF" />
            </form></td>
            <td width="91" height="100" align="center" valign="middle"><form id="form8" name="form8" method="get" action="hello.py">
              <input name="c_f_off" type="submit" class="arial" id="c_f_off"  value="FULL OFF" />
            </form></td>
	  </tr>
	  <tr>
            <td width="90" height="68" align="center" valign="middle" bgcolor="
	    """ + color_m + """
           "><form id="form9" name="form9" method="get" action="hello.py">
              <input name="radio_on_off" type="submit" class="arial"  id="radio_on_off"  value="    ON/OFF    " />
            </form></td>
	    <td width="93" height="68" align="center" valign="middle">&nbsp;</td>
            <td width="100" height="68" align="center" valign="middle" bgcolor="
	    """ + color_a +  """
            "><form id="form10" name="form10" method="get" action="hello.py">
              <input name="auto" type="submit" class="arial" id="auto"  value="   AUTO   " />
            </form></td>
	    <td colspan="2" rowspan="2" align="center" valign="top"> 
	    <textarea name="texte" id="texte" cols="55" rows="10">
	"""+variabila2+"""
	  </textarea></td>
	  </tr>
	  <tr>
            <td width="90" height="100" align="center" valign="middle"><form id="form11" name="form11" method="get" action="hello.py">
              <input name="meteo" type="submit" class="arial" id="meteo"  value="  METEO   " />
            </form></td>
            <td width="93" height="100" align="center" valign="middle"><form id="form12" name="form12" method="get" action="hello.py">
              <input name="rss" type="submit" class="arial" id="rss"  value="  RSS   " />
            </form></td>
            <td width="100" height="100" align="center" valign="middle"><form id="form13" name="form13" method="get" action="hello.py">
              <input name="mail" type="submit" class="arial" id="mail"  value="  MAIL   " />
            </form></td>
	  </tr>
	</table>
	</body>
	
	</html>
	""" 
	return

html_out(reply, color_merge, color_auto,status_cent, AUTO, radio_string)
#asta genereaza html-ul care va fi afisat, cu variabilele de mai sus
#reply e rss-ul, meteo etc, color arata daca radioul si centrala merg, restul
#sunt texte
