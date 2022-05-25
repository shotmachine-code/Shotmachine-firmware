# import the necessary packages

from threading import Thread
import numpy as np
import time
import datetime
import os
import logging
import platform
import pygame

currentOS = platform.system()
currentArch = platform.architecture()
if currentOS == 'Linux' and currentArch[0] != '64bit':
    import cv2
    from picamera.array import PiRGBArray
    from picamera import PiCamera


class CameraShotmachine:
    def __init__(self, storagepath='TakenImages/NotUploaded', HandleShotmachine=None):
        # function to use both the USB and CSI2 camera for live preview and taking pictures

        # Init variables
        self.getSmallFrame = True
        self.stopped = False
        self.grabbed_small = False
        self.grabFullFrame = False
        self.grabbed_full = False
        self.success_save = False
        self.SmallProcessed = False

        # Store inputs
        if HandleShotmachine is None:
            HandleShotmachine = []
        self.HandleShotmachine = HandleShotmachine
        self.StoragePath = storagepath

        # Set which type of camera is attached
        self.useCamera = "CSI2"  # , "CSI2" / "USB"

        # Prepare variables
        self.logger = logging.getLogger(__name__)
        self.onRaspberry = self.HandleShotmachine["Settings"]["OnRaspberry"]
        self.smallFrameSize = (1280, 720)
        self.fullFrameSize = (3840, 2160)

        # check if folder for saving pictures is there, or create it
        folderDirList = self.StoragePath.split("/")
        appPath = ""
        for i in range(0, len(folderDirList)):
            appPath = appPath + folderDirList[i] + "/"
            if not (os.path.isdir(appPath)):
                os.mkdir(appPath)
                self.logger.info("Created new folder: " + appPath)

        if self.onRaspberry and self.useCamera == "CSI2":  # CSI2 camera
            # initialize the camera and stream
            self.camera = PiCamera(resolution=(2048, 1520))
            # self.captured_image = PiRGBArray(camera)
            # self.camera.exposure_mode = 'nightpreview'
            # camera.resolution = (1640,1232)
            # self.camera.image_denoise = True
            # self.camera.rotation = 270
            self.camera.hflip = True
            self.camera.zoom = (0.25, 0.3, 0.5, 0.5)

        if self.onRaspberry and self.useCamera == "USB":  # USB camera
            # Open and prepare camera
            self.stream = cv2.VideoCapture(0)
            self.stream.open(0, apiPreference=cv2.CAP_V4L2)
            self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.smallFrameSize[0])
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.smallFrameSize[1])
            self.stream.set(cv2.CAP_PROP_FPS, 30.0)
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 4)

            # Take one frame from camera to ensure it's working correctly
            (success_grab, frame_raw) = self.stream.read()
            frame_raw = frame_raw[:, ::-1, ::-1]
            frame_init = frame_raw.swapaxes(0, 1)
            self.cameraImageSmallSurf = pygame.surfarray.make_surface(frame_init)

        else:
            # In simulation mode, use stationary test image
            TestImage = pygame.image.load('Functions/CameraShotmachine/testimage.png')
            self.TestImageSmall = pygame.transform.scale(TestImage, (self.smallFrameSize[0], self.smallFrameSize[1]))
            self.TestImageFull = pygame.transform.scale(TestImage, (1920, 1080))
            self.save_image_name = "Test mode, no picture taken"

        self.logger.info('Camera class started')

    def start(self):
        # start the camera so it starts producing images

        if self.onRaspberry and self.useCamera == "CSI2":
            # self.camera.start_preview(fullscreen=False, window=self.window, resolution=(1632, 1232))
            self.camera.start_preview()
            #self.start_time = time.time()
            self.captured_image = PiRGBArray(self.camera)
            self.elapsed_time = 0
            self.running = True
            self.logger.info("Start taking picture with CSI2 camera")


        if self.useCamera == "USB":
            # The USB camera is started by threads to read frames from the video stream

            # Prepare some variables for the capturing process
            self.getSmallFrame = True
            self.stopped = False
            self.grabbed_small = False
            self.grabFullFrame = False
            self.grabbed_full = False
            self.success_save = False
            self.SmallProcessed = False

            # Start threads that take and process the camera frames
            if self.onRaspberry:
                Thread(target=self.update, args=()).start()
                Thread(target=self.process_small, args=()).start()

        return self

    def update(self):
        # Function (thread) to get frames from USB camera in the background

        while not self.stopped:
            # In live (preview) mode, take low-res images from camera, it's much faster
            if self.getSmallFrame:
                success_grab = False
                try:
                    while not success_grab:
                        (success_grab, self.grabbedSmallFrame) = self.stream.read()
                        self.grabbed_small = success_grab
                except:
                    continue

            # Take full-res (4K) image from camera for picture
            else:
                # First switch camera to high-res mode, takes some time
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.fullFrameSize[0])
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.fullFrameSize[1])

                # Wait until command to take picture, controlled from other process to ensure correct timing
                while not self.grabFullFrame:
                    time.sleep(0.0001)

                # Take high-res picture, single frame
                success_grab = False
                while not success_grab:
                    (success_grab, frame) = self.stream.read()

                # Process frame
                ScreenFrame = frame[::2, ::-2,
                              ::-1]  # scale image by 0.5 by removing every second row and column, swap BGR to RGB, flip Up/down
                frame_full = ScreenFrame.swapaxes(0, 1)  # rotate image by flipping axis
                self.cameraImagefullSurf = pygame.surfarray.make_surface(frame_full)

                # Indicate that picture is ready and can be shown to user
                self.stopped = True
                self.grabbed_full = success_grab

                # Switch camera back to low-res mode for live camera
                self.stream.release()
                self.stream = cv2.VideoCapture(0)
                self.stream.open(0, apiPreference=cv2.CAP_V4L2)
                self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.smallFrameSize[0])
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.smallFrameSize[1])
                self.stream.set(cv2.CAP_PROP_FPS, 30.0)
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 4)

                # Save image to disk, use raw high-res frame from camera because saving process is bit different
                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.save_image_name = os.path.join(self.StoragePath, datetimestring + '.jpg')
                FrameToSave = np.fliplr(frame)
                cv2.imwrite(self.save_image_name, FrameToSave)
                self.logger.info('Image saved in: ' + self.save_image_name)
                self.success_save = True

    def process_small(self):
        # Function (thread) to process low-res images from USB camera to correct format
        # put in separate thread so capturing from USB camera is continued

        while not self.stopped:
            if self.getSmallFrame:
                if self.grabbed_small:
                    frameIn = self.grabbedSmallFrame
                    self.grabbed_small = False
                    frameFlip = frameIn[:, ::-1,
                                ::-1]  # flip Up/down with second operator, flip colors from BGR to RGB with last operator
                    frameRot = frameFlip.swapaxes(0, 1)  # Rotate image so it is now mirrored instead of flipped up/down
                    pygame.pixelcopy.array_to_surface(self.cameraImageSmallSurf, frameRot)
                    self.SmallProcessed = True

    def read_small(self):
        # Return the most recent low-res frame
        if self.onRaspberry and self.useCamera == "CSI2":
            pass            # CSI2 camera is already running, do nothing here
        if self.onRaspberry and self.useCamera == "USB":
            while not self.SmallProcessed and self.getSmallFrame:
                time.sleep(0.00001)
            self.grabbed_small = False
            return self.cameraImageSmallSurf
        else:
            self.grabbed_small = False
            return self.TestImageSmall

    def switch_to_full(self):
        # Function to indicate that camera must be switched to high-res mode
        self.grabFullFrame = False
        self.getSmallFrame = False

    def read_full(self):
        # Take still image using CSI2 camera
        if self.onRaspberry and self.useCamera == "CSI2":
            # take image using still port (high res, low noise)
            # self.camera.capture(self.captured_image, format='bgr', use_video_port=True)
            self.camera.capture(self.captured_image, format='rgb')

            # stop preview
            self.camera.stop_preview()

            # Process image to return to interface for displaying
            self.captured_image = self.captured_image.array
            self.captured_image = cv2.flip(self.captured_image, 1)
            self.image = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
            # self.image = np.rot90(self.image)
            self.cameraImagefullSurf = pygame.surfarray.make_surface(self.image)

            # Save image to file
            datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.save_image_name = os.path.join(self.StoragePath, datetimestring + '.jpg')
            self.captured_image = cv2.flip(self.captured_image, 1)
            cv2.imwrite(self.save_image_name, self.captured_image)
            self.logger.info('Image saved in: ' + self.save_image_name)

            return self.cameraImagefullSurf

        # Instruct to take high-res picture from USB camera and return scaled frame to display
        if self.onRaspberry and self.useCamera == "USB":
            # Indicate to take picture
            self.grabFullFrame = True

            # wait until picture is taken and ready to be shown
            while not self.grabbed_full and not self.getSmallFrame:
                time.sleep(0.0001)
            self.grabbed_full = False
            return self.cameraImagefullSurf



        else:
            self.grabbed_full = False
            return self.TestImageFull

    def get_imagename(self):
        # Fucntion that returns the filename of the most recent picture, for uploading
        if self.onRaspberry:
            while not self.success_save:
                time.sleep(0.0001)
            return self.save_image_name
        else:
            return "No Image"
