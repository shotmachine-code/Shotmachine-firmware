import threading
import queue
import time
import logging
from Functions.Interface import shotmachine_interface

logger = logging.getLogger(__name__)


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
    def __init__(self, _name, _To_interface_queue, _From_interface_queue):
        self.name = _name
        self.To_interface = _To_interface_queue
        self.From_interface = _From_interface_queue
        # controller has state
        self.state = 'Boot'
        self.quitprogram = False

        self.thread = threading.Thread(target=self.run, name=_name)
        self.thread.start()
        #return self

    def run(self):

        while not self.quitprogram:
            #print('First command')
            self.To_interface.put('Roll_screen')
            time.sleep(5)
            #self.To_interface.put('Start_roll')
            #time.sleep(15)
            self.To_interface.put('Take_picture')
            time.sleep(10)
            self.To_interface.put('Start_roll')
            time.sleep(10)
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

            except queue.Empty:
                continue
                
    def check_alive(self):
        return not self.quitprogram


logging.basicConfig(level=logging.DEBUG)
logger.info("Start")

To_interf_que = queue.Queue()
From_interf_que = queue.Queue()

shotmachine_interface.Shotmachine_Interface("Interface_main",
                                                    To_interf_que,
                                                    From_interf_que)

main_controller = Shotmachine_controller('Main_controller', 
                                                    To_interf_que, 
                                                    From_interf_que)

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
