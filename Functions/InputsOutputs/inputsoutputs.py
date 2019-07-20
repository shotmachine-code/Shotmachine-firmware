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


        # prepare variables
        self.makeshot = False
        self.shotnumber = 0

        self.shotglass = False
        self.CheckShotglass = False

        self.ShotHendelState = False
        self.ShotHendelSend = False

        self.FotoKnopState = False
        self.FotoKnopSend = False


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
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            i2cAddress = 0x20
            MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
            MCP.set_mode(0, 'output')
            MCP.set_mode(1, 'output')
            MCP.set_mode(2, 'output')
            MCP.set_mode(3, 'output')
            MCP.set_mode(4, 'output')
            MCP.output(0, 1)
            MCP.output(1, 1)
            MCP.output(2, 1)
            MCP.output(3, 1)
            MCP.output(4, 1)


        # init I2C bus
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            bus = smbus.SMBus(1)
            shotdetectorAddress = 0x70

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
                    self.recievebuffer = ''
                except queue.Empty:
                    pass
            time.sleep(0.1)

    def main_IO_interface(self):

        while self.run:
            # make shot if requested
            if self.makeshot:

                if self.HandleShotmachine["Settings"]["OnRaspberry"]:
                    MCP.output(self.shotnumber, 0)

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

                if self.HandleShotmachine["Settings"]["OnRaspberry"]:
                    MCP.output(i, 1)

                self.makeshot = False
                self.ToMainQueue.put("Done with shot")


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
            self.FotoKnopState = not self.GPIO.input(fotopin)
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
            bus.write_byte_data(shotdetectorAddress, 0, 0x51)
            time.sleep(0.7)
            msb = bus.read_byte_data(shotdetectorAddress, 2)
            lsb = bus.read_byte_data(shotdetectorAddress, 3)
            range = (msb << 8) + lsb
            if rng < 23:
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