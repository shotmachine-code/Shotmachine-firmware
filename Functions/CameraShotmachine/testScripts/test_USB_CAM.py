
import pygame
import pygame.camera
from pygame.locals import *




def get_and_flip(snapshot):
	# if you don't want to tie the framerate to the camera, you can check
	# if the camera has an image ready.  note that while this works
	# on most cameras, some will never return true.
	if cam.query_image():
		snapshot = self.cam.get_image(snapshot)

	# blit it to the display surface.  simple!
	display.blit(snapshot, (0,0))
	pygame.display.flip()




pygame.init()
font = pygame.font.Font(None, 30)
clock = pygame.time.Clock()
pygame.display.set_caption("USB camera test")
#display = pygame.display.set_mode([1920,1080])

size = (3840,2160)
# create a display surface. standard pygame stuff
display = pygame.display.set_mode(size, 0)

pygame.camera.init()
# this is the same as what we saw before
clist = pygame.camera.list_cameras()
if not clist:
	raise ValueError("Sorry, no cameras detected.")
print(clist)
cam = pygame.camera.Camera(clist[0], size)
cam.start()

print(cam.get_controls())

# create a surface to capture to.  for performance purposes
# bit depth is the same as that of the display surface.
snapshot = pygame.surface.Surface(size, 0, display)


going = True
while going:
	events = pygame.event.get()
	for e in events:
		if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
			# close the camera safely
			cam.stop()
			going = False

	#get_and_flip(snapshot)
	if cam.query_image():
		snapshot = cam.get_image(snapshot)
		# blit it to the display surface.  simple!
		display.blit(snapshot, (0,0))
		pygame.display.flip()
		#print("New image")
		pygame.display.update()
		fps = clock.get_fps()
		#screen.blit(fps, (50, 50))
		print(fps)
		clock.tick(30)
		

	


