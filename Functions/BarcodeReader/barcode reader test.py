
#Create text file /etc/udev/rules.d/99-garmin.rules with contents:
#SUBSYSTEM=="usb", ATTR{idVendor}=="ac90", ATTR{idProduct}=="3003", MODE="666"

import usb.core
VENDOR_LEGO = 0xac90
PRODUCT_EV3 = 0x3003
device = usb.core.find(idVendor=VENDOR_LEGO, idProduct=PRODUCT_EV3)
if device is None:
        print("Is the brick connected and turned on?")
configuration = device.get_active_configuration()
print(configuration[(1,0)][1])

# claim the device and it's two interfaces
if device.is_kernel_driver_active(0):
    print("Busy")
    device.detach_kernel_driver(0)

if device.is_kernel_driver_active(1):
    print("detach 1")
    device.detach_kernel_driver(1)

endpoint = device[0][(1,0)][0]
device.set_configuration()

collected = 0
interface = 0
attempts = 50
while True :
    try:
        data = device.read(endpoint.bEndpointAddress,endpoint.wMaxPacketSize)
        collected += 1
        #print(data)

        str1 = ''.join(chr(e) for e in data)
        print(int(str1))
    except usb.core.USBError as e:
        print("Timeout")
        data = None
        if e.args == ('Operation timed out',):
            continue
# release the device
usb.util.release_interface(device, interface)
# reattach the device to the OS kernel
device.attach_kernel_driver(interface)