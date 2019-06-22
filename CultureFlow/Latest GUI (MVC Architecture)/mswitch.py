

class Mswitch():

    def __init__(self):

        print("Mswitch object created")

        #variables standard to all devices
        self.call = "R"
        self.response = "65"
        self.ser = None
        self.baud = 9600
        self.reservoirs=6

    def set_reservoir(self,res):
        """
        This method sets the reservoir to pull fluid from.
        """
        self.send("P0"+str(res))
    def get_info(self):
        """
        This method sends the command "?" to the microcontroller which is programmed to send back a unique ID. The attribute uniqueID is set to the microcontrollers response.

        Returns:
            response (string): The unique ID that the microcontroller sends back through the serial connection.
        """

        self.send("S")
        response = self.ser.readline().decode()
        response = self.chop_return(response)
        self.uniqueID = response
        return response
