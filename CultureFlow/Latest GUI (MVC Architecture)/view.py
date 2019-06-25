"""
View
"""

from tkinter import Tk
from tkinter import  Frame, Button, Label, Entry, Scrollbar, Canvas
from tkinter import font, E, W, N, S, RIGHT, LEFT, CENTER, HORIZONTAL, VERTICAL, BOTH, TOP, BOTTOM, X, Y
from system_control import CultureFlow_Control
from gui_helper import Page, Pump_Widget, Circulation_Widget, Mswitch_Widget, Collection_Widget, Recipe_Creator_Widget, Recipe_Display_Widget, Plate_Control_Widget

#default_font = tkFont.nametofont("TkDefaultFont")
#default_font.configure(size=48)
#root.option_add("*Font", default_font)

class App(Tk):

    def __init__(self,*args,**kwargs):

        Tk.__init__(self,*args,**kwargs)

        # background_image=tk.PhotoImage(...)
        # background_label = tk.Label(parent, image=background_image)
        # background_label.place(x=0, y=0, relwidth=1, relheight=1)


        self.afont = font.Font(family='Arial', size=16, weight='bold')
        self.bfont = font.Font(family='Verdana', size=12, weight='bold')
        self.pfont = font.Font(family='Faktos', size=18, weight='bold')
        self.widget_background = 'PaleTurquoise1'
        self.geometry('450x600')
        self.resizable(width=True, height=True)
        container = Frame(self,relief='raised')
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0,weight = 1)
        container.grid_columnconfigure(0,weight = 1)

        self.app_name = "CultureFlow"
        self.title(self.app_name)
        self.system = CultureFlow_Control(self)
        self.channels = self.system.getNumberOfPumpChannels()


        self.navigation_buttons = {'Home': lambda: self.show_frame(Home),
         'Settings': lambda: self.show_frame(Settings)}

        self.pages = (Loading,Home,Settings)

        self.frames = {}
        for F in self.pages:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Loading)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class Loading(Page):

    #This screen displays serial communications and a load prompt
    def __init__(self, parent, controller):
        Page.__init__(self,parent,controller)

        self.page_buttons.pack_forget()

        self.loading_status = ''
        self.loading_label = Label(self.my_canvas.frame,text=self.loading_status,justify=LEFT)
        self.loading_label.pack(side="top",fill="both", expand=True)

        self.controller = controller

        self.exit_button     = Button(self,text = "Quit Program",command = controller.destroy, font=controller.bfont)
        self.continue_button = Button(self, text = "Continue", font= controller.bfont, command = lambda: controller.show_frame(Home))

        self.exit_button.pack(side="left",fill="both", expand=True)
        self.continue_button.pack(side="left",fill="both", expand=True)

        controller.system.load(self)

    def update_text(self):
            self.loading_status += self.controller.system.view_message + "\n"
            self.loading_label['text'] = self.loading_status

class Home(Page):
    def __init__(self, parent, controller):
        Page.__init__(self,parent,controller)


        #create and pack pump control widget
        self.pump_widget = Pump_Widget(self.my_canvas.frame,controller)
        self.pump_widget.pack(side='top',fill=X)

        #create and pack circulation control widget
        self.circulation_widget = Circulation_Widget(self.my_canvas.frame,controller)
        self.circulation_widget.pack(side='top',fill=X)

        #create and pack mswitch widget
        self.mswitch_widget = Mswitch_Widget(self.my_canvas.frame,controller)
        self.mswitch_widget.pack(side='top',fill=X)

        #create and pack collection widget
        self.collection_widget = Collection_Widget(self.my_canvas.frame,controller)
        self.collection_widget.pack(side='top',fill=X)

        #step editor widget - takes in values from all previous widgets/stores steps
        widget_dictionary = {'pump_widget':self.pump_widget,
        'circulation_widget':self.circulation_widget,
        'mswitch_widget':self.mswitch_widget,
        'collection_widget':self.collection_widget}

        self.recipe_creator_widget = Recipe_Creator_Widget(self.my_canvas.frame,controller,widget_dictionary=widget_dictionary)
        self.recipe_creator_widget.pack(side='top',fill=X)

        #step list widget - displays all steps and is passed to system_control.py
        self.recipe_display_widget = Recipe_Display_Widget(self.my_canvas.frame,controller,recipe_creator_widget=self.recipe_creator_widget)
        self.recipe_display_widget.pack(side='top',fill=X)
        self.recipe_creator_widget.widget_dictionary['recipe_display_widget'] = self.recipe_display_widget

        #plate control widget
        self.plate_control_widget = Plate_Control_Widget(self.my_canvas.frame,controller)
        self.plate_control_widget.pack(side='top',fill=X)

class Recipe_Creator(Page):
    def __init__(self, parent, controller):
        Page.__init__(self,parent,controller)

class Settings(Page):
    def __init__(self, parent, controller):
        Page.__init__(self,parent,controller)

app = App()
app.mainloop()
