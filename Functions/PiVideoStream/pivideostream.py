# import the necessary packages

from threading import Thread
# import cv2
import platform
import pygame


class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=32):
        currentOS = platform.system()
        currentArch = platform.architecture()
        if (currentOS == 'Linux' and currentArch[0] != '64bit'):
            self.onRaspberry = True
        else:
            self.onRaspberry = False

        if self.onRaspberry:
            # initialize the camera and stream
            from picamera.array import PiRGBArray
            from picamera import PiCamera

            self.camera = PiCamera()
            self.camera.resolution = resolution
            self.camera.framerate = framerate
            self.rawCapture = PiRGBArray(self.camera, size=resolution)
            self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr", use_video_port=True)
            self.frame = None

        else:
            # Create a black frame
            picture = pygame.image.load('Functions/PiVideoStream/testimage.png')
            picture = pygame.transform.scale(picture, resolution)
            self.boundbox = picture.get_rect()
            self.frame = picture

        # initialize the variable used to indicate if the thread should be stopped
        self.stopped = False


    def start(self):
        # start the thread to read frames from the video stream
        if self.onRaspberry:
            Thread(target=self.update_camera, args=()).start()
        elif platform.system() == 'Windows':
            pass
        return self


    def update_camera(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return


    def read(self):
        # return the frame most recently read
        return [self.frame, self.boundbox]


    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True