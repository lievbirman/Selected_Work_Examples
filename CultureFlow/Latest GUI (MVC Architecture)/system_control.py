"""
Controller

This is where you operate on the model through the gui
"""
from model import CultureFlow_Model
from serial_helper_functions import get_ports, locate_device_comport,serial_connect

class CultureFlow_Control():
    """
    controller for original hardware set-up
    """
    def __init__(self,controller):

        print('CultureFlow_Control object created')

        #model object
        self.model = CultureFlow_Model()

        #devices that we're supposed to have and their availability stored in immutable tuple
        self.available_devices = ()

        #the string that we update to publish messages to view
        self.view_message = "No updates available"

        #gui controller i.e. the app class that does frame handling.
        self.controller = controller

    def load(self,screen=None):
        """if using screen object to update while loading then
        screen object needs to its own update text option
        """

        #get list of comports available to computer
        comports = get_ports()
        if screen != None:


            for device in self.model.devices:
                self.view_message = "Sending call for %s to available comports..."%device
                screen.update_text()

                #returns device comport and unused ports if found. NC if no connections on PC. NF if not found.
                result = locate_device_comport(comports,self.model.devices[device].call,self.model.devices[device].response)

                #checking result from previous line and decides how to update view
                if result == "NC":
                    self.view_message = "No devices found..."
                    screen.update_text()

                elif result == "NF":
                    device_available = False
                    self.view_message = "%s not found..."%device
                    screen.update_text()
                else:
                    self.view_message = "%s found..."%device
                    screen.update_text()

                    device_available = True
                    comport = result[0]
                    comports = result[1]

                if device_available:
                    #tries to connect
                    self.serial_to_model(device,comport)
                    #add to available devices
                    self.available_devices = (*self.available_devices,device)

        #gives the user the option to load device without referencing any screen
        elif screen == None:
            self.available_devices =()
            #Iterate through devices listed in model
            for device in self.model.device_ids:
                #returns device comport and unused ports if found. NC if no connections on PC. NF if not found.
                result = locate_device_comport(comports,self.model.device_ids[device][0],self.model.device_ids[device][1])
                if result != "NC" and result != "NF":
                    device_available = True
                    comport = result[0]
                    comports = result[1]
                #updates list of available devices
                if device_available:
                    self.available_devices = (*self.available_devices,device)
        else:
            raise Exception('screen input needs to be a tkinter Frame object or None')

    def serial_to_model(self,device,comport):
        #connects the proper serial object the the instance of the device in model
        self.model.devices[device].ser = serial_connect(comport,self.model.devices[device].baud)

    def getNumberOfPumpChannels(self):
        return self.model.devices['pump'].number_of_channels

    def getNumberOfReservoirs(self):
        return self.model.devices['mswitch'].reservoirs

    def setRecirculate(self,channel):
        print("recirculating", channel)

    def setCollect(self,channel):
        print("collecting", channel)

    def setReservoir(self,reservoir):
        print('setting reservoirs', reservoir)

    def start_pump_channel(self,channel_number,flowrate):
        print('starting',channel_number,flowrate)

    def stop_pump_channel(self,channel_number):
        print('stopping',channel_number)

    def start_all(self):
        print('starting all')

    def stop_all(self):
        print('stopping all')

    def start_collection(self,samples,time):
        print("this many ",samples,"for this long",time)
