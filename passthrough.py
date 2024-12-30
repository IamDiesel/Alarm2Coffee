import serial
import time
#TODO Sicherstellen der Seriennummern zu den jeweiligen Devices sicherstellen
try:
    dev_mainboard = "/dev/ttyUSB1" #TX_mainboard to RX_Pi_0, RX_mainboard to TX_Pi_0 
    dev_display = "/dev/ttyUSB0"
    ser_main = serial.Serial(dev_mainboard)
    ser_disp = serial.Serial(dev_display)
    ser_main.baudrate = 115200
    ser_main.bytesize = 8
    ser_main.parity = 'N'
    ser_main.stopbits = 1
    ser_disp.baudrate = 115200
    ser_disp.bytesize = 8
    ser_disp.parity = 'N'
    ser_disp.stopbits = 1
    time.sleep(1)
    while(True):
        if(ser_disp.inWaiting() > 0):
            #Display->Mainboard
            print("Read disp")
            input_disp = ser_disp.read(12)
            ser_disp.write(input_disp)
            print("Write to main finished")
        if(ser_main.inWaiting() >0):
            #Mainboard->Display
            print("Read main")
            input_main = ser_main.read(19)
            ser_main.write(input_main)
            print("Write to disp finished")
        
except serial.SerialException:
    ser_disp.close()
    ser_main.close()
    pass
    