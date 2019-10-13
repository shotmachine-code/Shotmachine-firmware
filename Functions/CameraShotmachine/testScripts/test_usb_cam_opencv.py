import cv2
import time
# Open the device at the ID 0

cap = cv2.VideoCapture("http://localhost:8080/?action=stream")

#Check whether user selected camera is opened successfully.
if not (cap.isOpened()):
	print('Could not open video device')

#To set the resolution
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'));

curr_millis = int(round(time.time() * 1000))

while(True):
	old_millis = curr_millis
	curr_millis = int(round(time.time() * 1000))
	diff = curr_millis-old_millis
	if diff>0:
		print(str(round(1000/diff)))
	else:
		print("inf")
	
	
	# Capture frame-by-frame
	ret, frame = cap.read()
	# Display the resulting frame
	#frame = cv2.flip(frame, flipCode=-1)
	cv2.imshow('preview',frame)
	#Waits for a user input to quit the application
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
		
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
