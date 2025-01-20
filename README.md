# Power on your Philips 2200 Coffeemachine when your smartphone-alarm goes off - via Raspberry Pi and Home-Assistant #
The following readme describes how to setup a raspberry pi / philips 2200 coffeemachine home assistant automation from scratch (incl. setting up home assistant on a Raspberry Pi5). Btw. thanks to https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee who gave me some inspiration / information on the coffee machine's UART-protocol.
This project is also capable of displaying the current coffeemachine state and remotly operating the coffeemachine via a smartphone's home assistant app:
![image](https://github.com/user-attachments/assets/db7b7070-5dab-4fe5-b921-18026534000e)



### Requirements: ###
- Coffee-Machine: Philips 2200
- MITM (inject & passthrough): Inject coffee selection commands and read current coffee configuration
- Use home assistant for automation and hub to the smartphone alarm
- Additional Fail-Safe mechanism in case RPi is dead and  the MITM configuration must be bridged

### Components used: ###
- Raspberry Pi5 + SD Card
- PicoFlex 90325-0008 socket
- Molex 92315-0815, Picoflex, ribbon cable 150mm
- AZDelivery 3 x 4-Relais Modul 5V
- LUCKFOX DSI Capacitive 7 inch Touch Screen with Case
- Jumper Wire / cables / glue / screws / ...

## Install home assistant on Raspberry Pi 5 ##
- Use Pi Imager to flash SD card (see https://developbyter.com/home-assistant-auf-raspberry-pi-installieren-und-einrichten/) 
- create empty file called "ssh" on sd card "bootfs"
- tell router to give RPi a constant IP address
- connect via ssh to RPi (ssh user@ipadress)
- update: sudo apt-get update && sudo apt-get upgrade -y
- install dependencies:
  - sudo apt-get install jq wget curl avahi-daemon udisks2 libglib2.0-bin network-manager dbus apparmor -y
  - sudo apt-get install systemd-journal-remote
- reboot: sudo reboot
- deactivate mac address randomisation:
  - sudo nano /etc/NetworkManager/conf.d/100-disable-wifi-mac-randomization.conf
  - Content:

~~~
[connection]
wifi.mac-address-randomization=1
[device]
wifi.scan-rand-mac-address=no
)
~~~

- install docker & add user:
  
~~~
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
docker –version
sudo usermod -aG docker <user>
~~~

- Download OS-Agent on raspberry pi: wget https://github.com/home-assistant/os-agent/releases/download/1.6.0/os-agent_1.6.0_linux_aarch64.deb
- install: sudo dpkg -i os-agent_1.6.0_linux_aarch64.deb

- install additional dependencies:

~~~
sudo apt install \
apparmor \
bluez \
cifs-utils \
curl \
dbus \
jq \
libglib2.0-bin \
lsb-release \
network-manager \
nfs-common \
systemd-journal-remote \
systemd-resolved \
udisks2 \
wget -y
~~~

- install home assistant superviced (https://github.com/home-assistant/supervised-installer/releases/download/2.0.0/homeassistant-supervised.deb)
  - sudo dpkg -i homeassistant-supervised.deb
  - during installation: choose raspberrypi5-64
  - reboot
- open home assistant in your browser: <ipadress_of_pi>:8123
- download and install smartphone app via QR-Code
- Show home assistant on startup on the 7" display:
  - configure autostart: sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
    - add the following lines:
      
~~~
@unclutter
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --noerrdialogs --check-for-update-interval=31536000 --disable-infobars --kiosk http://127.0.0.1:8123/
~~~
  if you want to keep a 5min display off timer, use the following settings:
~~~
@unclutter
@xset s off
@xset -dpms
@xset s 300 300
@xset s blank
@chromium-browser --noerrdialogs --check-for-update-interval=31536000 --disable-infobars --kiosk http://127.0.0.1:8123/
~~~


  - activate autologin on pi

~~~
cd /usr/share/hassio/homeassistant/
sudo nano configuration.yaml
~~~

  - add the following lines
    
~~~

homeassistant:
  auth_providers:
    - type: homeassistant
    - type: trusted_networks
      trusted_networks:
        - 192.168.2.0/24  # Example network, adjust to your network range
        - fd00::/8
      trusted_users:
        127.0.0.1: 6a24b8e59e2c45328cd1s97ds0b71221  # Map the IP address to the user ID
        192.168.2.43: 6a24b8249e22445x1cd1797123471221  # Map the IP address to the user ID
      allow_bypass_login: true
  ~~~
  
- install 7inch display (https://wiki.luckfox.com/):
  - sudo nano /boot/config.txt
  - add the following lines:
 
~~~
dtoverlay=vc4-kms-v3d
dtoverlay=vc4-kms-dsi-7inch
~~~

## configure home assistant ##
### Create entities (German) ###
Create entities (Einstellungen -> Geräte und Dienste -> Helfer)
![image](https://github.com/user-attachments/assets/c8b48b42-d767-49a4-8a26-b0aa1a9859a4)
![image](https://github.com/user-attachments/assets/30226f08-7ac6-44d0-a3ce-733fa3fd6ebd)




### setup alarm (Android) ###
- Open the Home Assistant App menu and select Settings
- Go to Companion App
- Select Manage Sensors
- Find the Next Alarm sensor
- Enable the Next Alarm sensor
- Create automation: „Einstellungen“->“Automatisierung & Szenen“->“Automatisierung erstellen““Neue Automatisierung“
  - Auslöser hinzufügen: “Andere Auslöser“-->“Template“
  - Template code:
  
   ~~~
    {{(now()+timedelta(0,60)).strftime('%a %h %d %H:%M %Z %Y') == (((state_attr('sensor.pixel_9_pro_next_alarm', 'Time in Milliseconds') | int / 1000) ) | timestamp_custom('%a %h %d %H:%M %Z %Y'))}}
   ~~~
   
  - add action:
![image](https://github.com/user-attachments/assets/566ee146-ef02-4c4b-a345-3907a6c4f3d8)

### setup alarm (iOs) ###
The focus sensor can be used to determine when the alarm went off.
- Create iOS shortcut named "HAss focus": deactivate focus
- Create iOS automation that executes the "Hass focus" everytime an alarm goes off
Now the companion app focus sensor of the iOS device can be used to trigger automations in Home-Assistant
- Create Home-Assistant automation:

![image](https://github.com/user-attachments/assets/62c23ed9-9666-426c-ba18-ccbea7c168bc)

![image](https://github.com/user-attachments/assets/0a2a4f7c-f723-4d27-8df9-fd5c5656f9df)

![image](https://github.com/user-attachments/assets/dd475ab2-37b0-4ae8-aaf6-07f92ecdaf46)




# Disassemble coffee machine #
The coffee machine's display can be disassembled using a plastic tool.

![image](https://github.com/user-attachments/assets/7165692b-b229-4711-93ef-43abf203967e)

The wiring between display and mainboard is as follows:

![image](https://github.com/user-attachments/assets/979c58ba-b3b3-43a2-ae99-369fd36aa86d)

Communication is run via UART @115200
The state of the coffeemachine ist sent from the mainboard to the display. The button events are sent from the display to the mainboard.

# Communication #
## Mainboard -> Display

![image](https://github.com/user-attachments/assets/1ac3123b-a995-4a80-84e9-cca3d36cf012)

## Display -> Mainboard

![image](https://github.com/user-attachments/assets/b3d6cad4-577e-4da2-b39c-02a41aa92d71)

### On / Off ###

~~~
On / Off Beep: d5 55 0a 00 00 03 02 00 00 00 32 25
Power on without cleaning cycle: d5 55 01 00 00 03 02 00 00 00 19 10	
Power Off no Cleaning cycle?: d5550000000302010000210c
~~~

### Drink Selection: ###

~~~
Select Nothing: 		d5 55 00 00 00 03 02 00 00 00 2d 01
Select Espresso:	d5 55 00 00 00 03 02 02 00 00 35 1a 	Nachricht wird 13x gesendet
perl -e 'print pack "H*", "d5550000000302020000351a"' > /dev/ttyUSB2

Hot Water:		d5 55 00 00 00 03 02 04 00 00 1d 36
Select Coffee:		d5 55 00 00 00 03 02 08 00 00 05 2b	Nachricht wird 8x gesendet
Steam:			d5 55 00 00 00 03 02 10 00 00 35 11	Nachricht wird 32x gesendet
~~~

### Settings: ###

~~~

d5 55 00 00 00 03 02 00 02 00 35 18	Bean Size
d5 55 00 00 00 03 02 00 04 00 1c 32	Coffee Size
Play:
d5 55 00 00 00 03 02 00 00 01 25 05 	Play-Button (espresso, 39x)
perl -e 'print pack "H*", "d55500000003020000012505"' > /dev/ttyUSB2
~~~

For both mainboard messages and display messages the CRC algorithm is currently unknown. So it might be necessary to record the messages individually.

## Connect relais, UART and power ##

The relayboard 1 is used as a failsafe when the pi does not power on. In that case the UART connection will be without the MITM and therby the mainboard is directly connected to the display. When the relay is activated the raspberry pi acts as MITM between mainboard and display.
Relayboard 2 is used to reset the display when activated via power on command incection. A power cycle will activate the display. This relay is also failsafe for the case, that RPi is powered off, since Display GND is connected to the Relay-Normally-Closed Pin and Relay-Common is connected to the Mainboard GND.
Here is the connection diagram:

![image](https://github.com/user-attachments/assets/06c0d2ef-7039-492d-913c-45ca3747fa98)

## Activate UART2/3 and GPIO on RPi5 & ## 

Add the following lines via "sudo nano /boot/config.txt":

![image](https://github.com/user-attachments/assets/f6b4094f-8aa5-4367-96f9-00942d288cfb)

As a result the GPIO configuration will be as follows:
- ttyAMA2	Display	Pin 7 (GPIO 4)	TX
- ttyAMA2	Display	Pin 29 (GPIO 5)	RX
- ttyAMA3	Mainboard	Pin 24 (GPIO 8)	TX
- ttyAMA3	Mainboard	Pin 21 (GPIO 9)	RX

- In order to use GPIO on RPi5 another package is required: .coffee/bin/pip install rpi-lgpio
- It could be necessary to uninstall the RPi GPIO first: .coffee/bin/pip uninstall Rpi.GPIO

## Setup Home Assistant API / install the required python packages ##

- Create a longliving HAss token in HAss: Profil->Sicherheit
  - safe this token in a file called "HASS_Token.py" with: token = "asdjalksdjkasjdklasjd your token asdlkalösdkaölsd"
- Create venv:  python3 -m venv .coffee
- install Home assistant: .coffee/bin/pip install homeassistant_api
- install pyserial: .coffee/bin/pip install pyserial

## Home Assistant WIFI Stability Issues ##
Home Assistant started beeing offline from time to time. Where the device was not reachable via ssh or the home assistant app.
The only thing that seemed to help was a wifi reset. So I wrote a little script that (e.g.) pings the local router. In case the router is not reachable the script will reset wifi, making the HAss available again.

## Finish ##

![WhatsApp Bild 2025-01-12 um 21 23 38_4eb5911e](https://github.com/user-attachments/assets/73a34edb-14ac-4d31-bebd-994a65028bc4)

- Thats it. Now run Philips_2200.py and the RPI will inject the respective display commands, when the respective Home Assistant buttons are pushed. If no button is pushed, the RPi will forward all messages from display to mainboard and vice versa. In Addition a alarm will trigger a power on command sent to the coffee machine.
- the relay boards fit nicely behind the display. I glued screws on the backside of the display module in order to fit the relay boards to the display.
- In order to run the python script on startup the following lines can be added to rc.local via sudo nano /etc/rc.local:
~~~
sudo bash -c '/home/youruser/.coffee/bin/python3 /home/youruser/Documents/philips_pi/Philips_2200.py > /home/fuchsi/Documents/philips_pi/alarm2coffee.log 2>&1' &
~~~
Of course the path must be set to your local Philips_2200.py. In addition Wifi_Reset.py must be in the same folder as Philips_2200.py.
- Also a dashboard can be created in order to interact with the coffeemachine via smartphone. Here is mine:

~~~

views:
  - type: sections
    max_columns: 2
    title: Kaffee
    path: kaffee
    icon: mdi:coffee
    sections:
      - type: grid
        cards:
          - type: tile
            entity: input_button.philips_display_power_btn
            name: Power On
            icon_tap_action:
              action: toggle
            tap_action:
              action: toggle
            hide_state: true
          - type: tile
            entity: input_button.philips_display_power_off_btn
            name: Power Off
            tap_action:
              action: toggle
            hide_state: true
          - show_name: true
            show_icon: true
            type: button
            tap_action:
              action: perform-action
              perform_action: automation.trigger
              target:
                entity_id: automation.philips_display_steam_event_helper
              data:
                skip_condition: true
            entity: input_boolean.philips_mainboard_espresso_led
            show_state: false
            name: Espresso
            icon: mdi:cup
          - show_name: true
            show_icon: true
            type: button
            tap_action:
              action: perform-action
              perform_action: automation.trigger
              target:
                entity_id: automation.philips_event_coffee_btn
              data:
                skip_condition: true
            entity: input_boolean.philips_mainboard_coffee_led
            show_state: false
            name: Coffee
            icon: mdi:coffee
          - show_name: true
            show_icon: true
            type: button
            tap_action:
              action: perform-action
              perform_action: automation.trigger
              target:
                entity_id: automation.philips_event_hot_water_btn
              data:
                skip_condition: true
            entity: input_boolean.philips_mainboard_hot_water_led
            show_state: false
            name: Hot Water
            icon: mdi:tea-outline
          - show_name: true
            show_icon: true
            type: button
            tap_action:
              action: perform-action
              perform_action: automation.trigger
              target:
                entity_id: automation.neue_automatisierung
              data:
                skip_condition: true
            entity: input_boolean.philips_mainboard_steam_led
            show_state: false
            name: Steam
            icon: mdi:weather-windy
      - type: grid
        cards:
          - show_name: true
            show_icon: true
            type: button
            tap_action:
              action: toggle
            entity: input_button.input_button_philips_display_play_btn
            grid_options:
              columns: 12
              rows: 2
            name: Start
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_bean_led
                state: '1'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_bean_btn
              icon: mdi:network-strength-1
              hold_action:
                action: toggle
              name: Strength
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_bean_led
                state: '2'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_bean_btn
              icon: mdi:network-strength-3
              hold_action:
                action: toggle
              name: Strength
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_bean_led
                state: '3'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_bean_btn
              icon: mdi:network-strength-4
              hold_action:
                action: toggle
              name: Strength
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_bean_led
                state: 'Off'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_button.philips_display_bean_btn
              icon: mdi:cancel
              hold_action:
                action: none
              name: Strength
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_cup_size_led
                state: '1'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_cup_btn
              icon: mdi:network-strength-1
              hold_action:
                action: toggle
              name: Size
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_cup_size_led
                state: '2'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_cup_btn
              icon: mdi:network-strength-3
              hold_action:
                action: toggle
              name: Size
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_cup_size_led
                state: '3'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_button.philips_display_cup_btn
              icon: mdi:network-strength-4
              hold_action:
                action: toggle
              name: Size
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philips_cup_size_led
                state: 'Off'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_button.philips_display_cup_btn
              icon: mdi:cancel
              hold_action:
                action: none
              name: Size
          - type: conditional
            conditions:
              - condition: state
                entity: input_boolean.philips_double_coffee_led
                state: 'on'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_boolean.philips_double_coffee_led
              name: Coffee
              hold_action:
                action: none
              icon: mdi:dice-2
          - type: conditional
            conditions:
              - condition: state
                entity: input_boolean.philips_double_espresso_led
                state: 'on'
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_boolean.philips_double_coffee_led
              name: Espresso
              hold_action:
                action: none
              icon: mdi:dice-2
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philipps_water_empty_led
                state: Water empty
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_select.philipps_water_empty_led
              name: No Water
              hold_action:
                action: none
              icon: mdi:water-off
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philipps_error_led
                state: Waste full
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_boolean.philips_waste_helper_led
              name: Waste full
              hold_action:
                action: none
              icon: mdi:delete-variant
          - type: conditional
            conditions:
              - condition: state
                entity: input_select.philipps_error_led
                state: Error active
            grid_options:
              columns: 6
              rows: 1
            card:
              show_name: true
              show_icon: true
              type: button
              tap_action:
                action: none
              entity: input_boolean.philips_error_helper_led
              name: Error
              hold_action:
                action: none
              icon: mdi:alert-circle
        column_span: 1
      - type: grid
        cards:
          - type: heading
            heading_style: title
            icon: mdi:alarm
            badges:
              - type: entity
                entity: input_boolean.philips_alarm_daniel
              - type: entity
                entity: sensor.pixel_9_pro_next_alarm
              - type: entity
                show_state: true
                show_icon: true
                entity: input_boolean.philips_alarm_fox
            heading: Mit Wecker einschalten
          - type: tile
            entity: input_boolean.philips_alarm_daniel
            tap_action:
              action: toggle
            name: Alarm2Coffee Daniel
            grid_options:
              columns: 12
              rows: 1
          - type: tile
            entity: input_boolean.philips_alarm_fox
            tap_action:
              action: toggle
            name: Alarm2Coffee Fox
            grid_options:
              columns: 12
              rows: 1
          - type: tile
            entity: sensor.pixel_9_pro_next_alarm
            grid_options:
              columns: 12
              rows: 2
            name: Nächster Wecker Daniel
            hide_state: false
            show_entity_picture: false
            vertical: true
            state_content:
              - state
              - Local Time
 

~~~

# TODOs #
- [ ] Create relay-circuit-board to avoid messy wiring (also 3 relays are unused)
- [ ] Refactor python software
  - [x] check for HAss availability on startup
  - [ ] refactor SW components (file / component is too big)
  - [ ] further evaluate power cycle code
  - [x] Read coffee strength and display this information in home assistant
  - [x] Read cup size and display this information in home assistant
  - [x] Read 1x / 2x and drink selection information and display this information in home assistant
  - [x] Check Home Assistant loosing WIFI connection to home net
    - [x] Write script to reset wifi when loosing connection to gateway
    - [x] evaluate power settings
