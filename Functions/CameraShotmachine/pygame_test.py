
import pygame
import WebcamVideoStream
from pygame.locals import *
import cv2
import time

#pygame.init()
#font = pygame.font.Font(None, 30)
#clock = pygame.time.Clock()
#pygame.display.set_caption("USB camera test")

size = [1240,720]
# create a display surface. standard pygame stuff
#display = pygame.display.set_mode(size, 0)

#pygame.camera.init()
# this is the same as what we saw before
#clist = pygame.camera.list_cameras()
#if not clist:
#	raise ValueError("Sorry, no cameras detected.")
#print(clist)
#cam = pygame.camera.Camera(clist[0], size)
#cam.start()

#print(cam.get_controls())

# create a surface to capture to.  for performance purposes
# bit depth is the same as that of the display surface.

#snapshot = pygame.surface.Surface(size, 0, display)


going = True


vs = WebcamVideoStream.WebcamVideoStream(src=0, _resx=size[0], _resy=size[1])
vs.start()
#fps = FPS().start()

frame = vs.read_small()
#snapshot = vs.read()

#snapshot = pygame.surfarray.make_surface(frame)


curr_millis = int(round(time.time() * 1000))
start_millis = curr_millis

# font FONT_HERSHEY_DUPLEX FONT_HERSHEY_TRIPLEX
font = cv2.FONT_HERSHEY_TRIPLEX
  
# org 
org = (500, 400) 
  
# fontScale 
fontScale = 10
   
# Blue color in BGR 
color = (255, 255, 255) 
  
# Line thickness of 2 px 
thickness = 20


#cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
#cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

while going:

	old_millis = curr_millis
	curr_millis = int(round(time.time() * 1000))
	diff = curr_millis-old_millis
	if diff>0:
		print(str(round(1000/diff)))
	else:
		print("inf")
	
	run_time = round((curr_millis - start_millis )/1000)
	camera_frame = vs.read_small()
	#frame = cv2.putText(camera_frame, str(run_time), org, font, fontScale, color, thickness, cv2.LINE_AA)
	cv2.imshow("window", camera_frame)  
	print("refresh frame")
	if cv2.waitKey(1) == 27:
		picture = vs.read_full()
		cv2.imwrite("Image.jpg", picture)
		vs.stop()
		going = False
		exit(0)
	


