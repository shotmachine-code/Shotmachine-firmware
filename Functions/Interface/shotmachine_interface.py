import pygame
import os
import threading
import queue
import time
import subprocess
import logging
import psutil
import glob
import shutil
import datetime
from random import randint
from threading import Timer
from Functions.Interface.roller import Roller
from Functions.CameraShotmachine import camerashotmachine
from Functions.Database import database_connection


class ShotmachineInterface:

    def __init__(self, name, to_interface_queue, from_interface_queue, HandleShotmachine):
        self.name = name
        self.To_interface = to_interface_queue
        self.From_interface = from_interface_queue
        self.HandleShotmachine = HandleShotmachine
        self.state = 'Boot'
        self.ReceiveBuffer = ''
        self.SendBuffer = ''
        self.run = True
        pygame.font.init()
        self.myfont = pygame.font.SysFont('freesansbold.ttf', 30)
        self.CountdownFont = pygame.font.SysFont('freesansbold.ttf', 600)
        self.showLastImage = False
        self.FileList = []

        self.NoUserTextFlash = False
        self.NoUserTextBlack = False
        self.NoUserTextFlashCounter = 0

        self.OperationMode = self.HandleShotmachine["Settings"]["OperationMode"]
        
        
        # Verplaats naar _main__.py volgende regeld niet meer uncommenten!
        # self.OperationMode = "PhotoBooth"
        # self.OperationMode = "Shotmachine"

        self.TakenPhotosDirNU = 'TakenImages/NotUploaded'
        self.TakenPhotosDirU = 'TakenImages/Uploaded'

        self.db_conn = database_connection.database_connection(self.HandleShotmachine)

        self.EnableBarcodeScanner = self.HandleShotmachine["Settings"]["EnableBarcodeScanner"]

        self.thread = threading.Thread(target=self.queue_watcher, name='Interface_queue_watcher')
        self.thread.start()

        self.thread = threading.Thread(target=self.interfaceMain, name=self.name)
        self.thread.start()

    def queue_watcher(self):
        while self.run:
            if self.ReceiveBuffer == '':
                try:
                    self.ReceiveBuffer = self.To_interface.get(block=True, timeout=0.1)
                except queue.Empty:
                    pass
            time.sleep(0.1)

    def button(self, msg, x, y, w, h, ic, ac, action=None, PumpNumber=-1):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            buttoncolor = ac
            if click[0] == 1 and action is not None and PumpNumber == -1:  # Wifi config
                action()
                time.sleep(2)
            if click[0] == 1 and action is not None and PumpNumber != -1:  # een van de spoelknoppen
                action(PumpNumber)
                time.sleep(2)
        else:
            buttoncolor = ic
        textSurf = self.myfont.render(msg, False, self.BLACK, buttoncolor)
        textRect = textSurf.get_rect()
        textRect.center = ((x + (w / 2)), (y + (h / 2)))
        self.screen.blit(textSurf, textRect)
        return textRect

    def flush_pump(self, number):
        self.From_interface.put('Flush:' + str(number))
        
    def SwitchToShotmachineMode(self):
        self.logger.info('Start switching to Shotmachine mode')
        #self.From_interface.put('Quit')
        self.From_interface.put('Switch to mode: Shotmachine')  
        self.run = False
    
    def SwitchToPhotoboothMode(self):
        self.logger.info('Start switching to Photobooth mode')
        #self.From_interface.put('Quit')
        self.From_interface.put('Switch to mode: Photobooth')  
        self.run = False
        

    def load_main_screen(self):
        self.screen.fill(self.BLACK)
        self.screen.blit(self.background_image, [0, 0])
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w, self.screeninfo.current_h)
        pygame.display.update(FullScreenRect)
        pygame.mouse.set_visible(False)
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
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w, self.screeninfo.current_h)
        #pygame.display.update(FullScreenRect)
        self.updatelist.append(FullScreenRect)

        self.update_photobooth_picture(1, True, True)

        # self.update_photoBoothPicture(2, False)
        # self.timer_PhotoBoothPhotoRefresh_2 = Timer(6.3, self.update_photoBoothPicture, [2, True])
        # self.timer_PhotoBoothPhotoRefresh_2.start()

        # self.timer_PhotoBoothPhoto1Refresh.cancel()

        self.logger.info('Photobooth screen loaded')

    def fotomap_legen(self):
        #if _ReloadFilelist or len(self.FileList) == 0:
            # print("Reload file list")
            
        FileListNU = sorted(os.listdir(self.TakenPhotosDirNU))
        FileListU = sorted(os.listdir(self.TakenPhotosDirU))
        
        if (len(FileListNU) + len(FileListU))==0:
            self.logger.info("No photos to move")
        else:
            #print('Make new folder to move files')
        
            datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            FolderPath = os.path.join('TakenImages/_old', datetimestring)
            os.mkdir(FolderPath)
            FolderPathNU = os.path.join(FolderPath, 'NotUploaded')
            os.mkdir(FolderPathNU)
            FolderPathU = os.path.join(FolderPath, 'Uploaded')
            os.mkdir(FolderPathU)
            self.logger.info("Created new folder: " + FolderPath)
        
            for i in range(len(FileListNU)):
                PhotoPath = os.path.join(self.TakenPhotosDirNU, FileListNU[i])
                shutil.move(PhotoPath, (FolderPathNU + '/'+ FileListNU[i]))
                #print('move ' + PhotoPath)
        
            for i in range(len(FileListU)):
                PhotoPath = os.path.join(self.TakenPhotosDirU, FileListU[i])
                shutil.move(PhotoPath, (FolderPathU + '/'+ FileListU[i]))
                #print('move ' + PhotoPath)
            self.logger.info("Moved " + str(len(FileListNU) + len(FileListU)) + ' photos')
        '''
        self.FileListNU = sorted(os.listdir(self.TakenPhotosDirNU)) 
        self.FileListU = sorted(os.listdir(self.TakenPhotosDirU))
        self.FileList = self.FileListNU + self.FileListU
        self.NrNUFiles = len(self.FileListNU)
        if len(self.FileList) != 0:
            if not self.showLastImage:
                PhotoNumber = randint(0, len(self.FileList) - 1)
            else:
                PhotoNumber = len(self.FileList) - 1
                self.showLastImage = False
            if PhotoNumber < self.NrNUFiles:
                PhotoPath = os.path.join(self.TakenPhotosDirNU, self.FileList[PhotoNumber])
            else:
                PhotoPath = os.path.join(self.TakenPhotosDirU, self.FileList[PhotoNumber])
        '''

    def update_photobooth_picture(self, Position, _StartTimer, _ReloadFilelist):
        #if _ReloadFilelist or len(self.FileList) == 0:
            # print("Reload file list")
        try:
            self.FileListNU = sorted(os.listdir(self.TakenPhotosDirNU)) 
            self.FileListU = sorted(os.listdir(self.TakenPhotosDirU))
            self.FileList = self.FileListNU + self.FileListU
            self.NrNUFiles = len(self.FileListNU)
            if len(self.FileList) != 0:
                if not self.showLastImage:
                    PhotoNumber = randint(0, len(self.FileList) - 1)
                else:
                    PhotoNumber = len(self.FileList) - 1
                    self.showLastImage = False
                if PhotoNumber < self.NrNUFiles:
                    PhotoPath = os.path.join(self.TakenPhotosDirNU, self.FileList[PhotoNumber])
                else:
                    PhotoPath = os.path.join(self.TakenPhotosDirU, self.FileList[PhotoNumber])
                PhotoSurface = pygame.image.load(PhotoPath).convert()
                PictureSize = (1024, 760)  # (845, 475)
                PhotoSurfaceScaled = pygame.transform.scale(PhotoSurface, PictureSize)
                PhotoRect = PhotoSurfaceScaled.get_rect()
                Position = 3
                if Position == 1:
                    PhotoRect.center = (700, 400)  # (500, 250)
                elif Position == 2:
                    PhotoRect.center = (1420, 280)  # (1420, 280)
                elif Position == 3:
                    PhotoRect.center = (960, 500)  # (960, 780)
                else:
                    PhotoRect.center = (0, 0)

                self.screen.blit(PhotoSurfaceScaled, PhotoRect)
                self.updatelist.append(PhotoRect)

            if _StartTimer:
                if Position == 1:
                    if hasattr(self,'timer_PhotoBoothPhotoRefresh_1'):
                        self.timer_PhotoBoothPhotoRefresh_1.cancel()
                    self.timer_PhotoBoothPhotoRefresh_1 = Timer(8, self.update_photobooth_picture, [1, True, False])  # 20                
                    self.timer_PhotoBoothPhotoRefresh_1.start()
                elif Position == 2:
                    if hasattr(self,'timer_PhotoBoothPhotoRefresh_2'):
                        self.timer_PhotoBoothPhotoRefresh_2.cancel()
                    self.timer_PhotoBoothPhotoRefresh_2 = Timer(20, self.update_photobooth_picture, [2, True, False])
                    self.timer_PhotoBoothPhotoRefresh_2.start()
                elif Position == 3:
                    if hasattr(self,'timer_PhotoBoothPhotoRefresh_3'):
                        self.timer_PhotoBoothPhotoRefresh_3.cancel()
                    self.timer_PhotoBoothPhotoRefresh_3 = Timer(7, self.update_photobooth_picture, [3, True, False])
                    self.timer_PhotoBoothPhotoRefresh_3.start()
        except pygame.error:
            self.logger.info('update photobooth image ging niet goed, stop refresh')
            

    def load_live_camera_screen(self):
        # stop photoboot function if needed
        if hasattr(self,'timer_PhotoBoothPhotoRefresh_1'):
            self.timer_PhotoBoothPhotoRefresh_1.cancel()
        if hasattr(self,'timer_PhotoBoothPhotoRefresh_2'):
            self.timer_PhotoBoothPhotoRefresh_2.cancel()
        if hasattr(self,'timer_PhotoBoothPhotoRefresh_3'):
            self.timer_PhotoBoothPhotoRefresh_3.cancel()
            
        #try:
        #    self.timer_PhotoBoothPhotoRefresh_1.cancel()
        #    
        #except:
        #    pass
        #self.timer_PhotoBoothPhotoRefresh_2.cancel()
        #    self.timer_PhotoBoothPhotoRefresh_3.cancel()
        self.screen.fill(self.WHITE)
        self.camera.start()
        self.CameraStartTime = time.time()
        pygame.display.update()
        self.logger.info('Live camera screen')
        self.imageSurf = self.camera.read_small()
        self.cameraImageRect = self.imageSurf.get_rect()
        self.cameraImageRect.center = (self.screeninfo.current_w / 2, self.screeninfo.current_h / 2)
        self.screen.blit(self.imageSurf, self.cameraImageRect)
        self.CameraTimeToGoPrev = 0
        self.updatelist.append(self.cameraImageRect)

    def load_picture_screen(self):
        self.screen.fill(self.WHITE)
        pygame.display.update()
        # image = self.camera.getimage() #CSI
        Picture = self.camera.read_full()
        PictureRect = Picture.get_rect()
        PictureRect.center = (self.screeninfo.current_w / 2, self.screeninfo.current_h / 2)

        self.screen.blit(Picture, PictureRect)
        FullScreenRect = pygame.Rect(0, 0, self.screeninfo.current_w, self.screeninfo.current_h)
        pygame.display.update(FullScreenRect)
        self.start_showtime = time.time()
        imagename = self.camera.get_imagename()
        if self.OperationMode == "PhotoBooth":
            self.showLastImage = True
        if imagename != "No Image":
            self.From_interface.put('Taken Image:' + imagename)
        self.logger.info('Taken picture screen')

    def Update_camera(self):
        self.imageSurf = self.camera.read_small()
        self.screen.blit(self.imageSurf, self.cameraImageRect)
        self.updatelist.append(self.cameraImageRect)

        CameraTimeToGo = round(self.cameraLiveTime - (time.time() - self.CameraStartTime) + 0.5)
        if CameraTimeToGo != self.CameraTimeToGoPrev:
            textsurface = self.CountdownFont.render(str(CameraTimeToGo), False, self.BLACK, self.WHITE)
            textRectL = textsurface.get_rect()
            textRectR = textsurface.get_rect()
            textRectL.center = (120, self.screeninfo.current_h / 2)
            textRectR.center = (1800, self.screeninfo.current_h / 2)
            self.screen.blit(textsurface, textRectL)
            self.screen.blit(textsurface, textRectR)
            self.updatelist.append(textRectL)
            self.updatelist.append(textRectR)
            self.CameraTimeToGoPrev = CameraTimeToGo

    def Prepare_camera_photo(self):
        self.camera.switch_to_full()
        self.screen.fill(self.WHITE)
        screenRect = self.screen.get_rect()
        self.updatelist.append(screenRect)

    def load_config_screen(self):
        self.screen.fill(self.GRAY)
        pygame.mouse.set_visible(True)
        try:
            CPUtemp_raw = psutil.sensors_temperatures()
            try:
                cputemp = str(CPUtemp_raw['cpu-thermal'][0].current).encode("utf-8").decode("utf-8")
            except (KeyError, AttributeError):
                cputemp = str(CPUtemp_raw['coretemp'][0].current).encode("utf-8").decode("utf-8")
        except (KeyError, AttributeError):
            cputemp = "error"



        cputemp_surface = self.myfont.render(cputemp, False, (0, 0, 0))
        self.screen.blit(cputemp_surface, (100, 100))

        #last_sync = self.db_conn.getLastSyncTime()
        #lastSyncMessage_surf = self.myfont.render("last db sync: " + str(last_sync), False, (0, 0, 0))
        #self.screen.blit(lastSyncMessage_surf, (100, 200))
        
        filelist_NU = glob.glob("/home/pi/Shotmachine/Shotmachine-firmware/TakenImages/NotUploaded/*.jpg")
        filelist_U = glob.glob("/home/pi/Shotmachine/Shotmachine-firmware/TakenImages/Uploaded/*.jpg")
        n_images = len(filelist_NU) + len(filelist_U)
        n_images_surf = self.myfont.render("Number of images taken: " + str(n_images), False, (0, 0, 0))
        to_upload_surf = self.myfont.render("Number of images yet to upload: " + str(len(filelist_NU)), False, (0, 0, 0))
        self.screen.blit(n_images_surf, (100, 180))
        self.screen.blit(to_upload_surf, (100, 200))

        quitmessage_surf = self.myfont.render('press q to quit', False, (0, 0, 0))
        self.screen.blit(quitmessage_surf, (300, 100))

        backmessage_surf = self.myfont.render('press b to go back to normal screen', False, (0, 0, 0))
        self.screen.blit(backmessage_surf, (300, 130))

        pygame.display.update()

    def start_WIFI_config(self):
        subprocess.Popen("wicd-client")

    def ShotglassSimbol(self):
        if self.current_screen == 'main':
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
        if self.current_screen == 'main':
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
        progress = 1 - ((curr_time - self.timeout_start) / self.CurrentTimeoutValue)
        progressbarRect_back = pygame.Rect(0, self.screeninfo.current_h - 300, self.screeninfo.current_w, 50)
        progressbarSurf_back = pygame.draw.rect(self.screen, (0, 0, 0, 0), progressbarRect_back)
        if progress >= 0:
            progressbarRect = pygame.Rect(0, self.screeninfo.current_h - 300,
                                          round(self.screeninfo.current_w * progress), 50)
            progressbarSurf = pygame.draw.rect(self.screen, self.WHITE, progressbarRect)
        elif (progress < 0) and not (self.currentUser == ""):
            self.UserTimeout()
        return progressbarRect_back

    def reset_timeoutBarcode(self):
        self.timeout_start = time.time()
        self.CurrentTimeoutValue = self.timeoutValue

    def reset_timeoutBarcodeAfterPhoto(self):
        self.timeout_start = time.time()
        self.CurrentTimeoutValue = self.timeoutValuePhoto

    def stop_timeoutBarcode(self):
        self.timeout_start = time.time() - self.timeoutValue

    def newUserScanned(self):
        # cancel flashing text if needed
        if self.NoUserTextFlash == True:
            self.NoUserTextTimer.cancel()
            self.NoUserTextFlash = False
            self.NoUserTextBlack = False

        ChangedName = self.db_conn.getOnlineLogin(self.currentBarcode)

        textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w - 550, 250)
        textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
        self.updatelist.append(textboxRect)

        self.currentTextMessage = 'Hallo ' + self.currentUser
        maintext = self.textfont.render('Hallo ' + self.currentUser, True, self.WHITE, self.BLACK)
        maintextRect = maintext.get_rect()

        if (ChangedName == 0):
            maintextRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
            self.screen.blit(maintext, maintextRect)
            self.updatelist.append(maintextRect)

            ChangeNameTextMessage = "Verander je naam en bekijk je shots + foto's op:"
            ChangeNameText = self.smalltextfont.render(ChangeNameTextMessage, True, self.WHITE, self.BLACK)
            ChangeNameTextRect = ChangeNameText.get_rect()
            ChangeNameTextRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 130)
            self.screen.blit(ChangeNameText, ChangeNameTextRect)
            self.updatelist.append(ChangeNameTextRect)

            WebsiteTextMessage = "shotmachine.nl"
            WebsiteText = self.textfont.render(WebsiteTextMessage, True, self.WHITE, self.BLACK)
            WebsiteTextRect = WebsiteText.get_rect()
            WebsiteTextRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 80)
            self.screen.blit(WebsiteText, WebsiteTextRect)
            self.updatelist.append(WebsiteTextRect)
        else:
            maintextRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 150)
            self.screen.blit(maintext, maintextRect)
            self.updatelist.append(maintextRect)

        # self.CameraSimbol()
        # self.ShotglassSimbol()

        # self.reset_timeoutBarcode()

    def UserTimeout(self):
        self.currentUser = ""
        self.NoUserText()

    def NoUserText(self):
        if self.OperationMode == "Shotmachine" and self.current_screen == 'main':
            # textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w - 550, 250)
            # textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
            # self.updatelist.append(textboxRect)

            if self.EnableBarcodeScanner:

                if self.NoUserTextFlash == True:
                    self.NoUserTextFlashCounter = self.NoUserTextFlashCounter + 1
                    # print(self.NoUserTextFlashCounter)
                    if self.NoUserTextFlashCounter < 10:

                        if self.NoUserTextBlack:
                            self.text = self.textfont.render('Scan eerst je bandje', True, self.WHITE, self.BLACK)
                            self.NoUserTextBlack = False
                        else:
                            self.text = self.textfont.render('Scan eerst je bandje', True, self.BLACK, self.BLACK)
                            self.NoUserTextBlack = True
                        self.NoUserTextTimer.cancel()
                        self.NoUserTextTimer = Timer(0.5, self.NoUserText)
                        self.NoUserTextTimer.start()
                    else:
                        self.NoUserTextTimer.cancel()
                        self.NoUserTextFlash = False
                        self.text = self.textfont.render('Scan eerst je bandje', True, self.WHITE, self.BLACK)
                        self.NoUserTextBlack = False
                elif self.currentTextMessage == 'Scan eerst je bandje':
                    self.NoUserTextFlash = True
                    self.NoUserTextBlack = False
                    self.NoUserTextFlashCounter = 0
                    # self.NoUserTextTimer.cancel()
                    self.NoUserTextTimer = Timer(0.5, self.NoUserText)
                    self.NoUserTextTimer.start()

                else:
                    self.text = self.textfont.render('Scan eerst je bandje', True, self.WHITE, self.BLACK)
                    self.NoUserTextBlack = False
                    self.currentTextMessage = 'Scan eerst je bandje'
                self.textRect = self.text.get_rect()
                self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
                self.screen.blit(self.text, self.textRect)
                self.updatelist.append(self.textRect)
            # self.ShotglassSimbol()
            # self.CameraSimbol()
        else:
            self.NoUserTextFlash = False
        self.From_interface.put('NoUser')
        
    def SwitchNotOnMessage(self):
        if (self.OperationMode == "Shotmachine" or self.OperationMode == "PhotoBooth") and self.current_screen == 'main':
            textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w - 550, 250)
            textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
            self.updatelist.append(textboxRect)
            
            self.text = self.textfont.render('Power schakelaar nog niet aan', True, self.WHITE, self.BLACK)
            self.textRect = self.text.get_rect()
            self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
            self.screen.blit(self.text, self.textRect)
            self.updatelist.append(self.textRect)
            # self.ShotglassSimbol()
            # self.CameraSimbol()
        #self.From_interface.put('NoUser')

    def FlashNoUserText(self):
        if self.OperationMode == "Shotmachine" and self.current_screen == 'main':
            textboxRect = pygame.Rect(275, self.screeninfo.current_h - 250, self.screeninfo.current_w - 550, 250)
            textboxSurf = pygame.draw.rect(self.screen, (0, 0, 0, 0), textboxRect)
            self.updatelist.append(textboxRect)
            if self.EnableBarcodeScanner and self.currentTextMessage == 'Scan je bandje':
                self.text = self.textfont.render('Scan je bandje', True, self.WHITE, self.BLACK)
                self.textRect = self.text.get_rect()
                self.textRect.center = (self.screeninfo.current_w // 2, self.screeninfo.current_h - 200)
                self.screen.blit(self.text, self.textRect)
                self.updatelist.append(self.textRect)
            # self.ShotglassSimbol()
            # self.CameraSimbol()
        self.From_interface.put('NoUser')

    def DisplayMissingShotglass(self):
        if self.current_screen == 'main':
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

            timer_missingShotglass = Timer(10, self.ResetMissingShotglass)
            timer_missingShotglass.start()

    def ResetMissingShotglass(self):
        if self.currentTextMessage == "Zet eerst een shotglaasje neer":
            if self.currentUser != "":
                self.newUserScanned()
                self.reset_timeoutBarcode()
            else:
                self.NoUserText()

    def run_rollers(self):
        self.roller1.start_roller(self.rollerspeed)
        self.roller2.start_roller(self.rollerspeed)
        self.roller3.start_roller(self.rollerspeed)
        stopimage = randint(1, 100)
        timer1 = Timer(2, self.roller1.stop_roller_smooth, [stopimage])
        timer1.start()
        timer2 = Timer(3, self.roller2.stop_roller_smooth, [stopimage])
        timer2.start()
        timer3 = Timer(4, self.roller3.stop_roller_smooth, [stopimage])
        timer3.start()
        timer4 = Timer(5, self.From_interface.put, ['RollsStopped'])
        timer4.start()

        self.logger.info('Starting rollers')

    def interfaceMain(self):
        # Define some colors
        self.BLACK = (0, 0, 0)
        self.GRAY = (100, 100, 100)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)

        # Define some general variables
        screensize = [1920, 1080]
        self.textfont = pygame.font.Font('freesansbold.ttf', 60)
        self.smalltextfont = pygame.font.Font('freesansbold.ttf', 30)
        Roll_Images_dir = 'Functions/Interface/Images/Roll_images'
        Background_image_dir = 'Functions/Interface/Images/background_image'
        Appname = "Shotmachine Interface"
        self.rollerspeed = 50  # defines how fast the rollers move before stopped
        self.cameraLiveTime = 5  # duration in seocnds before picture is taken
        self.cameraPictureTime = 5  # amount of seconds the picture is shown
        self.timeoutValue = 20  # amount of seconds before the user is kicked out
        self.timeoutValuePhoto = 5  # amount of seconds before the user is kicked out after a photo

        # Init some system variables, do not change those
        self.shotglassStatus = True
        self.cameraScreenStarted = False
        self.timeout_start = time.time()
        self.CurrentTimeoutValue = self.timeoutValue
        self.currentUser = ""
        self.currentBarcode = ""
        self.currentTextMessage = ""
        self.updatelist = []

        # Define positions and size of rollers
        Roll_1_posx = 610 #610
        Roll_2_posx = 965 #965
        Roll_3_posx = 1320 #1320
        Roll_posy = 500  # was 300 before removing bottom bar #540
        Roll_width = 300 #300
        Roll_height = 420  # 420 Must be less than 2x width

        # Initialize program
        self.logger = logging.getLogger(__name__)
        pygame.init()
        self.screeninfo = pygame.display.Info()
        self.screensize = [self.screeninfo.current_w, self.screeninfo.current_h]
        #self.screen = pygame.display.set_mode(self.screensize, (pygame.DOUBLEBUF | pygame.HWSURFACE))
        self.screen = pygame.display.set_mode((0,0), (pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.HWSURFACE))
        pygame.mouse.set_pos([0,0])
        
        self.logger.info("Start interface in mode: " + self.OperationMode)

        self.logger.info("Set screensize to: " + str(self.screensize[0]) + "x" + str(self.screensize[1]))
        pygame.display.set_caption(Appname)
        clock = pygame.time.Clock()
        
        try:
            background_file = os.listdir(Background_image_dir)
            background_path = os.path.join(Background_image_dir, background_file[0])
            self.background_image = pygame.transform.smoothscale(pygame.image.load(background_path).convert(),
                                                             self.screensize)
        except IndexError:
            self.From_interface.put('Quit')
            self.logger.info("No background image in folder, quit")
            self.run = False
        

        # Init camera
        self.camera = camerashotmachine.CameraShotmachine(storagepath=self.TakenPhotosDirNU,
                                                          HandleShotmachine=self.HandleShotmachine)
        self.cameraSwitchedToPhoto = False

        try:
            # Init rollers
            self.roller1 = Roller(Roll_1_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
            self.roller2 = Roller(Roll_2_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
            self.roller3 = Roller(Roll_3_posx, Roll_posy, Roll_height, Roll_width, Roll_Images_dir)
        except IndexError:
            self.From_interface.put('Quit')
            self.logger.info("No, or not enough, roll images in folder, quit")
            self.run = False
        

        if self.run:
            
            # Create screen
            if self.OperationMode == "Shotmachine":
                self.load_main_screen()
                self.current_screen = 'main'
            elif self.OperationMode == "PhotoBooth":
                self.load_photobooth_screen()
                self.current_screen = 'PhotoBooth'
            
            
            #self.SwitchNotOnMessage()
            
            # set text on bottom of screen to init value
            self.NoUserText()
            self.stop_timeoutBarcode()
            pygame.mouse.set_pos([1920,1080])
            pygame.mouse.set_visible(False)

            time.sleep(0.5)
            self.logger.info('Interface initialised')

        # -------- Main Program Loop -----------
        while self.run:
            #if self.ReceiveBuffer == "Quit":
            #    self.From_interface.put('Quit')
            #    self.run = False
            #    self.ReceiveBuffer = ''
            
            if not self.ReceiveBuffer == '' and not self.current_screen == 'config':
                if self.ReceiveBuffer == 'Take_picture':
                    if ((self.EnableBarcodeScanner and not (self.currentUser == "")) or not self.EnableBarcodeScanner):
                        self.load_live_camera_screen()
                        self.current_screen = 'livecamera'
                    else:
                        self.NoUserText()
                        self.logger.warning("Photo requested, but no user scanned and barcode is enabled")
                elif self.ReceiveBuffer == 'Start_roll' and self.current_screen == 'main':
                    if ((self.EnableBarcodeScanner and not (self.currentUser == "")) or not self.EnableBarcodeScanner):
                        if self.shotglassStatus:
                            self.logger.info('Start roll')
                            self.run_rollers()
                            timer_resetuser = Timer(10, self.stop_timeoutBarcode)
                            timer_resetuser.start()
                        else:
                            self.DisplayMissingShotglass()
                            self.logger.warning("Shot requested, but no shotglass is detected")
                    else:
                        self.NoUserText()
                        self.logger.warning("Shot requested, but no user scanned and barcode is enabled")
                elif "New_User:" in self.ReceiveBuffer:
                    self.currentBarcode = self.ReceiveBuffer.split(':')[2]
                    self.currentUser = self.ReceiveBuffer.split(':')[3]
                    if self.EnableBarcodeScanner:
                        self.newUserScanned()
                        self.reset_timeoutBarcode()
                elif "Shotglass:" in self.ReceiveBuffer:
                    self.shotglassStatus = bool(int(self.ReceiveBuffer[-1:]))
                #     self.ShotglassSimbol()
                    if self.shotglassStatus:
                        self.ResetMissingShotglass()
                # elif 'Missing_Shotglass' in self.ReceiveBuffer:
                #     self.DisplayMissingShotglass()
                elif "Quit" in self.ReceiveBuffer:
                    #self.From_interface.put('Quit')
                    self.run = False
                else:
                    self.logger.info("Unknown command from interface " + self.ReceiveBuffer)
                    self.From_interface.put('Cant_make_shot')
                self.ReceiveBuffer = ''

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    #self.From_interface.put('Quit')
                    self.logger.info("interface quit")
                    self.run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == 32:  # Space
                        self.load_config_screen()
                        self.current_screen = 'config'
                    if event.key == 115:  # s
                        self.From_interface.put("Shothendel")
                    if event.key == 102:  # f
                        self.From_interface.put("Fotoknop")
                    if event.key == 113 and self.current_screen == 'config':  # q
                        self.From_interface.put('Quit')
                        self.run = False
                    if event.key == 98 and self.current_screen == 'config':  # b
                        if self.OperationMode == "Shotmachine":
                            self.load_main_screen()
                            self.current_screen = 'main'
                        elif self.OperationMode == "PhotoBooth":
                            self.load_photobooth_screen()
                            self.current_screen = 'PhotoBooth'
                        self.NoUserText()

            # Update the rollers if needed
            if self.current_screen == 'main':
                # self.screen.blit(self.background_image, [0, 0])
                self.updatelist.append(self.roller1.update_roller())
                self.updatelist.append(self.roller2.update_roller())
                self.updatelist.append(self.roller3.update_roller())

                # self.updatelist.append(self.update_timeoutBarcode())

            if self.current_screen == 'config':
                self.updatelist.append(
                    self.button("Wifi settings", 150, 250, 150, 50, self.RED, self.GREEN, self.start_WIFI_config))
                self.updatelist.append(
                    self.button("Fotomap legen", 150, 300, 150, 50, self.RED, self.GREEN, self.fotomap_legen))
                self.updatelist.append(
                    self.button("Spoel pomp 0", 400, 250, 150, 50, self.RED, self.GREEN, self.flush_pump, 0))
                self.updatelist.append(
                    self.button("Spoel pomp 1", 400, 300, 150, 50, self.RED, self.GREEN, self.flush_pump, 1))
                self.updatelist.append(
                    self.button("Spoel pomp 2", 400, 350, 150, 50, self.RED, self.GREEN, self.flush_pump, 2))
                self.updatelist.append(
                    self.button("Spoel pomp 3", 400, 400, 150, 50, self.RED, self.GREEN, self.flush_pump, 3))
                self.updatelist.append(
                    self.button("Spoel pomp 4", 400, 450, 150, 50, self.RED, self.GREEN, self.flush_pump, 4))
                self.updatelist.append(
                    self.button("Spoelen alles 10 sec", 400, 500, 150, 50, self.RED, self.GREEN, self.flush_pump, 6))
                self.updatelist.append(
                    self.button("Spoelen alles 1 min", 400, 550, 150, 50, self.RED, self.GREEN, self.flush_pump, 7))
                self.updatelist.append(
                    self.button("Wissel naar Photobooth mode", 150, 350, 150, 50, self.RED, self.GREEN, self.SwitchToPhotoboothMode))  
                self.updatelist.append(
                    self.button("Wissel naar Shotmachine mode", 150, 400, 150, 50, self.RED, self.GREEN, self.SwitchToShotmachineMode)) 
                    
                    

            if self.current_screen == 'livecamera':
                self.CameraRunTime = time.time() - self.CameraStartTime

                if self.CameraRunTime + 0.5 > self.cameraLiveTime:
                    self.current_screen = 'picture'
                    self.load_picture_screen()
                elif self.CameraRunTime + 0.5 > self.cameraLiveTime:
                    if not self.cameraSwitchedToPhoto:
                        self.cameraSwitchedToPhoto = True
                        self.Prepare_camera_photo()
                else:
                    self.Update_camera()
                    self.cameraSwitchedToPhoto = False

            if self.current_screen == 'picture':
                showtime_elapsed = time.time() - self.start_showtime
                if showtime_elapsed > self.cameraPictureTime:
                    # self.load_main_screen()
                    # self.current_screen = 'main'
                    if self.OperationMode == "Shotmachine":
                        self.load_main_screen()
                        self.current_screen = 'main'
                    elif self.OperationMode == "PhotoBooth":
                        self.load_photobooth_screen()
                        self.current_screen = 'PhotoBooth'

                    if not self.EnableBarcodeScanner:
                        self.NoUserText()
                        self.stop_timeoutBarcode()
                    else:
                        self.newUserScanned()
                        self.reset_timeoutBarcodeAfterPhoto()

            # Limit to 60 frames per second
            clock.tick(60)
            # Print(clock.get_fps())

            # Update the screen with what has changed.
            pygame.display.update(self.updatelist)
            # pygame.display.update()
            self.updatelist = []

        # Close everything down
        #try:
        #    self.timer_PhotoBoothPhotoRefresh_1.cancel()
        #    self.timer_PhotoBoothPhotoRefresh_2.cancel()
        #    self.timer_PhotoBoothPhotoRefresh_3.cancel()
        #except:
        #    pass
        try:
            del(self.camera)
        except Exception as err:
            self.logger.info(err)  
        try:
            #if hasattr(self,'timer_PhotoBoothPhotoRefresh_1'):
            self.timer_PhotoBoothPhotoRefresh_1.cancel()
        except:
            pass
        try:
            #if hasattr(self,'timer_PhotoBoothPhotoRefresh_2'):
            self.timer_PhotoBoothPhotoRefresh_2.cancel()
        except:
            pass
        try:
         #   if hasattr(self,'timer_PhotoBoothPhotoRefresh_3'):
            self.timer_PhotoBoothPhotoRefresh_3.cancel()
        except:
            pass
            
        pygame.quit()
        self.logger.info('Interface stopped')
