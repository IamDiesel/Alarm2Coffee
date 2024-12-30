import serial
import time
#TODO Sicherstellen der Seriennummern zu den jeweiligen Devices

#state = hass.states.get('input_boolean.philips_mainboard_espresso_led').state
hass.services.call('persistent_notification', 'create', {'title': "Coffee Read Python Script",'message': "Passtrough Script started"})
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

def update_LED(input):
    try:
        #resParsed += protocolNames[i] + "[" + protocol[i][int(hexByte,0)] + "]"+" "
        #espresso
        rd_led_state ='on'
        if(protocol[3][int(hex(input[3]),0)] == 'Off'):
            rd_led_state = 'off'
        hass.states.set('input_boolean.philips_mainboard_espresso_led',rd_led_state)
        #hot water
        rd_led_state ='on'
        if(protocol[4][int(hex(input[4]),0)] == 'Off'):
            rd_led_state = 'off'
        hass.states.set('input_boolean.philips_mainboard_hot_water_led',rd_led_state)
        #coffee
        rd_led_state ='on'
        if(protocol[5][int(hex(input[5]),0)] == 'Off'):
            rd_led_state = 'off'
        hass.states.set('input_boolean.philips_mainboard_coffee_led',rd_led_state)
        #steam
        rd_led_state ='on'
        if(protocol[6][int(hex(input[6]),0)] == 'Off'):
            rd_led_state = 'off'
        hass.states.set('input_boolean.philips_mainboard_steam_led',rd_led_state)                 
    except KeyError:
        print("key error")

try:
    dev_mainboard = "/dev/ttyUSB0" #TX_mainboard to RX_Pi_0, RX_mainboard to TX_Pi_0 
    dev_display = "/dev/ttyUSB1"
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
            #print("Read disp")
            input_disp = ser_disp.read(12)
            ser_disp.write(input_disp)
            #print("Write to main finished")
        if(ser_main.inWaiting() >0):
            #Mainboard->Display
            #print("Read main")
            input_main = ser_main.read(19)
            ser_main.write(input_main)
            update_LED(input_main)
            #print("Write to disp finished")
        
except serial.SerialException:
    ser_disp.close()
    ser_main.close()
    pass
    
