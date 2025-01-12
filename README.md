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

### Set up home assistant ###
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
# Mauszeiger Ausblenden
@unclutter
# Bildschirmschoner ausschalten
@xset s off
@xset -dpms
@xset s noblank
# Startet Chromium im Vollbild und öffnet Home Assistant
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




![image](https://github.com/user-attachments/assets/6edd467b-ddb7-4753-a80a-c2255f193521)
![image](https://github.com/user-attachments/assets/7c53dc47-85c7-4b10-af37-67e7f8e76245)


![image](https://github.com/user-attachments/assets/dc2dd292-99fb-4197-b349-5e12bf7a544b)
![image](https://github.com/user-attachments/assets/8e20e739-89e3-49aa-bd87-213486f3c857)
![image](https://github.com/user-attachments/assets/353445e3-020b-46de-9627-82c6d6ceafdc)
