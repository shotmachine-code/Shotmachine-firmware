# import the necessary packages
from threading import Thread
import cv2
import imutils
import pygame
import time
 
class WebcamVideoStream:
	def __init__(self, _src=0, _resx=600, _resy=400):
		self.src = _src
		#self.resx = _resx
		#self.resy = _resy
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(self.src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 960) #800
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 540) #600
		self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
		self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
		(self.grabbed, self.frame) = self.stream.read()
		#self.small_frame = cv2.resize(self.frame, None, (0,0), fx = 0.4, fy = 0.4)
		
 
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
		#self.small_ready = False
		self.grabbed_small = False
		self.grabbed_full = False
		#self.small_flip_ready = False
		self.getSmallFrame = True

		
	def start_USB(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update_USB, args=()).start()
		return self
 
	def update_USB(self):
		while not self.stopped:

			# otherwise, read the next frame from the stream
			if self.getSmallFrame:
				try:
					(success_grab, self.frame) = self.stream.read()
					print("New frame")
					self.small_frame = self.frame
					#self.small_frame = cv2.resize(self.frame, None, (0,0), fx = 0.4, fy = 0.4)
					#self.small_frame_flip = cv2.flip(self.small_frame, 0)
					self.grabbed_small = success_grab
					self.grabbed_full = False
				except:
					continue
			if not self.getSmallFrame:
				try:
					self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 3840) #800
					self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160) #600
					(success_grab, self.frame) = self.stream.read()
					print("New full frame")
					self.full_frame = self.frame
					#self.small_frame = cv2.resize(self.frame, None, (0,0), fx = 0.4, fy = 0.4)
					#self.small_frame_flip = cv2.flip(self.small_frame, 0)
					self.grabbed_small = False
					self.grabbed_full = success_grab
					self.stopped = True
				except:
					continue
			


 
	def read_small(self):
		# return the frame most recently read
		while not self.grabbed_small and self.getSmallFrame:
			time.sleep(0.0001)
		self.grabbed_small = False
		return self.small_frame
		
		
	def read_full(self):
		self.getSmallFrame = False
		while not self.grabbed_full and not self.getSmallFrame:
			time.sleep(0.0001)
		self.grabbed_full = False
		self.stopped = True
		return self.full_frame
		
		# return the frame most recently read
		#self.stream.release()
		#stream = cv2.VideoCapture(self.src)
		#self.stopped = True
		#self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 3840) #800
		#self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160) #600
		#(success_grab, full_frame) = self.stream.read()
		#while not self.grabbed_full:
		#	time.sleep(0.0001)
		#self.full_frame_flip = cv2.flip(self.frame, 0)
		#return full_frame
		#self.grabbed_full = False

 
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
