import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
#from Functions.DatabaseSync import databasesync
from Functions.InputsOutputs import inputsoutputs
import platform
import random
import datetime


currentOS = platform.system()
currentArch = platform.architecture()
if (currentOS == 'Linux' and currentArch[0] != '64bit'):
    onRaspberry = True
else:
    onRaspberry = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info("Start")

HandleShotmachine = {
    "Settings": {
        "OnRaspberry": onRaspberry,
        "EnableSPI": True,
        "EnableI2C": False,
        "EnableDBSync": False,
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


if HandleShotmachine["Settings"]["OnRaspberry"]:
    #from Functions.MCP230XX.MCP230XX import MCP230XX
    #import RPi.GPIO as GPIO
    import spidev
    #import smbus
#else:
#    from Functions.GPIOEmulator.EmulatorGUI import GPIO


### SPI ####
if HandleShotmachine["Settings"]["EnableSPI"]:
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 7629

def SPIwrite(input):
    msb = input >> 8
    lsb = input & 0xFF
    spi.xfer([msb, lsb])

### GPIO ###

#GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
#hendelpin = 23
#fotopin = 24
#enablei2cpin = 4

#GPIO.setup(enablei2cpin, GPIO.OUT)
#GPIO.output(enablei2cpin, 0)
#GPIO.setup(hendelpin , GPIO.IN)
#GPIO.setup(fotopin , GPIO.IN)

### I2C ###


#if HandleShotmachine["Settings"]["EnableI2C"]:
#    i2cAddress = 0x20
#    MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
#    MCP.set_mode(0, 'output')
#    MCP.set_mode(1, 'output')
#    MCP.set_mode(2, 'output')
#    MCP.set_mode(3, 'output')
#    MCP.set_mode(4, 'output')
#    MCP.output(0,1)
#    MCP.output(1,1)
#    MCP.output(2,1)
#    MCP.output(3,1)
#    MCP.output(4,1)

#    bus = smbus.SMBus(1)
#    shotdetectorAddress = 0x70


#def range():
#    range1 = bus.read_byte_data(shotdetectorAddress, 2)
#    range2 = bus.read_byte_data(shotdetectorAddress, 3)
#    range3 = (range1 << 8) + range2
#    return range3

#def checkshotglas():
#    if HandleShotmachine["Settings"]["OnRaspberry"]:
#        bus.write_byte_data(shotdetectorAddress, 0, 0x51)
#        time.sleep(0.7)
#        rng = range()
#        if rng < 23:
#            return True
#        else:
#            return False
#    else:
#        return True



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

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()

    def run(self):

        while not self.quitprogram:
            if self.fotoknop:
                self.fotoknop = False
                if HandleShotmachine["Settings"]["OnRaspberry"]:
                    SPIwrite(0x48)
                self.ToInterfQueue.put('Take_picture')
                time.sleep(4)
                if HandleShotmachine["Settings"]["OnRaspberry"]:
                    SPIwrite(0x49)
                time.sleep(1)
                f = open(Logfile, "a")
                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                f.write("foto at " + datetimestring + " \n")
                f.close()


            if self.Shothendel:
                self.Shothendel = False
                if self.Shotglass:
                    self.ToInterfQueue.put('Start_roll')
                    i = random.randint(0, 4)
                    #i = 4
                    time.sleep(6)
                    self.ToIOQueue.put("Shot " + str(i))
                    time.sleep(2)

                    f = open(Logfile, "a")
                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    f.write("shot " + str(i)  + " at " + datetimestring + "\n")
                    f.close()

            try:
                s = self.ToMainQueue.get(block=True, timeout=0.1)
                if s == "Quit":
                    self.quitprogram = True
                    self.ToDBSyncQueue.put("Quit")
                    self.ToIOQueue.put("Quit")

                    logger.info("main quit")
                elif "ShotglassState" in s:
                    self.Shotglass = bool(int(s[-1:]))
                    print("Shotglasstate in main: "+ str(self.Shotglass))
                elif s == "Shothendel":
                    self.Shothendel = True
                    print("Shot hendel in main")
                elif s == "Fotoknop":
                    self.fotoknop = True
                    print("Foto knop in main")

                s = ""

            except queue.Empty:
                pass
                
    def check_alive(self):
        return not self.quitprogram


Logfile = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
Logfile = Logfile +".txt"

ToInterfQueue = queue.Queue()
ToMainQueue = queue.Queue()
#From_barcode_que = queue.Queue()
ToPhotoUploaderQueue = queue.Queue()
ToDBSyncQueue = queue.Queue()
ToIOQueue = queue.Queue()


shotmachine_interface.Shotmachine_Interface("Interface_main",
                                                    ToInterfQueue,
                                                    ToMainQueue)

#if HandleShotmachine["Settings"]["EnableDBSync"]:
#    db_syncer = databasesync.DatabaseSync(ToDBSyncQueue)

main_controller = Shotmachine_controller('Main_controller', 
                                                    ToInterfQueue,
                                                    ToMainQueue,
                                                    ToDBSyncQueue,
                                                    ToIOQueue)

inputsoutputs.InputsOutputs(HandleShotmachine, ToMainQueue, ToIOQueue)



controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
