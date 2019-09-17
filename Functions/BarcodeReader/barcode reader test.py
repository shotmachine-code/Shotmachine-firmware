
#Create text file /etc/udev/rules.d/99-garmin.rules with contents:
#SUBSYSTEM=="usb", ATTR{idVendor}=="ac90", ATTR{idProduct}=="3003", MODE="666"

import usb.core
#import pymysql
import time


VENDOR_BARCODE_READER = 0xac90
PRODUCT_BARCODE_READER = 0x3003
interface = 0
party_id = 2

run = True
sql_check_username = "Select name FROM users WHERE (barcode = {} AND party_id = {})"


try:
    #db = pymysql.connect("localhost", "root", "Aardslappel987", "shotmachine")
    #cursor = db.cursor()
    while run:

        device = usb.core.find(idVendor=VENDOR_BARCODE_READER, idProduct=PRODUCT_BARCODE_READER)
        if device is None:
                print("Is the barcode reader connected and turned on?")
                connected = False
        else:
            connected = True
            time.sleep(5)
        while connected:
            configuration = device.get_active_configuration()
            #print(configuration[(1,0)][1])

            # claim the device and it's two interfaces
            if device.is_kernel_driver_active(0):
                print("Device interface 0 is busy, claiming device")
                device.detach_kernel_driver(0)

            if device.is_kernel_driver_active(1):
                print("Device interface 1 is busy, claiming device")
                device.detach_kernel_driver(1)

            endpoint = device[0][(1,0)][0]
            device.set_configuration()


            print("Barcode reader ready, start scanning")
            while run:
                print('1')
                try:
                    data = device.read(endpoint.bEndpointAddress,endpoint.wMaxPacketSize)
                    #collected += 1
                    read_string = ''.join(chr(e) for e in data)
                    #read_string = "1111"
                    try:
                        read_number = int(read_string)
                    except:
                        read_number = 0
                    #try:
                        #cursor.execute(sql_check_username.format(read_number,party_id))
                        #result = cursor.fetchone()
                        #if result == None:
                        #    print("User not found, scanned barcode: " + str(read_number))
                        #else:
                        #    Username = result[0]
                        #    print("Barcode scanner from user: " + Username + " With barcode: " + str(read_number))
                    #except:
                        #print("Unexpected error:", sys.exc_info()[0])
                        #db.rollback()
                        #print("Error in sql")

                    print("Barcode scanned: " + str(read_number))

                except usb.core.USBError as e:
                    data = None
                    print(e)
                    if e.errno == 110:
                        continue
                    if e.errno == 19:
                        print("disconnected")
                        # release the device
                        #usb.util.release_interface(device, interface)
                        # reattach the device to the OS kernel
                        #device.attach_kernel_driver(interface)
                        print("Closed barcode scanner reader")
                        connected = False
                        break


finally:
    # release the device
    usb.util.release_interface(device, interface)
    # reattach the device to the OS kernel
    device.attach_kernel_driver(interface)
    print("Closed barcode scanner reader")
