"""
Written by:
D. Thiebaut
"""

# a Serial class emulator
class Serial:
    """
    This class is used for simulation of a Serial Connection.

    Attributes:
        name (string): the name of the port.
        port (string): the microcontrollers port for the serial connection.
        baudrate (int): The baud rate the serial connection is using.
        timeout (int): maximum milliseconds to wait for serial data.
        parity (string): parity bit type.
        stopbits (int): amount of stop bits.
        xonxoff (int): whether xonxoff is on or off for flow control.
        rtscts (int): whether rtscts flow control is on or off.
    """
    def __init__(self, port='COM1', baudrate = 19200, timeout=1,
                  bytesize = 8, parity = 'N', stopbits = 1, xonxoff=0,
                  rtscts = 0):

        self.name     = port
        self.port     = port
        self.timeout  = timeout
        self.parity   = parity
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.xonxoff  = xonxoff
        self.rtscts   = rtscts
        self._isOpen  = True


    def write(self,write_string,return_string=""):
        print(string)
        return return_string

    def comports():
        return ""

    def __str__( self ):
        """
        This method creates a string representation of the Serial class.

        Returns:
            string: String representation of Serial class.
        """

        return  "Serial<id=0xa81c10, open=%s>( port='%s', baudrate=%d," \
               % ( str(self.isOpen), self.port, self.baudrate ) \
               + " bytesize=%d, parity='%s', stopbits=%d, xonxoff=%d, rtscts=%d)"\
               % ( self.bytesize, self.parity, self.stopbits, self.xonxoff,
                   self.rtscts )
