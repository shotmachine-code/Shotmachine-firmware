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
        
        #if (currentOS == 'Linux' and currentArch[0] != '64bit'):
        #    self.onRaspberry = True
        #else:
        #    self.onRaspberry = False
        #self.onRaspberry = False

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
            #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])  # 800 960
            #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])  # 600 540
            self.stream.set(cv2.CAP_PROP_FPS, 30.0)
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            
            (success_grab, frame_raw) = self.stream.read()
            smallFrameRaw = cv2.resize(frame_raw, dsize=self.size, interpolation=cv2.INTER_NEAREST) 
                        #RGB_frame = cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB)
            RGB_frame = cv2.cvtColor(smallFrameRaw, cv2.COLOR_BGR2RGB)
            frame = np.rot90(RGB_frame)
            self.cameraImageSurf = pygame.surfarray.make_surface(frame)
            
            #(self.grabbed, self.frame) = self.stream.read()
            center_small = (self.size[0] /2, self.size[1] / 2)
            center_full = (3840 / 2, 2160 / 2)
            
            #self.rotationMatrix_small = cv2.getRotationMatrix2D(center_small, 90, 1)
            #self.rotationMatrix_full = cv2.getRotationMatrix2D(center_full, 90, 1)


            self.stopped = False
            self.grabbed_small = False
            self.grabbed_full = False
            self.getSmallFrame = True
            self.grabFullFrame = False

        else:
            # Create a black frame
            #picture = pygame.image.load('Functions/CameraShotmachine/testimage.png')
            img = Image.open('Functions/CameraShotmachine/testimage.png')
            img.load()
            img.resize((540, 960))
            picture_raw = np.asarray(img, dtype="int32")
            self.save_image_name = "Test mode, no picture taken"
            picture = np.rot90(picture_raw)
            #picture = pygame.transform.scale(picture, (1440, 1080))
            #self.boundbox = picture.get_rect()
            self.image = picture
        
        #Thread(target=self.run, args=()).start()
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
            return self


            self.logger.info("Start taking picture with USB")



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
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.onRaspberry:
            #picture = pygame.image.load('Functions/CameraShotmachine/testimage.png')
            img = Image.open('Functions/CameraShotmachine/testimage.png')
            img.load()
            img.resize(((540, 960)))
            picture_raw = np.asarray(img, dtype="int32")
            picture = np.rot90(picture_raw)
            self.save_image_name = "Test mode, no picture taken"
            #picture = pygame.transform.scale(picture, (960, 540))
            # self.boundbox = picture.get_rect()
            self.TestImage = picture

        if self.onRaspberry:
            Thread(target=self.update_USB, args=()).start()
        return self


    def update_USB(self): # USB camera

        while not self.stopped:
            if self.getSmallFrame:
                try:
                    success_grab = False
                    while not success_grab:
                        (success_grab, frame_raw) = self.stream.read()
                        #smallFrameRaw = cv2.resize(frame_raw, dsize=self.size, interpolation=cv2.INTER_NEAREST) 
                        RGB_frame = cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB)
                        #RGB_frame = cv2.cvtColor(smallFrameRaw, cv2.COLOR_BGR2RGB)
                        frame = np.rot90(RGB_frame)
                        pygame.pixelcopy.array_to_surface(self.cameraImageSurf, frame)
                    self.frame_small = frame
                    self.grabbed_small = success_grab
                except:
                    continue
            else:
                
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
                #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                success_grab = False
                while not success_grab:
                    (success_grab, frame) = self.stream.read()
                while not self.grabFullFrame:
                    time.sleep(0.0001)
                    #print("Waiting for grab")
                (success_grab, frame) = self.stream.read()
                #(success_grab, frame) = self.stream.retrieve()
                ScreenFrame = cv2.resize(frame, dsize=(1920, 1080), interpolation=cv2.INTER_NEAREST) #cv2.INTER_CUBIC)
                RGBScreenFrame = cv2.cvtColor(ScreenFrame, cv2.COLOR_BGR2RGB)
                #RGBScreenFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame_full = np.rot90(RGBScreenFrame)
                self.stopped = True
                self.grabbed_full = success_grab
                self.grabFullFrame = False
                
                self.stream.release()
                self.stream = cv2.VideoCapture()
                self.stream.open(0, apiPreference=cv2.CAP_V4L2)
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])  # 800 960
                #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])  # 600 540
                self.stream.set(cv2.CAP_PROP_FPS, 30.0)
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                
                #self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # 800 self.size[0]
                #self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # 600 self.size[1]

                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.save_image_name = os.path.join(self.storagepath, datetimestring + '.png')
                FrameToSave = np.fliplr(frame)
                cv2.imwrite(self.save_image_name, FrameToSave)
                self.logger.info('Image saved in: ' + self.save_image_name)
                
                self.success_save = True
                

    def read_small(self): # USB camera
        # return the frame most recently read
        if self.onRaspberry:
            while not self.grabbed_small and self.getSmallFrame:
                time.sleep(0.0001)
            self.grabbed_small = False
            #return self.frame_small
            return self.cameraImageSurf
        else:
            self.grabbed_small = False
            return self.TestImage

    def Switch_to_full(self):
        self.grabFullFrame = True
        self.getSmallFrame = False
        #print("Switch")

    def read_full(self): # USB camera
        
        #self.getSmallFrame = False
        #self.full_grabbed = True
        if self.onRaspberry:
            self.grabFullFrame == True
            #while True:
            #    print("try to grab")
            #    self.full_grabbed = self.stream.grab()
            #    if self.full_grabbed == True:
            #        break
            while not self.grabbed_full and not self.getSmallFrame:
                #print("Waiting for frame")
                time.sleep(0.0001)
            self.grabbed_full = False
            print("Frame ready")
            return self.frame_full
        else:
            self.grabbed_full = False
            return self.TestImage


    def getimagename_USB(self):
        if self.onRaspberry:
            while not self.success_save:
                time.sleep(0.0001)
            return self.save_image_name
        else:
            return "No Image"
