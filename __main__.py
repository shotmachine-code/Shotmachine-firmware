import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
from Functions.DatabaseSync import databasesync
import platform
import random
import datetime


currentOS = platform.system()
currentArch = platform.architecture()
if (currentOS == 'Linux' and currentArch[0] != '64bit'):
    onRaspberry = True
else:
    onRaspberry = False

if onRaspberry:
    from Functions.MCP230XX.MCP230XX import MCP230XX
    import RPi.GPIO as GPIO
    import spidev
    import smbus
else:
    from Functions.GPIOEmulator.EmulatorGUI import GPIO


EnableSPI = False
EnableI2C = False


if EnableSPI:
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 7629

def SPIwrite(input):
    msb = input >> 8
    lsb = input & 0xFF
    spi.xfer([msb, lsb])


logger = logging.getLogger(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
hendelpin = 23
fotopin = 24
enablei2cpin = 4

GPIO.setup(enablei2cpin, GPIO.OUT)
GPIO.output(enablei2cpin, 0)
GPIO.setup(hendelpin , GPIO.IN)
GPIO.setup(fotopin , GPIO.IN)

i2cAddress = 0x20

if EnableI2C:
    MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
    MCP.set_mode(0, 'output')
    MCP.set_mode(1, 'output')
    MCP.set_mode(2, 'output')
    MCP.set_mode(3, 'output')
    MCP.set_mode(4, 'output')
    MCP.output(0,1)
    MCP.output(1,1)
    MCP.output(2,1)
    MCP.output(3,1)
    MCP.output(4,1)

    bus = smbus.SMBus(1)
    shotdetectorAddress = 0x70

Logfile = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
Logfile = Logfile +".txt"


def range():
    range1 = bus.read_byte_data(shotdetectorAddress, 2)
    range2 = bus.read_byte_data(shotdetectorAddress, 3)
    range3 = (range1 << 8) + range2
    return range3

def checkshotglas():
    if onRaspberry:
        bus.write_byte_data(shotdetectorAddress, 0, 0x51)
        time.sleep(0.7)
        rng = range()
        if rng < 23:
            return True
        else:
            return False
    else:
        return True



class Shotmachine_controller():
    def __init__(self, _name, _To_interface_queue, _From_interface_queue, _To_dbsync_queue):
        self.name = _name
        self.To_interface = _To_interface_queue
        self.From_interface = _From_interface_queue
        self.To_db_sync = _To_dbsync_queue
        self.state = 'Boot'
        self.quitprogram = False

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()

    def run(self):

        while not self.quitprogram:
            if onRaspberry:
                fotoknop = GPIO.input(fotopin)
            else:
                fotoknop = not GPIO.input(fotopin)
            if not fotoknop:
                if onRaspberry:
                    SPIwrite(0x48)
                self.To_interface.put('Take_picture')
                time.sleep(4)
                if onRaspberry:
                    SPIwrite(0x49)
                time.sleep(1)
                f = open(Logfile, "a")
                datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                f.write("foto at " + datetimestring + " \n")
                f.close()
            shothendel = GPIO.input(hendelpin)
            if shothendel:
                shotglass = checkshotglas()
                if shotglass:
                    self.To_interface.put('Start_roll')
                    i = random.randint(0, 4)
                    #i = 4
                    print("pump " + str(i))
                    time.sleep(6)
                    MCP.output(i,0)
                    f = open(Logfile, "a")
                    datetimestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    if i == 0:
                        time.sleep(60) #8
                        f.write("shot 0 at " + datetimestring + "\n")
                    if i == 1:
                        time.sleep(60) #4
                        f.write("shot 1 at " + datetimestring + "\n")
                    if i == 2:
                        time.sleep(60) #5
                        f.write("shot 2 at " + datetimestring + "\n")
                    if i == 3:
                        time.sleep(60) #5
                        f.write("shot 3 at " + datetimestring + "\n")
                    if i == 4:
                        time.sleep(4) #4
                        f.write("shot 4 at " + datetimestring + "\n")
                    MCP.output(i,1)
                    time.sleep(2)
                    f.close()

            try:
                s = self.From_interface.get(block=True, timeout=0.1)
                print(s)
                if s == "Quit":
                    logger.info("interface quit")
                    self.quitprogram = True
                    self.To_db_sync.put("Quit")
                    GPIO.cleanup()


            except queue.Empty:
                continue
                
    def check_alive(self):
        return not self.quitprogram


logging.basicConfig(level=logging.DEBUG)
logger.info("Start")

To_interf_que = queue.Queue()
From_interf_que = queue.Queue()
From_barcode_que = queue.Queue()
To_PhotoUploader_que = queue.Queue()
To_DBSync_que = queue.Queue()


shotmachine_interface.Shotmachine_Interface("Interface_main",
                                                    To_interf_que,
                                                    From_interf_que)

#db_syncer = databasesync.DatabaseSync(To_DBSync_que)

main_controller = Shotmachine_controller('Main_controller', 
                                                    To_interf_que, 
                                                    From_interf_que,
                                                    To_DBSync_que)

controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
