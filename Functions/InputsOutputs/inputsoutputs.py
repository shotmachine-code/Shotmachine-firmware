import threading
import queue
import logging
import time
from collections import namedtuple


#HandleShotmachine = {
#    "Settings": {
#        "OnRaspberry": onRaspberry,
#        "EnableSPI": False,
#        "EnableI2C": False,
#        "EnableDBSync": False,
#        "EnableBarcodeScanner": False
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

        self.logger = logging.getLogger(__name__)
        self.logger.info('Starting IO program')

        # store given variables
        self.HandleShotmachine = _HandleShotmachine
        self.ToMainQueue = _ToMainQueue
        self.ToIOQueue = _ToIOQueue

        # import required libraries depending on the current platform
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            from Functions.MCP230XX.MCP230XX import MCP230XX
            import RPi.GPIO as GPIO
            from spidev import SpiDev
            from smbus import SMBus
            #from usb import core as usb_core
            #from usb import util as usb_util
            self.OnRaspberry = True
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import GPIO
            from Functions.GPIOEmulator.ShotmachineIOEmulator import MCP230XX
            from Functions.GPIOEmulator.ShotmachineIOEmulator import SpiDev
            from Functions.GPIOEmulator.ShotmachineIOEmulator import SMBus
            from Functions.GPIOEmulator.ShotmachineIOEmulator import usb_core_emu
            #from Functions.GPIOEmulator.ShotmachineIOEmulator import usb_util

            #usb_util = usb_util_emu()
            self.OnRaspberry = False
            


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

        self.busy = False

        #Barcode scanner settings
        self.barcode_vencor_id = 0xac90
        self.barcode_product_id = 0x3003
        #interface = 0

        #Temp variable/setting
        party_id = 2


        # init GPIO
        GPIO.setmode(GPIO.BCM)
        self.GPIO = GPIO
        self.GPIO.setwarnings(False)
        self.HendelSwitch = self.HandleShotmachine["Hardware"]["HendelSwitch"]
        self.FotoSwitch = self.HandleShotmachine["Hardware"]["FotoSwitch"]
        self.EnableI2COutputPin = self.HandleShotmachine["Hardware"]["EnableI2COutput"]
        self.EnableI2COutput = self.HandleShotmachine["Settings"]["EnableI2C"]
        self.EnableBarcodeScanner = self.HandleShotmachine["Settings"]["EnableBarcodeScanner"]
        self.EnableSPI = self.HandleShotmachine["Settings"]["EnableSPI"]

        self.GPIO.setup(self.EnableI2COutputPin, GPIO.OUT)
        self.GPIO.setup(self.HendelSwitch, GPIO.IN)
        self.GPIO.setup(self.FotoSwitch, GPIO.IN)

        self.GPIO.output(self.EnableI2COutputPin, 0)

        # init MCP IO extender
        if self.EnableI2COutput:
            i2cAddress = 0x20
            self.MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
            self.MCP.set_mode(0, 'output')
            self.MCP.set_mode(1, 'output')
            self.MCP.set_mode(2, 'output')
            self.MCP.set_mode(3, 'output')
            self.MCP.set_mode(4, 'output')
            self.MCP.output(0, 1)
            self.MCP.output(1, 1)
            self.MCP.output(2, 1)
            self.MCP.output(3, 1)
            self.MCP.output(4, 1)




        # init I2C bus
        if self.EnableI2COutput:
            self.bus = SMBus(1)
            self.shotdetectorAddress = 0x70

        # init SPI
        if self.EnableSPI:
            self.spi = SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 3900000

        # start threads
        self.run = True
        self.recievebuffer = ''

        self.mainThread = threading.Thread(target=self.main_IO_interface, name='IO_main')
        self.mainThread.start()
        self.queueThread = threading.Thread(target=self.queue_watcher, name='IO_watcher')
        self.queueThread.start()
        self.queueThread = threading.Thread(target=self.checkshotglas, name='Shotglass_watcher')
        self.queueThread.start()

        if self.EnableBarcodeScanner:
            self.queueThread = threading.Thread(target=self.barcodeReaderThreat, name='Barcode_reader')
            self.queueThread.start()

        # wrap up init
        self.logger.info('Input Output program started')

    def queue_watcher(self):
        self.run = True
        while self.run:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.ToIOQueue.get(block=True, timeout=0.1)
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
                    elif "Busy" in self.recievebuffer:
                        self.busy = True
                        self.logger.info('Machine busy, ignore inputs')
                    elif "Ready" in self.recievebuffer:
                        self.busy = False
                        self.logger.info('Machine ready, checking inputs')
                    self.recievebuffer = ''
                except queue.Empty:
                    pass
            time.sleep(0.1)

    def main_IO_interface(self):

        while self.run:
            # make shot if requested
            if self.makeshot:
                self.logger.info('Making shot' + str(self.shotnumber))
                if self.EnableI2COutput:
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

                    self.MCP.output(self.shotnumber, 1)

                self.makeshot = False
                self.ToMainQueue.put("Done with shot")

            if self.setflashlight:

                self.setflashlightfunc(self.flashlightState)
                self.setflashlight = False

            if not self.busy:
                self.checkshothandle()
                self.checkfotoknop()

    def barcodeReaderThreat(self):

        if self.OnRaspberry:
            from usb import core as usb_core
            from usb import util as usb_util
        else:
            from Functions.GPIOEmulator.ShotmachineIOEmulator import usb_core_emu
            usb_core = usb_core_emu()

        if self.EnableBarcodeScanner:
            self.device = usb_core.find(idVendor=self.barcode_vencor_id, idProduct=self.barcode_product_id)
            self.usbEndpointEmu = namedtuple("usbEndpointEmu", "bEndpointAddress wMaxPacketSize")
            # self.usb_util = usb_util()


        try:
            while self.run:
                if self.OnRaspberry:
                    #self.device = usb_core.find(idVendor=self.barcode_vencor_id, idProduct=self.barcode_product_id)
                    if self.device is None:
                        print("Is the barcode reader connected and turned on?")
                        connected = False
                        break
                        
                    else:
                        connected = True
                        time.sleep(5)
                    if connected:
                        configuration = self.device.get_active_configuration()
                        # print(configuration[(1,0)][1])

                        # claim the device and it's two interfaces
                        if self.device.is_kernel_driver_active(0):
                            print("Device interface 0 is busy, claiming device")
                            self.device.detach_kernel_driver(0)

                        # is dit nodig? lijkt er op dat we alleen 0 gebruiken
                        if self.device.is_kernel_driver_active(1):
                            print("Device interface 1 is busy, claiming device")
                            self.device.detach_kernel_driver(1)

                        endpoint = self.device[0][(1, 0)][0]
                        self.device.set_configuration()

                        print("Barcode reader ready, start scanning")
                else:
                    connected = True
                    endpoint = self.usbEndpointEmu(bEndpointAddress = None, wMaxPacketSize=None)


                while self.run and connected and self.OnRaspberry:
                    try:
                        data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)

                        read_string = ''.join(chr(e) for e in data)
                        try:
                            read_number = int(read_string)
                        except:
                            read_number = None

                        if read_number != None:
                            #print("Barcode scanned: " + str(read_number))
                            self.ToMainQueue.put("Barcode:" + str(read_number))

                    except usb_core.USBError as e:
                        data = None
                        print(e.errno)
                        if e.errno == 110:
                            continue
                        if e.errno == 19:
                            print("disconnected")
                            print("Closed barcode scanner reader")
                            connected = False
                            break
                            
                while self.run and connected and not self.OnRaspberry:
                    try:
                        data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                        read_string = ''.join(chr(e) for e in data)
                        try:
                            read_number = int(read_string)
                        except:
                            read_number = None

                        if read_number != None:
                            # print("Barcode scanned: " + str(read_number))
                            self.ToMainQueue.put("Barcode:" + str(read_number))

                    except Exception as e:
                        if str(e) == 'Timeout':
                            continue
                        else:
                            raise

        finally:
            if connected and self.OnRaspberry:
                # release the device (mss self.usb_util?)
                usb_util.release_interface(device, 0)
                # is dit nodig? lijkt er op dat we alleen 0 gebruiken
                usb_util.release_interface(device, 1)
                # reattach the device to the OS kernel
                self.device.attach_kernel_driver(0)
                # is dit nodig? lijkt er op dat we alleen 0 gebruiken
                self.device.attach_kernel_driver(1)
            print("Closed barcode scanner reader")

    def checkshothandle(self):
        self.ShotHendelState = self.GPIO.input(self.HendelSwitch)

        if not self.ShotHendelSend and self.ShotHendelState:
            self.logger.info('shothendel pulled')
            self.ToMainQueue.put("Shothendel")
            self.ShotHendelSend = True
        if not self.ShotHendelState:
            self.ShotHendelSend = False

    def checkfotoknop(self):
        if self.HandleShotmachine["Settings"]["OnRaspberry"]:
            self.FotoKnopState = not self.GPIO.input(self.FotoSwitch)
        else:
            self.FotoKnopState = self.GPIO.input(self.FotoSwitch)
        if not self.FotoKnopSend and self.FotoKnopState:
            self.logger.info('fotoknop pressed')
            self.ToMainQueue.put("Fotoknop")
            self.FotoKnopSend = True
        if not self.FotoKnopState:
            self.FotoKnopSend = False

    def checkshotglas(self):
        while self.run:
            if self.EnableI2COutput:
                self.bus.write_byte_data(self.shotdetectorAddress, 0, 0x51)
                time.sleep(0.7)
                msb = self.bus.read_byte_data(self.shotdetectorAddress, 2)
                lsb = self.bus.read_byte_data(self.shotdetectorAddress, 3)
                measuredRange = (msb << 8) + lsb
                if measuredRange < 23:
                    self.CheckShotglass = True
                else:
                    self.CheckShotglass = False
                if self.shotglass != self.CheckShotglass:
                    self.logger.info('shotglas status changed to: ' + str(int(self.CheckShotglass)))
                    self.ToMainQueue.put("ShotglassState " + str(int(self.CheckShotglass)))
                    self.shotglass = self.CheckShotglass


    def setflashlightfunc(self, state):

        self.logger.info('changing flashlight state to: ' + str(state))
        string_to_send = str(state)
        string_to_bytes = str.encode(string_to_send)
        if self.EnableSPI:
            self.spi.xfer(string_to_bytes)
