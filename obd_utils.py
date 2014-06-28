import serial
import platform

def scanSerial():
    """scan for available ports. return a list of serial names"""
    available = []
 # Enable Bluetooh connection
    for i in range(10):
      try:
		s = serial.Serial("/dev/rfcomm"+str(i))
		available.append( (str(s.port)))
		s.close()   # explicit close 'cause of delayed GC in java
      except serial.SerialException:
		pass
 # Enable USB connection
    for i in range(256):
      try:
        s = serial.Serial("/dev/ttyUSB"+str(i))
        available.append(s.portstr)
        s.close()   # explicit close 'cause of delayed GC in java
      except serial.SerialException:
        pass
 # Enable obdsim 
    #for i in range(256):
      #try: #scan Simulator
        #s = serial.Serial("/dev/pts/"+str(i))
        #available.append(s.portstr)
        #s.close()   # explicit close 'cause of delayed GC in java
      #except serial.SerialException:
        #pass
    
    return available