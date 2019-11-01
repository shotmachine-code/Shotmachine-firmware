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
    def __init__(self, _windowPosSize=(200,0,900, 1200), waittime=3, _storagepath = '', HandleShotmachine = []):
        if _storagepath == '':
            self.storagepath = 'TakenImages/NotUploaded'
        else:
            self.storagepath = _storagepath
        self.HandleShotmachine = HandleShotmachine
        self.logger = logging.getLogger(__name__)
        self.wait_time = waittime
        self.start_time = time.time()
        self.elapsed_time = 0
        self.window = _windowPosSize
        self.image = None
        self.stop = False
        self.running = False
        self.onRaspberry = self.HandleShotmachine["Settings"]["OnRaspberry"]

        self.useCamera = "USB" #, "CSI"

        if self.onRaspberry and self.useCamera == "CSI":
            # initialize the camera and stream
            self.camera = PiCamera(sensor_mode = 4, resolution = (1632,1232))
            # self.captured_image = PiRGBArray(camera)
            self.camera.exposure_mode = 'nightpreview'
            # camera.resolution = (1640,1232)
            self.camera.image_denoise = True
            self.camera.rotation = 270
            self.camera.hflip = True
        if self.onRaspberry and self.useCamera == "USB":
            #self.size = (960, 540)
            self.size = (640, 480)
            #self.size = (1025, 577)
            self.stream = cv2.VideoCapture()
            self.stream.open(0, apiPreference=cv2.CAP_V4L2)
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])  # 800 960
            #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])  # 600 540
            self.stream.set(cv2.CAP_PROP_FPS, 30.0)
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            
            (success_grab, frame_raw) = self.stream.read()
            #smallFrameRaw = cv2.resize(frame_raw, dsize=self.size, interpolation=cv2.INTER_NEAREST) 
            #RGB_frame = cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB)
            frame_raw = frame_raw[:,::-1,::-1]
            #frame_raw = frame_raw[:,::-1,::-1]
            #RGB_frame = cv2.cvtColor(smallFrameRaw, cv2.COLOR_BGR2RGB)
            #frame = np.rot90(RGB_frame)
            #frame = np.rot90(frame_raw)
            frame = frame_raw.swapaxes(0,1)
            self.cameraImageSmallSurf = pygame.surfarray.make_surface(frame)
            #self.ImageSmallArray = pygame.surfarray.pixels3d(self.cameraImageSurf)
            
            #(self.grabbed, self.frame) = self.stream.read()
            #center_small = (self.size[0] /2, self.size[1] / 2)
            #center_full = (3840 / 2, 2160 / 2)
            
            #self.rotationMatrix_small = cv2.getRotationMatrix2D(center_small, 90, 1)
            #self.rotationMatrix_full = cv2.getRotationMatrix2D(center_full, 90, 1)


            self.stopped = False
            self.grabbed_small = False
            self.grabbed_full = False
            self.getSmallFrame = True
            self.grabFullFrame = False
        else:  # In simulation mode, use stationary test image
            TestImage = pygame.image.load('Functions/CameraShotmachine/testimage.png')
            self.TestImageSmall = pygame.transform.scale(TestImage, (640, 480))
            self.TestImageFull = pygame.transform.scale(TestImage, (1920, 1080))
            self.save_image_name = "Test mode, no picture taken"

        self.logger.info('Class started')
        
    def run(self): # CSI
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
                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    self.save_image_name = os.path.join(self.storagepath, datetimestring + '.png')
                    self.captured_image = cv2.flip(self.captured_image, 1)
                    cv2.imwrite(self.save_image_name,self.captured_image)
                    self.logger.info('Image saved in: ' + self.save_image_name)
                self.running = False
            time.sleep(0.1)
        if self.onRaspberry:
            self.camera.close()
        self.logger.info('Camera module stopped')
        

    def start_CSI(self):
        # start the thread to read frames from the video stream
        if self.onRaspberry and self.useCamera == "CSI":
            self.camera.start_preview(fullscreen = False, window = self.window, resolution = (1632,1232))
            self.start_time = time.time()
            self.captured_image = PiRGBArray(self.camera)
            self.elapsed_time = 0
            self.running = True
            self.logger.info("Start taking picture withh CSI camera")
        if self.onRaspberry and self.useCamera == "USB":
            Thread(target=self.update, args=()).start()
            self.logger.info("Start taking picture with USB")
            return self


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


################## USB camera ########################

    def start_USB(self):
        # start the thread to read frames from the video stream
        self.grabbed_small = False
        self.grabbed_full = False
        self.getSmallFrame = True
        self.stopped = False
        self.success_save = False
        self.SmallProcessed = False

        if self.onRaspberry:
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            Thread(target=self.update_USB, args=()).start()
            Thread(target=self.Process_small, args=()).start()
        return self


    def update_USB(self): # USB camera
        while not self.stopped:
            if self.getSmallFrame:
                try:
                    success_grab = False
                    while not success_grab:
                        (success_grab, self.grabbedSmallFrame) = self.stream.read()
                        #print("Frame")
                        self.grabbed_small = success_grab
                except:
                    continue
            else:
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
                success_grab = False
                while not success_grab:
                    (success_grab, frame) = self.stream.read()
                while not self.grabFullFrame:
                    time.sleep(0.0001)
                (success_grab, frame) = self.stream.read()
                ScreenFrame = frame[::2,::-2,::-1] # scale image by 0.5 by removing every second row and column, swap BGR to RGB, flip Up/down
                frame_full = ScreenFrame.swapaxes(0,1) # rotate image by flipping axis
                self.cameraImagefullSurf = pygame.surfarray.make_surface(frame_full)
                self.stopped = True
                self.grabbed_full = success_grab
                self.grabFullFrame = False
                
                self.stream.release()
                self.stream = cv2.VideoCapture()
                self.stream.open(0, apiPreference=cv2.CAP_V4L2)
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.stream.set(cv2.CAP_PROP_FPS, 30.0)
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.save_image_name = os.path.join(self.storagepath, datetimestring + '.jpg')
                FrameToSave = np.fliplr(frame)
                cv2.imwrite(self.save_image_name, FrameToSave)
                self.logger.info('Image saved in: ' + self.save_image_name)
                
                self.success_save = True
    
    
    def Process_small(self):
        while not self.stopped:
            if self.getSmallFrame:
                if self.grabbed_small:
                    frameIn = self.grabbedSmallFrame
                    self.grabbed_small = False
                    frameFlip = frameIn[:,::-1,::-1] # flip Up/down with second operator, flip colors from BGR to RGB with last operator
                    frameRot = frameFlip.swapaxes(0,1) # Rotate image so it is now mirrored instead of flipped up/down
                    pygame.pixelcopy.array_to_surface(self.cameraImageSmallSurf, frameRot)
                    self.SmallProcessed = True
        

    def read_small(self): # USB camera
        # return the frame most recently read
        if self.onRaspberry:
            while not self.SmallProcessed and self.getSmallFrame:
                time.sleep(0.00001)
            self.grabbed_small = False
            return self.cameraImageSmallSurf
        else:
            self.grabbed_small = False
            return self.TestImageSmall
            

    def Switch_to_full(self):
        self.grabFullFrame = True
        self.getSmallFrame = False
        

    def read_full(self): # USB camera
        # return scaled full frame to display picture
        if self.onRaspberry:
            while not self.grabbed_full and not self.getSmallFrame:
                time.sleep(0.0001)
            self.grabbed_full = False
            return self.cameraImagefullSurf
        else:
            self.grabbed_full = False
            return self.TestImageFull


    def getimagename_USB(self):
        if self.onRaspberry:
            while not self.success_save:
                time.sleep(0.0001)
            return self.save_image_name
        else:
            return "No Image"
