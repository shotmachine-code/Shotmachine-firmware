from tkinter import *
import tkinter as tk
from Functions.GPIOEmulator.PIN import PIN
from Functions.GPIOEmulator.TypeChecker import typeassert
import threading
import time
from array import array

dictionaryPins = {}
dictionaryPinsTkinter = {}

GPIONames=["27","21","16","23","24","4","17","13","21","12","25","MCP0","MCP1","MCP2","MCP3","MCP4", "SPISendBuffer", "shotdetector"]
    
class App(threading.Thread):
        
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
        

    def callback(self):
        self.root.quit()


    def run(self):
        self.root = tk.Tk()
        self.root.wm_title("Shotmachine GPIO EMULATOR")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        # On/Off knop (GPIO27)
        pin13btn = Button(text="On/off\nswitch", command="27", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin13btn.grid(row=0, column=0, padx=(10, 10))
        dictionaryPinsTkinter["27"] = pin13btn

        # Config knop (GPIO21)
        pin40btn = Button(text="Config knop", command="21", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin40btn.grid(row=1, column=0, padx=(10, 10))
        dictionaryPinsTkinter["21"] = pin40btn

        # Spoel knop (GPIO16)
        pin36btn = Button(text="Spoel knop", command="16",  padx ="1px", pady="1px", bd="0px", fg="blue", relief="sunken", activeforeground="blue")
        pin36btn.grid(row=2, column=0, padx=(10, 10))
        dictionaryPinsTkinter["16"] = pin36btn

        # Shot hendel (GPIO23)
        pin16btn = Button(text="Shot\nhendel", command="23", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin16btn.grid(row=3, column=0, padx=(10, 10))
        dictionaryPinsTkinter["23"] = pin16btn

        # Foto knop (GPIO24)
        pin18btn = Button(text="Foto\nknop", command="24", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin18btn.grid(row=4, column=0, padx=(10, 10))
        dictionaryPinsTkinter["24"] = pin18btn


        # On/off led (GPIO17)
        pin11btn = Button(text="On/off\nled", command="17", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin11btn.grid(row=0, column=1, padx=(10, 10))
        dictionaryPinsTkinter["17"] = pin11btn

        # Config led (GPIO21)
        pin40btn = Button(text="Config\nled", command="21", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin40btn.grid(row=1, column=1, padx=(10, 10))
        dictionaryPinsTkinter["21"] = pin40btn

        # Spoel led (GPIO12)
        pin32btn = Button(text="Spoel\nled", command="12", padx ="1px", pady="1px", bd="0px", fg="blue", relief="sunken", activeforeground="blue")
        pin32btn.grid(row=2, column=1, padx=(10, 10))
        dictionaryPinsTkinter["12"] = pin32btn

        # signal led (GPIO25)
        pin22btn = Button(text="Signal\nled", command="25", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken", activeforeground="blue")
        pin22btn.grid(row=3, column=1, padx=(10, 10))
        dictionaryPinsTkinter["25"] = pin22btn

        # I2C Enabled (GPIO04)
        pin07btn = Button(text="I2C\nEnabled", command="4", padx="1px", pady="1px", bd="0px", fg="blue", relief="sunken",
                          activeforeground="blue")
        pin07btn.grid(row=4, column=1, padx=(10, 10))
        dictionaryPinsTkinter["4"] = pin07btn


        # Pump 0 (MCP230xx 0)
        mcp230xx0btn = Button(text="Pomp 0", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                          relief="sunken",
                          activeforeground="blue")
        mcp230xx0btn.grid(row=0, column=2, padx=(10, 10))
        dictionaryPinsTkinter["MCP0"] = mcp230xx0btn

        # Pump 1 (MCP230xx 1)
        mcp230xx1btn = Button(text="Pomp 1", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                             relief="sunken",
                             activeforeground="blue")
        mcp230xx1btn.grid(row=1, column=2, padx=(10, 10))
        dictionaryPinsTkinter["MCP1"] = mcp230xx1btn

        # Pump 2 (MCP230xx 2)
        mcp230xx2btn = Button(text="Pomp 2", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                             relief="sunken",
                             activeforeground="blue")
        mcp230xx2btn.grid(row=2, column=2, padx=(10, 10))
        dictionaryPinsTkinter["MCP2"] = mcp230xx2btn

        # Pump 3 (MCP230xx 3)
        mcp230xx3btn = Button(text="Pomp 3", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                             relief="sunken",
                             activeforeground="blue")
        mcp230xx3btn.grid(row=3, column=2, padx=(10, 10))
        dictionaryPinsTkinter["MCP3"] = mcp230xx3btn

        # Pump 4 (MCP230xx 4)
        mcp230xx4btn = Button(text="Pomp 4", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                             relief="sunken",
                             activeforeground="blue")
        mcp230xx4btn.grid(row=4, column=2, padx=(10, 10))
        dictionaryPinsTkinter["MCP4"] = mcp230xx4btn

        # flits licht foto
        flashlightbtn = Button(text="Flits\nlicht", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                              relief="sunken",
                              activeforeground="blue")
        flashlightbtn.grid(row=0, column=3, padx=(10, 10))
        dictionaryPinsTkinter["SPISendBuffer"] = flashlightbtn
        objTemp = PIN("OUT")
        objTemp.Out = "1"
        #objPin.Out = "1"
        dictionaryPins["SPISendBuffer"] = objTemp
        drawGPIOOut("SPISendBuffer")


        # shotglas detector
        shotdetector = Button(text="Shot\nglas", command="4", padx="1px", pady="1px", bd="0px", fg="blue",
                               relief="sunken",
                               activeforeground="blue")
        shotdetector.grid(row=1, column=3, padx=(10, 10))

        objTemp = PIN("IN")
        dictionaryPins["shotdetector"] = objTemp

        dictionaryPinsTkinter["shotdetector"] = shotdetector

        #objBtn = dictionaryPinsTkinter[gpioID]
        #drawBindUpdateButtonIn(str(channel), objTemp.In)
        #dictionaryPins[str(channel)] = objTemp

        #dictionaryPinsTkinter

        shotdetector.configure(background='gainsboro')
        shotdetector.configure(activebackground='gainsboro')
        shotdetector.configure(relief='raised')
        shotdetector.configure(bd="1px")
        shotdetector.bind("<Button-1>", toggleshotglasButton)
        shotdetector.In = "1"

        dictionaryPins["shotdetector"] = shotdetector
        #dictionaryPinsTkinter["shotdetector"] = shotdetector


        # objPin.Out = "1"
        #dictionaryPins["SPISendBuffer"] = objTemp


        #shotdetectorSlider = Scale(self.root, from_=22, to=23, sliderlength = 10, showvalue = 0, length = 30, orient=VERTICAL)
        #shotdetectorSlider.grid(row=1, column=3, padx=(10, 10))
        #dictionaryPinsTkinter["Shotdetector"] = shotdetectorSlider

        #SPIsendedString = Label(self.root, text="Empty")
        #SPIsendedString.grid(row = 4, column=3, padx =(10,20))
        #dictionaryPinsTkinter["SPISendBuffer"] = SPIsendedString

        # wrap up GUI
        self.root.geometry('%dx%d+%d+%d' % (300, 300, 0, 0))
       
        self.root.mainloop()


app = App()


def toggleshotglasButton(self):
    #objBtn = dictionaryPinsTkinter["shotdetector"]
    objPin = dictionaryPins["shotdetector"]
    if (objPin.In == "1"):
        objPin.In = "0"
        objPin.configure(bg="red", activebackground="Red")
    elif (objPin.In == "0"):
        objPin.configure(bg="green", activebackground="green")
        objPin.In = "1"
    dictionaryPins["shotdetector"] = objPin

def toggleButton(gpioID):
    objBtn = dictionaryPinsTkinter[str(gpioID)]
    objPin = dictionaryPins[str(gpioID)]
    
    if(objPin.In == "1"):
        objPin.In = "0"
    elif(objPin.In == "0"):
        objPin.In = "1"

  
def buttonClick(self):
    gpioID = (self.widget.config('command')[-1])
    toggleButton(gpioID)
    

def buttonClickRelease(self):
    gpioID = (self.widget.config('command')[-1])
    toggleButton(gpioID)

    
def drawGPIOOut(gpioID):
    global dictionaryPins
    global dictionaryPinsTkinter

    gpioID = str(gpioID)
    objPin = dictionaryPins[gpioID]
    objBtn = dictionaryPinsTkinter[gpioID]

    if(objPin.SetMode == "OUT"):
        if(str(objPin.Out) == "1"):
            objBtn.configure(background='tan2')
            objBtn.configure(activebackground='tan2')
        else:
            objBtn.configure(background='DarkOliveGreen3')
            objBtn.configure(activebackground='DarkOliveGreen3')
    

def drawBindUpdateButtonIn(gpioID,In):
    objBtn = dictionaryPinsTkinter[gpioID]
    objBtn.configure(background='gainsboro')
    objBtn.configure(activebackground='gainsboro')
    objBtn.configure(relief='raised')
    objBtn.configure(bd="1px")
    objBtn.bind("<Button-1>", buttonClick)
    objBtn.bind("<ButtonRelease-1>", buttonClickRelease)


class GPIO:

    #constants
    LOW = 0 
    HIGH = 1
    OUT = 2
    IN = 3
    PUD_OFF = 4
    PUD_DOWN = 5
    PUD_UP = 6
    BCM = 7

    #flags
    setModeDone = False

    #Extra functions
    def checkModeValidator():
        if(GPIO.setModeDone == False):
            raise Exception('Setup your GPIO mode. Must be set to BCM')

    
    #GPIO LIBRARY Functions
    @typeassert(int)
    def setmode(mode):
        time.sleep(1)
        if(mode == GPIO.BCM):
            GPIO.setModeDone = True
        else:
            GPIO.setModeDone = False

    @typeassert(bool)
    def setwarnings(flag):
        pass

    @typeassert(int,int,int,int)        
    def setup(channel, state, initial=-1,pull_up_down=-1):
        global dictionaryPins
        
        GPIO.checkModeValidator()

        if str(channel) not in GPIONames:
            raise Exception('GPIO ' + str(channel) + ' does not exist')

        #check if channel is already setup
        if str(channel) in dictionaryPins:
            raise Exception('GPIO is already setup')

        if(state == GPIO.OUT):
            #GPIO is set as output, default OUT 0
            objTemp =  PIN("OUT")
            if(initial == GPIO.HIGH):
                objTemp.Out = "1"
                
            dictionaryPins[str(channel)] =objTemp
            drawGPIOOut(channel)
            
        elif(state == GPIO.IN):
            #set input
            objTemp =  PIN("IN")
            if(pull_up_down == -1):
                objTemp.pull_up_down = "PUD_DOWN" #by default pud_down
                objTemp.In = "0"
            elif(pull_up_down == GPIO.PUD_DOWN):
                objTemp.pull_up_down = "PUD_DOWN"
                objTemp.In = "0"
             
            elif(pull_up_down == GPIO.PUD_UP):
                objTemp.pull_up_down = "PUD_UP"
                objTemp.In = "1"
                
            drawBindUpdateButtonIn(str(channel),objTemp.In)
            dictionaryPins[str(channel)] =objTemp


    @typeassert(int,int)
    def output(channel, outmode):
        global dictionaryPins
        channel = str(channel)
        
        GPIO.checkModeValidator()

        if channel not in dictionaryPins:
            #if channel is not setup
            raise Exception('GPIO must be setup before used')
        else:
            objPin = dictionaryPins[channel]
            if(objPin.SetMode == "IN"):
                #if channel is setup as IN and used as an OUTPUT
                raise Exception('GPIO must be setup as OUT')
        
        if(outmode != GPIO.LOW and outmode != GPIO.HIGH):
            raise Exception('Output must be set to HIGH/LOW')
            
        objPin = dictionaryPins[channel]
        if(outmode == GPIO.LOW):
            objPin.Out = "0"
        elif(outmode == GPIO.HIGH):
            objPin.Out = "1"

        drawGPIOOut(channel)


    @typeassert(int)
    def input(channel):
        global dictionaryPins
        channel = str(channel)

        GPIO.checkModeValidator()

        if channel not in dictionaryPins:
            #if channel is not setup
            raise Exception('GPIO must be setup before used')
        else:
            objPin = dictionaryPins[channel]
            if(objPin.SetMode == "OUT"):
                #if channel is setup as OUTPUT and used as an INPUT
                raise Exception('GPIO must be setup as IN')

        objPin = dictionaryPins[channel]
        if(objPin.In == "1"):
            return True
        elif(objPin.Out == "0"):
            return False

    
    def cleanup():
        app.callback()
        pass


class MCP230XX:

    LOW = 0
    HIGH = 1
    OUT = 2
    IN = 3
    PUD_OFF = 4
    PUD_DOWN = 5
    PUD_UP = 6
    BCM = 7

    global dictionaryPins
    global dictionaryPinsTkinter

    # flags
    setModeDone = True

    def __init__(self,boardname, i2cAddress, size):
        pass


    def set_mode(self, channel, state, initial=-1, pull_up_down=-1):
        global dictionaryPins

        pinname = "MCP" + str(channel)

        if (state == 'output'):
            objTemp = PIN("OUT")
            dictionaryPins[pinname] = objTemp
            drawGPIOOut(pinname)

        elif (state == GPIO.IN):
            # set input
            objTemp = PIN("IN")
            if (pull_up_down == -1):
                objTemp.pull_up_down = "PUD_DOWN"  # by default pud_down
                objTemp.In = "0"
            elif (pull_up_down == GPIO.PUD_DOWN):
                objTemp.pull_up_down = "PUD_DOWN"
                objTemp.In = "0"

            elif (pull_up_down == GPIO.PUD_UP):
                objTemp.pull_up_down = "PUD_UP"
                objTemp.In = "1"

            drawBindUpdateButtonIn(str(channel), objTemp.In)
            dictionaryPins[str(channel)] = objTemp


    def output(self, channel, outmode):
        global dictionaryPins
        channel = "MCP" + str(channel)

        objPin = dictionaryPins[channel]
        if (objPin.SetMode == "IN"):
            # if channel is setup as IN and used as an OUTPUT
            raise Exception('GPIO must be setup as OUT')

        if (outmode != GPIO.LOW and outmode != GPIO.HIGH):
            raise Exception('Output must be set to HIGH/LOW')

        objPin = dictionaryPins[channel]
        if (outmode == GPIO.LOW):
            objPin.Out = "0"
        elif (outmode == GPIO.HIGH):
            objPin.Out = "1"

        drawGPIOOut(channel)


    def input(channel):
        global dictionaryPins
        channel = str(channel)

        GPIO.checkModeValidator()

        if channel not in dictionaryPins:
            # if channel is not setup
            raise Exception('GPIO must be setup before used')
        else:
            objPin = dictionaryPins[channel]
            if (objPin.SetMode == "OUT"):
                # if channel is setup as OUTPUT and used as an INPUT
                raise Exception('GPIO must be setup as IN')

        objPin = dictionaryPins[channel]
        if (objPin.In == "1"):
            return True
        elif (objPin.Out == "0"):
            return False


    def cleanup():
        app.callback()
        pass


class SpiDev():

    def __init__(self):
        self.max_speed_hz = 0


    def open(self, bus, device):
        pass


    def xfer(self, data):
        objPin = dictionaryPins["SPISendBuffer"]
        if data.decode() == '1':
            objPin.Out = "0"
        else:
            objPin.Out = "1"

        drawGPIOOut("SPISendBuffer")


class SMBus():

    def __init__(self, bus):
        slider = dictionaryPinsTkinter["shotdetector"]
        #slider.set(20)
        self.value = self.value = (22).to_bytes(2, byteorder="big")


    def write_byte_data(self, adress, bus, data):
        if (data == 0x51):
            slidervalue = dictionaryPins["shotdetector"].In
            #slidervalue = slider.get()
            #if (objPin.In == "1"):
            if slidervalue == "1":
                self.value = (22).to_bytes(2, byteorder="big")
            if slidervalue == "0":
                self.value = (23).to_bytes(2, byteorder="big")


    def read_byte_data(self, adress, int):
        if int == 2:
            return  self.value[0]
        if int == 3:
            return  self.value[1]


class usb_core_emu():

    def __init__(self):
        self.active = [True, True]
        #self.active.append(True)

    def find(self, idVendor=None, idProduct=None):
        #self.active[0] = True
        #self.active[1] = True
        #self.dict = {0: {[(1, 0)]: {[0]}}}
        #self.selflist = [0]
        #self.selflist[0] = self
        return self

    def get_active_configuration(self):
        pass

    def is_kernel_driver_active(self, channel):
        return self.active[channel]

    def detach_kernel_driver(self, channel):
        self.active[channel] = False

    def read(self, bEndpointAddress = None, wMaxPacketSize = None):
        print("Read")
        x = array('b')
        returndata = x.frombytes('1111'.encode())
        return returndata


class usb_util():

    #def __init__(self):
    #    pass

    def release_interface(handler, channel):
        pass
