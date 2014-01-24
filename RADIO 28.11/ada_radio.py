#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an Adafruit RGB-backlit LCD plate for Raspberry Pi.
# $Id: ada_radio.py,v 1.15 2013/07/02 13:16:54 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# 
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc' 
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#

import os
import signal
import subprocess
import sys
import time
import string
import datetime 
import atexit
import shutil
from ada_lcd_class import Adafruit_lcd
from time import strftime

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from log_class import Log
from rss_class import Rss

# Switch definitions
MENU_SWITCH = 25
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 17
DOWN_SWITCH = 18

UP = 0
DOWN = 1

# Player options
RANDOM = 0
CONSUME = 1
REPEAT = 2
RELOADLIB = 3
OPTION_LAST = RELOADLIB

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile

log = Log()
radio = Radio()
rss = Rss()
lcd = Adafruit_lcd()

# Register exit routine
def finish():
        lcd.clear()
        lcd.line1("Radio stopped")

atexit.register(finish)

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile
		log.init('radio')

		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio daemon version " + radio.getVersion(), log.INFO)

		hostname = exec_cmd('hostname')
		ipstring = "IP " + exec_cmd('hostname -I')
		myos = exec_cmd('uname -a')
                log.message(myos, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.line1(message)
		lcd.line2(ipstring)
                time.sleep(4)
		log.message("Restarting MPD", log.INFO)
		lcd.line2("Starting MPD")
		radio.start()
		log.message("MPD started", log.INFO)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.scroll2(mpd_version,no_interrupt)
		time.sleep(1)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

		# Main processing loop
		count = 0 
		while True:
			get_switch_states(lcd,radio,rss)
			radio.setSwitch(0)

			display_mode = radio.getDisplayMode()
			lcd.setScrollSpeed(0.3) # Scroll speed normal 

			# Shutdown command issued
                        if display_mode == radio.MODE_SHUTDOWN:
                                lcd.line1("Stopping radio")
                                radio.execCommand("service mpd stop")
                                radio.execCommand("shutdown -h now")
                                lcd.line2("Shutdown issued")
                                time.sleep(3)
                                lcd.line1("Radio stopped")
                                lcd.line2("Power off radio")
                                while True:
                                        time.sleep(1)

			if display_mode == radio.MODE_TIME:
				todaysdate = strftime("%H:%M %d/%m/%Y")
				lcd.line1(todaysdate)
				if radio.muted():
					lcd.line2("Sound muted")
				else:
					display_current(lcd,radio)

			elif display_mode == radio.MODE_SEARCH:
				display_search(lcd,radio)

			elif display_mode == radio.MODE_SOURCE:
				display_source_select(lcd,radio)

			elif display_mode == radio.MODE_OPTIONS:
				display_options(lcd,radio)

			elif display_mode == radio.MODE_IP:
				lcd.line2("Radio v" + radio.getVersion())
				ipstring = "IP " + exec_cmd('hostname -I')
				lcd.scroll1(ipstring, interrupt)

			elif display_mode == radio.MODE_RSS:
                                lcd.line1(todaysdate)
                                display_rss(lcd,rss)

			time.sleep(0.3)

	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "radiod status: not running"
	    		log.message(message, log.INFO)
			print message 
		else:
			message = "radiod running pid " + str(pid)
	    		log.message(message, log.INFO)
			print message 
		return

# End of class overrides

# Interrupt scrolling LCD routine
def interrupt():
	global lcd
	global radio
	global rss
	interrupt = get_switch_states(lcd,radio,rss)
	return interrupt

def no_interrupt():
	return False

# Call back routine called by switch events
def switch_event(switch):
	global radio
	radio.setSwitch(switch)
	return

# Check switch states
def get_switch_states(lcd,radio,rss):
	interrupt = False	# Interrupt display
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()	
	
	if lcd.buttonPressed(lcd.MENU):
		log.message("MENU switch mode=" + str(display_mode), log.DEBUG)
		radio.unmute()
		display_mode = display_mode + 1

		if display_mode > radio.MODE_LAST:
			display_mode = radio.MODE_TIME

		if display_mode == radio.MODE_RSS:
                        if not rss.isAvailable():
                                display_mode = display_mode + 1
			else:
                                lcd.line2("Getting RSS feed")

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+ 
					"(" + str(display_mode) + ")", log.DEBUG)

                # Shutdown if menu button held for > 3 seconds
                MenuSwitch = lcd.buttonPressed(lcd.MENU)
                count = 15
                while MenuSwitch:
                        time.sleep(0.2)
                        MenuSwitch = lcd.buttonPressed(lcd.MENU)
                        count = count - 1
                        if count < 0:
                                log.message("Shutdown", log.DEBUG)
                                MenuSwitch = False
                                radio.setDisplayMode(radio.MODE_SHUTDOWN)

		if radio.getUpdateLibrary():
			update_library(lcd,radio)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.getReload(): 
			source = radio.getSource()
			log.message("Reload " + str(source), log.INFO)
			lcd.line2("Reloading ")
			reload(lcd,radio)
			radio.setReload(False)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.optionChanged():
			radio.setDisplayMode(radio.MODE_TIME)
			radio.optionChangedFalse()

		elif radio.loadNew():
			log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
			radio.playNew(radio.getSearchIndex())
			radio.setDisplayMode(radio.MODE_TIME)

		time.sleep(0.2)
		interrupt = True

	elif lcd.buttonPressed(lcd.UP):
		log.message("UP switch", log.DEBUG)
		radio.unmute()

		if display_mode == radio.MODE_SOURCE:
			radio.toggleSource()
			radio.setReload(True)

		elif display_mode == radio.MODE_SEARCH:
 			scroll_search(radio,UP)

		elif display_mode == radio.MODE_OPTIONS:
			cycle_options(radio,UP)

		else:
			radio.channelUp()
			if display_mode == radio.MODE_RSS:
                                radio.setDisplayMode(radio.MODE_TIME)

		interrupt = True

	elif lcd.buttonPressed(lcd.DOWN):
		log.message("DOWN switch", log.DEBUG)
		radio.unmute()

		if display_mode == radio.MODE_SOURCE:
			radio.toggleSource()
			radio.setReload(True)

		elif display_mode == radio.MODE_SEARCH:
 			scroll_search(radio,DOWN)

		elif display_mode == radio.MODE_OPTIONS:
			cycle_options(radio,DOWN)

		else:
			radio.channelDown()
			if display_mode == radio.MODE_RSS:
                                radio.setDisplayMode(radio.MODE_TIME)

		interrupt = True

	elif lcd.buttonPressed(lcd.LEFT):
		log.message("LEFT switch" ,log.DEBUG)
		if display_mode == radio.MODE_OPTIONS:
 			toggle_option(radio,lcd)
			interrupt = True

		elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
 			scroll_artist(radio,DOWN)
			interrupt = True

		else:
			# Decrease volume
			volChange = True
			while volChange:

				# Mute function (Both buttons depressed)
				if lcd.buttonPressed(lcd.RIGHT):
					radio.mute()
					lcd.line2("Mute")
					time.sleep(2)
					volChange = False
					interrupt = True
				else:
					volume = radio.decreaseVolume()
					lcd.line2("Volume " + str(volume))
					volChange = lcd.buttonPressed(lcd.LEFT)

					if volume <= 0:
						volChange = False
					time.sleep(0.2)

	elif lcd.buttonPressed(lcd.RIGHT):
		log.message("RIGHT switch" ,log.DEBUG)
		if display_mode == radio.MODE_OPTIONS:
 			toggle_option(radio,lcd)
			interrupt = True

		elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
 			scroll_artist(radio,UP)
			interrupt = True
		else:
			# Increase volume
			volChange = True
			while volChange:

				# Mute function (Both buttons depressed)
				if lcd.buttonPressed(lcd.LEFT):
					radio.mute()
					lcd.line2("Mute")
					time.sleep(2)
					volChange = False
					interrupt = True
				else:
					volume = radio.increaseVolume()
					lcd.line2("Volume " + str(volume))
					volChange = lcd.buttonPressed(lcd.RIGHT) 

					if volume >= 100:
						volChange = False
					time.sleep(0.2)

	return interrupt

# Cycle through the options
# Only display reload the library if in PLAYER mode
def cycle_options(radio,direction):
	log.message("cycle_options " + str(direction) , log.DEBUG)

	option = radio.getOption()

	if direction == UP:
		option += 1
	else:
		option -= 1

	# Don;t display reload if not player mode
	source = radio.getSource()
	if option == RELOADLIB:
		if source != radio.PLAYER:
			if direction == UP:
				option = option+1
			else:
				option = option-1

	if option > OPTION_LAST:
		option = RANDOM
	elif option < 0:
		if source == radio.PLAYER:
			option = OPTION_LAST
		else:
			option = OPTION_LAST-1

	radio.setOption(option)
	radio.optionChangedTrue()
	return

# Toggle random mode
def toggle_option(radio,lcd):
	option = radio.getOption() 
	log.message("toggle_option option="+ str(option), log.DEBUG)

	if option == RANDOM:
		if radio.getRandom():
			radio.randomOff()
		else:
			radio.randomOn()

	elif option == CONSUME:
		if radio.getSource() == radio.PLAYER:
			if radio.getConsume():
				radio.consumeOff()
			else:
				radio.consumeOn()
		else:
			lcd.line2("Not allowed")
			time.sleep(2)

	elif option == REPEAT:
		if radio.getRepeat():
			radio.repeatOff()
		else:
			radio.repeatOn()
	elif option == RELOADLIB:
		if radio.getUpdateLibrary():
			radio.setUpdateLibOff()
		else:
			radio.setUpdateLibOn()

	radio.optionChangedTrue()
	return

# Update music library
def update_library(lcd,radio):
	log.message("Initialising music library", log.INFO)
	lcd.line1("Initialising")
	lcd.line2("Please wait")
	exec_cmd("/bin/umount /media")
	exec_cmd("/bin/umount /share")
	radio.updateLibrary()
	mount_usb(lcd)
	mount_share()
	log.message("Updatimg music library", log.INFO)
	lcd.line1("Updating Library")
	lcd.line2("Please wait")
	radio.updateLibrary()
	radio.loadMusic()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
	lcd.line1("Loading:")
	exec_cmd("/bin/umount /media")  # Unmount USB stick
	exec_cmd("/bin/umount /share")  # Unmount network drive

	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Radio Stations")
		dirList=os.listdir("/var/lib/mpd/playlists")
		for fname in dirList:
		       log.message("Loading " + fname, log.DEBUG)
		       lcd.line2(fname)
		       time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		mount_usb(lcd)
		mount_share()
		radio.loadMusic()
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			update_library(lcd,radio)
	return

# Mount USB  drive
def mount_usb(lcd):
	usbok = False
	if os.path.exists("/dev/sda1"):
		device = "/dev/sda1"
		usbok = True

	elif os.path.exists("/dev/sdb1"):
		device = "/dev/sdb1"
		usbok = True

	if usbok:
		exec_cmd("/bin/mount -o rw "+ device + " /media")
		log.message(device + " mounted on /media", log.DEBUG)
		dirList=os.listdir("/var/lib/mpd/music")
		for fname in dirList:
			lcd.line2(fname)
			time.sleep(0.1)
	else:
		msg = "No USB stick found!"
		lcd.line2(msg)
		time.sleep(2)
		log.message(msg, log.WARNING)
	return

# Mount any remote network drive
def mount_share():
	if os.path.exists("/var/lib/radiod/share"):
		myshare = exec_cmd("cat /var/lib/radiod/share")
		if myshare[:1] != '#':
			exec_cmd(myshare)
			log.message(myshare,log.DEBUG)
	return

# Display the RSS feed
def display_rss(lcd,rss):
        rss_line = rss.getFeed()
	lcd.setScrollSpeed(0.2) # Display rss feeds a bit quicker
        lcd.scroll2(rss_line,interrupt)
        return

# Display the currently playing station or track
def display_current(lcd,radio):
	current = radio.getCurrentPlaying()
	current_id = radio.getCurrentID()
	errorStr = radio.getErrorString()
	leng = len(current)

	if ( current_id < 0 ):
		lcd.scroll2(errorStr,interrupt)
	else:
		if leng > 16:
			lcd.scroll2(current[0:80],interrupt)
		elif  leng < 1:
			lcd.line2("No input stream!")
			time.sleep(1)
			radio.play(1) # Reset station or track
		else:
			lcd.line2(current)
	return

# Get currently playing station or track number from MPC
def get_current_id():
	current_id = 1
	status = radio.execMpcCommand("status | grep \"\[\" ")
	if len(status) > 1:
		x = status.index('#')+1
		y = status.index('/')
		current_id = int(status[x:y])
	exec_cmd ("echo " + str(current_id) + " > " + CurrentFile)
	return current_id

# Get the last ID stored in /var/lib/radiod
def get_stored_id(current_file):
	current_id = 5
	if os.path.isfile(current_file):
		current_id = int(exec_cmd("cat " + current_file) )
	return current_id

# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# Get list of tracks or stations
def get_mpc_list(cmd):
	list = []
	line = ""
	p = os.popen("/usr/bin/mpc " + cmd)
	while True:
		line =  p.readline().strip('\n')
		if line.__len__() < 1:
			break
		list.append(line)

	return list

# Scroll up and down between stations/tracks
def scroll_search(radio,direction):
	current_id = radio.getCurrentID()
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()

	# Artist displayed then don't increment track first time in
	
	if not radio.displayArtist():
		leng = len(playlist)
		log.message("len playlist =" + str(leng),log.DEBUG)
		if leng > 0:
			if direction == UP:
				index = index + 1
				if index >= leng:
					index = 0 
			else:
				index = index - 1
				if index < 0:
					index = leng - 1
			
	radio.setDisplayArtist(False)
	track =  radio.getTrackName(index)
 	radio.setSearchIndex(index)	
 	radio.setLoadNew(True)	
	return 

# Scroll through tracks by artist
def scroll_artist(radio,direction):
	radio.setLoadNew(True)
	index = radio.getSearchIndex()
	playlist = radio.getPlayList()
	current_artist = radio.getArtistName(index)

	found = False
	leng = len(playlist)
	count = leng
	while not found:
		if direction == UP:
			index = index + 1
			if index >= leng:
				index = 0
		elif direction == DOWN:
			index = index - 1
			if index < 1:
				index = leng - 1

		new_artist = radio.getArtistName(index)
		if current_artist != new_artist:
			found = True

		count = count - 1

		# Prevent everlasting loop
		if count < 1:
			found = True
			index = current_id

	# If a Backward Search find start of this list
	found = False
	if direction == DOWN:
		current_artist = new_artist
		while not found:
			index = index - 1
			new_artist = radio.getArtistName(index)
			if current_artist != new_artist:
				found = True
		index = index + 1
		if index >= leng:
			index = leng-1

	radio.setSearchIndex(index)
	return

# Source selection display
def display_source_select(lcd,radio):

	lcd.line1("Input Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Internet Radio")
	elif source == radio.PLAYER:
		lcd.line2("Music library")
	return

# Display search (Station or Track)
def display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		lcd.scroll1("(" + str(index+1) + ")" + current_artist[0:80],interrupt)
		current_track = radio.getTrackName(index)
		lcd.scroll2(current_track,interrupt)
	else:
		lcd.line1("Search:" + str(index+1))
		current_station = radio.getStationName(index)
		lcd.scroll2(current_station[0:80],interrupt)

	time.sleep(0.25)
	return



# Options menu
def display_options(lcd,radio):

	lcd.line1("Menu selection:")
	option = radio.getOption()

	if option == RANDOM:
		if radio.getRandom():
			lcd.line2("Random on")
		else:
			lcd.line2("Random off")

	elif option == CONSUME:
		if radio.getConsume():
			lcd.line2("Consume on")
		else:
			lcd.line2("Consume off")

	elif option == REPEAT:
		if radio.getRepeat():
			lcd.line2("Repeat on")
		else:
			lcd.line2("Repeat off")

	elif option == RELOADLIB:
		if radio.getUpdateLibrary():
			lcd.line2("Update list:Yes")
		else:
			lcd.line2("Update list:No")

	return


### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/radiod.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			os.system("service mpd stop")
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version " + radio.getVersion()
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 

