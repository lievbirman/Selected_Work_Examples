#
  # def prime_window(self,controller):
  #     """
  #     creates a window for the priming function
  #     """
  #     #first let's run through each of the m-switch channels
  #     window = controller.message_window("Priming")
  #     #start button - calls warning script
  #     window.start_button = tk.Button(window,text = "OK",bg = "#ff6464",font = self.buttonFont,width = 5, command = self.prime_validate(window))
  #     #entry for m-switch channels to prime
  #     window.m_switch_channels = StringVar()
  #     window.m_switch_channels_entry = tk.Entry(window, text = "Enter M-switch channels Ex: 1, 2, 4, 5", textvariable = window.m_switch_channels)
  #     #entry for pump channels to prime
  #     window.pump_channels = StringVar()
  #     window.pump_channels_entry = tk.Entry(window, text = "Enter pump channels Ex: 1, 2, 3", textvariable = window.pump_channels)
  #
  #     window.m_switch_channels_entry.grid(column = 1, row = 3)
  #     window.pump_channels_entry.grid(column = 1, row = 4)
  #
  # def prime_validate(self,window):
  #
  #     good_to_go = True
  #     pump_channels = self.csv_list_checker(window.pump_channels.get())
  #     m_switch_channels = self.csv_list_checker(window.m_switch_channels.get())
  #
  #     if not pump_channels:
  #         error = controller.message_window("Invalid entry for pump channels. Format should be: 1, 2, 3")
  #         good_to_go = False
  #
  #     if not m_switch_channels:
  #         error = controller.message_window("Invalid entry for m-switch channels. Format should be: 1, 2, 3")
  #         good_to_go = False
  #
  #     if good_to_go:
  #
  #         accept_priming = controller.message_window(\
  #         "WARNING! Please make surfairue that none\n \
  #          of the m-switch or pump channels you\n \
  #          selected are blocked or clogged. Running\n \
  #          anyway will cause leaks and potantial hardware problems.")
  #
  #         accept_priming.start_button = tk.Button(window,text = "OK, lets prime. ",bg = "#ff6464",font = self.buttonFont,width = 5, command = self.prime(pump_channels,m_switch_channels))
  #         accept_priming.start_button.grid(column = 1, row = 3)
  #
  # def prime(self,pump_channels,m_switch_channels):
  #
  #     priming = controller.message_window("Priming!")
  #     #running = tk.BooleanVar()
  #     #running.set(True)
  #
  #     starting_volume_to_dispense = 5000 #uL
  #     m_switch_volume_to_dispense = 1000
  #
  #     length_of_tubing_after_2_switch = 100
  #     tubing_area = np.pi*(0.51/2)**2 #mm^2
  #     two_switch_to_chip_volume = length_of_tubing_after_2_switch*tubing_area #mm^3
  #
  #     prime_flowrate = 200
  #
  #     #initial flowrate setting
  #     controller.myPump.setFlow(0,prime_flowrate)
  #     for channel in pump_channel:
  #         controller.my2Switch.setRecirculate(int(channel))
  #         controller.myPump.setFlow(channel,200)
  #
  #     #initial flow thru
  #     time_0 = time.time()
  #     controller.myPump.start_all()
  #     controller.myMani.set_reservoir(int(m_switch_channels[0])
  #     while time.time()-time_0 < starting_volume_to_dispense/prime_flowrate and running:
  #         print(time.time()-time_0)
  #
  #     #flowing through the m-switch channels
  #     time_0 = time.time()
  #     for channel in m_switch_channels:
  #         controller.myMani.set_reservoir(channel)
  #         while time.time()-time_0 < m_switch_volume_to_dispense/prime_flowrate and running:
  #             print(time.time()-time_0)
  #
  #     #flowing through the perfusion bit between the 2-switch and the chip
  #     time_0 = time.time()
  #     for channel in pump_channel:
  #         controller.my2Switch.setCollect(int(channel))
  #     while time.time()-time_0 < two_switch_to_chip_volume/prime_flowrate and running:
  #         print(time.time()-time_0)
  #
  #     #stopping
  #     controller.myPump.stop_all()
  #
  # def csv_list_checker(self,entry,low_limit,high_limit):
  #
  #     reader = csv.reader([entry], skipinitialspace=True)
  #     entry_list = []
  #     for number in reader:
  #         try:
  #             int(number)
  #         except:
  #             entry_list = []
  #             return []
  #         if int(number) < low_limit or int(number) > high_limit:
  #             entry_list = []
  #             return []
  #         else:
  #             entry_list.append(number)
  #     return entry_list
