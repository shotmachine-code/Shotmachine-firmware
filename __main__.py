import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface
#from Functions.DatabaseSync import databasesync
import RPi.GPIO as GPIO
import random
import datetime

from Functions.MCP230XX.MCP230XX import MCP230XX

#!/usr/bin/python

import spidev

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 7629

# Split an integer input into a two byte array to send via SPI
def write_pot(input):
    msb = input >> 8
    lsb = input & 0xFF
    spi.xfer([msb, lsb])

# Repeatedly switch a MCP4151 digital pot off then on
#while True:


logger = logging.getLogger(__name__)
GPIO.setmode(GPIO.BCM)
# Zet waarschuwingen uit.
GPIO.setwarnings(False)
hendelpin = 23
fotopin = 24
enablei2cpin = 4

#GPIO.setup(enablei2cpin, GPIO.OUT)
GPIO.setup(enablei2cpin, GPIO.OUT)
GPIO.output(enablei2cpin, 0)
GPIO.setup(hendelpin , GPIO.IN)
GPIO.setup(fotopin , GPIO.IN)

i2cAddress = 0x20

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

#GPIO.setup(port_or_pin, GPIO.IN)  # set a port/pin as an input  
#GPIO.setup(port_or_pin, GPIO.OUT) # set a port/pin as an output   
#GPIO.output(port_or_pin, 1)       # set an output port/pin value to 1/HIGH/True  
#GPIO.output(port_or_pin, 0)       # set an output port/pin value to 0/LOW/False  
#i = GPIO.input(port_or_pin)

import smbus
import time
bus = smbus.SMBus(1)
address = 0x70

Logfile = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
Logfile = Logfile +".txt"

def write(value):
        bus.write_byte_data(address, 0, value)
        return -1


def range():
        range1 = bus.read_byte_data(address, 2)
        range2 = bus.read_byte_data(address, 3)
        range3 = (range1 << 8) + range2
        return range3

def checkshotglas():
    write(0x51)
    time.sleep(0.7)
    rng = range()
    if rng < 23:
        return True
    else:
        return False


#while True:
#        write(0x51)
#        time.sleep(0.7)
#        rng = range()
#        print(rng)


class Send():
    """base class for a sender"""

    def __init__(self, name, sQueue):
        self.name = name
        self.sQueue = sQueue

        self.thread = threading.Thread(target=self.run, name=name)
        self.thread.start()

    def run(self):
        """ no runner so far """
        pass


class Receive():
    """base class for a receiver"""

    def __init__(self, name, rQueue):
        self.name = name
        self.rQueue = rQueue

        self.thread = threading.Thread(target=self.run, name=name)
        self.thread.start()

    def run(self):
        """ no runner so far """
        while True:
            try:
                s = self.rQueue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue
            self.processMessage(s)

    def processMessage(self, s):
        pass


class TestSend(Send):
    def __init__(self, name, sQueue):
        Send.__init__(self, name, sQueue)

    def run(self):
        while True:
            """simulate some event"""
            time.sleep(1)
            logger.info("{name:s}: push event 'sendEvent'".format(name=self.name))
            self.sQueue.put('event')


class MotorReceive(Receive):
    def __init__(self, name, rQueue):
        Receive.__init__(self, name, rQueue)

    def processMessage(self, s):
        if 'on' == s:
            logger.info("{name:s}: Motor on".format(name=self.name))
        elif 'off' == s:
            logger.info("{name:s}: Motor off".format(name=self.name))
        else:
            logger.error("{name:s}: Unknown message '{msg:s}'".format(name=self.name, msg=s))


class Shotmachine_controller():
    def __init__(self, _name, _To_interface_queue, _From_interface_queue, _To_dbsync_queue):
        self.name = _name
        self.To_interface = _To_interface_queue
        self.From_interface = _From_interface_queue
        self.To_db_sync = _To_dbsync_queue
        # controller has state
        self.state = 'Boot'
        self.quitprogram = False

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()
        #return self

    def run(self):

        while not self.quitprogram:
            #shotglass = checkshotglas()
            #print(shotglass)
            fotoknop = GPIO.input(fotopin)
            if not fotoknop:
                write_pot(0x48)
                self.To_interface.put('Take_picture')
                time.sleep(4)
                write_pot(0x49)
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
                    i = 4
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
                    #MCP.output(i,0)
                    #time.sleep(1)
                    #MCP.output(i,1)
                    #
            #write_pot(0x48)
            #time.sleep(0.5)
            #write_pot(0x49)
            #time.sleep(0.5)
            
            #print('First command')
            #self.To_interface.put('Roll_screen')
            #time.sleep(5)
            #self.To_interface.put('Start_roll')
            #time.sleep(15)
            #self.To_interface.put('Take_picture')
            #time.sleep(10)time.sleep(10)   
            #self.To_interface.put('Start_roll')
            #time.sleep(10)
            #self.To_interface.put('Show_picture')
            #time.sleep(5)
            #self.To_interface.put('Roll_screen')
            #time.sleep(5)
            try:
                s = self.From_interface.get(block=True, timeout=0.1)
                print(s)
                if s == "Quit":
                    logger.info("interface quit")
                    self.quitprogram = True
                    self.To_db_sync.put("Quit")

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


#sQueue = queue.Queue()

#rQueue = queue.Queue()
#testSend = TestSend("simulate_send", rQueue)



#motor = MotorReceive("front_left", rQueue)

#logger.info("Some test ---")
#rQueue.put("off")
#rQueue.put("unqrqrqrq")
controller_alive = True
while controller_alive:
    time.sleep(1)
    controller_alive = not main_controller.quitprogram
