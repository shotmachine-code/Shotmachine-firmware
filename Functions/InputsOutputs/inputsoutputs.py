import threading
import queue
import logging
import time
from collections import namedtuple


class InputsOutputs:
    def __init__(self, _HandleShotmachine, _ToMainQueue, _ToIOQueue):

        # Start logger
        self.logger = logging.getLogger(__name__)
        self.logger.info('Starting IO program')

        # store given variables
        self.HandleShotmachine = _HandleShotmachine
        self.ToMainQueue = _ToMainQueue
        self.ToIOQueue = _ToIOQueue

        # Get needed settings from settings struct
        self.HendelSwitch = self.HandleShotmachine["Hardware"]["HendelSwitch"]
        self.FotoSwitch = self.HandleShotmachine["Hardware"]["FotoSwitch"]
        self.EnableI2COutputPin = self.HandleShotmachine["Hardware"]["EnableI2COutput"]
        self.EnableI2COutput = self.HandleShotmachine["Settings"]["EnableI2C"]
        self.EnableBarcodeScanner = self.HandleShotmachine["Settings"]["EnableBarcodeScanner"]
        self.EnableSPI = self.HandleShotmachine["Settings"]["EnableSPI"]
        self.ConfigSwitchPin = self.HandleShotmachine["Hardware"]["ConfigSwitch"]
        self.ResetArduinoPin = self.HandleShotmachine["Hardware"]["ResetArduino"]
        self.SPISSPin = self.HandleShotmachine["Hardware"]["SPISSPin"]
        # self.party_id = self.HandleShotmachine["Settings"]["PartyId"]

        # import required libraries depending on the current platform
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            from Functions.MCP230XX.MCP230XX import MCP230XX
            import RPi.GPIO as GPIO
            from spidev import SpiDev
            from smbus import SMBus
            self.OnRaspberry = True
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import GPIO
            # from Functions.GPIOEmulator.ShotmachineIOEmulator import MCP230XX
            from Functions.GPIOEmulator.ShotmachineIOEmulator import SpiDev
            from Functions.GPIOEmulator.ShotmachineIOEmulator import SMBus
            from Functions.GPIOEmulator.ShotmachineIOEmulator import usb_core_emu
            self.OnRaspberry = False

        # prepare general variables
        self.makeshot = False
        self.shotnumber = 0
        self.shotglass = False
        self.CheckShotglass = True
        self.ShotHendelState = False
        self.ShotHendelSend = False
        self.FotoKnopState = False
        self.FotoKnopSend = False
        self.ConfigSwitchState = False
        self.ConfigSwitchStateSend = False
        self.flashlightState = 1
        self.setflashlight = True
        self.SetShotLeds = True
        self.shotLedsState = 0
        self.FlushPump = False
        self.flushnumber = 0
        self.busy = False
        self.run = True
        self.recievebuffer = ''

        # Barcode scanner settings
        self.barcode_vencor_id = 0xac90
        self.barcode_product_id = 0x3003

        # init GPIO
        GPIO.setmode(GPIO.BCM)
        self.GPIO = GPIO
        self.GPIO.setwarnings(False)
        self.GPIO.setup(self.EnableI2COutputPin, GPIO.OUT)
        self.GPIO.setup(self.ResetArduinoPin, GPIO.OUT)
        self.GPIO.setup(self.SPISSPin, GPIO.OUT)
        self.GPIO.setup(self.HendelSwitch, GPIO.IN)
        self.GPIO.setup(self.FotoSwitch, GPIO.IN)
        self.GPIO.setup(self.ConfigSwitchPin, GPIO.IN)

        # set GPIO pins
        self.GPIO.output(self.EnableI2COutputPin, 0)
        self.GPIO.output(self.ResetArduinoPin, 0)
        self.GPIO.output(self.SPISSPin, 0)
        time.sleep(0.1)

        # init MCP IO extender
        if self.EnableI2COutput:
            self.MCPConnected = False
            self.queueThread = threading.Thread(target=self.MCPCommunication, name='MCPCommunication_thread')
            self.queueThread.start()

            # i2cAddress = 0x20
            # self.MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
            # self.MCP.set_mode(0, 'output')
            # self.MCP.output(0, 1)
            # time.sleep(0.1)
            # self.MCP.set_mode(1, 'output')
            # self.MCP.output(1, 1)
            # time.sleep(0.1)
            # self.MCP.set_mode(2, 'output')
            # self.MCP.output(2, 1)
            # time.sleep(0.1)
            # self.MCP.set_mode(3, 'output')
            # self.MCP.output(3, 1)
            # time.sleep(0.1)
            # self.MCP.set_mode(4, 'output')
            # self.MCP.output(4, 1)
            # self.MCP.set_mode(5, 'input')
            # self.MCP.output(4, 1)

        # init I2C bus
        if self.EnableI2COutput:
            self.bus = SMBus(1)
            self.shotdetectorAddress = 0x70

        # init SPI
        if self.EnableSPI:
            self.spi = SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 390000

        # start threads
        self.mainThread = threading.Thread(target=self.main_IO_interface, name='IO_main')
        self.mainThread.start()
        # self.queueThread = threading.Thread(target=self.queue_watcher, name='IO_watcher')
        # self.queueThread.start()
        self.queueThread = threading.Thread(target=self.checkshotglas, name='Shotglass_watcher')
        self.queueThread.start()

        if self.EnableBarcodeScanner:
            self.queueThread = threading.Thread(target=self.barcodeReaderThreat, name='Barcode_reader')
            self.queueThread.start()

        # wrap up init
        self.logger.info('Input Output program started')

    def queue_watcher(self):
        # Watch queue from interface and process commands
        # self.run = True
        # while self.run:
        # if self.recievebuffer == '':
        try:
            self.recievebuffer = self.ToIOQueue.get(block=True, timeout=0.1)
            if self.recievebuffer == "Quit":
                self.run = False
                self.logger.info("IO quit")
            elif "MakeShot" in self.recievebuffer:
                self.shotnumber = int(self.recievebuffer[-1:])
                self.makeshot = True
            elif "ShotLeds" in self.recievebuffer:
                self.shotLedsState = int(self.recievebuffer[-1:])
                self.SetShotLeds = True
            elif "Flush" in self.recievebuffer:
                self.flushnumber = int(self.recievebuffer[-1:])
                self.FlushPump = True
            elif "Flashlight" in self.recievebuffer:
                self.flashlightState = int(self.recievebuffer[-1:])
                self.setflashlight = True
            elif "Ready" in self.recievebuffer:
                self.busy = False
                self.logger.info('Machine ready, checking inputs')
            self.recievebuffer = ''
        except queue.Empty:
            pass
        # time.sleep(0.1)

    def main_IO_interface(self):
        # Main loop that executes the commands
        while self.run:
            # Check queue from main program
            self.queue_watcher()

            # Make shot
            if self.makeshot:
                self.logger.info('Making shot: ' + str(self.shotnumber))
                if self.EnableI2COutput and self.MCPConnected:
                    try:
                        self.MCP.output(self.shotnumber, 0)
                    except OSError:
                        self.MCPConnected = False
                    if self.shotnumber == 0:
                        time.sleep(5)  # 8
                    elif self.shotnumber == 1:
                        time.sleep(6)  # 4
                    elif self.shotnumber == 2:
                        time.sleep(6)  # 5
                    elif self.shotnumber == 3:
                        time.sleep(5)  # 5
                    elif self.shotnumber == 4:
                        time.sleep(6)  # 4
                    try:
                        self.MCP.output(self.shotnumber, 1)
                    except OSError:
                        self.MCPConnected = False

                self.makeshot = False
                time.sleep(1)
                self.ToMainQueue.put("Done with shot")

            # Flush pump
            if self.FlushPump:
                self.logger.info('Spoelen van pomp: ' + str(self.flushnumber))
                if self.EnableI2COutput and self.MCPConnected:
                    self.MCP.output(self.flushnumber, 0)
                    time.sleep(10)
                    # TODO add possibility to stop on command
                    self.MCP.output(self.flushnumber, 1)
                self.FlushPump = False
                time.sleep(1)
                self.ToMainQueue.put("Klaar met spoelen")

            # Change flashlight state
            if self.setflashlight:
                self.setflashlightfunc(self.flashlightState)
                self.setflashlight = False

            # Change shot leds state
            if self.SetShotLeds:
                self.setShotLedsfunc(self.shotLedsState)
                self.SetShotLeds = False

            # Check inputs
            if not self.busy:
                self.checkshothandle()
                self.checkfotoknop()
                # self.checkArduinoReset()

        # cleanup GPIO and pumps and close program 
        if self.EnableI2COutput:
            del self.MCP
            time.sleep(1)
        self.GPIO.cleanup()

    def MCPCommunication(self):
        from contextlib import suppress
        if self.OnRaspberry:
            from Functions.MCP230XX.MCP230XX import MCP230XX
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import MCP230XX

        while self.run:
            if not self.MCPConnected:
                # try:
                with suppress(OSError):
                    i2cAddress = 0x20
                    self.MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
                    self.MCP.set_mode(0, 'output')
                    self.MCP.output(0, 1)
                    time.sleep(0.1)
                    self.MCP.set_mode(1, 'output')
                    self.MCP.output(1, 1)
                    time.sleep(0.1)
                    self.MCP.set_mode(2, 'output')
                    self.MCP.output(2, 1)
                    time.sleep(0.1)
                    self.MCP.set_mode(3, 'output')
                    self.MCP.output(3, 1)
                    time.sleep(0.1)
                    self.MCP.set_mode(4, 'output')
                    self.MCP.output(4, 1)
                    self.MCP.set_mode(5, 'output')
                    self.MCP.output(5, 1)
                    self.MCP.set_mode(6, 'input')
                    self.MCPConnected = True
                # except OSError as e:
                # self.MCPConnected = False
                # self.logger.warning('Failed to get communication back with MCP)')
            if self.MCPConnected:
                try:
                    value = self.MCP.input(6)
                except OSError as e:
                    self.logger.warning('No communication with pump module (MCP IO extender)')
                    self.MCPConnected = False

            time.sleep(1)

    def barcodeReaderThreat(self):
        # import required libraries for barcode scanner
        if self.OnRaspberry:
            from usb import core as usb_core
            from usb import util as usb_util
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import usb_core_emu
            usb_core = usb_core_emu()

        # make usb connection to scanner
        # if self.EnableBarcodeScanner:
        self.device = usb_core.find(idVendor=self.barcode_vencor_id, idProduct=self.barcode_product_id)
        self.usbEndpointEmu = namedtuple("usbEndpointEmu", "bEndpointAddress wMaxPacketSize")

        try:
            while self.run:
                # on raspberry, find actual scanner
                if self.OnRaspberry:
                    if self.device is None:
                        # No scanner found
                        self.logger.error("No barcode scanner found, is it connected and turned on?")
                        connected = False
                        break
                    else:
                        # Found scanner, give it some time to start
                        connected = True
                        time.sleep(5)
                    if connected:
                        # claim the device and it's interface
                        configuration = self.device.get_active_configuration()
                        if self.device.is_kernel_driver_active(0):
                            # fisrt detach scanner from os before it can be claimed
                            self.device.detach_kernel_driver(0)
                        endpoint = self.device[0][(1, 0)][0]
                        self.device.set_configuration()
                        self.logger.info("Barcode reader ready, start scanning")
                else:
                    # Barcode scanner in emulator mode
                    self.logger.info("Barcode scanner in emulation mode")
                    connected = True
                    endpoint = self.usbEndpointEmu(bEndpointAddress=None, wMaxPacketSize=None)

                while self.run and connected and self.OnRaspberry:
                    # check usb connection for messages and convert to barcode
                    try:
                        data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                        read_string = ''.join(chr(e) for e in data)
                        try:
                            read_number = int(read_string)
                        except:
                            read_number = None
                        if read_number is not None:
                            self.logger.info("Barcode scanned: " + str(read_number))
                            self.ToMainQueue.put("Barcode:" + str(read_number))

                    except usb_core.USBError as e:
                        # error in checking messsages from scanner
                        data = None
                        if e.errno == 110:
                            # timeout, just keep checking
                            continue
                        if e.errno == 19:
                            # Connection lost, try to reconnect 
                            self.logger.warning("Connection to barode scanner lost, closed connection if software")
                            connected = False
                            break

                while self.run and connected and not self.OnRaspberry:
                    # Emulator barcode scanner
                    try:
                        data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                        read_string = ''.join(chr(e) for e in data)
                        try:
                            read_number = int(read_string)
                        except:
                            read_number = None
                        if read_number is not None:
                            self.logger.info("Barcode scanned: " + str(read_number))
                            self.ToMainQueue.put("Barcode:" + str(read_number))
                    except Exception as e:
                        if str(e) == 'Timeout':
                            continue
                        else:
                            self.logger.error("Warning in barcode reader: " + e)
                            raise
        finally:
            # close connection to barcode scanner on closing
            if connected and self.OnRaspberry:
                usb_util.release_interface(self.device, 0)
            self.logger.info("Closed barcode scanner reader")

    def checkshothandle(self):
        # Controleer de sensor van de hendel
        self.ShotHendelState = self.GPIO.input(self.HendelSwitch)
        if not self.ShotHendelSend and self.ShotHendelState:
            self.logger.info('shothendel pulled')
            self.ToMainQueue.put("Shothendel")
            self.ShotHendelSend = True
            self.busy = True
        if not self.ShotHendelState:
            self.ShotHendelSend = False

    def checkArduinoReset(self):
        # reset function fro arduino, work in progress
        self.ConfigSwitchState = self.GPIO.input(self.ConfigSwitchPin)
        if self.ConfigSwitchState:
            time.sleep(0.5)
            self.ConfigSwitchState = self.GPIO.input(self.ConfigSwitchPin)
            if not self.ConfigSwitchStateSend and self.ConfigSwitchState:
                self.logger.info('Config button pressed, resetting arduino')
                self.ConfigSwitchStateSend = True
                self.GPIO.output(self.ResetArduinoPin, 1)
                time.sleep(1)
                self.GPIO.output(self.ResetArduinoPin, 0)
            if not self.ConfigSwitchState:
                self.ConfigSwitchStateSend = False

    def checkfotoknop(self):
        # Controleer fotoknop
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            self.FotoKnopState = not self.GPIO.input(self.FotoSwitch)
        else:
            # in emulation mode the input is inverted
            self.FotoKnopState = self.GPIO.input(self.FotoSwitch)
        if not self.FotoKnopSend and self.FotoKnopState:
            self.logger.info('fotoknop pressed')
            self.ToMainQueue.put("Fotoknop")
            self.FotoKnopSend = True
            self.busy = True
        if not self.FotoKnopState:
            self.FotoKnopSend = False

    def checkshotglas(self):
        # check Ultrasonic sensor for shotglass detector, takes some time therefore in a separate thread
        while self.run:
            if self.EnableI2COutput:
                try:
                    self.bus.write_byte_data(self.shotdetectorAddress, 0, 0x51)
                    time.sleep(0.3)
                    msb = self.bus.read_byte_data(self.shotdetectorAddress, 2)
                    lsb = self.bus.read_byte_data(self.shotdetectorAddress, 3)
                    measuredRange = (msb << 8) + lsb
                except:
                    # print("error in i2c")
                    measuredRange = 23
                if (measuredRange != 7) or (measuredRange != 110):
                    # print(measuredRange)
                    if measuredRange < 26:  # 25:
                        self.CheckShotglass = True
                    else:
                        self.CheckShotglass = False
                    if self.shotglass != self.CheckShotglass:
                        self.logger.info('shotglas status changed to: ' + str(int(self.CheckShotglass)))
                        self.ToMainQueue.put("ShotglassState " + str(int(self.CheckShotglass)))
                        self.shotglass = self.CheckShotglass
            else:
                if self.shotglass != self.CheckShotglass:
                    self.logger.info('shotglas status changed to: ' + str(int(self.CheckShotglass)))
                    self.ToMainQueue.put("ShotglassState " + str(int(self.CheckShotglass)))
                    self.shotglass = self.CheckShotglass

    def setflashlightfunc(self, state):
        # change flashlight mode by sending mode to arduino that controls the leds
        self.logger.info('changing flashlight state to: ' + str(state))
        # string_to_send = "state;" + str(state) + "\n"
        # string_to_bytes = str.encode(string_to_send)
        # self.GPIO.output(self.SPISSPin, 1)
        # time.sleep(0.03)
        # if self.EnableSPI:
           # self.spi.xfer(string_to_bytes)
        # self.GPIO.output(self.SPISSPin, 0)
        if self.EnableI2COutput and self.MCPConnected:
            try:
                self.MCP.output(5, state)
            except OSError as e:
                self.logger.warning('No communication with flashlight module (MCP IO extender)')
                self.MCPConnected = False

    def setShotLedsfunc(self, state):
        # change leds in shothok by sensing mode to arduino that controls the leds
        self.logger.info('changing shot leds state to: ' + str(state))
        string_to_send = "shot;" + str(state) + "\n"
        string_to_bytes = str.encode(string_to_send)
        self.GPIO.output(self.SPISSPin, 1)
        time.sleep(0.03)
        if self.EnableSPI:
            self.spi.xfer(string_to_bytes)
        self.GPIO.output(self.SPISSPin, 0)
