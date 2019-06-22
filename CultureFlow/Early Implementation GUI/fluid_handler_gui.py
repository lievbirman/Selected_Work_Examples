"""
Fluidic Handling Software
Ashutosh Agarwal Lab
University of Miami

by:
Liev Birman
Adiel Hernandez

Microfluidic Control Software and GUI for controlling:
ISMATEC REGLO Peristaltic Pump
Titan EX Manifold Switch
NResearch Two-Switch
Arduino based Collection System

System allows user to control system manually on a component by component
as well as by creating an automated recipe. System has been tested in a live
cell experiment, in an incubator, for a 48 hour experimental protocol
"""

import tkinter as tk
from tkinter import font
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from decimal import Decimal
import numpy as np
import time
import pandas as pd

import serial
from serial.tools.list_ports import comports

#Device classes
from Pump import ThreePump
from Mswitch import MSwitch
from Collection import Collectador
from TwoSwitch import TwoSwitch

LARGE_FONT = ("Verdana", 10)

#we can inherit into our GUI application.
#Let's try it with the pump class and see how that works.
#if messagebox.askyesno("Collection Pattern Change", "You sure you want to change the collection pattern? (WARNING: Stage will reset!)"):

def combine_funcs(*funcs):
    """Use this function for executing multiple functions simultaneously with Tkinter buttons"""
    def combined_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)
    return combined_func
def message_prompt(message):
    """Creates a pop-up message of your choice"""
    p = tk.Toplevel()
    p.grab_set()
    p.configure(bg='#00fff2')

    p.buttonFont = font.Font(family='Verdana', size=12, weight='bold')
    p.pageFont = font.Font(family='Faktos', size=18, weight='bold')

    p.exitbutton_text = tk.StringVar()
    p.exitbutton_text = "OK"

    p.label = tk.Label(p,text = message,bg = '#00fff2',justify=tk.LEFT)
    p.exitbutton = tk.Button(p, text = p.exitbutton_text,font = p.buttonFont,command = combine_funcs(p.destroy,p.grab_release))

    p.label.grid(column = 1, row = 1, columnspan = 2,rowspan = 2)
    p.exitbutton.grid(column = 2, row = 6, columnspan = 1)

    return p
def check_input(variable, desired_datatype, lower_limit = 0, upper_limit = 0):

    inputGood = False
    datatypeGood = False
    limitsGood = False

    if isinstance(variable,int) or isinstance(variable,float) or isinstance(variable,str):

        if isinstance(variable,desired_datatype):
            datatypeGood = True

            if isinstance(variable,str):
                limitsGood = True

            else:
                if lower_limit == upper_limit:
                    limitsGood = True
                else:
                    if lower_limit <= variable <= upper_limit:
                        limitsGood = True
                    else:
                        #message_prompt(controller,"variable is not within required limits")
                        limitsGood = False
        else:
            #message_prompt(controller,"variable datatype does not match required datatype")
            datatypeGood = False
    else:
        #message_prompt("invalid input, desired_datatype can be str, int, or float")
        datatypeGood = False

    if datatypeGood and limitsGood:
        inputGood = True

    return inputGood
class App(tk.Tk):
    """
    The App class
    - Does window handling
    - Holds objects and variables that need to be referenced by multiple windows
    """
    def __init__(self,*args,**kwargs):
        """
        - define window size and expandability
        - define fonts
        - instantiates windows
        """

        tk.Tk.__init__(self,*args,**kwargs)
        self.geometry('500x750')
        self.resizable(width=True, height=True)

        self.appHighlightFont = font.Font(family='Arial', size=16, weight='bold')
        self.buttonFont = font.Font(family='Verdana', size=12, weight='bold')
        self.pageFont = font.Font(family='Faktos', size=18, weight='bold')

        self.ports = self.get_ports()

        self.max_flowrate_1 = None
        self.max_flowrate_2 = None
        self.max_flowrate_3 = None
        self.max_flowrate_list = [self.max_flowrate_1,self.max_flowrate_2,self.max_flowrate_3]

        self.default_diameter_index = 5

        self.well_working_volume = 300 #uL/well

        ##########################################
        ########## DEVICE HANDLING ###############
        ##########################################

        self.hasPump = tk.BooleanVar()
        self.hasMani = tk.BooleanVar()
        self.hasColl = tk.BooleanVar()

        self.portPump = tk.StringVar()
        self.portMani = tk.StringVar()
        self.portColl = tk.StringVar()
        self.port2Switch = tk.StringVar()

        self.myPump = None
        self.myMani = None
        self.myColl = None
        self.my2Switch = None

        self.should_be_running = False

        ###########################################
        ############# FRAME HANDLING ##############
        ###########################################


        container = tk.Frame(self)
        #container.geometry('500x500')
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0,weight = 1)
        container.grid_columnconfigure(0,weight = 1)

        #define dictionary of frames
        self.frames = {}

        #
        for F in (WelcomePage,ManualPage,AutomaticPage,SettingsPage):

            #instance of object takes in container as parent and self as controller
            frame = F(container, self)
            #adds the object to the dictionary
            self.frames[F] = frame
            frame.grid(row=0, column=0,sticky="nsew")

        self.show_frame(WelcomePage)
    def show_frame(self, cont):
        """
        Raises frame from self.frames dictionary
        """
        frame = self.frames[cont]
        frame.tkraise()
    def get_comport(self,cmd,response):
        """Use this function to automatically identify
        a device. Input a command the device recognizes and a response you know
        it should return. Make sure to use unique commands when spotting multiple devices.
        """
        #Uncomment later when using full functioning system.
        response = response[:2] #Put this just in case some extra stuff gets appended to the end of the repsonse
        if len(self.ports) == 0:
            return ""

        for comport in self.ports:
            #resp = ""
            try:
                ser = serial.Serial(comport, 9600, timeout=3)
                time.sleep(1)

                ser.write(cmd.encode('ascii') + '\r'.encode('ascii'))
                time.sleep(1)

                resp = ser.readline().decode()
                resp = resp[:2]

                print("We sent " + cmd + " to " + comport + " and recieved " + resp)
                print("We are looking for: " + response)

                if resp == response:
                    self.ports.remove(comport)
                    print("We assigned the port: " + comport)
                    ser.close()
                    return comport

                ser.close()

            except:
                print("Error accesing comports!")
    def get_ports(self):
        """
        fills self.ports list with comports currently connected to device
        """
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            ports.append(port)
        self.ports = ports
    def set_pump_defaults(self):
        """
        Sets defaults as defined within function
        """

        self.myPump.ser.readline()
        self.myPump.ser.flush()
        self.max_flowrate_1 = float(self.myPump.send_return('1?')[:5])

        self.myPump.ser.readline()
        self.myPump.ser.flush()
        self.max_flowrate_2 = float(self.myPump.send_return('2?')[:5])

        self.myPump.ser.readline()
        self.myPump.ser.flush()
        self.max_flowrate_3 = float(self.myPump.send_return('3?')[:5])

        self.max_flowrate_list = [self.max_flowrate_1,self.max_flowrate_2,self.max_flowrate_3]
    def done_and_load(self,reset_stage):
        """
        This function checks if we have these devices and then creates instances for each one. Open ManualPage when done.
        When we've finished specifying our devices in the WelcomePage window we run this by clicking done.
        """

        if self.hasPump.get():
            self.myPump = ThreePump(self.portPump.get())
            self.set_pump_defaults()

        if self.hasMani.get():
            self.myMani = MSwitch(self.portMani.get()) #= #self.portMani.get()

        if self.hasColl.get():
            self.myColl = Collectador(self.portColl.get()) #= #self.portColl.get()
            self.my2Switch = TwoSwitch(self.portColl.get())
            self.my2Switch.ser = self.myColl.ser
            self.my2Switch.setCollect(1)
            self.my2Switch.setCollect(2)
            self.my2Switch.setCollect(3)

        if reset_stage == True:
            self.myColl.reset()

        self.show_frame(ManualPage)
    def positive_run_status(self):
        """
        sets self.should_be_running to True.
        """
        self.should_be_running = True
    def negative_run_status(self):
        """
        sets self.should_be_running to Fasle.
        """
        self.should_be_running = False
    def message_window(self,message):
        """Creates a pop-up message of your choice formatted with
        formatting from App class"""

        window = tk.Toplevel()
        window.grab_set()
        window.configure(bg='#00fff2')
        #exitbutton = tk.Button(window,text = "Exit",font = controller.buttonFont,command = combine_funcs(window.destroy,window.grab_release))
        abortbutton = tk.Button(window,text = "OK",bg = "#ff6464",font = self.buttonFont,width = 5, command = combine_funcs(window.destroy,window.grab_release))
        label = tk.Label(window,text = message, bg = '#00fff2')
        label.grid(column = 1, row = 1, columnspan = 1,sticky=tk.W)
        abortbutton.grid(column = 1, row = 2)
class WelcomePage(tk.Frame):
    #Port and device selection
    #Running function instantiating devices via their respective classes
    def __init__(self, parent, controller):

        tk.Frame.__init__(self,parent)
        #Organization and label frames for the buttons and labels

        self.mainlabel = tk.Label(self, text = "Welcome to FLUIPLEX!", font = LARGE_FONT)
        self.sublabelframe = tk.LabelFrame(self, text = "Please identify your devices:", font = LARGE_FONT)
        self.perfusorframe = tk.LabelFrame(self.sublabelframe, text = "PERFUSATRON", font = LARGE_FONT)
        self.collectorframe = tk.LabelFrame(self.sublabelframe, text = "COLLECTADOR", font = LARGE_FONT)
        ####################Port & Device Selection############################

        #finding all of the ports
        self.manilabel = tk.Label(self.perfusorframe,text='M-Switch: Not Found')
        self.pumplabel= tk.Label(self.perfusorframe,text='ISMATEC Pump: Not Found')
        self.coll_label = tk.Label(self.perfusorframe,text='XYStage/TwoSwitch Not Found')

        ##++##++##++##++
        ## CHECKPOINT 1
        ##++##++##++##++

        controller.get_ports()

        #print("M-Switch",controller.get_comport("R","65"))
        controller.portMani.set(controller.get_comport("R","65"))
        print("MSwitch has the following port: " + controller.portMani.get())

        #print("Pump",controller.get_comport("0xS","IS"))
        controller.portPump.set(controller.get_comport("0xS","IS"))
        print("Pump has the following port: " + controller.portPump.get())

        #print("XYStage/TwoSwitch",controller.get_comport("?","2xCS"))
        controller.portColl.set(controller.get_comport("?","2xCS"))
        controller.port2Switch.set(controller.portColl.get())
        print(controller.portColl.get())

        ##++##++##++##++
        ## END CHECKPOINT 1
        ##++##++##++##++

        #---------------------------------------

        ##**##**##**##**##**##**##**##**
        #TESTING OPTIONS---Comment all lines of CHECKPOINT 1
        #import fakeSerial as serial in header
        ##**##**##**##**##**##**##**##**

        # controller.portMani.set("COM_MANI")
        # print("MSwitch has the following port: " + controller.portMani.get())
        #
        # #print("Pump",controller.get_comport("0xS","IS"))
        # controller.portPump.set("COM_PUMP")
        # print("Pump has the following port: " + controller.portPump.get())
        #
        # #print("XYStage/TwoSwitch",controller.get_comport("?","2xCS"))
        # controller.portColl.set("COM_COLL")
        # controller.port2Switch.set(controller.portColl.get())
        # print("Collection has the following port: " + controller.portColl.get())
        #
        #
        # controller.hasColl.set(True)
        # controller.hasPump.set(True)
        # controller.hasMani.set(True)

        ##**##**##**##**##**##**##**##**
        #END OF TESTING OPTIONS
        ##**##**##**##**##**##**##**##**

        #port selection and checkbox functionality for the m-switch
        if controller.portMani.get() is not None and controller.portMani.get() is not "":
            controller.hasMani.set(True)
            self.manilabel['text'] = 'M-Switch: Connected'

        #port selection and checkbox functionality for the pump
        if controller.portPump.get() is not None and controller.portPump.get() is not "":
            controller.hasPump.set(True)
            self.pumplabel['text'] = 'ISMATEC Pump: Connected'

        #port selection and checkbox functionality for the XYStage/TwoSwitch
        if controller.portColl.get() is not None and controller.portColl.get() is not "":
            controller.hasColl.set(True)
            self.coll_label['text'] = 'XYStage/TwoSwitch: Connected'

        #the done button takes in all of the inputs and passes them to the controller for use in the next windows
        self.donebutton = tk.Button(self, text = "Start w/o reset",font = controller.buttonFont, command= lambda: controller.done_and_load(False))
        self.donesetbutton = tk.Button(self, text = "Start",font = controller.buttonFont, command=lambda: controller.done_and_load(True))
        #geometry
        self.mainlabel.pack(fill = tk.BOTH)
        self.sublabelframe.pack()
        self.perfusorframe.pack(side = tk.LEFT,fill=tk.BOTH)
        self.collectorframe.pack(side = tk.RIGHT,fill=tk.BOTH)
        #self.maniportselect.pack()
        self.manilabel.pack(fill=tk.BOTH)
        #self.pumpportselect.pack()
        self.pumplabel.pack(fill=tk.BOTH)
        #self.collportselect.pack()
        self.coll_label.pack(fill=tk.BOTH)
        #self.collcheck.pack(fill=tk.BOTH)
        self.donesetbutton.pack()
        self.donebutton.pack()
    def flip(self,widget):
        """
        Enables or disables a widget. It is run by the checkbuttons on the WelcomPage
        """
        myState = str(widget['state'])
        if myState == 'normal':
            widget.config(state = tk.DISABLED)
        else:
            widget.config(state = tk.NORMAL)

class ManualPage(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self,parent)

        self.configure(bg='#00fff2')

        #Python variables of the Manual Page
        self.channels = 3
        self.reservoirs = 6

        #String variables of the Manual page
        self.samplingrate = tk.DoubleVar()
        self.sites = tk.IntVar()

        #Buttons of the Manual Page
        self.autopagebutton =  tk.Button(self, text = "Experiment",font = controller.buttonFont,bg = "white", command = lambda: controller.show_frame(AutomaticPage), height = 1, width = 10,pady = 3)
        self.settingsbutton =  tk.Button(self, text = "Settings",font = controller.buttonFont,bg = "white", command = lambda: controller.show_frame(SettingsPage), height = 1, width = 10,pady = 3)
        self.startallbutton = tk.Button(self, text = "START ALL",font = controller.buttonFont,bg = "#64ff64",command = lambda: self.set_and_start_all(controller), height = 1, width = 20)
        self.startandcollectbutton = tk.Button(self, text = "START ALL CHANNELS\n + COLLECTION",bg = "#64ff64",font = controller.buttonFont,command = lambda: self.start_and_collect(controller,self.samplingrate.get()), height = 2, width = 20)
        self.stopallbutton = tk.Button(self, text = "STOP ALL",font = controller.buttonFont,bg = "#ff6464",command = lambda: self.stop_all(controller), height = 1, width = 20 )
        self.nextwellbutton = tk.Button(self, text = "NEXT WELL",font = controller.buttonFont,bg = "white",command = lambda: self.next(controller), height = 1, width = 20 )
        self.lastwellbutton = tk.Button(self, text = "PREVIOUS WELL",font = controller.buttonFont,bg = "white",command = lambda: self.prev(controller) , height = 1, width = 20)
        self.resetbutton = tk.Button(self, text = "RESET STAGE",font = controller.buttonFont,bg = "white",command = lambda: self.reset(controller) , height = 1, width = 20)
        self.ejectbutton = tk.Button(self, text = "EJECT PLATE",font = controller.buttonFont,bg = "white",command = lambda: self.eject(controller) , height = 1, width = 20)
        self.togglebutton = tk.Button(self, text = "TOGGLE PATTERN",font = controller.buttonFont,bg = "white",command = lambda: self.toggle(controller) , height = 1, width = 20)
        self.setOriginButton = tk.Button(self, text = "SET ORIGIN/MANUAL CONTROL",font = controller.buttonFont,bg = "white",command = lambda: self.setOrigin(controller) , height = 1, width = 30)
        #self.calibratebutton = tk.Button(self, text = "Calibrate", command = lambda: controller.myPump.calibrate() )
        #self.entercalibratedbutton = tk.Button(self, text = "Enter", command = lambda: controller.myPump.setMeasuredVolume() )

        #Entrys of the Manual Page
        self.samplingrateentry = tk.Entry(self,textvariable = self.samplingrate, bg = "white", font =controller.appHighlightFont)
        self.sitesentry = tk.Entry(self,textvariable = self.sites, font =controller.appHighlightFont,bg = "white")
        #self.entervolumeentry = tk.Entry(self,textvariable = self.calibratedvolume)

        #Labels of the Manual Manual Page
        self.mainlabel = tk.Label(self, text = "Manual Control",bg='#00fff2', font =controller.pageFont,width = 15)
        self.autocollectlabel = tk.Label(self,text = "Sampling Time (s)", font =controller.appHighlightFont,bg='#00fff2')

        self.reservoirlabel = tk.Label(self,text = "Reservoir", font =controller.appHighlightFont,bg='#00fff2')
        self.sampleslabel = tk.Label(self,text = "Samples", font =controller.appHighlightFont,bg='#00fff2')

        self.CollectionControlLabel = tk.Label(self, text = "                        Collection Control",bg='#00fff2', font =controller.appHighlightFont)
        self.positionLabel = tk.Label(self, text = "Current Position: 1", bg = '#00fff2', font = controller.appHighlightFont)
        self.patternLabel = tk.Label(self, text = "Current Pattern: Snake", bg = '#00fff2', font = controller.appHighlightFont)

        #creating the number of channels that we specified
        self.create_channels(controller,self.channels,self.reservoirs)

        for i in range(self.reservoirs):
            self.reservoirvalues.append(str(i+1))

        self.reservoircombobox = tk.ttk.Combobox(self,width = 10)
        self.reservoircombobox['values'] = self.reservoirvalues
        self.reservoircombobox.set(self.reservoirvalues[0])
        self.reservoircombobox.state(['!disabled', 'readonly'])


        #row 1
        self.mainlabel.grid(column = 1, row = 1, columnspan = 2)
        self.autopagebutton.grid(column = 3, row = 1)
        self.settingsbutton.grid(column = 4, row = 1)

        #row 2
        self.greaterlabelframe.grid(column = 1, row = 2, columnspan = 4, padx=30, pady=20)

        #row 3
        self.reservoirlabel.grid(column = 1, row = 3,columnspan = 2,sticky=tk.W)
        self.reservoircombobox.grid(column = 3, row = 3,columnspan = 2,sticky=tk.W)

        #row 4
        self.startallbutton.grid(column = 1, row = 4,columnspan = 2,sticky=tk.W, pady=20)
        self.stopallbutton.grid(column = 3, row = 4,columnspan = 2,sticky=tk.W, pady=20)

        #row 5
        self.sampleslabel.grid(column = 1, row = 5,columnspan = 2,sticky=tk.W)
        self.sitesentry.grid(column = 3, row = 5,columnspan = 2,sticky=tk.W)

        #row 6
        self.autocollectlabel.grid(column = 1, row = 6,columnspan = 2,sticky=tk.W)
        self.samplingrateentry.grid(column = 3, row = 6,columnspan = 2,sticky=tk.W)

        #row 7
        self.startandcollectbutton.grid(column = 2, row = 7,columnspan = 2,sticky=tk.W, pady=10)

        #row 8
        self.CollectionControlLabel.grid(column = 1, row = 8,columnspan = 4,sticky=tk.W)

        #row 9
        self.nextwellbutton.grid(column = 3, row = 9,columnspan = 2,sticky=tk.W)
        self.lastwellbutton.grid(column = 1, row = 9,columnspan = 2,sticky=tk.W)

        #row 10
        self.resetbutton.grid(column = 1, row = 10,columnspan = 2,sticky=tk.W, pady=5)
        self.ejectbutton.grid(column = 3, row = 10,columnspan = 2,sticky=tk.W, pady=5)

        #row 11
        self.positionLabel.grid(column = 1, row = 11, columnspan = 2, sticky=tk.W, pady=5)
        self.togglebutton.grid(column = 2, row = 11, columnspan = 4, sticky = tk.W, pady =5)

        #row 12
        self.positionLabel.grid(column = 1, row = 12, columnspan = 2, sticky=tk.W, pady=5)
        self.patternLabel.grid(column = 3, row = 12, columnspan = 2, sticky = tk.W, pady=5)

        #row 13
        self.setOriginButton.grid(column = 2, row = 13, columnspan = 2, sticky = tk.W, pady=5)
    def create_channels(self,controller,channels,reservoirs):
        """creates each channel for manual page. properties of channels are stored in lists in self.
        channels and reservoirs variables refer to res and ch number
        """
        self.greaterlabelframe = tk.LabelFrame(self, bg = "#43e7ef")

        self.channeltextlist = []
        self.labelframelist = []
        self.flowrateentrylist = []
        self.startbuttonlist = []
        self.stopbuttonlist = []
        self.reservoirvalues = []
        self.toplabels = []
        self.twoSwitchComboBoxList = []

        self.twoSwitchValues = ["Collect","Recirculate"]

        for i in range(channels+1):
            if i == 0:
                pass

            else:
            #here we create an instance of each of the buttons and append that to an element of a list.
            #Our unique identifier becomes, for example, self.startbuttonlist[0] for channel 1 startbutton
                mainlabelframe = tk.LabelFrame(self.greaterlabelframe, bg = "#7fdee2")
                mainlabelframe.grid(column = 1, row = i)
                self.labelframelist.append(mainlabelframe)

                flowrateentry = tk.Entry(mainlabelframe,bg = "white",font = controller.appHighlightFont, width = 8)
                flowrateentry.insert(tk.END,"100")
                self.flowrateentrylist.append(flowrateentry)

                channeltext = tk.Label(mainlabelframe, text = "CH%s"%i, bg = "#57c1bc", font = controller.appHighlightFont)
                self.channeltextlist.append(channeltext)

                #note the usage of i=i. If you don't do this then python uses the last known instance of i in that place.
                startbutton = tk.Button(mainlabelframe, text = "START",font = controller.buttonFont,bg = "#64ff64", command = lambda i=i: self.set_and_start(controller,i), height = 1, width = 6)
                self.startbuttonlist.append(startbutton)

                stopbutton = tk.Button(mainlabelframe, text = "STOP",font = controller.buttonFont,bg = "#ff9696", command = lambda i=i: self.stop(controller,i), height = 1, width = 6)
                self.stopbuttonlist.append(stopbutton)

                # Creates the twoSwitchComboBox and adds these instances to a list in self.
                twoSwitchComboBox = tk.ttk.Combobox(mainlabelframe,width = 10)
                twoSwitchComboBox['values'] = self.twoSwitchValues
                twoSwitchComboBox.set(self.twoSwitchValues[0])
                twoSwitchComboBox.state(['!disabled', 'readonly'])
                self.twoSwitchComboBoxList.append(twoSwitchComboBox)

                channeltext.grid(column = 1, row = i)
                flowrateentry.grid(column = 2, row = i)
                twoSwitchComboBox.grid(column = 3, row = i)
                startbutton.grid(column = 4, row = i)
                stopbutton.grid(column = 5, row = i)
    def stop(self,controller,channel):
        """
        stops pump channel"""
        controller.myPump.stop(channel)        #print("STOPPING CH%s"%channel)
    def stop_all(self,controller):
        """
        stops pump channel"""
        controller.myPump.stop_all()
        print("STOPPING ALL")
    def set_and_start(self,controller,channel):
            """
            sends input direction, flowrate, and reservoir to pump
            starts specified pump channel
            """
            goodToGo = self.check_channel(controller,channel)

            print("Are we good to go?: %s"%goodToGo)

            if goodToGo:

                flowrate = self.flowrateentrylist[channel-1].get()
                #direction = self.directionentrylist[channel-1].get()
                reservoir = self.reservoircombobox.get()

                controller.myPump.setFlow(channel,flowrate)
                #controller.myPump.setDir(channel,direction)
                controller.myMani.set_reservoir(reservoir)

                controller.myPump.start(channel)

                #Send serial command from TwoSwitch depending on which channel is asking to be set to Collect or Recirculate.
                if self.twoSwitchComboBoxList[channel - 1].get() == self.twoSwitchValues[0]:
                    controller.my2Switch.setCollect(channel)
                elif self.twoSwitchComboBoxList[channel - 1].get() == self.twoSwitchValues[1]:
                    controller.my2Switch.setRecirculate(channel)
    def set_and_start_all(self,controller):
        """
        sets all of the channels and then starts pump
        """

        goodToGo = self.check_all_manual(controller)

        print("Are we good to go?: %s"%goodToGo)

        if goodToGo:

            for i in range(len(self.flowrateentrylist)):
                flowrate = self.flowrateentrylist[i].get()
                controller.myPump.setFlow(i+1,flowrate)
                #controller.myPump.setDir(i+1,direction)

            reservoir = self.reservoircombobox.get()
            controller.myMani.set_reservoir(reservoir)
            controller.myPump.start_all()

            #Set all the Two Switches to the desired setting.
            counter = 1
            for setting in self.twoSwitchComboBoxList:
                if setting.get() == self.twoSwitchValues[0]:
                    controller.my2Switch.setCollect(counter)
                    counter += 1
                elif setting.get() == self.twoSwitchValues[1]:
                    controller.my2Switch.setRecirculate(counter)
                    counter += 1
    def coll_flip(self):
        self.coll_go = False
    def start_and_collect(self,controller,sampling_rate):

        goodToGo = self.check_all_manual_and_sampling(controller)
        print("Are we good to go?: %s"%goodToGo)

        self.coll_go = True

        if goodToGo and int(self.sitesentry.get()) > 0:

            sw = tk.Toplevel(controller)
            sw.grab_set()

            exitbutton = tk.Button(sw,text = "Exit/Abort",font = controller.buttonFont,command = combine_funcs(
            self.coll_flip,
            sw.destroy,
            sw.grab_release,
            controller.myPump.stop_all)
            )

            sw.info = tk.StringVar()
            infolabel = tk.Label(sw, anchor='w')
            infolabel['textvariable'] = sw.info

            sw.status = tk.StringVar()
            sw.status.set("Running...")
            statuslabel = tk.Label(sw, anchor='w')
            statuslabel['textvariable'] = sw.status
            statuslabel.pack(fill='both')

            infolabel.pack(side = tk.LEFT,fill='both')
            exitbutton.pack()

            sw.start_well = controller.myColl.position
            #this always starts at 0 as this is wells used for this experiment
            sw.wells_used = 0

            sw.res = self.reservoircombobox.get()

            sw.start_time = time.time()
            sw.time0 = time.time()
            self.set_and_start_all(controller)

            while sw.wells_used < self.sites.get() and self.coll_go:

                if (time.time() - sw.time0)/sampling_rate > 1:
                    sw.time0 = time.time()
                    sw.wells_used += 1
                    self.next(controller)
                    #send next command to collectador

                sw.info.set("\n sites: %s - %s \n sites used: %s \n sites available: %s \n sampling rate: %s \n time elapsed: %s \n reservoir: %s \n CH1: %s uL/m   CH2: %s uL/m   CH3: %s uL/m"%(
                sw.start_well,sw.start_well+sw.wells_used,
                sw.wells_used,
                32-sw.wells_used-sw.start_well,
                sampling_rate,
                np.trunc(time.time() - sw.start_time),
                sw.res,
                self.flowrateentrylist[0].get(),
                self.flowrateentrylist[1].get(),
                self.flowrateentrylist[2].get()
                ))
                sw.update()

            controller.myPump.stop_all()
            sw.status.set("Done!")
            #carryOn = True
            #start_well = 5
            #wells_used = 0

            #infoframe = tk.Frame(sw)
            #infoframe.pack()

            #stop when user stops or when at last well.
            #use a label for the update?

        else:

            if int(self.sitesentry.get()) > 0:
                message_prompt(errors)
            else:
                message_prompt("Enter number of samples to take.")
    def next(self,controller):
        if controller.myColl.position < 31 and controller.myColl.position != 32:
            controller.myColl.next_site()
            self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
        else:
            message_prompt("Have reached the end of the wells or in eject position, can't move forward!")
    def prev(self,controller):
        if controller.myColl.position > 0 and controller.myColl.position != 32:
            controller.myColl.last_site()
            self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
        else:
            message_prompt("At the beginning of the wells or in eject position, can't move backward!")
    def reset(self,controller):
        controller.myColl.reset()
        self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
    def eject(self,controller):
        controller.myColl.eject()
        self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
    def toggle(self,controller):
        if messagebox.askyesno("Collection Pattern Change", "You sure you want to change the collection pattern? (WARNING: Stage will reset!)"):
            controller.myColl.reset()
            controller.message_window("Changing Collection Pattern! Stage will be reset!")
            controller.myColl.toggle_pattern()
            self.patternLabel['text'] = "Current Pattern: " + controller.myColl.currentPattern
            self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
    def setOrigin(self,controller):
        window = tk.Tk()
        window.title("Set Origin/Manual Control")
        upButton = tk.Button(window, text = "UP",font = controller.buttonFont,bg = "white",command = lambda: self.moveOneUp(controller), repeatdelay = 500, repeatinterval = 10, height = 5, width = 10)
        downButton = tk.Button(window, text = "DOWN",font = controller.buttonFont,bg = "white",command = lambda: self.moveOneDown(controller), repeatdelay = 500, repeatinterval = 10, height = 5, width = 10)
        rightButton = tk.Button(window, text = "RIGHT",font = controller.buttonFont,bg = "white",command = lambda: self.moveOneRight(controller), repeatdelay = 500, repeatinterval = 10, height = 5, width = 10)
        leftButton = tk.Button(window, text = "LEFT",font = controller.buttonFont,bg = "white",command = lambda: self.moveOneLeft(controller), repeatdelay = 500, repeatinterval = 10, height = 5, width = 10)
        doneButton = tk.Button(window, text = "DONE", font = controller.buttonFont, bg = "white", command = lambda: self.done(controller, window), height = 5, width = 10)

        #row 1
        upButton.grid(row = 1, column = 2, sticky = tk.W)

        #row 2
        leftButton.grid(row = 2, column = 1, sticky = tk.W)
        rightButton.grid(row = 2, column = 3, sticky = tk.W)

        #row 3
        downButton.grid(row = 3, column = 2, sticky = tk.W)

        #row 4
        doneButton.grid(row = 4, column = 2, sticky = tk.W, pady = 40)
    def moveOneUp(self, controller):
        controller.myColl.moveOneUp()
    def moveOneDown(self, controller):
        controller.myColl.moveOneDown()
    def moveOneRight(self, controller):
        controller.myColl.moveOneRight()
    def moveOneLeft(self, controller):
        controller.myColl.moveOneLeft()
    def done(self, controller, window):
        controller.myColl.setOrigin()
        self.positionLabel['text'] = "Current Position: " + str(controller.myColl.position + 1)
        window.destroy()
    def check_all_manual_and_sampling(self,controller):
        """
        use when running all channels together
        """
        goodToGo = all([self.check_channel(controller,i+1) for i in range(3)])

        try:
            float(self.samplingrateentry.get())

        except:
            controller.message_window("Sampling rate must be float!")
            goodToGo = False

        try:
            int(self.sitesentry.get())

        except:
            controller.message_window("Sample number must be integer!")
            goodToGo = False

        #self.sitesentry.set(int(self.sitesentry.get()))

        if goodToGo:
            for i in range(3):
                if float(self.samplingrateentry.get())*(1.0/60)*float(self.flowrateentrylist[i].get()) > controller.well_working_volume:
                    goodToGo = False
                    max_time = (controller.well_working_volume/float(self.flowrateentrylist[i].get()))*60
                    controller.message_window("Sampling time for channel %s needs to be under %s s"%(i+1,max_time))
                    break

        return goodToGo
    def check_all_manual(self,controller):
        """
        use when running all channels together
        """
        goodToGo = all([self.check_channel(controller,i+1) for i in range(3)])

        return goodToGo
    def check_channel(self,controller,channel):

        goodToGo = True

        try:
            float(self.flowrateentrylist[channel-1].get())

        except:
            controller.message_window("Entry must be float!")
            goodToGo = False

        #print("printing max flow" + str(controller.max_flowrate_list[channel-1]*1000))
        flowrateOK = (0 <= float(self.flowrateentrylist[channel-1].get()) <= controller.max_flowrate_list[channel-1]*1000)

        if not flowrateOK:
            goodToGo = False
            controller.message_window("Entry must be between %s and %s! uL/m"%(0,1000*controller.max_flowrate_list[channel-1]))

        return goodToGo
class AutomaticPage(tk.Frame):
    "Recipe creator page"
    def __init__(self, parent, controller):

        tk.Frame.__init__(self,parent)

        self.configure(bg='#00fff2')

        self.mainlabel = tk.Label(self, text = "Recipe Creator", bg='#00fff2', font=controller.pageFont,width = 15)

        self.channels = 3
        self.reservoirs = 6
        self.steplist = []
        self.stepnumbers = []
        self.numberlist = []

        self.number_deleted = 0

        self.todelete = tk.StringVar()
        self.deletestepcombo = tk.ttk.Combobox(self, textvariable = self.todelete,width = 10)

        self.newstep = tk.Button(self,text = "Add",font = controller.buttonFont,bg = "white",command = self.add_step, height = 1, width = 10)
        self.deletestep = tk.Button(self,text = "Delete",font = controller.buttonFont,bg = "white", command = lambda: self.delete_step(self.todelete), height = 1, width = 10)
        self.manualbutton = tk.Button(self, text = "Manual",font = controller.buttonFont,bg = "white", command = lambda: controller.show_frame(ManualPage), height = 1, width = 10,pady = 3)
        self.settingsbutton =  tk.Button(self, text = "Settings", font = controller.buttonFont,bg = "white",command = lambda: controller.show_frame(SettingsPage), height = 1, width = 10,pady = 3)
        self.savebutton = tk.Button(self, text = "Save",font = controller.buttonFont,bg = "white", command = lambda: self.file_save(), height = 1, width = 10)
        self.ejectbutton = tk.Button(self, text = "Eject",font = controller.buttonFont,bg = "white", command = lambda: controller.frames[ManualPage].eject(controller), height = 1, width = 10)
        self.loadbutton = tk.Button(self, text = "Load",font = controller.buttonFont,bg = "white", command = lambda: self.file_load(), height = 1, width = 10)
        self.runbutton = tk.Button(self, text = "Start", font = controller.buttonFont,bg = "#64ff64",command = lambda: self.run_recipe(controller), height = 1, width = 10)
        self.clearbutton = tk.Button(self, text = "Clear All", font = controller.buttonFont,bg = "white",command = lambda: self.clear_recipe(), height = 1, width = 10)

        heading_string = "       STEP       "
        for i in range(self.channels):
            heading_string += "CH%s          "%(i+1)
        heading_string +="Samples      s/Sample  Reservoir"


        #row 1:
        self.mainlabel.grid(column = 1, row = 1, columnspan=2)

        #row 2
        self.savebutton.grid(column = 1,row = 2)
        self.loadbutton.grid(column = 2,row = 2)
        self.clearbutton.grid(column = 3,row = 2)
        self.ejectbutton.grid(column = 4, row = 2)

        #row 3
        self.newstep.grid(column = 1,row = 4)
        self.deletestepcombo.grid(column = 2,row = 4)
        self.deletestep.grid(column = 3,row = 4)
        self.runbutton.grid(column = 4,row = 4)

        #row 4
        self.settingsbutton.grid(column = 4,row = 1)
        self.manualbutton.grid(column = 3,row = 1)

        #row 5
        self.headinglabel = tk.Label(self, text = heading_string, bg='#00fff2').grid(column = 1, row = 5, columnspan = 8)
    def file_save(self):

        f = filedialog.asksaveasfile(mode='w', defaultextension=".txt",  filetypes = (("text files","*.txt"),("all files","*.*")))
        text2save = ""

        text2save += \
        "FR1" + "," + \
        "FR2" + "," + \
        "FR3" + "," + \
        "2S1" + "," + \
        "2S2" + "," + \
        "2S3" + "," + \
        "RES" + "," + \
        "SRA" + "," + \
        "RTI" + "\n"

        for i in range(len(self.steplist)):
            text2save += '%i,'%i + \
            str(self.steplist[i].flowrateentrylist[0].get()) + "," + \
            str(self.steplist[i].flowrateentrylist[1].get()) + "," + \
            str(self.steplist[i].flowrateentrylist[2].get()) + "," + \
            str(self.steplist[i].twoSwitchComboBoxList[0].get()) + "," + \
            str(self.steplist[i].twoSwitchComboBoxList[1].get()) + "," + \
            str(self.steplist[i].twoSwitchComboBoxList[2].get()) + "," + \
            str(self.steplist[i].reservoircombobox.get()) + "," + \
            str(self.steplist[i].samplingrate.get()) + "," + \
            str(self.steplist[i].samples.get()) + "\n"

        f.write(text2save)
        f.close()
    def file_load(self):

        f = filedialog.askopenfilename(initialdir = "/",title = "Select file", filetypes = (("text files","*.txt"),("all files","*.*")))
        df = pd.read_csv(f)
        print(df)
        for i in range(len(self.steplist)):
            zeroth = tk.StringVar()
            zeroth.set("0")
            self.delete_step(zeroth)

        for i in range(len(df["FR1"])):

            self.add_step()


            fr1 = df["FR1"][i]
            fr2 = df["FR2"][i]
            fr3 = df["FR3"][i]
            ts1 = df["2S1"][i]
            ts2 = df["2S2"][i]
            ts3 = df["2S3"][i]
            res = df["RES"][i]
            sra = df["SRA"][i]
            rti = df["RTI"][i]

            print("TS2",ts2)


            self.steplist[i].flowrateentrylist[0].delete(0,'end')
            self.steplist[i].flowrateentrylist[0].insert(0,fr1)
            self.steplist[i].flowrateentrylist[1].delete(0,'end')
            self.steplist[i].flowrateentrylist[1].insert(0,fr2)
            self.steplist[i].flowrateentrylist[2].delete(0,'end')
            self.steplist[i].flowrateentrylist[2].insert(0,fr3)

            self.steplist[i].twoSwitchComboBoxList[0].delete(0,'end')
            self.steplist[i].twoSwitchComboBoxList[0].set(ts1)
            self.steplist[i].twoSwitchComboBoxList[1].delete(0,'end')
            self.steplist[i].twoSwitchComboBoxList[1].set(ts2)
            self.steplist[i].twoSwitchComboBoxList[2].delete(0,'end')
            self.steplist[i].twoSwitchComboBoxList[2].set(ts3)

            self.steplist[i].reservoircombobox.delete(0,'end')          # delete between two indices, 0-based
            self.steplist[i].reservoircombobox.insert(0,res)

            self.steplist[i].samples.delete(0,'end')          # delete between two indices, 0-based
            self.steplist[i].samples.insert(0,rti)

            self.steplist[i].samplingrate.delete(0,'end')          # delete between two indices, 0-based
            self.steplist[i].samplingrate.insert(0,sra)

            print(self.steplist[i].flowrateentrylist[0].get())
    def delete_step(self,step_number):
        """ Note that step number is not an int but a tk.StringVar
        """

        #so, since we're deleting a step we unpack it on our screen then we delete the widget entirely
        #print('before  ',len(self.steplist),self.steplist)
        self.steplist[int(step_number.get())-1].grid_forget()
        #print('after  ',len(self.steplist),self.steplist)
        del self.steplist[int(step_number.get())-1]
        #print('after  ',len(self.steplist),self.steplist)
        #repopulating (and renumbering) the stepnumbers list which holds the steps we have available
        self.stepnumbers = []
        for i in range(len(self.steplist)):
            self.stepnumbers.append(str(i+1))
        #update the values in the combobox so we can select them
        self.deletestepcombo['values'] = self.stepnumbers
        self.deletestepcombo.delete(0, 'end')

        self.number_deleted += 1

        for i in range(len(self.steplist)):
            self.steplist[i].number['text'] = str(i+1)
    def clear_recipe(self):
        for i in range(len(self.steplist)):
            one = tk.StringVar()
            one.set("1")
            self.delete_step(one)
    def add_step(self):

        #create step
        print('before  ',len(self.steplist),self.steplist)

        self.steplist.append(self.create_step(self.channels,self.reservoirs))

        print('after  ',len(self.steplist),self.steplist)

        #repopulate stepnumbers list
        self.stepnumbers = []

        for i in range(len(self.steplist)):
            self.stepnumbers.append(str(i+1))

        #add new options to deletestepcombobox
        self.deletestepcombo['values'] = self.stepnumbers
    def create_step(self,channels,reservoirs):

        greaterlabelframe = tk.LabelFrame(self, bg = "#43e7ef")
        greaterlabelframe.channeltextlist = []
        greaterlabelframe.labelframelist = []
        greaterlabelframe.flowrateentrylist = []
        greaterlabelframe.reservoirvalues = []
        greaterlabelframe.toplabels = []
        greaterlabelframe.twoSwitchComboBoxList = []

        for i in range(reservoirs):
            greaterlabelframe.reservoirvalues.append(str(i+1))
        greaterlabelframe.reservoirvalues.append("wait")

        greaterlabelframe.reservoircombobox = tk.ttk.Combobox(greaterlabelframe, width = 8)
        greaterlabelframe.reservoircombobox['values'] = greaterlabelframe.reservoirvalues
        greaterlabelframe.reservoircombobox.insert(tk.END,'1')

        greaterlabelframe.samples = tk.Entry(greaterlabelframe, width = 8)
        greaterlabelframe.samples.insert(tk.END,"1")

        greaterlabelframe.samplingrate = tk.Entry(greaterlabelframe, width = 8)
        greaterlabelframe.samplingrate.insert(tk.END,"1")

        greaterlabelframe.number = tk.Label(greaterlabelframe,text = str(len(self.steplist)+1),font = ("Verdana",10), width = 8)

        self.twoSwitchValues = ["Collect","Recirculate"]

        for i in range(channels):

            flowrateentry = tk.Entry(greaterlabelframe, width = 8)
            flowrateentry.insert(tk.END,"100")
            greaterlabelframe.flowrateentrylist.append(flowrateentry)

            # Creates the twoSwitchComboBox and adds these instances to a list in self.
            twoSwitchComboBox = tk.ttk.Combobox(greaterlabelframe,width = 6)
            twoSwitchComboBox['values'] = self.twoSwitchValues
            twoSwitchComboBox.set(self.twoSwitchValues[0])
            twoSwitchComboBox.state(['!disabled', 'readonly'])
            greaterlabelframe.twoSwitchComboBoxList.append(twoSwitchComboBox)


            flowrateentry.grid(column = 2+i ,row = 1)
            twoSwitchComboBox.grid(column = 2+i ,row = 2)


        greaterlabelframe.grid(column = 1 , row = len(self.steplist) + 6 + self.number_deleted,columnspan = 9)

        #greaterlabelframe.directioncombo.grid(column = 1+channels+1+1 ,row = 1)
        greaterlabelframe.reservoircombobox.grid(column = 1+channels+4+1 ,row = 1)
        greaterlabelframe.samples.grid(column = 1+channels+2+1 ,row = 1)
        greaterlabelframe.samplingrate.grid(column = 1+channels+3+1 ,row = 1)
        greaterlabelframe.number.grid(column = 1 ,row = 1)

        return greaterlabelframe
    def check_channel(self,controller,channel,frame_object):

        goodToGo = True

        #--------------------------------------------------
        #check if the flowrate entry can be cast as a float
        try:
            float(frame_object.flowrateentrylist[channel-1].get())
        except:
            controller.message_window("Step %s. Entry must be float!" %frame_object.number["text"])
            goodToGo = False

        #--------------------------------------------------
        #check if the sampling rate can be cst as a float
        try:
            float(frame_object.samplingrate.get())
        except:
            controller.message_window("Step %s. Sampling rate must be float!" %frame_object.number["text"])
            goodToGo = False

        #-------------------------------------------------
        #check if number of samples can be cast to int
        try:
            int(frame_object.samples.get())

        except:
            controller.message_window("Step %s. Sample number must be integer!" %frame_object.number["text"])
            goodToGo = False

        #frame_object.samples.set(int(frame_object.samples.get()))
        #print("printing max flow" + str(controller.max_flowrate_list[channel-1]*1000))

        flowrateOK = (0 <= float(frame_object.flowrateentrylist[channel-1].get()) <= controller.max_flowrate_list[channel-1]*1000)

        if not flowrateOK:
            goodToGo = False
            controller.message_window("Step %s. Entry must be between %s and %s! uL/m"%(frame_object.number["text"],0,1000*controller.max_flowrate_list[channel-1]))

        all_recirc = []

        if frame_object.twoSwitchComboBoxList[channel-1].get() == "Recirculate":
            all_recirc.append(True)
        else:
            all_recirc.append(False)

        print("channels set to recirculate %s"%all_recirc)

        if not all(all_recirc):
            if float(frame_object.samplingrate.get())*(1.0/60)*float(frame_object.flowrateentrylist[channel-1].get()) > controller.well_working_volume:
                goodToGo = False
                max_time = (controller.well_working_volume/float(frame_object.flowrateentrylist[channel-1].get()))*60
                controller.message_window("Step %s. Sampling time for channel %s needs to be under %s s"%(frame_object.number["text"],channel,max_time))

        return goodToGo
    def run_recipe(self,controller):
        """Build in abort functionality and progress tracker
        """
        #If the step list has a number of samples above the amount of tripet wells.
        #Display error and return.

        if len(self.steplist) == 0:
            message_prompt("No steps are in queue please create or load steps!")
            return

        for frame_object in self.steplist:
            if not all([self.check_channel(controller,channel,frame_object) for channel in np.arange(3)+1]):
                return

        numsamples = 0

        #not counting full recirculation steps in total well number
        full_recircs = 0
        for i in range(len(self.steplist)):
            all_recirc= []
            for j in range(3):
                if self.steplist[i].twoSwitchComboBoxList[j].get() == "Recirculate":
                    all_recirc.append(True)
                else:
                    all_recirc.append(False)
            if all(all_recirc):
                full_recircs = full_recircs + 1
        numsamples = numsamples - full_recircs

        for steps in self.steplist:
            numsamples += int(steps.samples.get())

        if ((numsamples + controller.myColl.position) - 1) > 31:
            message_prompt("Can't run experiment due to overstepping amount of wells. Current position is: " + str(controller.myColl.position))
            return
        # If there are no steps ask user to create or load steps and do nothing.

        controller.positive_run_status()

        start = time.time()

        ap = tk.Toplevel(controller)
        ap.grab_set()

        ap.exitbutton = tk.Button(ap, text = "Exit/Abort", font = controller.buttonFont, command = combine_funcs(
        controller.myPump.stop_all,
        ap.destroy,
        ap.grab_release,
        controller.negative_run_status))

        ap.info = tk.StringVar()
        ap.infolabel = tk.Label(ap, anchor='w')
        ap.infolabel['textvariable'] = ap.info

        ap.status = tk.StringVar()
        ap.status.set("Running...")

        statuslabel = tk.Label(ap)
        statuslabel['textvariable'] = ap.status
        statuslabel.pack(fill='both')

        ap.infolabel.pack(side = tk.LEFT,fill='both')
        ap.exitbutton.pack(side=tk.BOTTOM)

        a = len(self.steplist)

        #getting number of steps
        b = 0
        for i in range(len(self.steplist)):
            b += int(self.steplist[i].samples.get())

        #getting total number of samples
        c = 0
        for i in range(len(self.steplist)):
            c += int(self.steplist[i].samples.get())*float(self.steplist[i].samplingrate.get())

        start_time = time.time()


        for i in range(len(self.steplist)):
            if controller.should_be_running == False:
                break

            ap.res = self.steplist[i].reservoircombobox.get()
            controller.myMani.set_reservoir(ap.res)

            self.two_switches_recirculating = []
            for j in range(len(self.steplist[i].flowrateentrylist)):
                flowrate = self.steplist[i].flowrateentrylist[j].get()
                controller.myPump.setFlow(j+1,flowrate)
                #controller.myPump.setDir(j+1,ap.direction)

                twoswitchstate = self.steplist[i].twoSwitchComboBoxList[j].get()
                if twoswitchstate == "Collect":
                    controller.my2Switch.setCollect(j+1)
                    self.two_switches_recirculating.append(False)
                elif twoswitchstate == "Recirculate":
                    controller.my2Switch.setRecirculate(j+1)
                    self.two_switches_recirculating.append(True)

            steps = int(self.steplist[i].samples.get())
            rate = float(self.steplist[i].samplingrate.get())

            tot_steps = steps

            time0 = time.time()

            if ap.res != "wait":
                if not controller.myPump.isOn:
                    controller.myPump.start_all()

                else:
                    pass
            else:
                controller.myPump.stop_all()


            while steps > 0:

                if controller.should_be_running == False:
                    break

                #print(controller.should_be_running)

                ap.info.set("""
                Number of steps: %s
                Total samples: %s
                Runtime: %s s
                Time Elapsed: %s s

                Step #: %s
                Samples Left: %s
                Samples in Step: %s
                Sampling Rate: %s s
                Reservoir: %s
                CH1: %s %s
                CH2: %s %s
                CH3: %s %s
                """%(a,
                b,
                c,
                np.trunc(time.time() - start_time),
                i+1,
                steps,
                tot_steps,
                rate,
                ap.res,
                self.steplist[i].flowrateentrylist[0].get(),
                self.steplist[i].twoSwitchComboBoxList[0].get(),
                self.steplist[i].flowrateentrylist[1].get(),
                self.steplist[i].twoSwitchComboBoxList[1].get(),
                self.steplist[i].flowrateentrylist[2].get(),
                self.steplist[i].twoSwitchComboBoxList[2].get()))

                if (time.time() - time0)/rate > 1:
                    #print(controller.myColl.position,steps,np.trunc(time.time()-start))
                    if not all(self.two_switches_recirculating):
                        controller.myColl.next_site()


                    controller.frames[ManualPage].positionLabel['text'] = "Current Position: " + str(controller.myColl.position)
                    time0 = time.time()
                    steps -= 1

                ap.update()

                """
                sw.info.set("\n step: % \n substeps left: %s \n wells available: %s \n sampling rate: %s \n time elapsed: %s \n reservoir: %s \n CH1: %s uL/m   CH2: %s uL/m   CH3: %s uL/m"%(
                i,
                sw.wells_used,
                96-sw.wells_used-sw.start_well,
                sampling_rate,
                np.trunc(time.time() - sw.start_time),
                sw.res,
                self.flowrateentrylist[0].get(),
                self.flowrateentrylist[1].get(),
                self.flowrateentrylist[2].get()
                ))
                sw.update()
                """

        controller.myPump.stop_all()
        ap.status.set("Done!")

class SettingsPage(tk.Frame):
    """ Everything that is being sent and all experimental parameters
    are be recorded here. Start and stop events. Serial commands. Status.
    """
    def __init__(self, parent, controller):

        tk.Frame.__init__(self,parent)

        #background color
        self.configure(bg='#00fff2')

        #should be automatic from single loc
        self.channels = 3
        self.reservoirs = 6

        #main label
        self.mainlabel = tk.Label(self, text = "Settings",bg='#00fff2', font =controller.pageFont,width = 15)

        #page navigation
        self.autopagebutton =  tk.Button(self, text = "Experiment",font = controller.buttonFont,bg = "white", command = lambda: controller.show_frame(AutomaticPage), height = 1, width = 10)
        self.manualbutton =  tk.Button(self, text = "Manual",font = controller.buttonFont,bg = "white", command = lambda: controller.show_frame(ManualPage), height = 1, width = 10)

        #updating tubing diameters and direction of peristaltic pump channels
        self.updatebutton = tk.Button(self, text = "Update",font = controller.buttonFont,bg = "#64ff64", command = lambda: self.update(controller), height = 1, width = 20)

        #calibration button
        self.calibratebutton = tk.Button(self, text = "Begin Calibration", command = lambda: self.request_calibration(controller),width = 30)

        # self.measuredVolume = tk.StringVar()
        # self.measuredVolumeEntry = tk.Entry(self,textvariable = self.measuredVolume,bg = "white",width = 15)
        # self.entercalibratedbutton = tk.Button(self, text = "Enter", command = lambda: controller.myPump.setMeasuredVolume( int(self.calibratecombobox.get()) , float(self.measuredVolume.get()) ),width = 15 )
        self.calibrationlabel = tk.Label(self, text = "Calibration",bg='#00fff2', font =controller.pageFont,width = 15)

        self.directionheading = tk.Label(self, text = "Direction",bg='#00fff2')
        self.directionslist = []
        self.directionlabellist = []
        self.directions = ["CW","CCW"]

        self.pumpsettingslabel = tk.Label(self, text = "Pump Settings",bg='#00fff2', font =controller.pageFont, width = 15)


        #pump comms options
        self.input_string = tk.StringVar()
        self.send_return_bool = tk.BooleanVar()
        self.return_print = tk.Label(self,text = "", bg='#00fff2', width = 15)
        self.return_print.grid(column = 3, row = 13, columnspan=1)

        self.input = tk.Entry(self,text=self.input_string, width = 15)
        self.input.grid(column = 1, row = 13, columnspan=1)
        self.send_button = tk.Button(self,text="Send",command = lambda: self.send_to_pump(controller), width = 15)
        self.send_button.grid(column = 4, row = 13, columnspan=1)
        self.send_return_check = tk.Checkbutton(self,var=self.send_return_bool, width = 15,bg='#00fff2')
        self.send_return_check.grid(column = 2, row = 13, columnspan=1)

        self.input_label = tk.Label(self,text="Input",bg='#00fff2', width = 15)
        self.input_label.grid(column = 1, row = 12, columnspan=1)
        self.return_label = tk.Label(self,text="Response",bg='#00fff2', width = 15)
        self.return_label.grid(column = 3, row = 12, columnspan=1)
        self.send_return_label = tk.Label(self,text="Toggle Response",bg='#00fff2', width = 15)
        self.send_return_label.grid(column = 2, row = 12, columnspan=1)

        self.pump_com_text = "Pump Comms: See ISMATEC pump manual for list of serial commands \n WARNING: For testing purposes only. \n No safeguards in place. Set to defaults after using."

        self.pump_com_label = tk.Label(self,text=self.pump_com_text,bg='#00fff2', width = 60)
        self.pump_com_label.grid(column = 1, row = 11, columnspan=4)


        #row 1
        self.mainlabel.grid(column = 1, row = 1, columnspan = 2)
        self.autopagebutton.grid(column = 3, row = 1)
        self.manualbutton.grid(column = 4, row = 1)

        #row 2
        self.calibrationlabel.grid(column = 1, row = 2,columnspan = 4)

        #row 3

        self.calibratebutton.grid(column = 2, row = 3,columnspan = 2)

        #row 4
        self.pumpsettingslabel.grid(column = 2, row = 4,columnspan = 2)

        #row 5
        for i in range(self.channels):
            directionlabel = tk.Label(self, text = "CH%s"%(i+1),bg='#00fff2',width = 15)
            directionlabel.grid(column = i+2, row = 5, columnspan=1)
            self.directionlabellist.append([directionlabel])

        #row 6
        self.directionheading.grid(column = 1, row = 6, columnspan = 1)
        for i in range(self.channels):
            directioncombobox = tk.ttk.Combobox(self,width = 15)
            directioncombobox['values'] = self.directions
            directioncombobox.set(self.directions[0])
            directioncombobox.state(['!disabled', 'readonly'])
            directioncombobox.grid(column = i+2, row = 6, columnspan=1)
            self.directionslist.append([directioncombobox])

        #row 7
        self.diameterlist = []
        self.diameterlabel = tk.Label(self, text = "Tubing Diameter",bg='#00fff2',width = 15)
        self.diametervalues = ['0013','0019','0025','0038','0044','0051','0057','0064','0076','0089','0095','0102','0109','0114','0122','0130','0142','0152','0165','0175','0185','0206','0229','0254','0279','0317']
        for i in range(self.channels):
            diametercombobox = tk.ttk.Combobox(self,width = 15)
            diametercombobox['values'] = self.diametervalues
            diametercombobox.set(self.diametervalues[controller.default_diameter_index])
            diametercombobox.state(['!disabled', 'readonly'])
            self.diameterlist.append(diametercombobox)
            diameterlabel = tk.Label(self, text = "Tubing Diameter",bg='#00fff2', font=controller.pageFont,width = 15)
            diametercombobox.grid(column = i+2,row = 7,columnspan=1)

        self.diameterlabel.grid(column = 1, row = 7,columnspan = 1)
        #row 9
        #row 10
        self.updatebutton.grid(column = 1, row = 10,columnspan = 2,sticky=tk.W, pady=5)
    def send_to_pump(self,controller):



        if self.send_return_bool.get() == 0:
            self.return_print['text'] = "N/A"
            command = self.input.get()
            controller.myPump.send(command)

        elif self.send_return_bool.get() == 1:
            self.return_print['text'] = "waiting..."
            command = self.input.get()
            response = controller.myPump.send_return(command)
            self.return_print["text"] = "%s"%response
    def update(self,controller):
        for i in range(self.channels):
            print(i)
            direction = self.directionslist[i][0].get()
            controller.myPump.setDir(i+1,direction)
            tubing_diameter = self.diameterlist[i].get()
            controller.myPump.send(str(i+1)+'+'+tubing_diameter)

        #Here we assume the same tubing diameter for each (initially)
        controller.max_flowrate_1 = controller.myPump.send_return('1?')
        controller.max_flowrate_2 = controller.max_flowrate_1
        controller.max_flowrate_3 = controller.max_flowrate_1
        time.sleep(2)
        controller.myPump.ser.readline()
        controller.myPump.ser.flush()
        time.sleep(2)
    def request_calibration(self,controller):

        window = tk.Toplevel(controller)
        window.grab_set()
        window.configure(bg='#00fff2')

        #get option
        #window.option = self.calibratecombobox.get()
        channels = [1,2,3]

        #labels for the entries 1
        label_1 = tk.Label(window, text = "Channel" ,bg='#00fff2',font = LARGE_FONT)
        label_2 = tk.Label(window, text = "Volume (uL)"  ,bg='#00fff2',font = LARGE_FONT)
        label_3 = tk.Label(window, text = "Time (m)"    ,bg='#00fff2',font = LARGE_FONT)
        label_1.grid(column = 1, row = 2, columnspan = 1)
        label_2.grid(column = 2, row = 2, columnspan = 1)
        label_3.grid(column = 3, row = 2, columnspan = 1)

        #present entry boxes for choosing volume and time
        window.settings = []
        for channel in channels:
            vol  = tk.StringVar()
            time = tk.StringVar()
            vol_entry  = tk.Entry(window, textvariable = vol, bg = "white",width = 20)
            time_entry = tk.Entry(window, textvariable = time, bg = "white",width = 20)
            Ch = str(channel)
            label = tk.Label(window, text = Ch ,bg='#00fff2',font = LARGE_FONT)
            info = [channel,label,vol_entry,time_entry]
            window.settings.append(info)

        #labels for the entries 2
        label_3 = tk.Label(window, text = "Channel" ,bg='#00fff2',font = LARGE_FONT)
        label_4 = tk.Label(window, text = "Measured Volume (uL)"  ,bg='#00fff2',font = LARGE_FONT)
        label_3.grid(column = 1, row = 7, columnspan = 1)
        label_4.grid(column = 2, row = 7, columnspan = 1)

        #present entry boxes for choosing volume and time
        window.measured = []

        for channel in channels:
            vol_meas  = tk.StringVar()
            vol_meas_entry  = tk.Entry(window, textvariable = vol_meas, bg = "white",width = 20)
            vol_meas_entry['state'] = tk.DISABLED
            Ch = str(channel)
            label = tk.Label(window, text = Ch ,bg='#00fff2',font = LARGE_FONT)
            info = [channel,label,vol_meas,vol_meas_entry]
            window.measured.append(info)

        vol_entries = []
        time_entries = []
        measured_entries = []
        for i in range(len(channels)):
            window.settings[i][1].grid(column = 1, row = 3+i, columnspan = 1)
            window.settings[i][2].grid(column = 2, row = 3+i, columnspan = 1)
            window.settings[i][3].grid(column = 3, row = 3+i, columnspan = 1)
            window.measured[i][1].grid(column = 1, row = 8+i, columnspan = 1)
            window.measured[i][3].grid(column = 2, row = 8+i, columnspan = 1)
            vol_entries.append(window.settings[i][2])
            time_entries.append(window.settings[i][3])
            measured_entries.append(window.measured[i][3])

        window.calibratebutton = tk.Button(window,text = "Start Calibration",bg = "#64ff64",font = controller.buttonFont,
        command = lambda: combine_funcs(
        self.check(controller,vol_entries,time_entries,measured_entries,window)))
        window.calibratebutton.grid(column = 1, row = 6, columnspan = 2)

        window.send_button = tk.Button(window,text = "Send Measurements",bg = "#64ff64",font = controller.buttonFont,
        command = lambda: combine_funcs(
        self.update_measured_volumes(controller,window),
        window.destroy(),
        window.grab_release()))
        window.send_button.grid(column = 1, row = 12, columnspan = 2)
        window.send_button.config(state = tk.DISABLED)
    def update_measured_volumes(self,controller,window):
        for i in range(len(window.measured)):
            if window.measured[i][3]['state'] == 'normal':
                channel = window.measured[i][0]
                volume = window.measured[i][3].get()
                controller.myPump.set_measured_volume(channel,volume)
    def update_calibration_settings(self,controller,settings):
        for setting in settings:
            channel = setting[0]
            volume  = setting[2].get()
            time    = setting[3].get()
            controller.myPump.set_calibration_volume(channel,volume,'uL')
            controller.myPump.set_calibration_time(channel,time)
            controller.myPump.calibrate(channel)
    def check(self,controller,vol_entries,time_entries,measured_entries,window):
        """checks if the entry is a float,
        if it is it checks if it's in range,
        if it is it sets that channel as OK
        it then gives option to proceed or not
        """

        window.update()
        truth_table = []
        message_list = []
        for i in range(len(vol_entries)):
            truth_table.append(True)
            message_list.append("")
        for i in range(len(vol_entries)):

            message_list[i] += "Channel %s \n"%(i+1)

            #empty or not check
            if truth_table[i]:
                if not len(vol_entries[i].get()) > 0:
                    truth_table[i] = False
                    message_list[i] += "volume entry is empty\n"
                if not len(vol_entries[i].get()) > 0:
                    truth_table[i] = False
                    message_list[i] += "time entry is empty\n"

            #float check 1
            if truth_table[i]:
                try:
                    np.float(vol_entries[i].get())
                except:
                    truth_table[i] = False
                    message_list[i] += "volume entry must be float\n"

            #float check 2
            if truth_table[i]:
                try:
                    np.float(time_entries[i].get())
                except:
                    truth_table[i] = False
                    message_list[i] += "time entry must be float\n"

            #range check 1
            if truth_table[i]:
                if np.float(time_entries[i].get()) < 0.1 or np.float(time_entries[i].get()) > 16:
                    truth_table[i] = False
                    message_list[i] += "time entry must be between 0.1 and 16 minutes\n"

            #range check 2
            if truth_table[i]:
                if np.float(vol_entries[i].get()) < 0.1 or np.float(vol_entries[i].get()) > 1000:
                    truth_table[i] = False
                    message_list[i] += "volume entry must be between 0.1 and 1000 uL \n"

            if truth_table[i]:
                message_list[i] += "OK \n"
        message = ""
        for i in range(len(message_list)):
            message += message_list[i] + "\n"
        if any(truth_table):
            message2 = "CALIBRATE"
            for i in range(len(truth_table)):
                if truth_table[i]:
                    message2 += " %s"%(i+1)
            message += message2 + "?"
        prompt = message_prompt(message)
        prompt.exitbutton["text"] = "Cancel"

        new_settings = []
        window.new_measured = []

        for i in range(len(truth_table)):
            if truth_table[i]:
                new_settings.append(window.settings[i])
                window.new_measured.append(window.measured[i])

        """
        for widget_set in window.settings:

             myState1 = str(widget_set[2]['state'])
             myState2 = str(widget_set[3]['state'])

             if myState1 == 'normal':
                 widget_set[2].config(state = tk.DISABLED)
             else:
                 widget_set[2].config(state = tk.NORMAL)

             if myState2 == 'normal':
                 widget_set[3].config(state = tk.DISABLED)
             else:
                 widget_set[3].config(state = tk.NORMAL)

        for widget in new_measured:

            myState = str(widget[3]['state'])

            if myState == 'normal':
                widget[3].config(state = tk.DISABLED)
            else:
                widget[3].config(state = tk.NORMAL)
        """


        process_name = "Calibrating"

        new_times = []
        for i in range(len(new_settings)):
            a = float(new_settings[i][3].get())
            new_times.append(a)

        total_time = np.max(new_times)

        total_time = total_time*60

        prompt.continue_button = tk.Button(prompt,text = "Continue",font = prompt.buttonFont,
        command = lambda: combine_funcs(
        prompt.grab_release(),
        prompt.destroy(),
        self.update_calibration_settings(controller,new_settings),
        self.time_progress(controller,process_name,total_time),
        window.send_button.config(state = tk.NORMAL),
        window.calibratebutton.config(state = tk.DISABLED),
        self.toggle_editable(window)
        ))

        prompt.continue_button.grid(column = 1, row = 6, columnspan = 1)
        prompt.update()
    def time_progress(self, controller, process_name, total_time):

        w = tk.Toplevel(controller)
        w.grab_set()
        w.configure(bg='#00fff2')

        initial_time = time.time()
        w.label_1 = tk.Label(w,text = "%s Runtime = %s"%(process_name,total_time),bg = '#00fff2')
        w.label_2 = tk.Label(w,text = "Time Elapsed    = %s"%(time.time() - initial_time),bg = '#00fff2')

        w.cancelbutton = tk.Button(w,text = "Quit process",bg = "#ff6464",font = controller.buttonFont,width = 10,
        command = lambda : combine_funcs(w.destroy,w.grab_release,controller.myPump.abort_calibration()))

        w.label_1.grid(column=1,row=1,columnspan=1)
        w.label_2.grid(column=1,row=2,columnspan=1)
        w.cancelbutton.grid(column=1,row=3,columnspan=1)

        while time.time()-initial_time < total_time:
            w.label_2["text"] = "Time Elapsed    = %s"%(np.round(time.time() - initial_time,0))
            w.update()

        w.destroy()
        w.grab_release()
    def toggle_editable(self,window):

                for widget_set in window.settings:

                     myState1 = str(widget_set[2]['state'])
                     myState2 = str(widget_set[3]['state'])

                     if myState1 == 'normal':
                         widget_set[2].config(state = tk.DISABLED)
                     else:
                         widget_set[2].config(state = tk.NORMAL)

                     if myState2 == 'normal':
                         widget_set[3].config(state = tk.DISABLED)
                     else:
                         widget_set[3].config(state = tk.NORMAL)

                for widget in window.new_measured:

                    myState = str(widget[3]['state'])

                    if myState == 'normal':
                        widget[3].config(state = tk.DISABLED)
                    else:
                        widget[3].config(state = tk.NORMAL)
    def update_measured_volume(controller,entry_list,option):

        if option =="All":
            for i in range(len(entry_list)):
                vol = entry_list[i].get()
                controller.myPump.set_measured_volume(self,i,vol)
        else:
            vol = entry_list[0].get()
            controller.myPump.set_measured_volume(self,option,vol)

app = App()
app.mainloop()
