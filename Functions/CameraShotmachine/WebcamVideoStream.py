# import the necessary packages
from threading import Thread
import cv2
import imutils
import pygame
import time
 
class WebcamVideoStream:
	def __init__(self, src=0, _resx=600, _resy=400):
		
		self.resx = _resx
		self.resy = _resy
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
		self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
		self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
		(self.grabbed, self.frame) = self.stream.read()
		#self.small_frame = cv2.resize(self.frame, None, (0,0), fx = 0.33, fy = 0.33)
		
 
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
		self.small_ready = False
		self.grabbed_small = False
		self.grabbed_full = False
		self.small_flip_ready = False

		
	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self
 
	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return
 
			#while(True):
			#	prev_time=time.time()
			#	frame_ref = self.stream.grab()
			#	duration = time.time()-prev_time
			#	print(duration)
			#	if (duration)>0.030:#something around 33 FPS
			#		break
			#(success_grab,self.frame) = self.stream.retrieve(frame_ref)
			
			# otherwise, read the next frame from the stream
			(success_grab, self.frame) = self.stream.read()
			print("New frame")
			
			#self.small_frame = cv2.resize(self.frame, None, (0,0), fx = 0.3, fy = 0.3)
			#self.small_frame_flip = cv2.flip(self.small_frame, 0)
			self.grabbed_small = success_grab
			self.grabbed_full = success_grab
			


 
	def read_small(self):
		# return the frame most recently read
		while not self.grabbed_small:
			time.sleep(0.001)
		self.grabbed_small = False
		return self.frame
		
		
	def read_full(self):
		# return the frame most recently read
		while not self.grabbed_full:
			time.sleep(0.001)
		#self.full_frame_flip = cv2.flip(self.frame, 0)
		return self.frame
		self.grabbed_full = False

 
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
