### Power on Philips 2200 Coffeemachine on smartphone-alarm via Raspberry Pi and Home-Assistant ###
![image](https://github.com/user-attachments/assets/1eeee930-636a-45a1-ab63-98c0c5c57c0b)


- Coffee-Machine: Philips 2200
- MITM (inject & passthrough): Inject coffee selection commands and read current coffee configuration
- Use home assistant for automation and hub to the smartphone alarm
- Additional Fail-Safe mechanism in case RPi is dead and  the MITM configuration must be bridged

Components used:
- Raspberry Pi5 + SD Card
- PicoFlex 90325-0008 socket
- Molex 92315-0815, Picoflex, ribbon cable 150mm
- AZDelivery 3 x 4-Relais Modul 5V
- LUCKFOX DSI Capacitive 7 inch Touch Screen with Case
- Jumper Wire / cables / glue / screws / ...

### Install home assistant on Raspberry Pi 5 ###
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
```
[connection]
wifi.mac-address-randomization=1
[device]
wifi.scan-rand-mac-address=no
)
```
- install docker & add user:
´´´
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
docker –version
sudo usermod -aG docker <user>
´´´
- Download OS-Agent on raspberry pi: wget https://github.com/home-assistant/os-agent/releases/download/1.6.0/os-agent_1.6.0_linux_aarch64.deb
- install: sudo dpkg -i os-agent_1.6.0_linux_aarch64.deb

- install additional dependencies:
´´´
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
´´´
- install home assistant superviced (https://github.com/home-assistant/supervised-installer/releases/download/2.0.0/homeassistant-supervised.deb)
  - sudo dpkg -i homeassistant-supervised.deb
  - during installation: choose raspberrypi5-64
  - reboot
- open home assistant in your browser: <ipadress_of_pi>:8123
- download and install smartphone app via QR-Code
- Show home assistant on startup on the 7" display:
  - configure autostart: sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
    - add the following lines:
´´´
@unclutter
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --noerrdialogs --check-for-update-interval=31536000 --disable-infobars --kiosk http://127.0.0.1:8123/
´´´
  - activate autologin on pi
´´´
cd /usr/share/hassio/homeassistant/
sudo nano configuration.yaml
´´´
  - add the following lines
´´´
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
   ´´´   
- install 7inch display (https://wiki.luckfox.com/):
  - sudo nano /boot/config.txt
  - add the following lines:
 
´´´
dtoverlay=vc4-kms-v3d
dtoverlay=vc4-kms-dsi-7inch
´´´
### configure home assistant ###
## Create entities (German) ##
Create entities (Einstellungen -> Geräte und Dienste -> Helfer)
![image](https://github.com/user-attachments/assets/92806d0c-d983-4e49-8316-0e5e1caac7e1)
![image](https://github.com/user-attachments/assets/e3ebc246-aa10-4801-9fed-4610fc1dc235)
![image](https://github.com/user-attachments/assets/1ed82db4-cce8-4a71-af64-9677af77bd7e)

## setup alarm (Android) ##
- Open the Home Assistant App menu and select Settings
- Go to Companion App
- Select Manage Sensors
- Find the Next Alarm sensor
- Enable the Next Alarm sensor
- Create automation: „Einstellungen“->“Automatisierung & Szenen“->“Automatisierung erstellen““Neue Automatisierung“
  - Auslöser hinzufügen: “Andere Auslöser“-->“Template“
  - Template code:
    ´´´
    {{(now()+timedelta(0,60)).strftime('%a %h %d %H:%M %Z %Y') == (((state_attr('sensor.pixel_9_pro_next_alarm', 'Time in Milliseconds') | int / 1000) ) | timestamp_custom('%a %h %d %H:%M %Z %Y'))}}
    ´´´
  - add action:
![image](https://github.com/user-attachments/assets/566ee146-ef02-4c4b-a345-3907a6c4f3d8)

## setup alarm (iOs) ##
The focus sensor can be used to determine when the alarm went off.
- Create iOS shortcut named "HAss focus": deactivate focus
- Create iOS automation that executes the "Hass focus" everytime an alarm goes off
Now the companion app focus sensor of the iOS device can be used to trigger automations in Home-Assistant
- Create Home-Assistant automation:
![image](https://github.com/user-attachments/assets/f4baeaf1-41d1-4444-a85e-a35bb300ae05)
![image](https://github.com/user-attachments/assets/251a9fb4-3a34-449d-9c30-0792378ff227)
![image](https://github.com/user-attachments/assets/eac863b2-9854-4228-8236-fb4d34a07f53)
![image](https://github.com/user-attachments/assets/31d42838-ae8a-4857-8097-fc2410e5e0dc)

### Disassemble coffee machine ###
The coffee machine's display can be disassembled using a plastic tool.
![image](https://github.com/user-attachments/assets/7165692b-b229-4711-93ef-43abf203967e)
The wiring between display and mainboard is as follows:
![image](https://github.com/user-attachments/assets/979c58ba-b3b3-43a2-ae99-369fd36aa86d)
Communication is run via UART @115200
The state of the coffeemachine ist sent from the mainboard to the display. The button events are sent from the display to the mainboard.
## Mainboard -> Display
![image](https://github.com/user-attachments/assets/1ac3123b-a995-4a80-84e9-cca3d36cf012)
## Display -> Mainboard
![image](https://github.com/user-attachments/assets/b3d6cad4-577e-4da2-b39c-02a41aa92d71)
# On / Off #
On / Off Beep: d5 55 0a 00 00 03 02 00 00 00 32 25
Power on without cleaning cycle: d5 55 01 00 00 03 02 00 00 00 19 10	
Power Off no Cleaning cycle?: d5550000000302010000210c
# Drink Selection: # 
Select Nothing: 		d5 55 00 00 00 03 02 00 00 00 2d 01
Select Espresso:	d5 55 00 00 00 03 02 02 00 00 35 1a 	Nachricht wird 13x gesendet
perl -e 'print pack "H*", "d5550000000302020000351a"' > /dev/ttyUSB2

Hot Water:		d5 55 00 00 00 03 02 04 00 00 1d 36
Select Coffee:		d5 55 00 00 00 03 02 08 00 00 05 2b	Nachricht wird 8x gesendet
Steam:			d5 55 00 00 00 03 02 10 00 00 35 11	Nachricht wird 32x gesendet

# Settings: #
d5 55 00 00 00 03 02 00 02 00 35 18	Bean Size
d5 55 00 00 00 03 02 00 04 00 1c 32	Coffee Size
Play:
d5 55 00 00 00 03 02 00 00 01 25 05 	Play-Button (espresso, 39x)
perl -e 'print pack "H*", "d55500000003020000012505"' > /dev/ttyUSB2

For both mainboard messages and display messages the CRC algorithm is currently unknown. So it might be necessary to record the messages individually.

### Connect relais, UART and power ###


![image](https://github.com/user-attachments/assets/6edd467b-ddb7-4753-a80a-c2255f193521)
![image](https://github.com/user-attachments/assets/7c53dc47-85c7-4b10-af37-67e7f8e76245)


![image](https://github.com/user-attachments/assets/dc2dd292-99fb-4197-b349-5e12bf7a544b)
![image](https://github.com/user-attachments/assets/8e20e739-89e3-49aa-bd87-213486f3c857)
![image](https://github.com/user-attachments/assets/353445e3-020b-46de-9627-82c6d6ceafdc)
