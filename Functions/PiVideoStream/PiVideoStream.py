# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import numpy as np
import time

import cv2


class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=25):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.exposure_mode = 'night'
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr", use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.frame_raw = None
        self.stopped = False
        self.initialised = False
        self.newframe = False


    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        Thread(target=self.processImage, args=()).start()
        return self


    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            
            self.frame_raw = f.array
            self.rawCapture.truncate(0)
            self.newframe = True
            
            #print('new frame!')
            
            # prepare the frame
            #frame_rgb= cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB)
            #self.frame = np.rot90(frame_rgb)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return


    def processImage(self):
        while True:
            if self.newframe == True:
                self.initialised = True
                self.frame = cv2.cvtColor(self.frame_raw, cv2.COLOR_BGR2RGB)
                #self.frame = np.rot90(frame_rgb)
                self.initialised = True
                self.newframe = False
                
            else:
                time.sleep(0.01)
            
            if self.stopped:
                return
    

    def read(self):
        # return the frame most recently read
        while not self.initialised == True:
            time.sleep(0.1)
        return self.frame


    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
