from tkinter import Frame, Canvas, Scrollbar, Button, Label, LabelFrame, Entry, Tk, DoubleVar, Radiobutton, StringVar, IntVar, Text
from tkinter import LEFT, BOTH, font, DISABLED, NORMAL, X, Y
from tkinter.ttk import Combobox
import copy

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

        self.buttons = [self.start_button,self.stop_button]

    def getFlowRate(self):
        return self.flowrate.get()

    def toggleButtons(self):
        print('togglin 2')
        for button in self.buttons:
            if str(button['state']) == 'disabled':
                button['state'] = 'normal'
            elif str(button['state']) == 'normal':
                button['state'] ='disabled'

class Pump_Widget(Frame):

    def __init__(self,parent,controller):

        self.system = controller.system
        self.num_channels = controller.channels
        background_color = controller.widget_background

        font3 = font.Font(family='Helvetica', size=12, weight='bold')

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")

        self.configure(bg=background_color)

        self.title = 'Pump Control'
        self.title_label = Label(self,text=self.title,bg=background_color).pack()

        self.all_button_frame = Frame(self)

        self.start_all = Button(self.all_button_frame,text="START ALL",command=lambda:system.start_all(),bg='green2')
        self.start_all.pack(side='left',fill=X)
        self.stop_all = Button(self.all_button_frame,text="STOP ALL",command=lambda:system.stop_all(), bg='red2')
        self.stop_all.pack(side="left",fill=X)

        self.channels = {}

        self.buttons = [self.start_all,self.stop_all]

        for i in range(self.num_channels):
            self.channels[str(i+1)] = Pump_Channel(self,self.system,i+1,background_color)
            self.channels[str(i+1)].pack()

        self.all_button_frame.pack(side="bottom")

    def getVals(self):
        vals = []
        for i in range(self.num_channels):
            vals.append(self.channels[str(i+1)].getFlowRate())
        return vals

    def toggleButtons(self):
        print('togglin!')

        for i in range(self.num_channels):
            self.channels[str(i+1)].toggleButtons()

        for button in self.buttons:
            if str(button['state']) == 'disabled':
                button['state'] = 'normal'
            elif str(button['state']) == 'normal':
                button['state'] ='disabled'

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
        self.circulation_mode.set('collect')
        self.recirculate = Radiobutton(self, text='Recirculate', variable=self.circulation_mode, value='recirculate',bg=background_color,indicatoron=0,width=self.button_width)
        self.collect = Radiobutton(self, text='Collect', variable=self.circulation_mode, value='collect',bg=background_color,indicatoron=0,width=self.button_width)
        #add validation for entry using vcmd

        self.recirculate['command'] = lambda: system.setRecirculate(channel_number)
        self.collect['command'] = lambda: system.setCollect(channel_number)


        self.recirculate.pack(side="right",padx=5)
        self.collect.pack(side="right",padx=5)
        self.ch_label.pack(side="left",padx=5)

    def getCirculationMode(self):
        return self.circulation_mode.get()

class Circulation_Widget(Frame):

        def __init__(self,parent,controller,system=None,num_channels=None,background_color=None):

            if system == None:
                system=controller.system
            if num_channels == None:
                self.num_channels=controller.channels
            if background_color == None:
                background_color=controller.widget_background

            font3 = font.Font(family='Helvetica', size=12, weight='bold')

            Frame.__init__(self,parent)

            self.configure(borderwidth=3, relief="ridge")

            self.configure(bg=background_color)

            self.title = 'Circulation Control'
            self.title_label = Label(self,text=self.title,bg=background_color).pack()

            self.channels = {}

            for i in range(self.num_channels):
                self.channels[str(i+1)] = Circulation_Channel(self,system,i+1,background_color)
                self.channels[str(i+1)].pack(side="top",pady=2)

        def getVals(self):
            vals = []
            for i in range(self.num_channels):
                vals.append(self.channels[str(i+1)].getCirculationMode())
            return vals

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
        self.reservoir_combobox.bind("<<ComboboxSelected>>", self.setRes)

        self.label.pack(side="left",padx=5)
        self.reservoir_combobox.pack(side="right",padx=5)

        self.reservoir_combobox.set('1')

    def setRes(self,event):
        self.system.setReservoir(self.reservoir_combobox.get())

    def getVals(self):
        return [self.reservoir_combobox.get()]

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

        self.start_collection_button = Button(self,text="Start Collection",command=self.start_coll,bg="green2",width=2*self.button_width)
        self.start_collection_button.pack(side="bottom")

    def start_coll(self):
        self.system.start_collection(self.samples.get(),self.time.get())

    def getVals(self):
        vals = []
        vals.append(self.samples.get())
        vals.append(self.time.get())
        return vals

    def toggleButtons(self):
        if str(self.start_collection_button['state']) == 'disabled':
            self.start_collection_button['state'] = 'normal'
        elif str(self.start_collection_button['state']) == 'normal':
            self.start_collection_button['state'] ='disabled'

class Recipe_Creator_Widget(Frame):

    def __init__(self,parent,controller,background_color=None,widget_dictionary={}):

        if background_color == None:
            background_color=controller.widget_background

        font1 = font.Font(family='Calibri', size=12, weight='bold')
        font2 = font.Font(family='Verdana', size=8)
        font3 = font.Font(family='Verdana', size=10, weight='bold')

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")
        self.configure(height=8,width=5)
        self.configure(bg=background_color)

        self.main_title = 'Recipe Creator'
        self.title_label = Label(self,text=self.main_title,bg=background_color).pack()

        self.button_width = 18

        self.widget_dictionary = widget_dictionary
        self.step_list=[]

        self.add_step_button = Button(self,text="Add Step",command=self.add_step,state ='disabled',width=self.button_width)
        self.add_step_button.pack(side='top')
        self.delete_step_button = Button(self,text="Delete Step",command=self.delete_step,state ='disabled',width=self.button_width)
        self.delete_step_button.pack(side='top')



        self.insert_step_button = Button(self,text="Insert Step",command=self.insert_step,state ='disabled',width=self.button_width)
        self.insert_step_button.pack(side='top')

        self.step_numbers = []
        self.step_combobox = Combobox(self,values=self.step_numbers,state ='disabled',width=self.button_width)
        self.step_combobox.pack(side='top')

        self.clear_button = Button(self,text="Clear All",command=self.clear_steps,state ='disabled',width=self.button_width)
        self.clear_button.pack(side='top')

        self.tkinter_widgets = [self.add_step_button,self.delete_step_button,self.step_combobox, self.insert_step_button,self.clear_button]
        self.toggle_button = Button(self,text="Toggle Recipe Creator",command=self.toggle_on_off,width=self.button_width).pack(side='top')
    def add_step(self):

        vals_list = []
        for widget in self.widget_dictionary:
            try:
                widget_vals = self.widget_dictionary[widget].getVals()
                for value in widget_vals:
                    vals_list.append(value)
            except:
                pass

        self.step_list.append(vals_list)
        print(vals_list)
        self.update_step_numbers()

    def delete_step(self):
        step = self.step_combobox.get()
        self.step_combobox.set('')
        self.step_list.pop(int(step)-1)
        self.update_step_numbers()
    def insert_step(self):
        vals_list = []
        for widget in self.widget_dictionary:
            try:
                widget_vals = self.widget_dictionary[widget].getVals()
                for value in widget_vals:
                    vals_list.append(value)
            except:
                pass
        self.step_list.insert(int(self.step_combobox.get())-1,vals_list)
        print(vals_list)
        self.update_step_numbers()
    def update_step_numbers(self):
        self.step_numbers = [i+1 for i in range(len(self.step_list))]
        print(self.step_list)
        self.step_combobox['values'] = self.step_numbers
        self.widget_dictionary['recipe_display_widget'].repopulate()
    def clear_steps(self):
        for i in range(len(self.step_list)):
            self.step_list.pop(0)
        self.step_combobox.set('')
        self.update_step_numbers()
    def toggle_on_off(self):
        for widget in self.tkinter_widgets:
            if str(widget['state']) == 'disabled':
                widget['state'] = 'normal'
            elif str(widget['state']) == 'normal':
                widget['state'] ='disabled'

        for widget in self.widget_dictionary:
            try:
                self.widget_dictionary[widget].toggleButtons()
            except:
                pass

class Recipe_Display_Widget(Frame):

    def __init__(self,parent,controller,background_color=None,recipe_creator_widget=None):

        self.recipe_creator_widget = recipe_creator_widget

        self.width = 15

        if background_color == None:
            background_color=controller.widget_background

        font1 = font.Font(family='Calibri', size=11)

        Frame.__init__(self,parent)

        self.configure(borderwidth=3, relief="ridge")
        self.configure(height=8,width=5)
        self.configure(bg=background_color)

        self.long_string = StringVar()
        self.text_box = Label(self,textvariable=self.long_string,bg=background_color)
        self.text_box.pack(side="top")

    def repopulate(self):
        string = ""
        for step_num in range(len(self.recipe_creator_widget.step_list)):
            step = copy.deepcopy(step_num)
            step = str(step)
            while len(step) < self.width:
                step += " "
            string += "%s|"%step
            for value in self.recipe_creator_widget.step_list[step_num]:
                value = str(value)
                while len(value) < self.width:
                    value += " "
                string += "%s|"%value
            string += "\n"
        self.long_string.set(string)
        print(self.long_string.get())

class Plate_Control_Widget(Frame):
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

        self.main_title = 'Stage Control'
        self.title_label = Label(self,text=self.main_title,bg=background_color).pack()

        self.next_button = Button(self,text="Next Site",width = self.button_width,command=self.next).pack()
        self.prev_button = Button(self,text="Previous Site",width = self.button_width,command=self.prev).pack()
        self.eject = Button(self,text="Eject",width = self.button_width,command=self.eject).pack()
        self.reset = Button(self,text="Reset",width = self.button_width,command=self.reset).pack()

        self.pos = StringVar()
        self.pos_label = Label(self,textvariable=self.pos,bg=background_color).pack()

        self.update_pos()

    def eject(self):
        self.system.eject()
        self.update_pos()
        ""
    def reset(self):
        self.system.reset()
        self.update_pos()
        ""
    def next(self):
        self.system.next()
        self.update_pos()
        ""
    def prev(self):
        self.system.prev()
        self.update_pos()
        ""
    def update_pos(self):
        self.pos.set(self.system.getPos())
        print(self.system.getPos())
        ""



#
# class Recipe_Frame(Frame):
#     def __init__(self,parent,controller,background_color=None,widget_dictionary={}):
#
#         font1 = font.Font(family='Calibri', size=12, weight='bold')
#         font2 = font.Font(family='Verdana', size=8)
#         font3 = font.Font(family='Verdana', size=10, weight='bold')
#
#         Frame.__init__(self,parent)
#
#         self.configure(borderwidth=3, relief="ridge")
#         self.configure(height=8,width=5)
#         self.configure(bg=background_color)
#
#         self.system=controller.system
#         background_color=controller.widget_background
#
#         self.widget_dictionary=widget_dictionary
#
#         self.label_width = 5
#
#         self.label_frame = Frame(self).pack()
#         #self.step_frame = Frame(self).pack()
#
#         self.create_header(self.label_frame)
#         #self.add_step_button = Button(self,text="Add Step",command=self.add_step).pack(side='right')
#
#     def create_header(self,pack_frame):
#
#         ### Here you define how to parse the various widgets
#         try:
#             self.flow_channels = self.widget_dictionary['pump_widget'].num_channels
#             for i in range(self.flow_channels):
#                 flow_label = Label(pack_frame,text = "FR%s"%(i+1),width=self.label_width).pack(side="left")
#         except:
#             pass
#
#         try:
#             self.circulation_channels = self.widget_dictionary['circulation_widget'].num_channels
#             for i in range(self.circulation_channels):
#                 switch_label = Label(pack_frame,text = "SW%s"%(i+1),width=self.label_width).pack(side="left")
#         except:
#             pass
#
#         try:
#             self.widget_dictionary['mswitch_widget']
#             res_label = Label(pack_frame,text = "RES",width=self.label_width).pack(side="left")
#         except:
#             pass
#
#         try:
#             self.widget_dictionary['collection_widget']
#             samples_label = Label(pack_frame,text = "SAM",width=self.label_width).pack(side="left")
#             time_label = Label(pack_frame,text = "SATI",width=self.label_width).pack(side="left")
#
#         except:
#             pass
#
#     def add_step(self):
#         print("adding step!")
#         new_step = Recipe_Step(self.step_frame, self.widget_dictionary).pack(side='top')
#
# class Recipe_Step(Frame):
#
#     def __init__(self,parent,widget_dictionary={}):
#
#         font1 = font.Font(family='Calibri', size=12, weight='bold')
#         font2 = font.Font(family='Verdana', size=8)
#         font3 = font.Font(family='Verdana', size=10, weight='bold')
#
#         Frame.__init__(self,parent)
#
#         self.variable_dictionary = {}
#
#         try:
#             for i in range(widget_dictionary['pump_widget'].num_channels):
#                 flow_var = DoubleVar()
#                 flow_var.set(widget_dictionary['pump_widget'].channels[str(i+1)].getFlowRate())
#                 flow_entry = Entry(self,textvariable=flow_var).pack(side='left')
#                 self.add_to_dictionary("FR%s"%(i+1),flow_var)
#                 print(flow_var.get())
#
#         except:
#             pass
#
#     def add_to_dictionary(self,key,value):
#         my_key = str(key)
#         my_value = value
#         self.variable_dictionary[my_key] = my_value


        # try:
        #     self.circulation_channels = widget_dictionary['circulation_widget'].num_channels
        #     for i in range(self.circulation_channels):
        #         switch_label = Label(self,text = "SW%s"%(i+1),width=self.label_width).pack(side="left")
        # except:
        #     pass
        #
        # try:
        #     widget_dictionary['mswitch_widget']
        #     res_label = Label(self,text = "RES",width=self.label_width).pack(side="left")
        # except:
        #     pass
        #
        # try:
        #     widget_dictionary['collection_widget']
        #     samples_label = Label(self,text = "SAM",width=self.label_width).pack(side="left")
        #     time_label = Label(self,text = "SATI",width=self.label_width).pack(side="left")
        #
        # except:
        #     pass

#uncomment and input classes to test
if __name__ == "__main__":
    root=Tk()
    background_color = 'cyan'
    Circulation_Widget(root,'yes',"pump",2,'cyan').pack(side="top", fill="both", expand=True)
    root.mainloop()
