import threading
import queue
import logging
import time

#HandleShotmachine = {
#    "Settings": {
#        "OnRaspberry": onRaspberry,
#        "EnableSPI": False,
#        "EnableI2C": False,
#        "EnableDBSync": False,
#    },
#    "Hardware": {
#        "OnOffSwitch": 27,
#        "ConfigSwitch": 21,
#        "SpoelSwitch": 16,
#        "HendelSwitch": 23,
#        "FotoSwitch": 24,
#        "EnableI2COutput": 4,
#        "OnOffLed": 17,
#        "ResetArduino": 13,
#        "LedConfig": 21,
#        "LedSpoel": 12,
#        "LedSignal": 25
#    },
#    "Logger": logger
#}


class InputsOutputs:
    def __init__(self, _HandleShotmachine, _ToMainQueue, _ToIOQueue):

        # store given variables
        self.HandleShotmachine = _HandleShotmachine
        self.ToMainQueue = _ToMainQueue
        self.ToIOQueue = _ToIOQueue

        # import required libraries depending on the current platform
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            from Functions.MCP230XX.MCP230XX import MCP230XX
            import RPi.GPIO as GPIO
            import spidev
            import smbus
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import GPIO
            from Functions.GPIOEmulator.ShotmachineIOEmulator import MCP230XX
            from Functions.GPIOEmulator.ShotmachineIOEmulator import SpiDev


        # prepare variables
        self.makeshot = False
        self.shotnumber = 0

        self.shotglass = False
        self.CheckShotglass = False

        self.ShotHendelState = False
        self.ShotHendelSend = False

        self.FotoKnopState = False
        self.FotoKnopSend = False

        self.flashlightState = 0
        self.setflashlight = False


        # init GPIO
        GPIO.setmode(GPIO.BCM)
        self.GPIO = GPIO
        self.GPIO.setwarnings(False)
        self.HendelSwitch = self.HandleShotmachine["Hardware"]["HendelSwitch"]
        self.FotoSwitch = self.HandleShotmachine["Hardware"]["FotoSwitch"]
        self.EnableI2COutput = self.HandleShotmachine["Hardware"]["EnableI2COutput"]

        self.GPIO.setup(self.EnableI2COutput, GPIO.OUT)
        self.GPIO.setup(self.HendelSwitch, GPIO.IN)
        self.GPIO.setup(self.FotoSwitch, GPIO.IN)

        self.GPIO.output(self.EnableI2COutput, 0)

        # init MCP IO extender
        i2cAddress = 0x20
        self.MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
        self.MCP.set_mode(0, 'output')
        self.MCP.set_mode(1, 'output')
        self.MCP.set_mode(2, 'output') #self.MCP.set_mode(2, 'output')
        self.MCP.set_mode(3, 'output')
        self.MCP.set_mode(4, 'output') #self.MCP.config(4, OUTPUT)
        self.MCP.output(0, 1)
        self.MCP.output(1, 1)
        self.MCP.output(2, 1)
        self.MCP.output(3, 1)
        self.MCP.output(4, 1)


        # init I2C bus
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            self.bus = smbus.SMBus(1)
            self.shotdetectorAddress = 0x70

        # init SPI
        self.spi = SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 7629

        # start threads
        self.run = True
        self.recievebuffer = ''
        self.logger = logging.getLogger("InputOutput")

        self.mainThread = threading.Thread(target=self.main_IO_interface, name='IO_main')
        self.mainThread.start()
        self.queueThread = threading.Thread(target=self.queue_watcher, name='IO_watcher')
        self.queueThread.start()

        # wrap up init
        self.logger.info('Input Output program started')

    def queue_watcher(self):
        self.run = True
        while self.run:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.ToIOQueue.get(block=True, timeout=0.1)
                    #print(self.recievebuffer)
                    if self.recievebuffer == "Quit":
                        self.run = False
                        self.GPIO.cleanup()
                        self.logger.info("IO quit")
                    elif "Shot" in self.recievebuffer:
                        self.shotnumber = int(self.recievebuffer[-1:])
                        self.makeshot = True
                    elif "Flashlight" in self.recievebuffer:
                        self.flashlightState = int(self.recievebuffer[-1:])
                        self.setflashlight = True
                    self.recievebuffer = ''
                except queue.Empty:
                    pass
            time.sleep(0.1)

    def main_IO_interface(self):

        while self.run:
            # make shot if requested
            if self.makeshot:

                #if self.HandleShotmachine["Settings"]["OnRaspberry"]:
                self.MCP.output(self.shotnumber, 0)

                if self.shotnumber == 0:
                    time.sleep(8)  # 8
                elif self.shotnumber == 1:
                    time.sleep(4)  # 4
                elif self.shotnumber == 2:
                    time.sleep(5)  # 5
                elif self.shotnumber == 3:
                    time.sleep(5)  # 5
                elif self.shotnumber == 4:
                    time.sleep(4)  # 4

                #if self.HandleShotmachine["Settings"]["OnRaspberry"]:
                self.MCP.output(self.shotnumber, 1)

                self.makeshot = False
                self.ToMainQueue.put("Done with shot")

            if self.setflashlight:
                self.setflashlightfunc(self.flashlightState)
                self.setflashlight = False


            self.checkshothandle()
            self.checkshotglas()
            self.checkfotoknop()


    def checkshothandle(self):
        self.ShotHendelState = self.GPIO.input(self.HendelSwitch)

        if not self.ShotHendelSend and self.ShotHendelState:
            self.ToMainQueue.put("Shothendel")
            self.ShotHendelSend = True
            print("Shot hendel send")
        if not self.ShotHendelState:
            self.ShotHendelSend = False

    def checkfotoknop(self):
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            self.FotoKnopState = not self.GPIO.input(self.FotoSwitch)
        else:
            self.FotoKnopState = self.GPIO.input(self.FotoSwitch)
        if not self.FotoKnopSend and self.FotoKnopState:
            self.ToMainQueue.put("Fotoknop")
            self.FotoKnopSend = True
            print("Foto knop send")
        if not self.FotoKnopState:
            self.FotoKnopSend = False

    def checkshotglas(self):
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            self.bus.write_byte_data(self.shotdetectorAddress, 0, 0x51)
            time.sleep(0.7)
            msb = self.bus.read_byte_data(self.shotdetectorAddress, 2)
            lsb = self.bus.read_byte_data(self.shotdetectorAddress, 3)
            measuredRange = (msb << 8) + lsb
            print(measuredRange)
            if measuredRange < 23:
                self.CheckShotglass = True
            else:
                self.CheckShotglass = False
        else:
            #time.sleep(10)
            self.CheckShotglass = True #not self.CheckShotglass

        if self.shotglass != self.CheckShotglass:
            self.ToMainQueue.put("ShotglassState " + str(int(self.CheckShotglass)))
            self.shotglass = self.CheckShotglass
            print("Shotglass state: " + str(self.shotglass))


    def setflashlightfunc(self, state):
        #if state:
        #    msb = 0x48 >> 8
        #    lsb = 0x48 & 0xFF
        #    self.spi.xfer([msb, lsb])
        #else:
        #    msb = 0x49 >> 8
        #    lsb = 0x49 & 0xFF
        #    self.spi.xfer([msb, lsb])
        string_to_send = str(state)
        string_to_bytes = str.encode(string_to_send)
        self.spi.xfer(string_to_bytes)
