import pygame
from pygame.locals import *
import cv2
import numpy as np
import sys
import imutils
import time
from Functions.PiVideoStream.PiVideoStream import PiVideoStream

resolution = (720, 1280)
framerate = 40


camera = PiVideoStream(resolution, framerate)
camera.start()
time.sleep(2.0)
#camera = cv2.VideoCapture()
pygame.init()
font = pygame.font.Font(None, 30)
clock = pygame.time.Clock()
pygame.display.set_caption("OpenCV camera stream on Pygame")
screen = pygame.display.set_mode([1280,720])

try:
	while True:
		#stream.update()
		
		frame = camera.read()

		#ret, frame = camera.read()
		
		screen.fill([0,0,0])
		
		frame = pygame.surfarray.make_surface(frame)
		screen.blit(frame, (0,0))
		#fps = font.render(str(int(clock.get_fps())), True, pygame.Color('white'))
		fps = clock.get_fps()
		#screen.blit(fps, (50, 50))
		print(fps)
		pygame.display.update()
		clock.tick(60)

		for event in pygame.event.get():
			if (event.type == KEYDOWN):
				sys.exit(0)

except(KeyboardInterrupt,SystemExit):
	pygame.quit()
	camera.stop()
	cv2.destroyAllWindows()
