import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
from Functions.DatabaseSync import databasesync
from Functions.InputsOutputs import inputsoutputs
from Functions.Database import database_connection
# from Functions.PhotoUploader.PhotoUploader import PhotoUploader
from Functions.PhotoUploader import photo_uploader
from urllib import request

import platform
import random
import datetime
import os

import json

currentOS = platform.system()
currentArch = platform.architecture()
if currentOS == 'Linux' and currentArch[0] != '64bit':
    onRaspberry = True
else:
    onRaspberry = False
# onRaspberry = False



try:
    request.urlopen('https://www.google.com/', timeout=1)
    InternetConnection = True
    #print('Internet')
except request.URLError as err: 
    InternetConnection = False
    #print('No internet')
Logdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

if not (os.path.isdir("Logs/")):
    os.mkdir("Logs/")

Logname = "Logs/" + Logdate + ".log"
logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler(Logname),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

logger.info("Start")


try:
    with open('HardwareSettings.json', 'r') as openfile:
        HardwareSettings = json.load(openfile)
except:
    # fallback settings
    logger.warning("HardwareSettings.json not found, use fallback settings and create new file")
    HardwareSettings = {
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
        "LedSignal": 25,
        "SPISSPin": 6
    }
    with open("HardwareSettings.json", "w") as outfile:
        json.dump(HardwareSettings, outfile)

try:
    with open('SoftwareSettings.json', 'r') as openfile:
        SoftwareSettings = json.load(openfile)
except:   
    # fallback settings  
    logger.warning("SoftwareSettings.json not found, use fallback settings and create new file")   
    SoftwareSettings = {
        "OnRaspberry": onRaspberry,
        "InternetConnection": InternetConnection,
        "OperationMode": "PhotoBooth",
        #"OperationMode": "Shotmachine",
        "EnableSPI": True,  # for leds
        "EnableI2C": True,  # for shotdetector & pumps
        "EnableDBSync": False,  # database synchronisatie
        "EnableBarcodeScanner": False,  # duh
        "EnablePhotoUploader": True,  # tja, wat zou dit nou zijn..
        "PartyId": 7,  # feest ID, per feest instelbaar
        "MachineId": 1,  # niet aanpassen!
        "EnableShot0": True,  # False als pomp 0 niet aan mag, True als deze wel mag
        "EnableShot1": True,  # enz...
        "EnableShot2": True,
        "EnableShot3": True,
        "EnableShot4": True
    }
    with open("SoftwareSettings.json", "w") as outfile:
        json.dump(SoftwareSettings, outfile)

HandleShotmachine = {
    "Settings": SoftwareSettings,
    "Hardware": HardwareSettings,
    "Logger": logger
}
    
'''    
HandleShotmachine = {
    "Settings": {
        "OnRaspberry": onRaspberry,
        "InternetConnection": InternetConnection,
        "OperationMode": "PhotoBooth",
        #"OperationMode": "Shotmachine",
        "EnableSPI": True,  # for leds
        "EnableI2C": True,  # for shotdetector & pumps
        "EnableDBSync": False,  # database synchronisatie
        "EnableBarcodeScanner": False,  # duh
        "EnablePhotoUploader": True,  # tja, wat zou dit nou zijn..
        "PartyId": 7,  # feest ID, per feest instelbaar
        "MachineId": 1,  # niet aanpassen!
        "EnableShot0": True,  # False als pomp 0 niet aan mag, True als deze wel mag
        "EnableShot1": True,  # enz...
        "EnableShot2": True,
        "EnableShot3": True,
        "EnableShot4": True
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
        "LedSignal": 25,
        "SPISSPin": 6
    },
    "Logger": logger
}
'''
#print(HandleShotmachine)
#print(HandleShotmachineJson)

'''
with open("HardwareSettings.json", "w") as outfile:
    json.dump(HandleShotmachine['Hardware'], outfile)
with open("SoftwareSettings.json", "w") as outfile:
    json.dump(HandleShotmachine['Settings'], outfile)
'''


class Shotmachine_controller:
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

        self.Shotglass = True
        self.Shothendel = False
        self.ShutdownPi = False
        self.possibleShots = list(range(0, 5))
        if not HandleShotmachine["Settings"]["EnableShot4"]:
            self.possibleShots.remove(4)
        if not HandleShotmachine["Settings"]["EnableShot3"]:
            self.possibleShots.remove(3)
        if not HandleShotmachine["Settings"]["EnableShot2"]:
            self.possibleShots.remove(2)
        if not HandleShotmachine["Settings"]["EnableShot1"]:
            self.possibleShots.remove(1)
        if not HandleShotmachine["Settings"]["EnableShot0"]:
            self.possibleShots.remove(0)
        self.MakeShot = False
        self.DoneWithShot = False

        self.fotoknop = False

        self.EnableBarcodeScanner = HandleShotmachine["Settings"]["EnableBarcodeScanner"]

        self.db_conn = database_connection.database_connection(HandleShotmachine)

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()

    def run(self):
        try:
            time.sleep(5)
            reset_queue = self.ToMainQueue.get(block=True, timeout=0.1)
            reset_queue = ""
        except queue.Empty:
            pass

        while not self.quitprogram:
            if self.fotoknop:
                self.fotoknop = False
                self.ToInterfQueue.put('Take_picture')
                if (self.username != "") or not self.EnableBarcodeScanner:
                    self.ToIOQueue.put("Busy")
                    self.ToIOQueue.put("Flashlight 2")
                    time.sleep(7)
                    self.ToIOQueue.put("Flashlight 1")
                    time.sleep(1)
                self.ToIOQueue.put("Ready")

            if self.Shothendel:
                self.Shothendel = False
                # self.ToInterfQueue.put('Start_roll')
                if self.Shotglass and ((self.username != "") or not self.EnableBarcodeScanner):
                    self.ToInterfQueue.put('Start_roll')
                    logger.info("start roller")
                elif not self.Shotglass and ((self.username != "") or not self.EnableBarcodeScanner):
                    logger.warning("Shot requested, but no shotglass present")
                    self.ToIOQueue.put("ShotLeds:3")
                    self.ToIOQueue.put("Ready")
                    self.ToInterfQueue.put("Missing_Shotglass")
                    ShotLedBlinkTimer = threading.Timer(5, self.ToIOQueue.put,
                                                        ["ShotLeds:" + str(int(self.Shotglass) + 1)])
                    ShotLedBlinkTimer.start()
                else:
                    # logger.warning("Shot requeested, but no user scanned and barcode is enabled")
                    # self.ToInterfQueue.put('Start_roll')
                    self.ToIOQueue.put("Ready")

            if self.MakeShot:
                self.MakeShot = False
                if len(self.possibleShots) == 0:
                    self.possibleShots = list(range(0, 5))
                    if not HandleShotmachine["Settings"]["EnableShot4"]:
                        self.possibleShots.remove(4)
                    if not HandleShotmachine["Settings"]["EnableShot3"]:
                        self.possibleShots.remove(3)
                    if not HandleShotmachine["Settings"]["EnableShot2"]:
                        self.possibleShots.remove(2)
                    if not HandleShotmachine["Settings"]["EnableShot1"]:
                        self.possibleShots.remove(1)
                    if not HandleShotmachine["Settings"]["EnableShot0"]:
                        self.possibleShots.remove(0)
                    print("self.possibleShots")
                index = random.randint(0, len(self.possibleShots) - 1)
                i = self.possibleShots[index]
                self.possibleShots.remove(i)
                self.ToIOQueue.put("MakeShot " + str(i))
                self.db_conn.ShotToDatabase(self.barcode, str(i))

            if self.DoneWithShot:
                self.DoneWithShot = False
                self.ToIOQueue.put("Ready")

            try:
                s = self.ToMainQueue.get(block=True, timeout=0.1)
                if s == "OnOffSwitch_released" or s == "Quit":
                    self.ShutdownPi = True
                    logger.info("Shutdown command recieved in main")
                    self.ToIOQueue.put("Ready")
                    #if s == "Quit":
                    self.quitprogram = True
                    self.ToIOQueue.put("Flashlight 0")  # turn off all leds on machine
                    time.sleep(0.1)
                    try:
                        ShotLedBlinkTimer.cancel()
                    except:
                        pass
                    self.ToIOQueue.put("ShotLeds:0")
                    time.sleep(0.1)
                    self.ToDBSyncQueue.put("Quit")
                    self.ToIOQueue.put("Quit")
                    self.ToInterfQueue.put("Quit")
                    self.ToPhotoUploaderQueue.put("Quit")
                    logger.info("main quit")
                elif "ShotglassState" in s:
                    self.Shotglass = bool(int(s[-1:]))
                    self.ToInterfQueue.put("Shotglass:" + str(int(self.Shotglass)))
                    try:
                        ShotLedBlinkTimer.cancel()
                    except:
                        pass
                    self.ToIOQueue.put("ShotLeds:" + str(int(self.Shotglass) + 1))
                elif s == "Shothendel":
                    self.Shothendel = True
                    logger.info("shothendel in main")
                elif s == "RollsStopped":
                    self.MakeShot = True
                elif s == "Done with shot":
                    self.DoneWithShot = True
                elif s == "Cant_make_shot":
                    logger.info("shotmachine nog bezig, shot request geweigerd")
                    self.DoneWithShot = True
                elif s == "Fotoknop":
                    self.fotoknop = True
                elif "Barcode:" in s:
                    self.barcode = s.split(':')[1]
                    self.username = self.db_conn.getUserName(self.barcode)
                    logger.info("barcode scanned in main: " + str(self.barcode) + " User: " + self.username)
                    self.ToInterfQueue.put('New_User:' + ':' + str(self.barcode) + ':' + self.username)
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
                elif 'Switch to mode: Photobooth' in s:
                    # Shutdown interface and IO subprogram
                    logger.info("Switch to Photobooth mode, via main")
                    self.ToIOQueue.put("Quit")
                    #self.ToInterfQueue.put("Quit")
                    
                    time.sleep(5)
                    
                    # Change settings and store to file
                    HandleShotmachine["Settings"]["OperationMode"] = "PhotoBooth"
                    #HandleShotmachine["Settings"]["OperationMode"]: "Shotmachine"  
                    with open("SoftwareSettings.json", "w") as outfile:
                        json.dump(HandleShotmachine['Settings'], outfile)
                    #print(HandleShotmachine)
                    
                    # Restart interface and IO subprogram
                    inputsoutputs.InputsOutputs(HandleShotmachine,
                        ToMainQueue,
                        ToIOQueue)
                    shotmachine_interface.ShotmachineInterface("Interface_main",
                        ToInterfQueue,
                        ToMainQueue,
                        HandleShotmachine)
                elif 'Switch to mode: Shotmachine' in s:
                    # Shutdown interface and IO subprogram
                    logger.info("Switch to Shotmachine mode, via main")
                    self.ToIOQueue.put("Quit")
                    #self.ToInterfQueue.put("Quit")
                    
                    time.sleep(5)
                    
                    # Change settings and store to file
                    #HandleShotmachine["Settings"]["OperationMode"]: "PhotoBooth"
                    HandleShotmachine["Settings"]["OperationMode"] = "Shotmachine"  
                    with open("SoftwareSettings.json", "w") as outfile:
                        json.dump(HandleShotmachine['Settings'], outfile)
                    
                    #print(HandleShotmachine)
                    # Restart interface and IO subprogram
                    inputsoutputs.InputsOutputs(HandleShotmachine,
                        ToMainQueue,
                        ToIOQueue)
                    shotmachine_interface.ShotmachineInterface("Interface_main",
                        ToInterfQueue,
                        ToMainQueue,
                        HandleShotmachine)    
                    
                else:
                    logger.warning("Unknown command to main: " + s)
                # s = ""

            except queue.Empty:
                pass

    # def check_alive(self):
    # return not self.quitprogram q


ToInterfQueue = queue.Queue()
ToMainQueue = queue.Queue()
ToPhotoUploaderQueue = queue.Queue()
ToDBSyncQueue = queue.Queue()
ToIOQueue = queue.Queue()

shotmachine_interface.ShotmachineInterface("Interface_main",
                                           ToInterfQueue,
                                           ToMainQueue,
                                           HandleShotmachine)

if HandleShotmachine["Settings"]["EnableDBSync"]:
    db_syncer = databasesync.DatabaseSync(ToDBSyncQueue, ToMainQueue, HandleShotmachine)

main_controller = Shotmachine_controller('Main_controller',
                                         ToInterfQueue,
                                         ToMainQueue,
                                         ToDBSyncQueue,
                                         ToIOQueue,
                                         ToPhotoUploaderQueue)

if HandleShotmachine["Settings"]["EnablePhotoUploader"]:
    logger.info("start uploader")
    PhotoUploader_program = photo_uploader.photo_uploader(ToPhotoUploaderQueue, HandleShotmachine)

inputsoutputs.InputsOutputs(HandleShotmachine,
                            ToMainQueue,
                            ToIOQueue)

controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
