import os
from homeassistant_api import Client, State, errors
import serial
import subprocess
import sys
from HASS_Token import token
import RPi.GPIO as GPIO
import time
from threading import Thread
from Reset_Wifi import Wifi_Deamon

printSerial = False

class Philips_2200(Thread):
    def __init__(self,persistant_HASS_token, sn_serial_main=None, sn_serial_disp=None):

        GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
        self.RELAIS_PWR_DISP_GPIO = 17
        self.RELAIS_TX_RX_GPIO = 27 #RELAIS ON = MITM mode, #RELAIS Off = Normal mode

        self.sn_serial_main = sn_serial_main
        self.sn_serial_disp = sn_serial_disp
        
        self.persistant_HASS_token = persistant_HASS_token
        
        #send repetitions for the display commands
        self.cmd_rep = 20

        #mainboard protocol state definitions (mainboard -> display)
        self.preAmbelStates = {0xd5:'correct_0',0x55:'correct_1'}
        self.statesDrinkSelection = {0x00: 'Off', 0x03: 'Half Brightness', 0x07: 'Full Brightness', 0x38: 'Double', 0x3F:'Full Brightness'}
        self.beanLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED'}
        self.beanLEDStatesCtrl = {0x07: 'Show LED Group', 0x38: 'Powder Selected', 0x00:'Off'}
        self.sizeLEDStates = {0x00:'1LED/Off', 0x38:'2LED', 0x3F:'3LED', 0x07: 'TopLED'}
        self.sizeAquaLEDStates = {0x00: 'Off', 0x07:'Show LED Group',0x38:'Aqua Clean Orange'}
        self.calcCleanLEDStates = {0x00: 'Both Off', 0x38:'Calc / Clean orange', 0x07:'unknown'}
        self.emptyWaterLEDStates = {0x00: 'No error', 0x38:'Water empty'}
        self.wasteWarningLEDStates = {0x00: 'No error', 0x07:'Waste full', 0x38:'Error active'}
        self.playPauseLEDStates = {0x00:'Off', 0x07:'On'}
        
        #mainboard protocol (mainboard -> display)
        self.protocol = {0:self.preAmbelStates, 1:self.preAmbelStates,3:self.statesDrinkSelection, 4:self.statesDrinkSelection, 5:self.statesDrinkSelection, 6:self.statesDrinkSelection, 8:self.beanLEDStates, 9:self.beanLEDStatesCtrl, 10:self.sizeLEDStates, 11:self.sizeAquaLEDStates, 12:self.calcCleanLEDStates, 14:self.emptyWaterLEDStates, 15:self.wasteWarningLEDStates, 16:self.playPauseLEDStates}
        self.protocolNames = {0:'Pre_0',1:'Pre_1', 3:'Espresso LED', 4:'Hot Water LED', 5:'Coffe LED', 6:'Steam LED', 8:'Bean LED 0', 9:'Bean LED 1', 10:'Size LED', 11:'Size Aqua LED', 12:'Calc Clean', 14:'Water LED', 15:'Waste / Warning', 16:'Play LED'}
    
        #init serial
        if(sn_serial_main is None or sn_serial_disp is None):
            self.ser_display="/dev/ttyAMA2"
            self.ser_mainboard="/dev/ttyAMA3"
        else:           
            self.sn_serial_main = sn_serial_main
            self.sn_serial_disp = sn_serial_disp
            self.ser_mainboard = self.getSerialDeviceBySerialnumber(self.sn_mainboard)#"/dev/ttyUSB0" #TX_mainboard to RX_Pi_0, RX_mainboard to TX_Pi_0 
            self.ser_display = self.getSerialDeviceBySerialnumber(self.sn_display)
        self.__init_serial()
        self.__init_relais()
        self.__relais_on()
        
        self._running = False
        
        #helper for reading and setting HASS entities, blocks program until HAss is online
        self.hass_helper = self.HASS_Helper(self.persistant_HASS_token)
        #if a button was pressed inside HASS, this variable will be set to the corresponding display serial command
        self.next_cmd = None
        super(Philips_2200, self).__init__()

        #TODO enable relais for intercepting TX/RX

    def __init_serial(self):

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
            self.__relais_off(self)
    
    def __init_relais(self):
        GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
        GPIO.setup(self.RELAIS_PWR_DISP_GPIO, GPIO.OUT)  # GPIO Modus zuweisen
        GPIO.setup(self.RELAIS_TX_RX_GPIO, GPIO.OUT)  # GPIO Modus zuweisen
    
    def __relais_on(self):
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # LOW-Pegel --> Relais An	 (Normally Off connected)
        GPIO.output(self.RELAIS_TX_RX_GPIO, GPIO.LOW)
    
    def __relais_off(self):
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # LOW-Pegel --> Relais An	 (Normally Off connected)
        GPIO.output(self.RELAIS_TX_RX_GPIO, GPIO.HIGH)
    
    def __relais_pwr_toggle(self, t_off):
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.LOW)  # PWR Display Off, GND not connected
        time.sleep(t_off)
        GPIO.output(self.RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # PWR Display On, GND connected
        #time.sleep(t_off)

    # display commands (display->mainboard:

    def forward_mainboard_to_display_update_hass(self):
        if (self.dev_mainboard.inWaiting() >= 19):
            input_main = self.dev_mainboard.read(19)
            self.dev_mainboard.write(input_main)
            self.update_HASS_LED(input_main)
            return 1
        return 0

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
    def power_on_cmd_routine(self, clean=True):
        cmd_beep = b'\xd5\x55\x0a\x00\x00\x03\x02\x00\x00\x00\x32\x25'
        if(clean):
            cmd_power_on = b'\xd5\x55\x02\x01\x02\x00\x02\x00\x00\x00\x38\x15'
        else:
            cmd_power_on = b'\xd5\x55\x01\x00\x00\x03\x02\x00\x00\x00\x19\x10'
        cmd_select_nothing = 	b'\xd5\x55\x00\x00\x00\x03\x02\x00\x00\x00\x2d\x01'
        self.__relais_pwr_toggle(0.4)#0.485
        for i in range(23): #23 from recording
            self.dev_display.write(cmd_beep)
        #TODO test
        #send power on command from DisplayIntercept to Maiboard until the mainboard sends messages to the display
        count = 0
        while(self.dev_mainboard.inWaiting() <= 0):
            if(count < 7500):#150
                self.dev_display.write(cmd_power_on)
            count +=1
            if(count > 10000):
                print("No response from Mainboard to power on message")
                break
        print(count)
        #time.sleep(1)
        count_iter = 0
        count_disp_msg = 0
        count_main_msg = 0
        #time.sleep(1)
        while(True):
            count_iter +=1   
            time.sleep(0.5)
            
            while(self.dev_display.inWaiting() > 0):
                if (self.dev_display.read(1) == b'\xd5'): #Startbit received                                         
                    if (self.dev_display.inWaiting() >= 11): #In case there is data and startbit was received: Forward Display->Mainboard
                        count_disp_msg +=1
                        input_disp = b'\xd5' + self.dev_display.read(11)
                        #print("D: "+ " ".join(format(x, "02x") for x in input_disp))
                        count_main_msg += self.forward_mainboard_to_display_update_hass()
                        self.dev_display.write(input_disp)
                        
                        if(count_disp_msg >= 200):
                            break
                        
            if(count_disp_msg + count_main_msg >= 200):
                break
            if(count_iter%3==0):
                self.__relais_pwr_toggle(0.4)#0.485
                count_disp_msg = 0
                count_main_msg = 0
                print("toggle")
            count_disp_msg = 0
            count_main_msg = 0
            print("Waiting for disp")

    class HASS_Helper:
        #helper for i/o from and to homeassistant
        def __init__(self, persistant_HASS_token):
            self.persistant_HASS_token = persistant_HASS_token
            self.URL = "http://localhost:8123/api"
            self.wait_for_api()
            
        def wait_for_api(self):
            exception_thrown = True
            while(exception_thrown):
                try:
                    self.get_entity_state("binary_sensor.rpi_power_status")
                    exception_thrown = False
                    time.sleep(15)
                except errors.EndpointNotFoundError:
                    time.sleep(15)
                    print("Waiting for API")
                    continue
                except Exception:
                    time.sleep(15)
                    print("Waiting for API")
                    continue
        
        def set_entity_state(self,entity_id, value):
            client = Client(self.URL, self.persistant_HASS_token)
            client.set_state(State(state=value, entity_id=entity_id))
            
        def get_entity_state(self, entity_id):
            client = Client(self.URL, self.persistant_HASS_token) 
            entity = client.get_entity(entity_id=entity_id) #session is closed after this call
            return entity.get_state().state

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
            #espresso LED
            rd_led_state ='on'
            if(self.protocol[3][int(hex(input[3]),0)] == 'Off'):
                rd_led_state = 'off'
            elif(self.protocol[3][int(hex(input[3]),0)] == 'Double'):
                self.hass_helper.set_entity_state('input_boolean.philips_double_espresso_led','on')
            else:
                self.hass_helper.set_entity_state('input_boolean.philips_double_espresso_led','off')
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_espresso_led',rd_led_state)
            
            #hot water
            rd_led_state ='on'
            if(self.protocol[4][int(hex(input[4]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_hot_water_led',rd_led_state)

            #coffee
            rd_led_state ='on'
            if(self.protocol[5][int(hex(input[5]),0)] == 'Off'):
                rd_led_state = 'off'
            elif(self.protocol[5][int(hex(input[5]),0)] == 'Double'):
                self.hass_helper.set_entity_state('input_boolean.philips_double_coffee_led','on')
            else:
                self.hass_helper.set_entity_state('input_boolean.philips_double_coffee_led','off')
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_coffee_led',rd_led_state)
            
            #steam
            rd_led_state ='on'
            if(self.protocol[6][int(hex(input[6]),0)] == 'Off'):
                rd_led_state = 'off'
            self.hass_helper.set_entity_state('input_boolean.philips_mainboard_steam_led',rd_led_state)
 
            #Water empty
            rd_led_state ='No error'
            if(self.protocol[14][int(hex(input[14]),0)] == 'Water empty'):
                  rd_led_state = 'Water empty'
            self.hass_helper.set_entity_state('input_select.philipps_water_empty_led',rd_led_state)
            
            #Error LED
            self.hass_helper.set_entity_state('input_select.philipps_error_led',self.protocol[15][int(hex(input[15]),0)])
            
            #Cup Size
            if(self.protocol[11][int(hex(input[11]),0)] == 'Off'):
                if(self.protocol[10][int(hex(input[10]),0)] == '1LED/Off'):
                    self.hass_helper.set_entity_state('input_select.philips_cup_size_led','Off')
            elif(self.protocol[11][int(hex(input[11]),0)] == 'Show LED Group'):
                match self.protocol[10][int(hex(input[10]),0)]:
                    case '1LED/Off': rd_led_state = '1'
                    case '2LED': rd_led_state = '2'
                    case '3LED': rd_led_state = '3'
                    case 'TopLED': rd_led_state = 'TopLED'
                    case _: rd_led_state = 'Off'
                self.hass_helper.set_entity_state('input_select.philips_cup_size_led',rd_led_state)       

            #Bean / Coffee strength
            if(self.protocol[9][int(hex(input[9]),0)] == 'Off'):
                if(self.protocol[8][int(hex(input[8]),0)] == '1LED/Off'):
                    self.hass_helper.set_entity_state('input_select.philips_bean_led','Off')
            elif(self.protocol[9][int(hex(input[9]),0)] == 'Show LED Group'):
                match self.protocol[8][int(hex(input[8]),0)]:
                    case '1LED/Off': rd_led_state = '1'
                    case '2LED': rd_led_state = '2'
                    case '3LED': rd_led_state = '3'
                    case _: rd_led_state = 'Off'
                self.hass_helper.set_entity_state('input_select.philips_bean_led',rd_led_state)  
            elif(self.protocol[9][int(hex(input[9]),0)] == 'Powder Selected'):
                self.hass_helper.set_entity_state('input_select.philips_bean_led','Powder')

        except KeyError:
            print("key error")
        except Exception:
            self.__relais_off()
            
    def read_HASS_button_actions(self):
        self.next_cmd = None
        try:
            power_action = self.hass_helper.get_entity_state('input_boolean.philips_display_power_btn_event')
            power_action_nc = self.hass_helper.get_entity_state('input_boolean.philips_display_power_nc_btn_event')
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
                self.next_cmd = self.power_on_cmd_routine
                print("power on")
            elif (power_action_nc == 'on'):
                self.hass_helper.set_entity_state('input_boolean.philips_display_power_nc_btn_event', 'off')
                self.next_cmd = lambda: self.power_on_cmd_routine(False)
                print("power on - no cleaning")
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
                #print("none")
                pass
        except Exception:
            self.__relais_off()

    def run(self):
        self._running = True
        i = 0
        while (self._running):
            try:
                while (self.dev_display.inWaiting() > 0): #if there is data from display, wait until startbit is received                  
                    if (self.dev_display.read(1) == b'\xd5'):
                        break
                #In case there is data and startbit was received: Forward Display->Mainboard
                if (self.dev_display.inWaiting() >= 11):
                    input_disp = b'\xd5' + self.dev_display.read(11)
                    #print("D: "+ " ".join(format(x, "02x") for x in input_disp))
                    self.dev_display.write(input_disp)

                while (self.dev_mainboard.inWaiting() > 0): #if there is data from mainboard, wait until startbit is received
                    if (self.dev_mainboard.read(1) == b'\xd5'):
                        #print("mainboard data rec")
                        break
                        # Mainboard->Display
                if (self.dev_mainboard.inWaiting() >= 18): #In case there is data from mainboard and startbit was received: Forward Mainboard->Display, update HASS
                    input_main = b'\xd5' + self.dev_mainboard.read(18)
                    self.dev_mainboard.write(input_main)
                    if(i % 10 == 0):
                        self.update_HASS_LED(input_main)
                    #print("sent mainb->disp")
                    #print("M: "+ " ".join(format(x, "02x") for x in input_main))
                i += 1

                if (i % 100 == 0):
                    # inject commands
                    self.read_HASS_button_actions()
                    if (self.next_cmd is not None):
                        self.next_cmd()
                        print("cmd executed")
                    #Mainboard->Display

            except serial.SerialException as e:
                print(e.message + "error at serial i/o")
                self.dev_display.close()
                self.dev_mainboard.close()
                self.__init_serial()
                pass
            except Exception as e:
                self.__relais_off()
                print(str(type(e)),e)
                
if __name__ == '__main__':
    #sn_mainboard = "0001"
    #sn_display = "TGLBK1NM"

    try:
        #time.sleep(90)
        #Philips_2200 init method blocks the program until HAss is online
        coffee = Philips_2200(token) #this call halts the program until HAss is available
        coffee_thread = Thread(target = coffee.run)
        wifi = Wifi_Deamon("192.168.2.1")
        wifi_thread = Thread(target=wifi.run)        
        coffee_thread.start()
        wifi_thread.start()
        wifi_thread.join()
        coffee_thread.join()
    except Exception as e:
        print("Exception Main thread: ",e)
        coffee.__relais_off()

    '''TODO implement cmd routines
    -DONE power_off_no_clean_cmd_routine
    -power_off_clean_cmd_routine
    -DONE power_on_clean_cmd_routine
    -DONE select_bean_cmd_routine
    -DONE select_cup_cmd_routine
    '''