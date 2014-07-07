#!/usr/bin/env python
###########################################################################
# obd_gui.py
#
# Created by Paul Bartek (pbartek@cowfishstudios.com)
#
###########################################################################
#-------------------------------------------------------------------------------

import os
import wx
import time
from threading import Thread

from obd_capture import OBD_Capture
from obd_sensors import SENSORS
from obd_sensors import *

#-------------------------------------------------------------------------------

# OBD variables
BACKGROUND_FILENAME = "bg_black.jpg"
LOGO_FILENAME 		= "cowfish.png"

#-------------------------------------------------------------------------------

def obd_connect(o):
    o.connect()

class OBDConnection(object):
    """
    Class for OBD connection. Use a thread for connection.
    """
    
    def __init__(self):
        self.c = OBD_Capture()

    def get_capture(self):
        return self.c

    def connect(self):
        self.t = Thread(target=obd_connect, args=(self.c,))
        self.t.start()

    def is_connected(self):
        return self.c.is_connected()

    def get_output(self):
        if self.c and self.c.is_connected():
            return self.c.capture_data()
        return ""

    def get_port(self):
        return self.c.is_connected()

    def get_port_name(self):
        if self.c:
            port = self.c.is_connected()
            if port:
                try:
                    return port.port.name
                except:
                    pass
        return None
    
    def get_sensors(self):
        sensors = []
        if self.c:
            sensors = self.c.getSupportedSensorList()
        return sensors

#-------------------------------------------------------------------------------

class OBDText(wx.TextCtrl):
    """
    Text display while loading OBD application.
    """

    def __init__(self, parent):
        """
        Constructor.
        """
        style = wx.TE_READONLY | wx.TE_MULTILINE
        wx.TextCtrl.__init__(self, parent, style=style)

        self.SetBackgroundColour('#21211f')
        self.SetForegroundColour(wx.WHITE)  

        font = wx.Font(12, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
        self.SetFont(font)

    def AddText(self, text):
        self.AppendText(text)

#-------------------------------------------------------------------------------

class OBDStaticBox(wx.StaticBox):
    """
    OBD StaticBox.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        wx.StaticBox.__init__(self, *args, **kwargs)

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc): 
        dc.DrawBitmap(self.bitmap, 0, 0)     

#-------------------------------------------------------------------------------

class OBDPanelGauges(wx.Panel):
    """
    Panel for gauges.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(OBDPanelGauges, self).__init__(*args, **kwargs)

        # Background image
        image = wx.Image(BACKGROUND_FILENAME) 
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        self.bitmap = wx.BitmapFromImage(image) 
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # Create an accelerator table
        lid = wx.NewId()
        cid = wx.NewId()
        rid = wx.NewId()
        self.Bind(wx.EVT_MENU, self.onCtrlC, id=cid)
        self.Bind(wx.EVT_MENU, self.onLeft, id=lid)
        self.Bind(wx.EVT_MENU, self.onRight, id=rid)
        self.accel_tbl = wx.AcceleratorTable([ 
                (wx.ACCEL_CTRL, ord('C'), cid), 
                (wx.ACCEL_NORMAL, wx.WXK_LEFT, lid), 
                (wx.ACCEL_NORMAL, wx.WXK_RIGHT, rid), 
                ])
        self.SetAcceleratorTable(self.accel_tbl)

        # Handle events for mouse clicks
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeft)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRight)
        
        # Connection
        self.connection = None

        # Sensors 
        self.istart = 0
        self.sensors = []
        
        # Port 
        self.port = None

        # List to hold children widgets
        self.boxes = []
        self.texts = []


    def setConnection(self, connection):
        self.connection = connection
    
    def setSensors(self, sensors):
        self.sensors = sensors
        
    def setPort(self, port):
        self.port = port

    def getSensorsToDisplay(self, istart):
        """
        Get at most 6 sensors to be display on screen.
        """
        sensors_display = []
        if istart<len(self.sensors):
            iend = istart + 6
            sensors_display = self.sensors[istart:iend]
        return sensors_display

    def ShowSensors(self):
        """
        Display the sensors.
        """
        
        sensors = self.getSensorsToDisplay(self.istart)

        # Destroy previous widgets
        for b in self.boxes: b.Destroy()
        for t in self.texts: t.Destroy()
        self.boxes = []
        self.texts = []

        # Main sizer
        boxSizerMain = wx.BoxSizer(wx.VERTICAL)

        # Grid sizer
        nrows, ncols = 2, 3
        vgap, hgap = 50, 50
        gridSizer = wx.GridSizer(nrows, ncols, vgap, hgap)

        # Create a box for each sensor
        for index, sensor in sensors:
            
            (name, value, unit) = self.port.sensor(index)

            box = OBDStaticBox(self, wx.ID_ANY)
            self.boxes.append(box)
            boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)

            # Text for sensor value 
            if type(value)==float:  
                value = str("%.2f"%round(value, 3))                    
            t1 = wx.StaticText(parent=self, label=str(value), style=wx.ALIGN_CENTER)
            t1.SetForegroundColour('WHITE')
            font1 = wx.Font(32, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
            t1.SetFont(font1)
            boxSizer.Add(t1, 0, wx.ALIGN_CENTER | wx.ALL, 20)
            boxSizer.AddStretchSpacer()
            self.texts.append(t1)

            # Text for sensor name
            t2 = wx.StaticText(parent=self, label=unit+"\n"+name, style=wx.ALIGN_CENTER)
            t2.SetForegroundColour('WHITE')
            font2 = wx.Font(13, wx.ROMAN, wx.NORMAL, wx.BOLD, faceName="Monaco")
            t2.SetFont(font2)
            boxSizer.Add(t2, 0, wx.ALIGN_CENTER | wx.ALL, 5)
            self.texts.append(t2)
            gridSizer.Add(boxSizer, 1, wx.EXPAND | wx.ALL)

        # Add invisible boxes if necessary
        nsensors = len(sensors)
        for i in range(6-nsensors):
            box = OBDStaticBox(self)
            boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            self.boxes.append(box)
            box.Show(False)
            gridSizer.Add(boxSizer, 1, wx.EXPAND | wx.ALL)
           
        # Layout
        boxSizerMain.Add(gridSizer, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(boxSizerMain)
        self.Refresh()
        self.Layout() 

        # Timer for update
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
        self.timer.Start(2000)


    def refresh(self, event):
        sensors = self.getSensorsToDisplay(self.istart)   
        
        itext = 0
        for index, sensor in sensors:

            (name, value, unit) = self.port.sensor(index)
            if type(value)==float:  
                value = str("%.2f"%round(value, 3))                    

            if itext<len(self.texts):
                self.texts[itext*2].SetLabel(str(value))
            
            itext += 1


    def onCtrlC(self, event):
        self.GetParent().Close()

    def onLeft(self, event):
        """
        Get data from 6 previous sensors in the list.
        """
        istart = self.istart-6 
        if istart<0: istart = 0
        self.istart = istart
        self.ShowSensors()

    def onRight(self, event):
        """
        Get data from 6 next sensors in the list.
        """
        istart = self.istart+6
        if istart<len(self.sensors):
            self.istart = istart
            self.ShowSensors()

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc): 
        dc.DrawBitmap(self.bitmap, 0, 0)     

#-------------------------------------------------------------------------------

class OBDLoadingPanel(wx.Panel):
    """
    Main panel for OBD application. 

    Show loading screen. Handle event from mouse/keyboard.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(OBDLoadingPanel, self).__init__(*args, **kwargs)

        # Background image
        image = wx.Image(BACKGROUND_FILENAME) 
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        self.bitmap = wx.BitmapFromImage(image) 
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # Logo
        bitmap = wx.Bitmap(LOGO_FILENAME)
        width, height = bitmap.GetSize()
        image = wx.ImageFromBitmap(bitmap)
        image = image.Scale(width/6, height/6, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.BitmapFromImage(image)
        control = wx.StaticBitmap(self, wx.ID_ANY, bitmap)
        control.SetPosition((10, 10)) 

        # Create an accelerator table
        cid = wx.NewId()
        self.Bind(wx.EVT_MENU, self.onCtrlC, id=cid)
        self.accel_tbl = wx.AcceleratorTable([ 
                (wx.ACCEL_CTRL, ord('C'), cid), 
                ])
        self.SetAcceleratorTable(self.accel_tbl)

        # Connection
        self.c = None

        # Sensors list
        self.sensors = []

        # Port
        self.port = None

    def getConnection(self):
        return self.c

    def showLoadingScreen(self):
        """
        Display the loading screen.
        """
        boxSizer = wx.BoxSizer(wx.VERTICAL)
        self.textCtrl = OBDText(self)
        boxSizer.Add(self.textCtrl, 1, wx.EXPAND | wx.ALL, 92)
        self.SetSizer(boxSizer)
        font3 = wx.Font(16, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
        self.textCtrl.SetFont(font3)
        self.textCtrl.AddText(" Opening interface (serial port)\n")     
        self.textCtrl.AddText(" Trying to connect...\n")
        
        self.timer0 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.connect, self.timer0)
        self.timer0.Start(1000)


    def connect(self, event):
        if self.timer0:
            self.timer0.Stop()

        # Connection
        self.c = OBDConnection()
        self.c.connect()
        connected = False
        while not connected:
            connected = self.c.is_connected()
            self.textCtrl.Clear()
            self.textCtrl.AddText(" Trying to connect ..." + time.asctime())
            if connected: 
                break

        if not connected:
            self.textCtrl.AddText(" Not connected\n")
            return False
        else:
            self.textCtrl.Clear()
            #self.textCtrl.AddText(" Connected\n")
            port_name = self.c.get_port_name()
            if port_name:
                self.textCtrl.AddText(" Failed Connection: " + port_name +"\n")
                self.textCtrl.AddText(" Please hold alt & esc to view terminal.")
            self.textCtrl.AddText(str(self.c.get_output()))
            self.sensors = self.c.get_sensors()
            self.port = self.c.get_port()

            self.GetParent().update(None)


    def getSensors(self):
        return self.sensors
    
    def getPort(self):
        return self.port

    def onCtrlC(self, event):
        self.GetParent().Close()

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc): 
        dc.DrawBitmap(self.bitmap, 0, 0)     
        
#-------------------------------------------------------------------------------

class OBDFrame(wx.Frame):
    """
    OBD frame.
    """

    def __init__(self):
        """
        Constructor.
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, "OBD-Pi")

        image = wx.Image(BACKGROUND_FILENAME) 
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        self.bitmap = wx.BitmapFromImage(image) 
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.panelLoading = OBDLoadingPanel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelLoading, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.panelLoading.showLoadingScreen()
        self.panelLoading.SetFocus()

        
    def update(self, event):
        if self.panelLoading:
            connection = self.panelLoading.getConnection()
            sensors = self.panelLoading.getSensors()
            port = self.panelLoading.getPort()
            self.panelLoading.Destroy()
        self.panelGauges = OBDPanelGauges(self)
        
        if connection:
            self.panelGauges.setConnection(connection)

        if sensors:
            self.panelGauges.setSensors(sensors)
            self.panelGauges.setPort(port)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelGauges, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.panelGauges.ShowSensors()
        self.panelGauges.SetFocus()
        self.Layout()

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc): 
        dc.DrawBitmap(self.bitmap, 0, 0)     
        
#-------------------------------------------------------------------------------

class OBDFrame0(wx.Frame):
    """
    OBD starting frame. Used only for full screen purpose at startup.
    """

    def __init__(self):
        """
        Constructor.
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, "")

        image = wx.Image(BACKGROUND_FILENAME) 
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        self.bitmap = wx.BitmapFromImage(image) 
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc): 
        dc.DrawBitmap(self.bitmap, 0, 0)     

#-------------------------------------------------------------------------------

class OBDSplashScreen(wx.SplashScreen):
    """
    Splash screen.
    """

    def __init__(self, parent=None, frame0=None):
        """
        Constructor.
        """
        self.frame0 = frame0

        image = wx.Image(SPLASHSCREEN_FILENAME)
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.BitmapFromImage(image) 
        
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = SPLASHSCREEN_TIMEOUT
        wx.SplashScreen.__init__(self, bitmap, splashStyle, splashDuration, parent)

        self.Bind(wx.EVT_CLOSE, self.OnExit)
        wx.Yield()

    def OnExit(self, evt):
        """
        Exit splash screen and pass over other to main OBD frame.
        """
        
        # Main frame                                           
        frame = OBDFrame()
        app.SetTopWindow(frame)
        frame.ShowFullScreen(True)
        frame.Show(True)

        # Delete frame0
        if self.frame0:
            self.frame0.Destroy()
            del self.frame0 
        
        evt.Skip()          

#-------------------------------------------------------------------------------

class OBDApp(wx.App):
    """
    OBD Application.
    """

    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True):
        """
        Constructor.
        """
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)

    def OnInit(self):
        """
        Initializer.
        """
        # Main frame                                           
        frame = OBDFrame()
        self.SetTopWindow(frame)
        frame.ShowFullScreen(True)
        frame.Show(True)
        #frame.showLoadingPanel()

        # This frame is used only to set the full screen mode  
        # for the splash screen display and for transition with 
        # the loading screen.
        # This frame is not shown and will be deleted later on.
        #frame0 = OBDFrame0()
        #self.SetTopWindow(frame0)
        #frame0.ShowFullScreen(True)
        #self.SetTopWindow(frame0)

        # Splash screen
        #splash = OBDSplashScreen(frame0, frame0)
        #self.SetTopWindow(splash)
        #splash.Show(True)
        #splash.ShowFullScreen(True)

        return True

    def FilterEvent(self, event):
        if event.GetEventType == wx.KeyEvent:
            pass

#-------------------------------------------------------------------------------

app = OBDApp(False)
app.MainLoop()

#-------------------------------------------------------------------------------

