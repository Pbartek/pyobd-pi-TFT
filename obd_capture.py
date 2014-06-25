#!/usr/bin/env python

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time

from obd_utils import scanSerial

class OBD_Capture():
    def __init__(self):
        self.supportedSensorList = []
        self.port = None
        localtime = time.localtime(time.time())

    def connect(self):
        portnames = scanSerial()
        print portnames
        for port in portnames:
            self.port = obd_io.OBDPort(port, None, 2, 2)
            if(self.port.State == 0):
                self.port.close()
                self.port = None
            else:
                break

        if(self.port):
            print "Connected to "+self.port.port.name
            
    def is_connected(self):
        return self.port
        
    def getSupportedSensorList(self):
        return self.supportedSensorList 

    def capture_data(self):

        text = ""
        #Find supported sensors - by getting PIDs from OBD
        # its a string of binary 01010101010101 
        # 1 means the sensor is supported
        self.supp = self.port.sensor(0)[1]
        self.supportedSensorList = []
        self.unsupportedSensorList = []

        # loop through PIDs binary
        for i in range(0, len(self.supp)):
            if self.supp[i] == "1":
                # store index of sensor and sensor object
                self.supportedSensorList.append([i+1, obd_sensors.SENSORS[i+1]])
            else:
                self.unsupportedSensorList.append([i+1, obd_sensors.SENSORS[i+1]])
        
        for supportedSensor in self.supportedSensorList:
            text += "supported sensor index = " + str(supportedSensor[0]) + " " + str(supportedSensor[1].shortname) + "\n"
        
        time.sleep(3)
        
        if(self.port is None):
            return None

        #Loop until Ctrl C is pressed        
        localtime = datetime.now()
        current_time = str(localtime.hour)+":"+str(localtime.minute)+":"+str(localtime.second)+"."+str(localtime.microsecond)
        #log_string = current_time + "\n"
        text = current_time + "\n"
        results = {}
        for supportedSensor in self.supportedSensorList:
            sensorIndex = supportedSensor[0]
            (name, value, unit) = self.port.sensor(sensorIndex)
            text += name + " = " + str(value) + " " + str(unit) + "\n"

        return text

if __name__ == "__main__":

    o = OBD_Capture()
    o.connect()
    time.sleep(3)
    if not o.is_connected():
        print "Not connected"
    else:
        o.capture_data()
