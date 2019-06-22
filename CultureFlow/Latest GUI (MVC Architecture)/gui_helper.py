from tkinter import Frame, Canvas, Scrollbar, Button, Label, LabelFrame, Entry, Tk, DoubleVar, Radiobutton, StringVar, IntVar
from tkinter import LEFT, BOTH, font, DISABLED, NORMAL, X, Y
from tkinter.ttk import Combobox

class Scrolling_Canvas(Frame):

    def __init__(self, root):

        Frame.__init__(self, root)
        self.canvas = Canvas(root, borderwidth=0, background="#ffffff")
        self.frame = Frame(self.canvas, background="#ffffff")
        self.vsb = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class Horizontal_Button_Frame(Frame):

    def __init__(self,root,button_functions = {}):

        my_font = font.Font(family='Verdana', size=12, weight='bold')

        Frame.__init__(self, root)

        self.button = {}

        for name in button_functions:

            next_button = Button(self,text=name,font = my_font, padx=50)
            next_button['command'] = button_functions[name]
            next_button.config(height=3,width=3)
            next_button.pack(side=LEFT,fill=BOTH)
            self.button[name] = next_button

    def set_command(self,name,command):
        self.button[name]['command'] = command

class Page(Frame):
    #This screen displays devices found and asks user if they want to continue
    def __init__(self, parent, controller):

        Frame.__init__(self,parent)

        self.title = str(self.__class__.__name__).replace("_"," ")
        self.title_label = Label(self,text = self.title, font=controller.pfont)
        self.title_label.pack(side="top")

        self.my_canvas = Scrolling_Canvas(self)
        self.my_canvas.pack(side="top")

        #now we can create as many panels as we want!
        self.page_buttons = Horizontal_Button_Frame(self,controller.navigation_buttons)
        self.page_buttons.pack(side="bottom",fill='x')

class Pump_Channel(Frame):

    def __init__(self,parent,system,channel_number,background_color=None):

        font1 = font.Font(family='Calibri', size=12, weight='bold')
        font2 = font.Font(family='Verdana', size=8)
        font3 = font.Font(family='Verdana', size=10, weight='bold')

        Frame.__init__(self,parent)

        self.config(height=5,width=3)
        self.configure(bg=background_color)

        self.button_width = 5

        self.ch_title = "Flowrate %s "%str(channel_number)
        self.ch_label = Label(self,text = self.ch_title, font=font1,bg=background_color)

        self.flowrate_label = Label(self,text = "(uL/m)", font=font2,bg=background_color)
        self.flowrate = DoubleVar()
        self.flowrate_entry = Entry(self, textvariable = self.flowrate,width=self.button_width)
        # self.flowrate_entry.config(width=10)

        self.start_button = Button(self,text="START",width=self.button_width,bg='green2',font=font3)
        self.stop_button = Button(self,  text="STOP",width=self.button_width,bg='red2',font=font3)

        #functions
        self.start_button['command'] = lambda: system.start_pump_channel(channel_number,self.flowrate.get())
        self.stop_button['command'] = lambda: system.stop_pump_channel(channel_number)

        #add validation for entry using vcmd
        self.ch_label.pack(side="left",fill=BOTH, expand=1,padx=5)
        self.flowrate_entry.pack(side="left",fill=X, expand=1)
        self.flowrate_label.pack(side="left",fill=X, expand=1)
        self.start_button.pack(side="left",fill=BOTH, expand=1)
        self.stop_button.pack(side="left",fill=BOTH, expand=1)
        ""

class Pump_Widget(Frame):

    def __init__(self,parent,controller):

        system = controller.system
        num_channels = controller.channels
        background_color = controller.widget_background

        font3 = font.Font(family='Helvetica', size=12, weight='bold')

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")

        self.configure(bg=background_color)

        self.title = 'Pump Control'
        self.title_label = Label(self,text=self.title,bg=background_color).pack()

        self.all_button_frame = Frame(self)

        self.start_all = Button(self.all_button_frame,text="START ALL",command=lambda:system.start_all(),bg='green2').pack(side='left',fill=X)
        self.stop_all = Button(self.all_button_frame,text="STOP ALL",command=lambda:system.stop_all(), bg='red2').pack(side="left",fill=X)

        self.channels = {}

        for i in range(num_channels):
            self.channels[str(i+1)] = Pump_Channel(self,system,i+1,background_color)
            self.channels[str(i+1)].pack()
        self.all_button_frame.pack(side="bottom")

class Circulation_Channel(Frame):

    def __init__(self,parent,system,channel_number,background_color=None):

        font1 = font.Font(family='Calibri', size=12, weight='bold')
        font2 = font.Font(family='Verdana', size=8)
        font3 = font.Font(family='Verdana', size=10, weight='bold')

        Frame.__init__(self,parent)

        self.config(height=8,width=5)
        self.configure(bg=background_color)

        self.button_width = 10

        self.ch_title = "Switch %s "%str(channel_number)
        self.ch_label = Label(self,text = self.ch_title, font=font1,bg=background_color)

        self.circulation_mode = StringVar()
        self.recirculate = Radiobutton(self, text='Recirculate', variable=self.circulation_mode, value='recirculate',bg=background_color,indicatoron=0,width=self.button_width)
        self.collect = Radiobutton(self, text='Collect', variable=self.circulation_mode, value='collect',bg=background_color,indicatoron=0,width=self.button_width)
        #add validation for entry using vcmd

        self.recirculate['command'] = lambda: system.setRecirculate(channel_number)
        self.collect['command'] = lambda: system.setCollect(channel_number)


        self.recirculate.pack(side="right",padx=5)
        self.collect.pack(side="right",padx=5)
        self.ch_label.pack(side="left",padx=5)

class Circulation_Widget(Frame):

        def __init__(self,parent,controller,system=None,num_channels=None,background_color=None):

            if system == None:
                system=controller.system
            if num_channels == None:
                num_channels=controller.channels
            if background_color == None:
                background_color=controller.widget_background

            font3 = font.Font(family='Helvetica', size=12, weight='bold')

            Frame.__init__(self,parent)

            self.configure(borderwidth=3, relief="ridge")

            self.configure(bg=background_color)

            self.title = 'Circulation Control'
            self.title_label = Label(self,text=self.title,bg=background_color).pack()

            self.channels = {}

            for i in range(num_channels):
                self.channels[str(i+1)] = Circulation_Channel(self,system,i+1,background_color)
                self.channels[str(i+1)].pack(side="top",pady=2)

class Mswitch_Widget(Frame):

    def __init__(self,parent,controller,system=None,num_channels=None,background_color=None):



        if system == None:
            self.system=controller.system
        if num_channels == None:
            num_channels=controller.channels
        if background_color == None:
            background_color=controller.widget_background

        font1 = font.Font(family='Calibri', size=12, weight='bold')
        font2 = font.Font(family='Verdana', size=8)
        font3 = font.Font(family='Verdana', size=10, weight='bold')

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")

        self.config(height=8,width=5)
        self.configure(bg=background_color)

        self.button_width = 10

        self.title = 'Reservoir Control'
        self.title_label = Label(self,text=self.title,bg=background_color).pack()

        self.title = "Reservoir"
        self.label = Label(self,text = self.title, font=font1,bg=background_color)

        self.values = list(range(1,self.system.getNumberOfReservoirs()+1))


        self.reservoir_combobox = Combobox(self,values=self.values,state='readonly')
        self.reservoir_combobox.bind("<<ComboboxSelected>>", self.set_res)

        self.label.pack(side="left",padx=5)
        self.reservoir_combobox.pack(side="right",padx=5)

    def set_res(self,event):
        self.system.setReservoir(self.reservoir_combobox.get())

class Collection_Widget(Frame):

    def __init__(self,parent,controller,system=None,num_channels=None,background_color=None):

        if system == None:
            self.system=controller.system
        if num_channels == None:
            num_channels=controller.channels
        if background_color == None:
            background_color=controller.widget_background

        font1 = font.Font(family='Calibri', size=12, weight='bold')
        font2 = font.Font(family='Verdana', size=8)
        font3 = font.Font(family='Verdana', size=10, weight='bold')

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")
        self.configure(height=8,width=5)
        self.configure(bg=background_color)

        self.button_width = 20

        self.main_title = 'Collection Control'
        self.title_label = Label(self,text=self.main_title,bg=background_color).pack()

        self.samples_frame=Frame(self,bg=background_color)
        self.samples = IntVar()
        self.samples_label = Label(self.samples_frame,text = "Samples", font=font1,bg=background_color,width=self.button_width).pack(side='left',fill=X)
        self.samples_entry = Entry(self.samples_frame,textvariable=self.samples,bg=background_color,width=self.button_width).pack(side='right',fill=X)
        self.samples_frame.pack(side='top')

        self.time = DoubleVar()
        self.time_frame = Frame(self,bg=background_color)
        self.sample_time = Label(self.time_frame,text = "Sample Time (s)", font=font1,bg=background_color,width=self.button_width).pack(side='left',fill=X)
        self.time_entry = Entry(self.time_frame,textvariable=self.time,bg=background_color,width=self.button_width).pack(side='right',fill=X)
        self.time_frame.pack(side='top')

        self.start_collection_button = Button(self,text="Start Collection",command=self.start_coll,bg="green2",width=2*self.button_width).pack(side="bottom")

    def start_coll(self):
        self.system.start_collection(self.samples.get(),self.time.get())

#uncomment and input classes to test
if __name__ == "__main__":
    root=Tk()
    background_color = 'cyan'
    Circulation_Widget(root,'yes',"pump",2,'cyan').pack(side="top", fill="both", expand=True)
    root.mainloop()
