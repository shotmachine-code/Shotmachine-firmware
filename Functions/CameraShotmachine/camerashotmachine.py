# import the necessary packages

from threading import Thread
import numpy as np
import time
import datetime
from PIL import Image

import os
import logging
import platform
import pygame

currentOS = platform.system()
currentArch = platform.architecture()
if (currentOS == 'Linux' and currentArch[0] != '64bit'):
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    import cv2

class CameraShotmachine:
    def __init__(self, _windowPosSize=(200,0,900, 1200), waittime=3, _storagepath = ''):
        if _storagepath == '':
            self.storagepath = '/TakenImages/NotUploaded'
        else:
            self.storagepath = _storagepath
        self.logger = logging.getLogger(__name__)
        self.wait_time = waittime
        self.start_time = time.time()
        self.elapsed_time = 0
        self.window = _windowPosSize
        self.image = None
        self.stop = False
        self.running = False
        if (currentOS == 'Linux' and currentArch[0] != '64bit'):
            self.onRaspberry = True
        else:
            self.onRaspberry = False

        if self.onRaspberry:
            # initialize the camera and stream
            self.camera = PiCamera(sensor_mode = 4, resolution = (1632,1232))
            # self.captured_image = PiRGBArray(camera)
            self.camera.exposure_mode = 'nightpreview'
            # camera.resolution = (1640,1232)
            self.camera.image_denoise = True
            self.camera.rotation = 90
        else:
            # Create a black frame
            #picture = pygame.image.load('Functions/CameraShotmachine/testimage.png')
            img = Image.open('Functions/CameraShotmachine/testimage.png')
            img.load()
            picture = np.asarray(img, dtype="int32")
            self.save_image_name = "No picture taken"
            #picture = pygame.transform.scale(picture, (1440, 1080))
            #self.boundbox = picture.get_rect()
            self.image = picture
        
        Thread(target=self.run, args=()).start()
        self.logger.info('Class started')
        
    def run(self):
        
        
        while not self.stop:
            self.elapsed_time = time.time() - self.start_time
            # print(self.elapsed_time)
            if (self.elapsed_time > self.wait_time) and self.running:
                if self.onRaspberry:
                    self.camera.capture(self.captured_image, format = 'bgr', use_video_port=True)
                    self.camera.stop_preview()
                    self.captured_image = self.captured_image.array
                    self.captured_image = cv2.flip(self.captured_image, 1)
                    self.image = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
                    self.image = np.rot90(self.image)
                    # self.image = cv2.flip(self.image, 1)

                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    self.save_image_name = os.path.join(self.storagepath, datetimestring + '.png')
                    self.captured_image = cv2.flip(self.captured_image, 1)
                    cv2.imwrite(self.save_image_name,self.captured_image)
                    self.logger.info('Image saved in: ' + self.save_image_name)
                self.running = False
            time.sleep(0.1)

        if self.onRaspberry:
            self.camera.close()
        self.logger.info('Class terminated')
        

    def start(self):
        # start the thread to read frames from the video stream
        if self.onRaspberry:
            self.camera.start_preview(fullscreen = False, window = self.window, resolution = (1632,1232))
            self.start_time = time.time()
            self.captured_image = PiRGBArray(self.camera)
        self.elapsed_time = 0
        self.running = True
        self.logger.info("Start taking picture")


    def getprogress(self):
        # returns a number between 0 and 1 indicating how much percent 
        # of the waittime is elapsed
        progress_percent = (self.elapsed_time/self.wait_time)
        progress_percent = min(progress_percent,1)
        return progress_percent


    def getimage(self):
        # return the frame most recently taken
        while self.running:
            time.sleep(0.001)
        return self.image


    def requeststop(self):
        # indicate that the thread should be stopped
        self.stop = True

    def getimagename(self):
        return self.save_image_name
