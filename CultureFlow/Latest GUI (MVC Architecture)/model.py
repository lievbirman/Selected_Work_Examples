"""
Model

This is where you define everything that's in the physical system

"""
from pump import Pump
from mswitch import Mswitch

class CultureFlow_Model():

    def __init__(self):
        print('CultureFlow_Model object created')

        self.pump = Pump()
        self.mswitch = Mswitch()

        self.devices = {"pump":self.pump,"mswitch":self.mswitch}

    def getPos(self):
        return 'none atm'
