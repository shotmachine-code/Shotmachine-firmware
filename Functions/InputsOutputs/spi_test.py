from spidev import SpiDev
import time



def setflashlightfunc(spi, state):
      print('changing flashlight state to: ' + str(state))
      string_to_send = str(state)
      string_to_bytes = str.encode(string_to_send)
      spi.xfer(string_to_bytes)



spi = SpiDev()
spi.open(0, 0)
#spi.max_speed_hz = 7629
spi.max_speed_hz = 3900000


while True:
      print("Enable leds")
      setflashlightfunc(spi, 1)
      time.sleep(5)
      print("disable leds")
      setflashlightfunc(spi, 0)
      time.sleep(5)
      
