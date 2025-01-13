import RPi.GPIO as GPIO
import time

RELAIS_PWR_DISP_GPIO = 17
RELAIS_TX_RX_GPIO = 27 #RELAIS ON = MITM mode, #RELAIS Off = Normal mode

def init():
    global RELAIS_PWR_DISP_GPIO, RELAIS_TX_RX_GPIO
    GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
    GPIO.setup(RELAIS_PWR_DISP_GPIO, GPIO.OUT)  # GPIO Modus zuweisen
    GPIO.setup(RELAIS_TX_RX_GPIO, GPIO.OUT)  # GPIO Modus zuweisen

def relais_off():
    global RELAIS_PWR_DISP_GPIO, RELAIS_TX_RX_GPIO
    GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.HIGH) #High-Pegel --> Relais Aus (Normally On connected)
    GPIO.output(RELAIS_TX_RX_GPIO, GPIO.HIGH)

def relais_on():
    global RELAIS_PWR_DISP_GPIO, RELAIS_TX_RX_GPIO
    GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # LOW-Pegel --> Relais An	 (Normally Off connected)
    GPIO.output(RELAIS_TX_RX_GPIO, GPIO.LOW)

def relais_toggle():
    global RELAIS_PWR_DISP_GPIO, RELAIS_TX_RX_GPIO
    for i in range(5):
        GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.LOW)  # an
        time.sleep(1)
        GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # aus
        time.sleep(1)


                
if __name__ == '__main__':
    init()
    #relais_toggle()
    #relais_off()
    #relais_on()
    GPIO.output(RELAIS_PWR_DISP_GPIO, GPIO.HIGH)  # LOW-Pegel --> Relais An	 (Normally Off connected)
    GPIO.output(RELAIS_TX_RX_GPIO, GPIO.HIGH)