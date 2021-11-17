from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
from RtpPacket import RtpPacket
import time
from tkinter.messagebox import showinfo
import math

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	STARTAGAIN = 4
	SPEEDUP = 5
	SLOWDOWN = 6
	DESCRIBE = 7
	
	recv_packet_count = 0
	download_rate = 0
	download_rate_sqr = 0
	last_recv_time = time.time()
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Start again button			
		self.startagain = Button(self.master, width=20, padx=3, pady=3)
		self.startagain["text"] = "Start again"
		self.startagain["command"] = self.startAgain
		self.startagain.grid(row=1, column=3, padx=2, pady=2)

		# Create Speed up button			
		self.speedup = Button(self.master, width=20, padx=3, pady=3)
		self.speedup["text"] = "Speed up"
		self.speedup["command"] = self.speedUp
		self.speedup.grid(row=2, column=0, padx=2, pady=2)

		# Create Slow down button			
		self.slowdown = Button(self.master, width=20, padx=3, pady=3)
		self.slowdown["text"] = "Slow down"
		self.slowdown["command"] = self.slowDown
		self.slowdown.grid(row=2, column=1, padx=2, pady=2)

		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=2, column=2, padx=2, pady=2)
		
		# Create Describe button
		self.descrb = Button(self.master, width=20, padx=3, pady=3)
		self.descrb["text"] = "Describe"
		self.descrb["command"] = self.describe
		self.descrb.grid(row=2, column=3, padx=2, pady=2)

		# Create progress bar
		self.progressbar = Progressbar(self.master, orient=HORIZONTAL, length=300, mode='determinate')
		self.progressbar.grid(row=3, column=1, padx=2, pady=2, columnspan=2)
		self.master.update_idletasks()
		self.progressbar['value'] = 0

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=6, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		# TODO
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def startAgain(self):
		"""Setup button handler."""
		# TODO
		threading.Thread(target=self.listenRtp).start()
		self.state = self.READY

		self.playEvent = threading.Event()

		self.playEvent.clear()

		self.sendRtspRequest(self.STARTAGAIN)

	def speedUp(self):
		threading.Thread(target=self.listenRtp).start()
		self.state = self.READY

		self.playEvent = threading.Event()

		self.playEvent.clear()

		self.sendRtspRequest(self.SPEEDUP)

	def slowDown(self):
		threading.Thread(target=self.listenRtp).start()
		self.state = self.READY

		self.playEvent = threading.Event()

		self.playEvent.clear()

		self.sendRtspRequest(self.SLOWDOWN)

	def exitClient(self):
		"""Teardown button handler."""
		#TODO
		self.sendRtspRequest(self.TEARDOWN)		

		self.master.destroy() # Close the gui window

		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video
		except:
			pass

	def pauseMovie(self):
		"""Pause button handler."""
		#TODO
		if self.state == self.PLAYING:

			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		if self.state == self.READY:

			# Create a new thread to listen for RTP packets

			threading.Thread(target=self.listenRtp).start()

			self.playEvent = threading.Event()

			self.playEvent.clear()

			self.sendRtspRequest(self.PLAY)
	
	def describe(self):
		"""Describe button handler."""
		if self.state != self.INIT:
			self.sendRtspRequest(self.DESCRIBE)

	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		self.last_recv_time = time.time()
		while True:

			try:

				data = self.rtpSocket.recv(20480)
				
				if data:
					download_time = (time.time() - self.last_recv_time)
					rtpPacket = RtpPacket()

					rtpPacket.decode(data)

					currFrameNbr = rtpPacket.seqNum()

					print ("Current Seq Num: " + str(currFrameNbr))
					self.recv_packet_count += 1
										
					if currFrameNbr > self.frameNbr or self.requestSent == self.STARTAGAIN: # Discard the late packet

						self.frameNbr = currFrameNbr

						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

						self.master.update_idletasks()
						self.progressbar['value'] = int(currFrameNbr/self.totalFrame*100)
						# print(int(currFrameNbr/self.totalFrame*100))
					
					payload_size = os.path.getsize(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
					# Calculate E(X)
					self.download_rate = self.download_rate*(self.recv_packet_count-1) + (payload_size/download_time)
					self.download_rate = self.download_rate/self.recv_packet_count

					# Calculate E(X^2)
					# self.download_rate_sqr = self.download_rate_sqr*(self.recv_packet_count-1) + (payload_size/download_time)**2
					# self.download_rate_sqr = self.download_rate_sqr/self.recv_packet_count
				self.last_recv_time = time.time()
			except:

				# Stop listening upon requesting PAUSE or TEARDOWN

				if self.playEvent.isSet(): 
					
					break

				

				# Upon receiving ACK for TEARDOWN request,

				# close the RTP socket

				if self.teardownAcked == 1:

					self.rtpSocket.shutdown(socket.SHUT_RDWR)

					self.rtpSocket.close()

					break

					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		#TODO
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT

		file = open(cachename, "wb")

		file.write(data)

		file.close()

		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		#TODO
		photo = ImageTk.PhotoImage(Image.open(imageFile))

		self.label.configure(image = photo, height=288) 

		self.label.image = photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:

			self.rtspSocket.connect((self.serverAddr, self.serverPort))

		except:

			messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)

	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		# Setup request

		if requestCode == self.SETUP and self.state == self.INIT:

			threading.Thread(target=self.recvRtspReply).start()

			# Update RTSP sequence number.

			self.rtspSeq += 1

			

			# Write the RTSP request to be sent.

			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			

			# Keep track of the sent request.

			self.requestSent = self.SETUP 

		# STARTAGAIN request

		elif requestCode == self.STARTAGAIN and self.state == self.READY:

			self.rtspSeq += 1

			request = 'STARTAGAIN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.STARTAGAIN

		# SPEEDUP request

		elif requestCode == self.SPEEDUP and self.state == self.READY:

			self.rtspSeq += 1

			request = 'SPEEDUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.SPEEDUP

		# SLOWDOWN request

		elif requestCode == self.SLOWDOWN and self.state != self.INIT:

			self.rtspSeq += 1

			request = 'SLOWDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.SLOWDOWN

		# Play request

		elif requestCode == self.PLAY and self.state == self.READY:

			self.rtspSeq += 1

			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.PLAY

		# Pause request

		elif requestCode == self.PAUSE and self.state == self.PLAYING:

			self.rtspSeq += 1

			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.PAUSE

			
		# Teardown request

		elif requestCode == self.TEARDOWN and not self.state == self.INIT:

			self.rtspSeq += 1

			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) 

			self.requestSent = self.TEARDOWN
		
		# Describe request

		elif requestCode == self.DESCRIBE:

			self.rtspSeq += 1

			request = "DESCRIBE " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSesssion: " + str(self.sessionId)
			
			self.requestSent = self.DESCRIBE

		else:

			return

		# Send the RTSP request using rtspSocket.

		self.rtspSocket.send(bytes(request, 'utf-8'))

		print ('\nData sent:\n' + request)
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply:
				self.parseRtspReply(reply.decode('utf-8'))
			

			# Close the RTSP socket upon requesting Teardown
			
			if self.requestSent == self.TEARDOWN:
				print("shutdown")
				self.rtspSocket.shutdown(socket.SHUT_RDWR)

				self.rtspSocket.close()

				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		lines = data.split('\n')

		seqNum = int(lines[1].split(' ')[1])

		# Process only if the server reply's sequence number is the same as the request's

		if seqNum == self.rtspSeq:

			session = int(lines[2].split(' ')[1])

			# New RTSP session ID

			if self.sessionId == 0:

				self.sessionId = session

			

			# Process only if the session ID is the same

			if self.sessionId == session:

				if int(lines[0].split(' ')[1]) == 200: 

					if self.requestSent == self.SETUP:

						# Update RTSP state.

						self.state = self.READY

						# Open RTP port.

						self.openRtpPort()

						# Update total number of frames
						self.totalFrame = int(lines[-1].split(" ")[-1])
						# print(f"Total Frame: {self.totalFrame}")

					elif self.requestSent == self.STARTAGAIN:
						
						self.state = self.PLAYING
						self.playEvent.set()

					elif self.requestSent == self.PLAY:

						self.state = self.PLAYING

					elif self.requestSent == self.PAUSE:

						self.state = self.READY

						# The play thread exits. A new thread is created on resume.

						self.playEvent.set()

					elif self.requestSent == self.SPEEDUP:

						self.state = self.PLAYING
						self.playEvent.set()

					elif self.requestSent == self.SLOWDOWN:

						self.state = self.PLAYING
						self.playEvent.set()

					elif self.requestSent == self.TEARDOWN:

						self.state = self.INIT

						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
					
					elif self.requestSent == self.DESCRIBE:
						description = ""
						for i in range(3, len(lines)-1):
							description += lines[i] + "\n\n"
						packet_sent = int(lines[-1].split(" ")[-1])
						description += f"Packet loss: {(packet_sent - self.recv_packet_count)/packet_sent*100:.2f}%"
						description += f"\n\n-->Sent: {packet_sent}"
						description += f"\n\n-->Received: {self.recv_packet_count}"
						description += f"\n\nData rate: {self.download_rate/(1024):.0f} KB/s"
						# description += f"\n\nStd of Data rate: {math.sqrt(self.download_rate_sqr - self.download_rate**2)/1024:.0f} KB/s"
						# print(f"\n\n-->Sent: {packet_sent}\n-->Received: {self.recv_packet_coun}")
						showinfo("Description", description)
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)
		
		try:

			# Bind the socket to the address using the RTP port given by the client user

			self.rtpSocket.bind(("", self.rtpPort))

		except:

			messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)


	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO

		self.pauseMovie()

		if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):

			self.exitClient()

		else: # When the user presses cancel, resume playing.

			self.playMovie()
