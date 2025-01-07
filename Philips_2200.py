import os
from homeassistant_api import Client, State
import serial
import subprocess
import sys
from HASS_Token import token
import RPi.GPIO as GPIO
import time

class Philips_2200:
    def __init__(self, sn_serial_main, sn_serial_disp, persistant_HASS_token):

        GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
        self.RELAIS_PWR_DISP_GPIO = 17
        self.RELAIS_TX_RX_GPIO = 27 #RELAIS ON = MITM mode, #RELAIS Off = Normal mode

        GPIO.setup(self.RELAIS_PWR_DISP_GPIO, GPIO.OUT)  # GPIO Modus zuweisen
        GPIO.setup(self.RELAIS_TX_RX_GPIO, GPIO.OUT)  # GPIO Modus zuweisen
        #GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.LOW)  # aus
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # an
        GPIO.output(self.RELAIS_TX_RX_GPIO, GPIO.HIGH)  # MITM Mode (intercept communication between mainboard and display)
        #usb <-> serial uart device serial numbers
        #can be retrieved e.g. via shell: /bin/udevadm info --name=/dev/ttyUSB0 | grep ID_USB_SERIAL_SHORT
        self.sn_serial_main = sn_serial_main
        self.sn_serial_disp = sn_serial_disp
        
        self.persistant_HASS_token = persistant_HASS_token
        
        #send repetitions for the display commands
        self.cmd_rep = 20 #35 #TODO check this parameter

        #mainboard protocol state definitions (mainboard -> display)
        self.preAmbelStates = {0xd5:'correct_0',0x55:'correct_1'}
        self.statesDrinkSelection = {0x00: 'Off', 0x03: 'Half Brightness', 0x07: 'Full Brightness', 0x38: 'Double', 0x3F:'Full Brightness'}
        self.beanLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED'}
        self.beanLEDStatesCtrl = {0x07: 'Show LED Group', 0x38: 'Powder Selected', 0x00:'Off'}
        self.sizeLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED', 0x07: 'TopLED'}
        self.sizeAquaLEDStates = {0x00: 'Off', 0x07:'Show LED Group',0x38:'Aqua Clean Orange'}
        self.calcCleanLEDStates = {0x00: 'Both Off', 0x38:'Calc / Clean orange', 0x07:'unknown'}
        self.emptyWaterLEDStates = {0x00: 'No error', 0x38:'Water emtpy'}
        self.wasteWarningLEDStates = {0x00: 'No error', 0x07:'Waste full', 0x38:'Error active'}
        self.playPauseLEDStates = {0x00:'Off', 0x07:'On'}
        
        #mainboard protocol (mainboard -> display)
        self.protocol = {0:self.preAmbelStates, 1:self.preAmbelStates,3:self.statesDrinkSelection, 4:self.statesDrinkSelection, 5:self.statesDrinkSelection, 6:self.statesDrinkSelection, 8:self.beanLEDStates, 9:self.beanLEDStatesCtrl, 10:self.sizeLEDStates, 11:self.sizeAquaLEDStates, 12:self.calcCleanLEDStates, 14:self.emptyWaterLEDStates, 15:self.wasteWarningLEDStates, 16:self.playPauseLEDStates}
        self.protocolNames = {0:'Pre_0',1:'Pre_1', 3:'Espresso LED', 4:'Hot Water LED', 5:'Coffe LED', 6:'Steam LED', 8:'Bean LED 0', 9:'Bean LED 1', 10:'Size LED', 11:'Size Aqua LED', 12:'Calc Clean', 14:'Water LED', 15:'Waste / Warning', 16:'Play LED'}
    
        #init serial
        self.__init_serial()
        
        self.running = False
        
        #helper for reading and setting HASS entities
        self.hass_helper = self.HASS_Helper(self.persistant_HASS_token)
        #if a button was pressed inside HASS, this variable will be set to the corresponding display serial command
        self.next_cmd = None

        #TODO enable relais for intercepting TX/RX

    def __init_serial(self):
        self.ser_mainboard = self.getSerialDeviceBySerialnumber(sn_mainboard)#"/dev/ttyUSB0" #TX_mainboard to RX_Pi_0, RX_mainboard to TX_Pi_0
        self.ser_display = self.getSerialDeviceBySerialnumber(sn_display)
        try:
            self.dev_display = serial.Serial(self.ser_display, write_timeout=1)
            self.dev_mainboard = serial.Serial(self.ser_mainboard,write_timeout=1)
            self.dev_mainboard.baudrate = 115200
            self.dev_mainboard.bytesize = 8
            self.dev_mainboard.parity = 'N'
            self.dev_mainboard.stopbits = 1
            self.dev_display.baudrate = 115200
            self.dev_display.bytesize = 8
            self.dev_display.parity = 'N'
            self.dev_display.stopbits = 1
        except serial.SerialException:
            self.dev_display.close()
            self.dev_mainboard.close()

    #TODO implement reading from HASS buttons --> sending display commands to mainboard
    #TODO write main
    # display commands (display->mainboard:

    def forward_mainboard_to_display_update_hass(self):
        if (self.dev_mainboard.inWaiting() >= 19):
            input_main = self.dev_mainboard.read(19)
            self.dev_mainboard.write(input_main)
            self.update_HASS_LED(input_main)

    def select_coffee_cmd_routine(self):
        cmd_select_coffee = b'\xd5\x55\x00\x00\x00\x03\x02\x08\x00\x00\x05\x2b'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_coffee)
            self.forward_mainboard_to_display_update_hass()
    def select_espresso_cmd_routine(self):
        cmd_select_espresso = b'\xd5\x55\x00\x00\x00\x03\x02\x02\x00\x00\x35\x1a'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_espresso)
            self.forward_mainboard_to_display_update_hass()
    def select_hot_water_cmd_routine(self):
        cmd_select_hot_water = b'\xd5\x55\x00\x00\x00\x03\x02\x04\x00\x00\x1d\x36'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_hot_water)
            self.forward_mainboard_to_display_update_hass()
    def select_steam_cmd_routine(self):
        cmd_select_steam = b'\xd5\x55\x00\x00\x00\x03\x02\x10\x00\x00\x35\x11'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_steam)
            self.forward_mainboard_to_display_update_hass()
    def select_play_cmd_routine(self):
        cmd_select_play = b'\xd5\x55\x00\x00\x00\x03\x02\x00\x00\x01\x25\x05'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_play)
            self.forward_mainboard_to_display_update_hass()

    def power_off_no_clean_cmd_routine(self):
        cmd_power_off = b'\xd5\x55\x00\x00\x00\x03\x02\x01\x00\x00\x21\x0c'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_power_off)
            self.forward_mainboard_to_display_update_hass()

    def select_bean_cmd_routine(self):
        cmd_select_bean_size = b'\xd5\x55\x00\x00\x00\x03\x02\x00\x02\x00\x35\x18'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_bean_size)
            self.forward_mainboard_to_display_update_hass()
    def select_cup_cmd_routine(self):
        cmd_select_cup_size = 	b'\xd5\x55\x00\x00\x00\x03\x02\x00\x04\x00\x1c\x32'
        for i in range(self.cmd_rep):
            self.dev_display.write(cmd_select_cup_size)
            self.forward_mainboard_to_display_update_hass()
    def power_on_no_clean_cmd_routine(self):
        cmd_beep = b'TODO'
        cmd_power_on = b'\xd5\x55\x01\x00\x00\x03\x02\x00\x00\x00\x19\x10'
        for i in range(10): #TODO validate repetitions
            self.dev_display.write(cmd_beep)
        #TODO test
        #send power on command from DisplayIntercept to Maiboard until the mainboard sends messages to the display
        count = 0
        while(self.dev_mainboard.inWaiting() <= 0):
            self.dev_display.write(cmd_power_on)
            count +=1
            if(count > 150):
                print("No response from Mainboard to power on message")
                break
        #power cycle display
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.LOW)  # aus
        time.sleep(0.3) #TODO evaluate this parameter
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # an
        self.forward_mainboard_to_display_update_hass()

    '''TODO implement cmd routines
    -DONE power_off_no_clean_cmd_routine
    -power_off_clean_cmd_routine
    -power_on_clean_cmd_routine
    -DONE select_bean_cmd_routine
    -DONE select_cup_cmd_routine
    '''

    class HASS_Helper:
        #helper for i/o from and to homeassistant
        def __init__(self, persistant_HASS_token):
            self.persistant_HASS_token = persistant_HASS_token
            self.URL = "http://localhost:8123/api"
        
        def set_entity_state(self,entity_id, value):
            client = Client(self.URL, self.persistant_HASS_token)
            client.set_state(State(state=value, entity_id=entity_id))
            
        def get_entity_state(self, entity_id):
            client = Client(self.URL, self.persistant_HASS_token) 
            entity = client.get_entity(entity_id=entity_id) #session is closed after this call
            return entity.get_state().state

    #class Machine_State:

        
    
    def getSerialDeviceBySerialnumber(self, serialnumber):
        device = None
        for i in range(10):
            tmpDevice = f'/dev/ttyUSB{i}'
            command = f'/bin/udevadm info --name={tmpDevice} | grep ID_USB_SERIAL_SHORT'
            try:
                result = subprocess.check_output(command, shell = True, executable = "/bin/bash", stderr = subprocess.STDOUT)
                #print(result.splitlines()[0].decode())
                if(result.splitlines()[0].decode().split('=')[1] == serialnumber):
                    #print(f"Found Device with S/N [{serialnumber}]: {tmpDevice}")
                    device = tmpDevice
            except subprocess.CalledProcessError as cpe:
                result = cpe.output
                #print(result)
                continue
        return device
    

    def update_HASS_LED(self,input):
        try:
            #resParsed += protocolNames[i] + "[" + protocol[i][int(hexByte,0)] + "]"+" "
            #espresso LED
            rd_led_state ='on'
            if(self.protocol[3][int(hex(input[3]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_espresso_led',rd_led_state)
            #hass.states.set('input_boolean.philips_mainboard_espresso_led',rd_led_state)
            #hot water
            rd_led_state ='on'
            if(self.protocol[4][int(hex(input[4]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_hot_water_led',rd_led_state)
            #hass.states.set('input_boolean.philips_mainboard_hot_water_led',rd_led_state)
            #coffee
            rd_led_state ='on'
            if(self.protocol[5][int(hex(input[5]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_coffee_led',rd_led_state)
            #hass.states.set('input_boolean.philips_mainboard_coffee_led',rd_led_state)
            #steam
            rd_led_state ='on'
            if(self.protocol[6][int(hex(input[6]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_steam_led',rd_led_state)
            #hass.states.set('input_boolean.philips_mainboard_steam_led',rd_led_state)                 
        except KeyError:
            print("key error")
            
    def read_HASS_button_actions(self):
        def read_HASS_button_actions(self):
            self.next_cmd = None
            power_action = self.hass_helper.get_entity_state('input_boolean.philips_display_power_btn_event')
            espresso_action = self.hass_helper.get_entity_state('input_boolean.philips_display_espresso_btn')
            coffee_action = self.hass_helper.get_entity_state('input_boolean.philips_display_coffee_btn_event')
            water_action = self.hass_helper.get_entity_state('input_boolean.philips_display_hot_water_btn_event')
            steam_action = self.hass_helper.get_entity_state('input_boolean.philips_display_steam_btn_event')
            play_action = self.hass_helper.get_entity_state('input_boolean.philips_display_play_btn_event')
            cup_action = self.hass_helper.get_entity_state('input_boolean.philips_display_cup_btn_event')
            bean_action = self.hass_helper.get_entity_state('input_boolean.philips_display_bean_btn_event')
            off_action = self.hass_helper.get_entity_state('input_boolean.philips_display_power_off_btn_event')

            if (espresso_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_espresso_btn', 'off')
                self.next_cmd = self.select_espresso_cmd_routine
            elif (coffee_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_coffee_btn_event', 'off')
                self.next_cmd = self.select_coffee_cmd_routine
            elif (water_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_hot_water_btn_event', 'off')
                self.next_cmd = self.select_hot_water_cmd_routine
            elif (steam_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_steam_btn_event', 'off')
                self.next_cmd = self.select_steam_cmd_routine
            elif (play_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_play_btn_event', 'off')
                self.next_cmd = self.select_play_cmd_routine
            elif (power_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_power_btn_event', 'off')
                self.next_cmd = self.power_on_no_clean_cmd_routine
                print("power on")
            elif (cup_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_cup_btn_event', 'off')
                self.next_cmd = self.select_cup_cmd_routine
            elif (bean_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_bean_btn_event', 'off')
                self.next_cmd = self.select_bean_cmd_routine
            elif (off_action == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_power_off_btn_event', 'off')
                self.next_cmd = self.power_off_no_clean_cmd_routine
            else:
                print("none")

    def run(self):
        self.running = True
        i = 0
        while (self.running):
            try:
                while (True):
                    if (self.dev_display.inWaiting() == 0):
                        break
                    if (self.dev_display.read(1) == b'\xd5'):
                        break
                        # Display->Mainboard
                if (self.dev_display.inWaiting() >= 11):
                    input_disp = b'\xd5' + self.dev_display.read(11)
                    # print(" ".join(format(x, "02x") for x in input_disp))
                    self.dev_display.write(input_disp)
                else:
                    # TODO: this cmd is only necessary, when the display does not start up
                    # should net be sent, when device is turned off
                    self.dev_display.write(self.cmd_select_nothing)
                while (True):
                    if (self.dev_mainboard.inWaiting() == 0):
                        break
                    if (self.dev_mainboard.read(1) == b'\xd5'):
                        break
                        # Mainboard->Display
                if (self.dev_mainboard.inWaiting() >= 19):
                    input_main = b'\xd5' + self.dev_mainboard.read(19)
                    self.dev_mainboard.write(input_main)
                    self.update_HASS_LED(input_main)
                i += 1

                if (i % 100 == 0):
                    # inject commands
                    self.read_HASS_button_actions()
                    if (self.next_cmd is not None):
                        self.next_cmd()
                            #Mainboard->Display

            except serial.SerialException as e:
                print(e.message + "error at serial i/o")
                self.dev_display.close()
                self.dev_mainboard.close()
                self.__init_serial()
                pass
            except Exception as e:
                print(str(type(e)) + e.message)
                
if __name__ == '__main__':
    sn_mainboard = "0001"
    sn_display = "TGLBK1NM"
    coffee = Philips_2200(sn_mainboard,sn_display,token)
    coffee.run()
