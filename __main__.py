import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
from Functions.DatabaseSync import databasesync
from Functions.InputsOutputs import inputsoutputs
from Functions.Database import database_connection
from Functions.GooglePhotos.PhotoUploader import PhotoUploader

import platform
import random
import datetime
import os
import sys


#TODO
party_id = 3


currentOS = platform.system()
currentArch = platform.architecture()
if (currentOS == 'Linux' and currentArch[0] != '64bit'):
    onRaspberry = True
else:
    onRaspberry = False
#onRaspberry = False


Logdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
Logname = "Logs/" + Logdate + ".log"
logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
                    level=logging.INFO,
                    handlers = [
                        logging.FileHandler(Logname),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)



logger.info("Start")

HandleShotmachine = {
    "Settings": {
        "OnRaspberry": onRaspberry,
        "EnableSPI": True,
        "EnableI2C": True,
        "EnableDBSync":False,
        "EnableBarcodeScanner": False,
        "EnablePhotoUploader": True
    },
    "Hardware": {
        "OnOffSwitch": 27,
        "ConfigSwitch": 21,
        "SpoelSwitch": 16,
        "HendelSwitch": 23,
        "FotoSwitch": 24,
        "EnableI2COutput": 4,
        "OnOffLed": 17,
        "ResetArduino": 13,
        "LedConfig": 20,
        "LedSpoel": 12,
        "LedSignal": 25
    },
    "Logger": logger
}



class Shotmachine_controller():
    def __init__(self, _name, _ToInterfQueue, _ToMainQueue, _ToDBSyncQueue, _ToIOQueue, _ToPhotoUploaderQueue):
        self.name = _name
        self.ToInterfQueue = _ToInterfQueue
        self.ToMainQueue = _ToMainQueue
        self.ToDBSyncQueue = _ToDBSyncQueue
        self.ToIOQueue = _ToIOQueue
        self.ToPhotoUploaderQueue = _ToPhotoUploaderQueue
        self.state = 'Boot'

        self.username = ""
        self.barcode = ""

        self.quitprogram = False

        self.Shotglass = False
        self.Shothendel = False
        self.possibleShots = list(range(0, 5))

        self.fotoknop = False

        self.EnableBarcodeScanner = HandleShotmachine["Settings"]["EnableBarcodeScanner"]

        self.db_conn = database_connection.database_connection()

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()

    def run(self):

        while not self.quitprogram:
            if self.fotoknop:
                self.fotoknop = False
                self.ToInterfQueue.put('Take_picture')
                if ((self.username != "") or not self.EnableBarcodeScanner):
                    self.ToIOQueue.put("Busy")
                    self.ToIOQueue.put("Flashlight 2")
                    time.sleep(7)
                    self.ToIOQueue.put("Flashlight 1")
                    time.sleep(1)
                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    logger.info("foto at " + datetimestring + " \n")
                self.ToIOQueue.put("Ready")

            if self.Shothendel:
                self.Shothendel = False
                self.ToInterfQueue.put('Start_roll')
                if self.Shotglass and ((self.username != "") or not self.EnableBarcodeScanner) :
                    if len(self.possibleShots) == 0:
                        self.possibleShots = list(range(0, 5))
                    index = random.randint(0, len(self.possibleShots)-1)
                    i = self.possibleShots[index]
                    self.possibleShots.remove(i)
                    time.sleep(6)
                    self.ToIOQueue.put("Shot " + str(i))
                    time.sleep(2)
                    self.db_conn.ShotToDatabase(self.barcode, str(i))

                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    logger.info("shot " + str(i)  + " at " + datetimestring + "\n")
                self.ToIOQueue.put("Ready")

            try:
                s = self.ToMainQueue.get(block=True, timeout=0.1)
                if s == "Quit":
                    self.quitprogram = True
                    self.ToIOQueue.put("Flashlight 0") # turn off all leds on machine
                    self.ToDBSyncQueue.put("Quit")
                    self.ToIOQueue.put("Quit")
                    self.ToPhotoUploaderQueue.put("Quit")
                    logger.info("main quit")
                elif "ShotglassState" in s:
                    self.Shotglass = bool(int(s[-1:]))
                    self.ToInterfQueue.put("Shotglass:" + str(int(self.Shotglass)))
                elif s == "Shothendel":
                    self.Shothendel = True
                elif s == "Fotoknop":
                    self.fotoknop = True
                elif "Barcode:" in s:
                    self.barcode = s.split(':')[1]
                    self.username = self.db_conn.getUserName(self.barcode)
                    logger.info("barcode scanned in main: " + str(self.barcode) + " User: " + self.username)
                    self.ToInterfQueue.put('New_User:'+self.username)
                elif "Flush" in s:
                    self.ToIOQueue.put(s)
                elif 'NoUser' in s:
                    self.username = ""
                    self.barcode = ""
                elif 'Taken Image' in s:
                    imagename = s.split(':')[1]
                    if imagename != "No Image":
                        logger.info("recieved Image in main:" + imagename + " for user: " + self.barcode)
                        self.ToPhotoUploaderQueue.put(imagename + ":" + self.barcode)
                else:
                    logger.warning("Unknown command to main: " + s)
                s = ""

            except queue.Empty:
                pass
                
    def check_alive(self):
        return not self.quitprogram



ToInterfQueue = queue.Queue()
ToMainQueue = queue.Queue()
ToPhotoUploaderQueue = queue.Queue()
ToDBSyncQueue = queue.Queue()
ToIOQueue = queue.Queue()


shotmachine_interface.Shotmachine_Interface("Interface_main",
                                            ToInterfQueue,
                                            ToMainQueue,
                                            HandleShotmachine)

if HandleShotmachine["Settings"]["EnableDBSync"]:
    db_syncer = databasesync.DatabaseSync(ToDBSyncQueue, ToMainQueue)



main_controller = Shotmachine_controller('Main_controller',
                                         ToInterfQueue,
                                         ToMainQueue,
                                         ToDBSyncQueue,
                                         ToIOQueue,
                                         ToPhotoUploaderQueue)

inputsoutputs.InputsOutputs(HandleShotmachine,
                            ToMainQueue,
                            ToIOQueue)

if HandleShotmachine["Settings"]["EnablePhotoUploader"]:
    PhotoUploader_program = PhotoUploader(party_id, ToPhotoUploaderQueue)

controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
