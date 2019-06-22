

class Pump():

    def __init__(self):

        print("Pump object created")

        ###declarations standard to all devices

        #call out to serial for device identification
        self.call = "0xS"

        #response from call out. must be 2 characters
        self.response = "IS"
        self.ser = None

        self.baud = 9600

        ###device specific

        self.number_of_channels = 3

    def FormatVolume(self,V,unit):
        """
        This method formats the volume.

        Parameters:
            V (int): The amount of volume.
            unit (string): The unit the volume should be set in.
        """
        if unit == "mL":
            S = 1
        elif unit == "uL":
            S = 10E-4
        A = '%E' % Decimal(str(float(V)*S))
        B = A[-3:]
        C = B[0]+B[2]
        D = str(int(float(A[:5])*1000))
        E = D+C
        return E
    def setFlow(self,channel,flowrate):
        """
        This method sets the flow rate of the pump.
        Parameters:
            channel (int): The channel whose flow rate will be set.
            flowrate (float): The flow rate which is to be set.
        """
        flowrate = self.FormatVolume(flowrate,"uL")
        print(flowrate)
        self.send(str(channel)+"f"+flowrate)
    def setDir(self,channel,direction):
        """
        This method sets the direction for the flow of fluid.

        Parameters:
            channel (int): The channel flow rate direction will be set.
            direction (string): The direction for the pump CW or CCW.
        """

        if direction == "CW":
            self.send(str(channel)+"J")
            self.send(str(channel)+"xRJ")

        if direction == "CCW":
            self.send(str(channel) + "K")
            self.send(str(channel) + "xRK")
    def start(self,channel):
        """
        This method sends a command to the microcontroller which is programmed to start the pump only for the channel chosen.

        Parameters:
            channel (int): the channel that will start.
        """
        self.send(str(channel)+"H")
    def stop(self,channel):
        """
        This method sends a command to the microcontroller which is programmed to stop the pump only for the channel chosen.

        Parameters:
            channel (int): the channel that will stop.
        """

        self.send(str(channel)+"I")
    def calibrate(self,channel):

        if channel == "All":
            for i in range(3):
                self.send(str(i+1)+"xY")
        else:
            self.send(str(channel)+"xY")
    def abort_calibration(self):
        """
        This method sends a command to the microcontroller which is programmed to abort calibration of the pump only for the channel chosen.

        Parameters:
            channel (int): the channel that will abort calibration.
        """

        self.send("0xZ")
    def set_calibration_volume(self,channel,volume,unit):
        to_send = str(channel)+"xU"+self.FormatVolume(volume,unit)
        self.send(to_send)
    def set_calibration_time(self,channel,time):
        #input is min
        time = float(time)*60
        if time < 0.1:
            time = 0.1
        elif time > 9999999.9:
            time = 99999999
        time = np.round(time,1)

        time = str(time)
        time = time.replace(".", "")
        time_len = len(time)
        len_zeros = 8 - time_len
        time_string = ""
        for i in range(len_zeros):
            time_string += "0"
        time_string += time

        to_send = str(channel)+"xW"+time_string
        self.send(to_send)
    def set_measured_volume(self,channel,volume):
        """
        This method sets the measured volume.
        """
        volume = self.FormatVolume(volume,"uL")
        self.send_return(str(channel)+"xV"+volume)
    def start_all(self):
        """
        This method sends a command to the microcontroller which is programmed to start the pump for all channels.
        """
        self.send("0H")
    def stop_all(self):
        """
        This method sends a command to the microcontroller which is programmed to stop the pump for all the channels.
        """
        self.send("0I")
    def setDefaults(self):
        """
        This method sets the deafults for the pump.
        """
        # self.send_return('1M')
        # self.send_return('2M')
        # self.send_return('3M')

        self.send('0xM')
        self.send('0xM')
        self.send("0xU1000+0")
        self.send("0xW00003000")
