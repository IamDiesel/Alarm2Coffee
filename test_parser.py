import serial
import time

preAmbelStates = {0xd5:'correct_0',0x55:'correct_1'}
statesDrinkSelection = {0x00: 'Off', 0x03: 'Half Brightness', 0x07: 'Full Brightness', 0x38: 'Double', 0x3F:'Full Brightness'}
beanLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED'}
beanLEDStatesCtrl = {0x07: 'Show LED Group', 0x38: 'Powder Selected', 0x00:'Off'}
sizeLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED', 0x07: 'TopLED'}
sizeAquaLEDStates = {0x00: 'Off', 0x07:'Show LED Group',0x38:'Aqua Clean Orange'}
calcCleanLEDStates = {0x00: 'Both Off', 0x38:'Calc / Clean orange', 0x07:'unknown'}
emptyWaterLEDStates = {0x00: 'No error', 0x38:'Water emtpy'}
wasteWarningLEDStates = {0x00: 'No error', 0x07:'Waste full', 0x38:'Error active'}
playPauseLEDStates = {0x00:'Off', 0x07:'On'}


protocol = {0:preAmbelStates, 1:preAmbelStates,3:statesDrinkSelection, 4:statesDrinkSelection, 5:statesDrinkSelection, 6:statesDrinkSelection, 8:beanLEDStates, 9:beanLEDStatesCtrl, 10:sizeLEDStates, 11:sizeAquaLEDStates, 12:calcCleanLEDStates, 14:emptyWaterLEDStates, 15:wasteWarningLEDStates, 16:playPauseLEDStates}
protocolNames = {0:'Pre_0',1:'Pre_1', 3:'Espresso LED', 4:'Hot Water LED', 5:'Coffe LED', 6:'Steam LED', 8:'Bean LED 0', 9:'Bean LED 1', 10:'Size LED', 11:'Size Aqua LED', 12:'Calc Clean', 14:'Water LED', 15:'Waste / Warning', 16:'Play LED'}
try:
    ser = serial.Serial("/dev/ttyUSB0")
    ser.baudrate = 115200
    ser.bytesize = 8
    ser.parity = 'N'
    ser.stopbits = 1
    time.sleep(1)
    while(True):
        input = ser.read(19)
        print("test: " + protocol[4][int(hex(input[3]),0)])
        resRaw = ""
        resParsed = ""
        i=0
        for byte in input:
            hexByte = hex(byte)
            resRaw += hexByte + " "
            try:
                resParsed += protocolNames[i] + "[" + protocol[i][int(hexByte,0)] + "]"+" "
            except KeyError:
                if i not in [2,7,13,17,18]:
                    print('New Value found: Byte Pos:' + str(i) + " Val:" + hexByte+ " " + protocolNames[i]) 
            i+=1
            #print(hex(byte))
            #print(" ")
        print(resRaw)
        print(resParsed)
except serial.SerialException:
    ser.close()
    pass
        

