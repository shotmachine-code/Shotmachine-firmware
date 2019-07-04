# import the necessary packages
from Functions.CameraShotmachine import camerashotmachine
import cv2
import time

camera = camerashotmachine.CameraShotmachine(waittime=1)
camera.start()
progress = 0
while not progress == 1:
	progress = camera.getprogress()
	print(progress)
	time.sleep(0.1)

image = camera.getimage()

cv2.imshow('image',image)
cv2.waitKey(0)
cv2.destroyAllWindows()
camera.requeststop()


