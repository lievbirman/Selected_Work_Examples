import numpy as np
from tkinter import Button, Tk

class App(Tk):

    def __init__(self,*args,**kwargs):

        Tk.__init__(self,*args,**kwargs)

        self.geometry('500x750')

        #This is OK
        self.my_button = Button(self,text="press me", command = lambda: print("stop pressing me!"))
        self.my_button.pack()
        #This is OK
        self.my_second_button = Button(self,text="press me 2", command = self.print_stop)
        self.my_second_button.pack()
        #This is OK
        self.my_third_button = Button(self,text="press me 3", command = lambda: self.print_stop_2("test_1"))
        self.my_third_button.pack()
        #---------------------------------------------
        #This is NOT OK
        self.my_fourth_button = Button(self,text="press me 4", command = self.print_stop())
        self.my_fourth_button.pack()
        #This is also NOT OK
        self.my_fifth_button = Button(self,text="press me 5", command = self.print_stop_2("test_2"))
        self.my_fifth_button.pack()

    def print_stop(self):
        print("Stop!")

    def print_stop_2(self,my_string):
        print("Stop!" + my_string)

app = App()

#app.print_stop()

app.mainloop()
