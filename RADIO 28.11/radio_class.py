#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.55 2013/07/19 08:03:24 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#

import os
import string
import time
from log_class import Log
from translate_class import Translate

# System files
RadioLibDir = "/var/lib/radiod"
CurrentStationFile = RadioLibDir + "/current_station"
CurrentTrackFile = RadioLibDir + "/current_track"
VolumeFile = RadioLibDir + "/volume"

log = Log()
translate = Translate()

Mpd = "/usr/bin/mpd"	# Music Player Daemon
Mpc = "/usr/bin/mpc"	# Music Player Client

class Radio:
	# Input source
	RADIO = 0
	PLAYER = 1

	# Player options
	RANDOM = 0
	CONSUME = 1
	REPEAT = 2
	OPTION_LAST = REPEAT

	# Display Modes
	MODE_TIME = 0
	MODE_SEARCH  = 1
	MODE_SOURCE  = 2
	MODE_OPTIONS  = 3
	MODE_RSS  = 4
	MODE_IP  = 5
	MODE_LAST = MODE_IP
	MODE_SHUTDOWN = -1
	UP = 0
	DOWN = 1

	volume = 80	# Volume level 0 - 100%
	playlist = []	# Play list (tracks or radio stations)
	current_id = 1	# Currently playing track or station
	source = RADIO	# Source RADIO or Player
	reload = False	# Reload radio stations or player playlists
	option = ''     # Any option you wish
	artist = ""	# Artist (Search routines)
	errorStr = ""   # Error string
	switch = 0	# Switch just pressed
	soundMuted = False # Sound muted
	updateLib = False	# Reload radio stations or player

	display_mode = MODE_TIME	# Display mode
	display_artist = False		# Display artist (or tracck) flag
	current_file = ""  		# Currently playing track or station
	option_changed = False		# Option changed
	
	# MPD Options
	random = False	# Random play
	repeat = False	# Repeat play
	consume = False	# Ronsume tracks

	option = RANDOM         # Player option
	search_index = 0        # The current search index
	loadnew = False         # Load new track from search
	VERSION	= "1.16"	# Version number

	def __init__(self):
		log.init('radio')

		if not os.path.isfile(CurrentStationFile):
			self.execCommand ("mkdir -p " + RadioLibDir )

		# Set up current radio staion file
		if not os.path.isfile(CurrentStationFile) or os.path.getsize(CurrentStationFile) == 0:
		        self.execCommand ("echo 1 > " + CurrentStationFile)

		# Set up current track file
		if not os.path.isfile(CurrentTrackFile) or os.path.getsize(CurrentTrackFile) == 0:
		        self.execCommand ("echo 1 > " + CurrentTrackFile)

		# Set up volume file
		if not os.path.isfile(VolumeFile) or os.path.getsize(VolumeFile) == 0:
		        self.execCommand ("echo 75 > " + VolumeFile)

		# Create mount point for USB stick link it to the music directory
		if not os.path.isfile("/media"):
			self.execCommand("mkdir -p /media")
			self.execCommand("ln -f -s /media /var/lib/mpd/music")

		# Create mount point for USB stick link it to the music directory
		if not os.path.isfile("/share"):
			self.execCommand("mkdir -p /share")
			self.execCommand("ln -f -s /share /var/lib/mpd/music")

		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)

	# Start the MPD daemon
	def start(self):
		# Start the player daemon
		self.execCommand("service mpd restart")
		time.sleep(2)
		self.execMpcCommand("clear")
		self.randomOff()
		self.loadStations()
		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.getStoredID(self.current_file)
		self.execMpcCommand("play " + str(self.current_id))
		self.volume = self.getStoredVolume()
		self.setVolume(self.volume)
		return

	# Input Source RADIO, NETWORK or PLAYER
	def getSource(self):
		return self.source

	def setSource(self,source):
		self.source = source

	# Reload playlists flag
	def getReload(self):
		return self.reload

	def setReload(self,reload):
		self.reload = reload

	# Reload music library flag
	def getUpdateLibrary(self):
		return self.updateLib

	def setUpdateLibOn(self):
		self.updateLib = True

	def setUpdateLibOff(self):
		self.updateLib = False

	# Load new track flag
	def loadNew(self):
		return self.loadnew

	def setLoadNew(self,loadnew):
		self.loadnew = loadnew
		return

	# Volume
	def getVolume(self):
		return self.volume

	def setVolume(self,volume):
		if self.soundMuted: 
			self.unmute()
		else:
			self.volume = volume
			self.execMpcCommand("volume " + str(self.volume))
			self.storeVolume(self.volume)
		return

	def increaseVolume(self):
		if self.soundMuted: 
			self.unmute()
		else:
			self.volume = self.volume + 1
			if self.volume > 100:
				self.volume = 100
			self.setVolume(self.volume)
		return  self.volume

	def decreaseVolume(self):
		if self.soundMuted: 
			self.unmute()
		else:
			self.volume = self.volume - 1
			if self.volume < 0:
				self.volume = 0
			self.setVolume(self.volume)
		return  self.volume

	# Mute sound functions (Also stops MPD)
	def mute(self):
		self.execMpcCommand("volume 0")
		self.execMpcCommand("pause")
		self.soundMuted = True
		return

	def unmute(self):
		log.message("unmute soundMuted=" + str(self.soundMuted), log.DEBUG)
		if self.soundMuted:
			self.execMpcCommand("play " + str(self.current_id))
			self.execMpcCommand("volume " + str(self.getStoredVolume()))
			self.soundMuted = False
		return

	def muted(self):
		return self.soundMuted

	# Get the stored volume
	def getStoredVolume(self):
		volume = 75
		if os.path.isfile(VolumeFile):
			try:
				volume = int(self.execCommand("cat " + VolumeFile) )
			except ValueError:
				volume = 75

		return volume

	# Store volume in volume file
        def storeVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + VolumeFile)
		return

	# Random
	def getRandom(self):
		return self.random

	def randomOn(self):
		self.random = True
		self.execMpcCommand("random on")
		return

	def randomOff(self):
		self.random = False
		self.execMpcCommand("random off")
		return

	# Repeat
	def getRepeat(self):
		return self.repeat

	def repeatOn(self):
		self.repeat = True
		self.execMpcCommand("repeat on")

	def repeatOff(self):
		self.repeat = False
		self.execMpcCommand("repeat off")
		return

	# Consume
	def getConsume(self):
		return self.consume

	def consumeOn(self):
		self.consume = True
		self.execMpcCommand("consume on")
		return

	def consumeOff(self):
		self.consume = False
		self.execMpcCommand("consume off")
		return

	# Option changed 
	def optionChanged(self):
		return self.option_changed

	def optionChangedTrue(self):
		self.option_changed = True
		return

	def optionChangedFalse(self):
		self.option_changed = False
		return

	# Set  and get Display mode
	def getDisplayMode(self):
		return self.display_mode

	# Mode string for debugging
	def getDisplayModeString(self):
		sMode = ["MODE_TIME", "MODE_SEARCH", "MODE_SOURCE",
			 "MODE_OPTIONS", "MODE_RSS", "MODE_IP"] 
		return sMode[self.display_mode]

	def setDisplayMode(self,display_mode):
		self.display_mode = display_mode
		return
	
	# Set any option you like here 
	def getOption(self):
		return self.option

	def setOption(self,option):
		self.option = option
		return
	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand
	def execMpcCommand(self,cmd):
		return self.execCommand(Mpc + " " + cmd)

	# Get the ID  of the currently playing track or station ID
	# Return -1  if an error
	def getCurrentID(self):
		if self.soundMuted:
			return self.current_id

		self.current_id = -1
		status = self.execMpcCommand("status | grep \"ERROR:\" ")

		if status.__len__() < 1:
			status = self.execMpcCommand("status | grep \"\[playing]\" ")
			if status.__len__() > 1:
				x = status.index('#')+1
				y = status.index('/')
				try:
					self.current_id = int(status[x:y])
				except ValueError:
					self.current_id = 1
		else:
			log.message(status, log.INFO)
			self.errorStr = status

		currentid = self.current_id
		if currentid <= 0:
			currentid = 1
			
		self.execCommand ("echo " + str(currentid) + " > " + self.current_file)
		return self.current_id

	# Get the error string if a bad channel
	def getErrorString(self):
		return self.errorStr

	# Get the current status
	def getStatus(self):
		status = self.execMpcCommand("status | grep \"ERROR:\" ")
		if status.__len__() > 1:
			status = self.execMpcCommand("status")
		return status
		

	# Set the new ID  of the currently playing track or station (Also set search index)
	def setCurrentID(self,newid):
		self.current_id = newid

		# If an error (-1) reset to 1
		if self.current_id <= 0:
			self.current_id = 1

		# Don't allow an ID greater than the playlist length
		if self.current_id >= len(self.playlist):
			self.current_id = len(self.playlist)
		
		self.search_index = self.current_id - 1
		self.execCommand ("echo " + str(self.current_id) + " > " + self.current_file)
		self.execCommand("/usr/bin/mpc status > /var/lib/radiod/status")
		name = self.getCurrentName()
		log.message("(" + str(self.current_id) + ") " + name, log.INFO)
		return

	# Get the currently playing track from mpd (only ued by radiod.py)
	def getCurrentPlaying(self):
		currentPlaying = self.execMpcCommand("current")
		currentPlaying = translate.escape(currentPlaying)
		return currentPlaying

	# Get the name of the currently playing track from mpd (used by radio4.py)
	def getCurrentName(self):
		currentName = self.execMpcCommand("current")
		if self.source == self.PLAYER:
			sections = currentName.split(' - ')
			leng = len(sections) 
			if leng > 1:
				currentName = sections[1]

		currentName = translate.escape(currentName)
		return currentName

	# Get the name of the currently playing artist from mpd
	def getCurrentArtist(self):
		currentArtist = self.execMpcCommand("current")
		if self.source == self.PLAYER:
			sections = currentArtist.split(' - ')
			leng = len(sections) 
			if leng > 1:
				currentArtist = sections[0]
			else:
				currentArtist = "Unknown Artiest"

		currentArtist = translate.escape(currentArtist)
		return currentArtist

	# Get the last ID stored in /var/lib/radiod
	def getStoredID(self,current_file):
		if os.path.isfile(self.current_file):
			current_id = 1
			try:
				current_id = int(self.execCommand("cat " + self.current_file) )
			except ValueError:
				current_id = 1
		if current_id <= 0:
			current_id = 1
		return current_id

	# Change radio station up
	def channelUp(self):
		current_id = self.getCurrentID() + 1
		if current_id > len(self.playlist):
			current_id = 1
			self.play(current_id)
		else:
			self.execMpcCommand("next")

		current_id = self.getCurrentID() + 1
		self.setCurrentID(current_id)
		return

	# Change radio station down
	def channelDown(self):
		current_id = self.getCurrentID() - 1
		if current_id <= 0:
			current_id = len(self.playlist)
			self.play(current_id)
		else:
			self.execMpcCommand("prev")

		current_id = self.getCurrentID() + 1
		self.setCurrentID(current_id)
		return

	# Toggle the input source (Reload is done when Reload requested)
	def toggleSource(self):
		if self.source == self.RADIO:
			self.source = self.PLAYER

		elif self.source == self.PLAYER:
			self.source = self.RADIO

		return

	# Load radio stations
	def loadStations(self):
		log.message("radio.loadStations", log.DEBUG)
		self.execMpcCommand("pause")
		self.execMpcCommand("clear")

		dirList = os.listdir("/var/lib/mpd/playlists")
		for fname in dirList:
			cmd = "load \"" + fname.strip("\n") + "\""
			self.execMpcCommand(cmd)

		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.playlist = self.createPlayList()
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)
		self.execMpcCommand("play " + str(self.current_id))
		self.search_index = self.current_id - 1
		self.source = self.RADIO
		return

	# Load music library 
	def loadMusic(self):
		log.message("radio.loadMusic", log.DEBUG)
		self.execMpcCommand("stop")
		self.execMpcCommand("clear")
		# self.execMpcCommand("update")

		dirList=os.listdir("/var/lib/mpd/music/")
		for fname in dirList:
			cmd = "add \"" + fname.strip("\n") + "\""
			log.message(cmd,log.DEBUG)
			self.execMpcCommand(cmd)

		self.randomOn()
		self.repeatOff()
		self.consumeOff()
		self.playlist = self.createPlayList()
		self.current_file = CurrentTrackFile
		self.current_id = self.getStoredID(self.current_file)
		self.execMpcCommand("play " + str(self.current_id))
		self.search_index = self.current_id - 1
		return

	# Update music library 
	def updateLibrary(self):
		log.message("Update Music Library", log.INFO)
		self.execMpcCommand("-w update")
		self.setUpdateLibOff()
		return

	# Play a new track using search index
	def playNew(self,index):
		self.setLoadNew(False)
		self.play(index + 1)
		return

	# Play a track number 
	def play(self,number):
		log.message("Play " + str(number), log.DEBUG)
		if number > 0 and  number <= len(self.playlist):
			self.current_id = number
			self.setCurrentID(self.current_id)
			
		else:	
			log.message("play invalid station/track number "+ str(number), log.ERROR)
			self.setCurrentID(1)

		self.execMpcCommand("play " + str(self.current_id))
		return

	# Get list of tracks or stations
	def getPlayList(self):
		return self.playlist

	# Create list of tracks or stations
	def createPlayList(self):
		list = []
		line = ""
		cmd = "playlist"	
		p = os.popen(Mpc + " " + cmd)
		while True:
			line =  p.readline().strip('\n')
			if line.__len__() < 1:
				break
			line = translate.escape(line)
			list.append(line)
		self.playlist = list
		return list

	# Get the length of the current list
	def getListLength(self):
		return len(self.playlist)	

	# Display artist True or False
	def displayArtist(self):
		return self.display_artist

	def setDisplayArtist(self,dispArtist):
		self.display_artist = dispArtist

	# Set Search index
	def getSearchIndex(self):
		return self.search_index

	def setSearchIndex(self,index):
		self.search_index = index
		return

	# Get track name by Index
	def getTrackName(self,index):
		if index < 0:
			log.message("Get track index < 0", log.ERROR)
		
		sections = self.playlist[index].split(' - ')
		leng = len(sections)
		if leng > 1:
			artist = sections[0]
			track = sections[1]
		else:
			artist = "Unknown Artiest"
			track = self.playlist[index]
		track = translate.escape(track)
		return track

	# Get Radio station name by Index
	def getStationName(self,index):
		return self.playlist[index]
		

	# Get track name by Index
	def getArtistName(self,index):
		if index < 0:
			log.message("Get track index < 0", log.ERROR)

		sections = self.playlist[index].split(' - ')
		leng = len(sections)
		if leng > 1:
			artist = sections[0]
			track = sections[1]
		else:
			artist = "Unknown"
			track = self.playlist[index]
		artist = translate.escape(artist)
		return artist

	# Switch store and retrieval routines
	def setSwitch(self,switch):
		self.switch = switch
		return

	def getSwitch(self):
		return self.switch

	# Version number
	def getVersion(self):
		return self.VERSION


# End of Radio Class
