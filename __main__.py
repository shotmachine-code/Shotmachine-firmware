import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
from Functions.DatabaseSync import databasesync
from Functions.InputsOutputs import inputsoutputs
from Functions.Database import database_connection

import platform
import random
import datetime
import os


import xml.etree.ElementTree as ET

xml_file_path = os.path.join(os.getcwd(), 'mysql_settings.xml')
tree = ET.parse(xml_file_path)
root = tree.getroot()

for mysqlXML in root.findall('mysql'):
    if mysqlXML.get('name') == 'local':
        localMysqlUser = mysqlXML.find('user').text
        localMysqlPass = mysqlXML.find('password').text
        localMysqlIP = mysqlXML.find('ip').text

party_id = 2


currentOS = platform.system()
currentArch = platform.architecture()
if (currentOS == 'Linux' and currentArch[0] != '64bit'):
    onRaspberry = True
else:
    onRaspberry = False
#onRaspberry = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info("Start")

HandleShotmachine = {
    "Settings": {
        "OnRaspberry": onRaspberry,
        "EnableSPI": True,
        "EnableI2C": True,
        "EnableDBSync":False,
        "EnableBarcodeScanner": True
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
        "LedConfig": 21,
        "LedSpoel": 12,
        "LedSignal": 25
    },
    "Logger": logger
}



class Shotmachine_controller():
    def __init__(self, _name, _ToInterfQueue, _ToMainQueue, _ToDBSyncQueue, _ToIOQueue):
        self.name = _name
        self.ToInterfQueue = _ToInterfQueue
        self.ToMainQueue = _ToMainQueue
        self.ToDBSyncQueue = _ToDBSyncQueue
        self.ToIOQueue = _ToIOQueue
        self.state = 'Boot'
        self.quitprogram = False

        self.Shotglass = False
        self.Shothendel = False

        self.fotoknop = False

        self.EnableBarcodeScanner = HandleShotmachine["Settings"]["EnableBarcodeScanner"]

        self.db_conn = database_connection.database_connection()

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()

    def run(self):

        while not self.quitprogram:
            if self.fotoknop:
                self.fotoknop = False
                self.ToIOQueue.put("Busy")
                self.ToIOQueue.put("Flashlight 1")
                self.ToInterfQueue.put('Take_picture')
                time.sleep(4)
                self.ToIOQueue.put("Flashlight 0")
                time.sleep(1)
                f = open(Logfile, "a")
                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                f.write("foto at " + datetimestring + " \n")
                f.close()
                self.ToIOQueue.put("Ready")


            if self.Shothendel:
                self.Shothendel = False
                if self.Shotglass:
                    self.ToIOQueue.put("Busy")
                    self.ToInterfQueue.put('Start_roll')
                    i = random.randint(0, 4)
                    #i = 0
                    time.sleep(6)
                    self.ToIOQueue.put("Shot " + str(i))
                    time.sleep(2)
                    self.db_conn.ShotToDatabase(barcode, str(i))

                    f = open(Logfile, "a")
                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    f.write("shot " + str(i)  + " at " + datetimestring + "\n")
                    f.close()
                    self.ToIOQueue.put("Ready")

            try:
                s = self.ToMainQueue.get(block=True, timeout=0.1)
                if s == "Quit":
                    self.quitprogram = True
                    self.ToDBSyncQueue.put("Quit")
                    self.ToIOQueue.put("Quit")

                    logger.info("main quit")
                elif "ShotglassState" in s:
                    self.Shotglass = bool(int(s[-1:]))
                    self.ToInterfQueue.put("Shotglass:" + str(int(self.Shotglass)))
                elif s == "Shothendel":
                    self.Shothendel = True
                elif s == "Fotoknop":
                    self.fotoknop = True
                elif "Barcode:" in s:
                    barcode = s.split(':')[1]
                    username = self.db_conn.getUserName(barcode)
                    print("barcode scanned in main: " + str(barcode) + " User: " + username)
                    self.ToInterfQueue.put('New_User:'+username)
                elif 'NoUser' in s:
                    username = ""
                    barcode = ""
                else:
                    print("Unknown command to main: " + s)
                s = ""

            except queue.Empty:
                pass
                
    def check_alive(self):
        return not self.quitprogram





Logfile = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
Logfile = Logfile +".txt"

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
                                         ToIOQueue)

inputsoutputs.InputsOutputs(HandleShotmachine,
                            ToMainQueue,
                            ToIOQueue)


controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
