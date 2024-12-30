import subprocess, sys

def getSerialDeviceBySerialnumer(serialnumber):
    device = None
    for i in range(2):
        tmpDevice = f'/dev/ttyUSB{i}'
        command = f'/bin/udevadm info --name={tmpDevice} | grep ID_USB_SERIAL_SHORT'
        try:
            result = subprocess.check_output(command, shell = True, executable = "/bin/bash", stderr = subprocess.STDOUT)
            if(result.splitlines()[0].decode().split('=')[1] == serialnumber):
                #print(f"Found Device with S/N [{serialnumber}]: {tmpDevice}")
                device = tmpDevice
        except subprocess.CalledProcessError as cpe:
            result = cpe.output            
        return device
   
if __name__ == "__main__":
    serialNumberMainboard = "0001"
    serialNumberDisplay = "TGLBK1NM"
    getSerialDeviceBySerialnumer("TGLBK1NM")
