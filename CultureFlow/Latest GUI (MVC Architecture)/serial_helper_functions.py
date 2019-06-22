import serial
from serial.tools.list_ports import comports
test_mode = True

def get_ports():


    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
        ports.append(port)
    print(ports)
    return ports

def locate_device_comport(ports,call,response):

      response = response[:2] #we only use the first two characters of the response

      if len(ports) == 0:
          return "NC"

      for comport in ports:

          try:
              ser = serial.Serial(comport, 9600, timeout=3)
              time.sleep(1)
              ser.write(call.encode('ascii') + '\r'.encode('ascii'))
              time.sleep(1)

              resp = ser.readline().decode()
              resp = resp[:2]

              print("We sent " + call + " to " + comport + " and recieved " + resp)
              print("We are looking for: " + response)

              if resp == response:
                  ports.remove(comport)
                  print("We assigned the port: " + comport)
                  ser.close()
                  return comport, ports

              ser.close()

          except:
              print("Error accesing comports!")

      return "NF"

def serial_connect(port,baud):
    
    ser = serial.Serial(port, baud, timeout=3)
    if ser.isOpen():
        return ser
    else:
        return None
