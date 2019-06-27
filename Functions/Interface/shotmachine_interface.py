"""
 User interface van de shotmachine

 Maker: Marcel van Wensveen
 Datum: 09-feb-2019

"""

import pygame
import os
from random import randint
from threading import Timer
from Functions.Interface.roller import Roller
from Functions.PiVideoStream.pivideostream import PiVideoStream
import threading
import queue
import time


class Shotmachine_Interface():

    def __init__(self, name, to_interface_queue, from_interface_queue):
        self.name = name
        self.To_interface = to_interface_queue
        self.From_interface = from_interface_queue
        # controller has state
        self.state = 'Boot'
        self.recievebuffer = ''
        self.sendbuffer = ''

        self.thread = threading.Thread(target=self.queue_watcher,name='Interface_queue_watcher')
        self.thread.start()

        self.thread = threading.Thread(target=self.run, name=self.name)
        self.thread.start()

    def queue_watcher(self):
        while True:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.To_interface.get(block=True, timeout=0.1)
                    print(self.recievebuffer)
                except queue.Empty:
                    continue
            if not self.sendbuffer == '':
                self.To_interface.put(self.sendbuffer)
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
        print('Main screen')

    def load_live_camera_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        pygame.display.update()
        print('Live camera screen')

    def load_picture_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        pygame.display.update()
        print('Picture screen')

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
        print('Start rollers')

    def run(self):
        # Define some colors
        self.BLACK = (0, 0, 0)
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
        Roll_1_posx = 400
        Roll_2_posx = 800
        Roll_3_posx = 1200
        Roll_posy = 550
        Roll_width = 300
        Roll_height = 420  # Must be less than 2x width

        # Define camera parameters
        CameraRes = (1200,900)
        CameraFPS = 30

        # Init some system variables, do not change those
        updatelist = []
        done = False

        # Initialize program
        pygame.init()
        self.screen = pygame.display.set_mode(screensize)
        pygame.display.set_caption(Appname)
        clock = pygame.time.Clock()
        background_file = os.listdir(Background_image_dir)
        background_path = os.path.join(Background_image_dir, background_file[0])
        self.background_image = pygame.image.load(background_path).convert()

        # Init camera
        camera = PiVideoStream(CameraRes, CameraFPS)
        camera.start()


        # Init rollers
        self.roller1 = Roller(Roll_1_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller2 = Roller(Roll_2_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller3 = Roller(Roll_3_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)

        # Create screen
        self.load_main_screen()
        current_screen = 'main'
        self.run_rollers()

        # -------- Main Program Loop -----------
        while not done:
            # --- Event Processing
            #for event in pygame.event.get():
            #    if event.type == pygame.QUIT:
            #        done = True
            #    if event.type == pygame.KEYDOWN:
            #        if event.key == 282:  # F1
            #            self.load_main_screen()
            #            current_screen = 'main'
            #        if event.key == 283:  # F2
            #            self.load_live_camera_screen()
            #            current_screen = 'livecamera'
            #        if event.key == 284:  # F3
            #            self.load_picture_screen()
            #            current_screen = 'picture'
            #        if event.key == 285 and current_screen == 'main':  # F4
            #            self.run_rollers()



            if not self.recievebuffer == '':
                if self.recievebuffer == 'Roll_screen':
                    self.load_main_screen()
                    current_screen = 'main'
                if self.recievebuffer == 'Take_picture':
                    self.load_live_camera_screen()
                    current_screen = 'livecamera'
                if self.recievebuffer == 'Show_picture':
                    self.load_picture_screen()
                    current_screen = 'picture'
                if self.recievebuffer == 'Start_roll' and current_screen == 'main':
                    self.run_rollers()
                self.recievebuffer = ''

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.To_interface.put('Quit')
                    done = True

            # Update the rollers if needed
            if current_screen == 'main':
                updatelist.append(self.roller1.update_roller())
                updatelist.append(self.roller2.update_roller())
                updatelist.append(self.roller3.update_roller())

            if current_screen == 'livecamera':
                [CamImage, CamBB] = camera.read()
                self.screen.blit(CamImage, CamBB, )
                updatelist.append(CamBB)

            # Limit to 60 frames per second
            clock.tick(60)

            # Update the screen with what has changed.
            pygame.display.update(updatelist)
            updatelist = []

        # Close everything down
        pygame.quit()
