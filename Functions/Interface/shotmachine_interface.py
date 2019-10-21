
import pygame
import os
import threading
import queue
import time
import subprocess
import logging
import psutil
from random import randint
from threading import Timer
from Functions.Interface.roller import Roller
from Functions.CameraShotmachine import camerashotmachine
from Functions.Database import database_connection


class Shotmachine_Interface():

    def __init__(self, name, to_interface_queue, from_interface_queue, HandleShotmachine):
        self.name = name
        self.To_interface = to_interface_queue
        self.From_interface = from_interface_queue
        self.HandleShotmachine = HandleShotmachine
        self.state = 'Boot'
        self.recievebuffer = ''
        self.sendbuffer = ''
        self.run = True
        pygame.font.init()
        self.myfont = pygame.font.SysFont('freesansbold.ttf', 30)
        self.CountdownFont = pygame.font.SysFont('freesansbold.ttf', 600)
        self.showLastImage = False
        self.FileList = []

        #self.OperationMode = "PhotoBooth"
        self.OperationMode = "Shotmachine"

        self.TakenPhotosDir = 'TakenImages/NotUploaded'

        self.db_conn = database_connection.database_connection()

        self.EnableBarcodeScanner = self.HandleShotmachine["Settings"]["EnableBarcodeScanner"]

        self.thread = threading.Thread(target=self.queue_watcher,name='Interface_queue_watcher')
        self.thread.start()

        self.thread = threading.Thread(target=self.interfaceMain, name=self.name)
        self.thread.start()


    def queue_watcher(self):
        while self.run:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.To_interface.get(block=True, timeout=0.1)
                except queue.Empty:
                    pass
            time.sleep(0.1)


    def button(self, msg, x, y, w, h, ic, ac, action=None, PumpNumber=-1):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            buttoncolor = ac
            if click[0] == 1 and action != None and PumpNumber == -1: # Wifi config
                action()
                time.sleep(2)
            if click[0] == 1 and action != None and PumpNumber != -1: # een van de spoelknoppen
                action(PumpNumber)
                time.sleep(2)
        else:
            buttoncolor = ic
        textSurf = self.myfont.render(msg, False, self.BLACK, buttoncolor)
        textRect = textSurf.get_rect()
        textRect.center = ((x + (w / 2)), (y + (h / 2)))
        self.screen.blit(textSurf, textRect)
        return textRect

    def FlushPump(self, number):
        self.From_interface.put('Flush:'+str(number))


    def load_main_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w , self.screeninfo.current_h)
        pygame.display.update(FullScreenRect)
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

    def load_photobooth_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w , self.screeninfo.current_h)
        pygame.display.update(FullScreenRect)

        self.update_photoBoothPicture(1, True, True)

        #self.update_photoBoothPicture(2, False)
        #self.timer_PhotoBoothPhotoRefresh_2 = Timer(6.3, self.update_photoBoothPicture, [2, True])
        #self.timer_PhotoBoothPhotoRefresh_2.start()

        #self.update_photoBoothPicture(3, False)
        #self.timer_PhotoBoothPhotoRefresh_3 = Timer(12.6, self.update_photoBoothPicture, [3, True])
        #self.timer_PhotoBoothPhotoRefresh_3.start()

        #self.timer_PhotoBoothPhoto1Refresh.cancel()

        self.logger.info('Photobooth screen loaded')

    def update_photoBoothPicture(self, Position, _StartTimer, _ReloadFilelist):
        if _ReloadFilelist or len(self.FileList) == 0:
            #print("Reload filelist")
            self.FileList = sorted(os.listdir(self.TakenPhotosDir))
        if len(self.FileList) != 0:
            if not self.showLastImage:
                PhotoNumber = randint(0, len(self.FileList)-1)
            else:
                #print("Show just taken image")
                PhotoNumber = len(self.FileList) - 1
                self.showLastImage = False
            #print(PhotoNumber)
        
            PhotoPath = os.path.join(self.TakenPhotosDir, self.FileList[PhotoNumber])
            PhotoSurface = pygame.image.load(PhotoPath).convert()
            PictureSize = (1280, 720) #(845, 475)
            PhotoSurfaceScaled = pygame.transform.scale(PhotoSurface, PictureSize)
            PhotoRect = PhotoSurfaceScaled.get_rect()
            if Position == 1:
                PhotoRect.center = (700, 400) #(500, 250)
            elif Position == 2:
                PhotoRect.center = (1420, 280) #(1420, 280)
            elif Position == 3:
                PhotoRect.center = (960, 780) #(960, 780)
            else:
                PhotoRect.center = (0, 0)

            self.screen.blit(PhotoSurfaceScaled, PhotoRect)
            self.updatelist.append(PhotoRect)

        if _StartTimer:
            if Position == 1:
                self.timer_PhotoBoothPhotoRefresh_1 = Timer(8, self.update_photoBoothPicture, [1, True, False]) #20
                self.timer_PhotoBoothPhotoRefresh_1.start()
            elif Position == 2:
                self.timer_PhotoBoothPhotoRefresh_2 = Timer(20, self.update_photoBoothPicture, [2, True, False])
                self.timer_PhotoBoothPhotoRefresh_2.start()
            elif Position == 3:
                self.timer_PhotoBoothPhotoRefresh_3 = Timer(20, self.update_photoBoothPicture, [3, True, False])
                self.timer_PhotoBoothPhotoRefresh_3.start()


    def load_live_camera_screen(self):
        # stop photoboot function if needed
        try:
            self.timer_PhotoBoothPhotoRefresh_1.cancel()
            self.timer_PhotoBoothPhotoRefresh_2.cancel()
            self.timer_PhotoBoothPhotoRefresh_3.cancel()
        except:
            pass
        self.screen.fill(self.WHITE)
        #self.camera.start_CSI()
        self.camera.start_USB()
        self.CameraStartTime = time.time() #progress = 0
        pygame.display.update()
        self.logger.info('Live camera screen')
        image = self.camera.read_small()
        cameraImageSurf = pygame.surfarray.make_surface(image)
        self.cameraImageRect = cameraImageSurf.get_rect()
        self.cameraImageRect.center = (self.screeninfo.current_w /2 , self.screeninfo.current_h /2)
        self.screen.blit(cameraImageSurf, self.cameraImageRect)
        self.updatelist.append(self.cameraImageRect)


    def load_picture_screen(self):
        self.screen.fill(self.WHITE)
        pygame.display.update()
        #image = self.camera.getimage() #CSI
        image = self.camera.read_full() #USB
        PictureSurface = pygame.surfarray.make_surface(image)
        PictureRect = PictureSurface.get_rect()
        PictureRect.center = (self.screeninfo.current_w / 2, self.screeninfo.current_h / 2)

        self.screen.blit(PictureSurface, PictureRect)
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w, self.screeninfo.current_h)
        pygame.display.update(FullScreenRect)
        self.start_showtime = time.time()
        imagename = self.camera.getimagename_USB()
        if self.OperationMode == "PhotoBooth":
            self.showLastImage = True
        if imagename != "No Image":
            self.From_interface.put('Taken Image:' + imagename)
        self.logger.info('Taken picture screen')


    def Update_camera(self):
        self.screen.fill(self.WHITE)
        image = self.camera.read_small()
        cameraImageSurf = pygame.surfarray.make_surface(image)
        self.screen.blit(cameraImageSurf, self.cameraImageRect)
        self.updatelist.append(self.cameraImageRect)

        CameraTimeToGo = self.cameraLiveTime - (time.time() - self.CameraStartTime)+0.5
        textsurface = self.CountdownFont.render(str(round(CameraTimeToGo)), False, self.BLACK)
        textRect = textsurface.get_rect()
        textRect.center = (200, self.screeninfo.current_h / 2)
        self.screen.blit(textsurface, textRect)
        self.updatelist.append(textRect)

        textsurface = self.CountdownFont.render(str(round(CameraTimeToGo)), False, self.BLACK)
        textRect = textsurface.get_rect()
        textRect.center = (1720, self.screeninfo.current_h / 2)
        self.screen.blit(textsurface, textRect)
        self.updatelist.append(textRect)


 

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

        last_sync = self.db_conn.getLastSyncTime()
        lastSyncMessage_surf = self.myfont.render("last db sync: " + str(last_sync), False, (0, 0, 0))
        self.screen.blit(lastSyncMessage_surf, (100, 200))
        
        quitmessage_surf = self.myfont.render('press q to quit', False, (0, 0, 0))
        self.screen.blit(quitmessage_surf,(300,100))

        backmessage_surf = self.myfont.render('press b to go back to normal screen', False, (0, 0, 0))
        self.screen.blit(backmessage_surf, (300, 130))
        
        pygame.display.update()


    def start_WIFI_config(self):
        subprocess.Popen("wicd-client")


    def ShotglassSimbol(self):
        textboxRect = pygame.Rect(self.screeninfo.current_w - 275, self.screeninfo.current_h - 250, 275, 250)
        textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
        self.updatelist.append(textboxRect)
        if (self.EnableBarcodeScanner and ("Hallo" in self.currentTextMessage)) or not self.EnableBarcodeScanner:
            if self.shotglassStatus:
                shotImagesurf = pygame.image.load('Functions/Interface/Images/shot.png')
            else:
                shotImagesurf = pygame.image.load('Functions/Interface/Images/shot_red.png')

            shotImagesurf = pygame.transform.scale(shotImagesurf, (150, 150))
            shotImagesurf = shotImagesurf.convert_alpha()
            shotImagesurfRect = shotImagesurf.get_rect()
            shotImagesurfRect.center = (self.screeninfo.current_w - 200, self.screeninfo.current_h - 150)
            self.screen.blit(shotImagesurf, shotImagesurfRect)
            self.updatelist.append(shotImagesurfRect)
            

    def CameraSimbol(self):
        textboxRect = pygame.Rect(0, self.screeninfo.current_h - 250, 275, 250)
        textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
        self.updatelist.append(textboxRect)
        if (self.EnableBarcodeScanner and ("Hallo" in self.currentTextMessage)) or not self.EnableBarcodeScanner:
            shotImagesurf = pygame.image.load('Functions/Interface/Images/camera.png')
            shotImagesurf = pygame.transform.scale(shotImagesurf, (150, 150))
            shotImagesurf = shotImagesurf.convert_alpha()
            shotImagesurfRect = shotImagesurf.get_rect()
            shotImagesurfRect.center = (200, self.screeninfo.current_h - 150)
            self.screen.blit(shotImagesurf, shotImagesurfRect)
            self.updatelist.append(shotImagesurfRect)


    def update_timeoutBarcode(self):
        curr_time = time.time()
        progress = 1-((curr_time - self.timeout_start)/self.timeout_value)
        progressbarRect_back = pygame.Rect(0, self.screeninfo.current_h - 300, self.screeninfo.current_w, 50)
        progressbarSurf_back = pygame.draw.rect(self.screen, (0, 0, 0, 0), progressbarRect_back)
        if progress >= 0:
            progressbarRect = pygame.Rect(0, self.screeninfo.current_h - 300, round(self.screeninfo.current_w*progress), 50)
            progressbarSurf = pygame.draw.rect(self.screen, self.WHITE, progressbarRect)
        elif (progress < 0) and not (self.currentUser == ""):
            self.UserTimeout()
        return progressbarRect_back


    def reset_timeoutBarcode(self):
        self.timeout_start = time.time()


    def stop_timeoutBarcode(self):
        self.timeout_start = time.time() - self.timeout_value


    def newUserScanned(self):
        textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w-550, 250)
        textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
        self.updatelist.append(textboxRect)
        self.currentTextMessage = 'Hallo ' + self.currentUser
        maintext = self.textfont.render('Hallo ' + self.currentUser, True, self.WHITE, self.BLACK)
        maintextRect = maintext.get_rect()
        maintextRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
        self.screen.blit(maintext, maintextRect)
        self.updatelist.append(maintextRect)
        
        self.CameraSimbol()
        self.ShotglassSimbol()
        
        self.reset_timeoutBarcode()


    def UserTimeout(self):
        self.currentUser = ""
        self.NoUserText()


    def NoUserText(self):
        if self.OperationMode == "Shotmachine":
            textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w-550, 250)
            textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
            self.updatelist.append(textboxRect)
            if self.EnableBarcodeScanner:
                self.currentTextMessage = 'Scan je bandje'
                self.text = self.textfont.render('Scan je bandje', True, self.WHITE, self.BLACK)
                self.textRect = self.text.get_rect()
                self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
                self.screen.blit(self.text, self.textRect)
                self.updatelist.append(self.textRect)
            self.ShotglassSimbol()

            self.CameraSimbol()
        self.From_interface.put('NoUser')


    def DisplayMissingShotglass(self):
        self.currentTextMessage = "Zet eerst een shotglaasje neer"
        textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w - 550, 250)
        textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
        self.updatelist.append(textboxRect)
        self.text = self.textfont.render('Zet eerst een shotglaasje neer', True, self.WHITE, self.BLACK)
        self.textRect = self.text.get_rect()
        if self.EnableBarcodeScanner:
            self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
        else:
            self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 150)
        self.screen.blit(self.text, self.textRect)
        self.updatelist.append(self.textRect)

        timer_missingShotglass = Timer(20, self.ResetMissingShotglass)
        timer_missingShotglass.start()


    def ResetMissingShotglass(self):
        if self.currentTextMessage == "Zet eerst een shotglaasje neer":
            if self.currentUser != "":
                self.newUserScanned()
            else:
                self.NoUserText()


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


    def interfaceMain(self):
        # Define some colors
        self.BLACK = (0, 0, 0)
        self.GRAY = (100,100,100)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)

        # Define some general variables
        screensize = [1920, 1080]
        self.textfont = pygame.font.Font('freesansbold.ttf', 60)
        Roll_Images_dir = 'Functions/Interface/Images/Roll_images'
        Background_image_dir = 'Functions/Interface/Images/background_image'
        Appname = "Shotmachine Interface"
        self.rollerspeed = 50  # defines how fast the rollers move before stopped
        self.cameraLiveTime = 5 # duration in seocnds before picture is taken
        self.cameraPictureTime = 5 # amount of seconds the picture is shown
        self.timeout_value = 20 # amount of seconds before the user is kicked out

        # Init some system variables, do not change those
        self.shotglassStatus = False
        self.cameraScreenStarted = False
        self.timeout_start = time.time()
        self.currentUser = ""
        self.currentTextMessage = ""
        self.updatelist = []

        # Define positions and size of rollers
        Roll_1_posx = 610
        Roll_2_posx = 965
        Roll_3_posx = 1320
        Roll_posy = 300
        Roll_width = 300
        Roll_height = 420  # Must be less than 2x width

        # Initialize program
        self.logger = logging.getLogger(__name__)
        pygame.init()
        self.screeninfo = pygame.display.Info()
        self.screensize = [self.screeninfo.current_w, self.screeninfo.current_h]
        self.screen = pygame.display.set_mode(self.screensize, (pygame.DOUBLEBUF)) #|pygame.HWSURFACE))
        #self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN) #, (pygame.DOUBLEBUF))

        self.logger.info("Set screensize to: " + str(self.screensize[0]) + "x" + str(self.screensize[1]))
        pygame.display.set_caption(Appname)
        clock = pygame.time.Clock()
        background_file = os.listdir(Background_image_dir)
        background_path = os.path.join(Background_image_dir, background_file[0])
        self.background_image = pygame.image.load(background_path).convert()

        # Init camera
        self.camera = camerashotmachine.CameraShotmachine(_windowPosSize = (270,0,1440, 1080), waittime=3, HandleShotmachine = self.HandleShotmachine)
        
        # Init rollers
        self.roller1 = Roller(Roll_1_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller2 = Roller(Roll_2_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        self.roller3 = Roller(Roll_3_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)

        # Create screen
        if self.OperationMode == "Shotmachine":
            self.load_main_screen()
            current_screen = 'main'
        elif self.OperationMode == "PhotoBooth":
            self.load_photobooth_screen()
            current_screen = 'PhotoBooth'

        # set text on bottom of screen to init value
        self.NoUserText()
        self.stop_timeoutBarcode()

        time.sleep(0.5)
        self.logger.info('Interface initialised')

        # -------- Main Program Loop -----------
        while self.run:
            if not self.recievebuffer == '' and not current_screen == 'config':
                if self.recievebuffer == 'Take_picture':
                    if ((self.EnableBarcodeScanner and not (self.currentUser == "")) or not self.EnableBarcodeScanner):
                        self.load_live_camera_screen()
                        current_screen = 'livecamera'
                    else:
                        self.NoUserText()
                elif self.recievebuffer == 'Start_roll' and current_screen == 'main':
                    if ((self.EnableBarcodeScanner and not (self.currentUser == "")) or not self.EnableBarcodeScanner):
                        if self.shotglassStatus:
                            print('roll')
                            self.run_rollers()
                            timer_resetuser = Timer(10, self.stop_timeoutBarcode)
                            timer_resetuser.start()
                        else:
                            self.DisplayMissingShotglass()
                    else:
                        self.NoUserText()
                elif "New_User:" in self.recievebuffer:
                    self.currentUser = self.recievebuffer.split(':')[1]
                    if self.EnableBarcodeScanner:
                        self.newUserScanned()
                elif "Shotglass:" in self.recievebuffer:
                    self.shotglassStatus = bool(int(self.recievebuffer[-1:]))
                    self.ShotglassSimbol()
                    if self.shotglassStatus:
                        self.ResetMissingShotglass()
                elif 'Missing_Shotglass' in self.recievebuffer:
                    self.DisplayMissingShotglass()
                else:
                    self.logger.info("Unknown commamd from interface" + self.recievebuffer)
                self.recievebuffer = ''

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.From_interface.put('Quit')
                    self.logger.info("interface quit")
                    self.run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == 32:  # Space
                        self.load_config_screen()
                        current_screen = 'config'
                    if event.key == 115: # s
                        self.From_interface.put("Shothendel") 
                    if event.key == 102: # f
                        self.From_interface.put("Fotoknop")
                    if event.key == 113 and current_screen == 'config':  # q
                        self.From_interface.put('Quit')
                        self.run = False
                    if event.key == 98 and current_screen == 'config':  # b
                        if self.OperationMode == "Shotmachine":
                            self.load_main_screen()
                            current_screen = 'main'
                        elif self.OperationMode == "PhotoBooth":
                            self.load_photobooth_screen()
                            current_screen = 'PhotoBooth'
                        self.NoUserText()

            # Update the rollers if needed
            if current_screen == 'main':
                self.updatelist.append(self.roller1.update_roller())
                self.updatelist.append(self.roller2.update_roller())
                self.updatelist.append(self.roller3.update_roller())

                self.updatelist.append(self.update_timeoutBarcode())

            if current_screen == 'config':
                self.updatelist.append(self.button("Wifi settings", 150, 250, 150, 50, self.RED, self.GREEN, self.start_WIFI_config))
                self.updatelist.append(self.button("Spoel pomp 0", 400, 250, 150, 50, self.RED, self.GREEN, self.FlushPump, 0))
                self.updatelist.append(self.button("Spoel pomp 1", 400, 300, 150, 50, self.RED, self.GREEN, self.FlushPump, 1))
                self.updatelist.append(self.button("Spoel pomp 2", 400, 350, 150, 50, self.RED, self.GREEN, self.FlushPump, 2))
                self.updatelist.append(self.button("Spoel pomp 3", 400, 400, 150, 50, self.RED, self.GREEN, self.FlushPump, 3))
                self.updatelist.append(self.button("Spoel pomp 4", 400, 450, 150, 50, self.RED, self.GREEN, self.FlushPump, 4))
                
            if current_screen == 'livecamera':
                self.CameraRunTime = time.time() - self.CameraStartTime
                if self.CameraRunTime > self.cameraLiveTime:
                    current_screen = 'picture'
                    self.load_picture_screen()
                else:
                    self.Update_camera()

            if current_screen == 'picture':
                showtime_elapsed = time.time() - self.start_showtime
                if showtime_elapsed > self.cameraPictureTime:
                    #self.load_main_screen()
                    #current_screen = 'main'
                    if self.OperationMode == "Shotmachine":
                        self.load_main_screen()
                        current_screen = 'main'
                    elif self.OperationMode == "PhotoBooth":
                        self.load_photobooth_screen()
                        current_screen = 'PhotoBooth'
                    
                    if not self.EnableBarcodeScanner:
                        self.NoUserText()
                        self.stop_timeoutBarcode()
                    else:
                        self.reset_timeoutBarcode()
                        self.newUserScanned()
                
            # Limit to 60 frames per second
            clock.tick(60)

            # Update the screen with what has changed.
            pygame.display.update(self.updatelist)
            self.updatelist = []

        # Close everything down
        try:
            self.timer_PhotoBoothPhotoRefresh_1.cancel()
            self.timer_PhotoBoothPhotoRefresh_2.cancel()
            self.timer_PhotoBoothPhotoRefresh_3.cancel()

        except:
            pass
        pygame.quit()
        self.logger.info('Interface stopped')
