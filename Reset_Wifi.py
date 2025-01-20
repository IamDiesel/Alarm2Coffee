import os
import time
from threading import Thread

class Wifi_Deamon(Thread):
    def __init__(self, gateway_ip):
        self.gateway_ip = gateway_ip
        self._running = False
        super(Wifi_Deamon, self).__init__()
        #disable wlan powermanagment
        self.interface = self.get_interface()
        self.shell_command(f"sudo iwconfig {self.interface} power off")
        
    def run(self):
        self._running = True
        while(self._running):
            
            if(self.is_gateway_reachable() == False):
                self.reset_WLAN()
                print("resetting WLAN")
            else:
                print("Connection OK")
            time.sleep(10)
            
    def is_gateway_reachable(self):
        try:
            reachable = False
            res = self.shell_command(f"ping {self.gateway_ip} -c 1 | grep 'received' | awk -F',' " +"'{ print $2}' | awk '{ print $1}'")
            print(res)

            if(int(res) == 1):
                reachable = True
        except Exception:
            pass
        return reachable
    
    def shell_command(self,input):
        return os.popen(input).read()

    def get_interface(self):
        interface = None
        res = self.shell_command("iwgetid")
        if("ESSID" in res):
            interface = res.split("     ")[0]
        return interface

    def get_SSID(self):
        interface = None
        res = self.shell_command("iwgetid")
        if("ESSID" in res):
            interface = res.split('"')[1]
        return interface

    def ip_link_up(self):
        print(self.shell_command(f"sudo ip link set {self.interface} up"))
        
    def ip_link_down(self):
        print(self.shell_command(f"sudo ip link set {self.interface} down"))

    def reset_WLAN(self):
        self.ip_link_down()
        time.sleep(15)
        self.ip_link_up()
    
if __name__ == '__main__':
    wlan_ref = Wifi_Deamon("192.168.2.1")
    wlan_thread = Thread(target = wlan_ref.run)
    wlan_thread.start()
    wlan_thread.join()


