"""
 User interface van de shotmachine

 Maker: Marcel van Wensveen
 Datum: 09-feb-2019

"""

import pygame
import os
import threading
import queue
import time
#import cv2
#import sys
import logging
import psutil
from random import randint
from threading import Timer
from Functions.Interface.roller import Roller
#from Functions.PiVideoStream.PiVideoStream import PiVideoStream
from Functions.CameraShotmachine import camerashotmachine


class Shotmachine_Interface():

    def __init__(self, name, to_interface_queue, from_interface_queue):
        self.name = name
        self.To_interface = to_interface_queue
        self.From_interface = from_interface_queue
        self.state = 'Boot'
        self.recievebuffer = ''
        self.sendbuffer = ''
        self.done = False
        self.stopwatcher = False
        pygame.font.init()
        self.myfont = pygame.font.SysFont('Comic Sans MS', 30)

        self.thread = threading.Thread(target=self.queue_watcher,name='Interface_queue_watcher')
        self.thread.start()

        self.thread = threading.Thread(target=self.run, name=self.name)
        self.thread.start()

    def queue_watcher(self):
        
        while not self.stopwatcher:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.To_interface.get(block=True, timeout=0.1)
                    #print(self.recievebuffer)
                except queue.Empty:
                    pass
            if not self.sendbuffer == '':
                self.logger.info("Sending from interface: " + self.sendbuffer)
                self.From_interface.put(self.sendbuffer)
                if self.sendbuffer == "Quit":
                    self.stopwatcher = True
                self.sendbuffer = ''
            time.sleep(0.1)



    def load_main_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        pygame.display.update()
        boundingboxes = []
        number = randint(1, 100)
        self.roller1.stop_roller_direct(number)
        self.roller2.stop_roller_direct(number)
        self.roller3.stop_roller_direct(number)
        boundingboxes.append(self.roller1.draw_roller())
        boundingboxes.append(self.roller2.draw_roller())
        boundingboxes.append(self.roller3.draw_roller())

        pygame.display.update(boundingboxes)
        self.logger.info('Main screen loaded')
        


    def load_live_camera_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        self.camera.start()
        self.progress = 0
        pygame.display.update()
        self.logger.info('Live camera screen')

    def load_picture_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        image = self.camera.getimage()
        imgsurface = pygame.surfarray.make_surface(image)
        picturesize = (1440, 1080)
        #picturesize = (round(self.screensize[1]*(4/3)), self.screensize[1])
        imgsurface  = pygame.transform.scale(imgsurface, picturesize)
        self.screen.blit(imgsurface, (270, 0))
        pygame.display.update()
        self.start_showtime = time.time()
        imagename = self.camera.getimagename()
        self.sendbuffer = 'Taken Image:' + imagename
        self.logger.info('Taken picture screen')

    def load_config_screen(self):
        self.screen.fill(self.GRAY)
        CPUtemp_raw = psutil.sensors_temperatures()
        try:
            cputemp = str(CPUtemp_raw['cpu-thermal'][0].current).encode("utf-8").decode("utf-8")
        except KeyError:
            try:
                cputemp = str(CPUtemp_raw['coretemp'][0].current).encode("utf-8").decode("utf-8")
            except:
                cputemp = "error"
        cputemp_surface = self.myfont.render(cputemp, False, (0, 0, 0))
        self.screen.blit(cputemp_surface,(100,100))
        
        quitmessage_surf = self.myfont.render('press q to quit', False, (0, 0, 0))
        self.screen.blit(quitmessage_surf,(300,100))
        
        pygame.display.update()
        

    def run_rollers(self):
        self.roller1.start_roller(self.rollerspeed)
        self.roller2.start_roller(self.rollerspeed)
        self.roller3.start_roller(self.rollerspeed)
        stopimage = randint(1, 100)
        timer1 = Timer(1, self.roller1.stop_roller_smooth, [stopimage])
        timer1.start()
        timer2 = Timer(2.5, self.roller2.stop_roller_smooth, [stopimage])
        timer2.start()
        timer3 = Timer(4, self.roller3.stop_roller_smooth, [stopimage])
        timer3.start()
        self.logger.info('Starting rollers')


    def run(self):
        # Define some colors
        self.BLACK = (0, 0, 0)
        self.GRAY = (100,100,100)
        WHITE = (255, 255, 255)
        GREEN = (0, 255, 0)
        RED = (255, 0, 0)

        # Define some general variables
        screensize = [1920, 1080]

        Roll_Images_dir = 'Functions/Interface/Images/Roll_images'
        Background_image_dir = 'Functions/Interface/Images/background_image'
        Appname = "Shotmachine Interface"
        self.rollerspeed = 50  # defines how fast the rollers move before stopped

        # Define positions and size of rollers
        Roll_1_posx = 610
        Roll_2_posx = 965
        Roll_3_posx = 1320
        Roll_posy = 300
        Roll_width = 300
        Roll_height = 420  # Must be less than 2x width
        showtime = 5 # Defines how long the taken picture is shown

        # Init some system variables, do not change those
        updatelist = []

        self.logger = logging.getLogger(__name__)
        # Initialize program
        pygame.init()
        screeninfo = pygame.display.Info()
        self.screensize = [screeninfo.current_w, screeninfo.current_h]
        self.screen = pygame.display.set_mode(self.screensize)
        #self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)


        print(self.screensize)
        pygame.display.set_caption(Appname)
        clock = pygame.time.Clock()
        background_file = os.listdir(Background_image_dir)
        background_path = os.path.join(Background_image_dir, background_file[0])
        print(background_path)
        self.background_image = pygame.image.load(background_path).convert()

        # Init camera
        self.camera = camerashotmachine.CameraShotmachine(_windowPosSize = (270,0,1440, 1080), waittime=3)
        
        
        # Init rollers
        self.roller1 = Roller(Roll_1_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller2 = Roller(Roll_2_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller3 = Roller(Roll_3_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)

        # Create screen
        self.load_main_screen()
        current_screen = 'main'

        time.sleep(0.5)
        self.logger.info('Interface initialised')

        # -------- Main Program Loop -----------
        while not self.done:
            if not self.recievebuffer == '' and not current_screen == 'config':
                if self.recievebuffer == 'Roll_screen':
                    self.load_main_screen()
                    current_screen = 'main'
                if self.recievebuffer == 'Take_picture':
                    self.load_live_camera_screen()
                    current_screen = 'livecamera'
                if self.recievebuffer == 'Start_roll' and current_screen == 'main':
                    self.run_rollers()
                self.recievebuffer = ''

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sendbuffer = 'Quit'
                    self.done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == 282:  # F1
                        self.load_config_screen()
                        current_screen = 'config'
                    if event.key == 113 and current_screen == 'config':  # q
                        self.sendbuffer = 'Quit'
                        self.done = True

            # Update the rollers if needed
            if current_screen == 'main':
                updatelist.append(self.roller1.update_roller())
                updatelist.append(self.roller2.update_roller())
                updatelist.append(self.roller3.update_roller())
                
            if current_screen == 'livecamera':
                self.screen.fill([0,0,0])
                self.progress = self.camera.getprogress()
                if self.progress == 1:
                    self.load_picture_screen()
                    current_screen = 'picture'        
                
            if current_screen == 'picture':
                showtime_elapsed = time.time() - self.start_showtime
                if showtime_elapsed > showtime:
                    self.load_main_screen()
                    current_screen = 'main'
                        
                
            # Limit to 60 frames per second
            clock.tick(60)

            # Update the screen with what has changed.
            pygame.display.update(updatelist)
            updatelist = []

        # Close everything down
        pygame.quit()
        self.camera.requeststop()
        while self.stopwatcher == False:
                time.sleep(0.1)
        self.logger.info('Interface stopped')
