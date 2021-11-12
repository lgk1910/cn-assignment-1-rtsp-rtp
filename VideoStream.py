import cv2

class VideoStream:
	def __init__(self, filename):
		self.filename = filename

		# self.totalFrame number of frames
		video = cv2.VideoCapture(filename)
		success = True
		self.totalFrame = 0
		while success:
			success,image = video.read()
			if success == False:
				break
			self.totalFrame += 1
		video.release()

		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0

	def nextFrame(self):
		"""Get next frame."""
		try:
			data = self.file.read(5) # Get the framelength from the first 5 bits
			if data: 
				framelength = int(data)
								
				# Read the current frame
				data = self.file.read(framelength)
				self.frameNum += 1
			return data
		except:
			pass
		return None
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	def currentFile(self):
		return self.file
	
	def getTotalFrame(self):
		return self.totalFrame