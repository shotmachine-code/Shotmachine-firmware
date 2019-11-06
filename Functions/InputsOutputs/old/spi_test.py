from spidev import SpiDev
import time
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(6, GPIO.OUT)

spi = SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 390000

print("Flashlight to waitstate")
#string_to_send = "state;1\n"
string_to_send = "shot;1\n"
string_to_bytes = str.encode(string_to_send)
GPIO.output(6, 1)
time.sleep(0.01)
spi.xfer(string_to_bytes)
GPIO.output(6, 0)
time.sleep(1)
GPIO.cleanup()
