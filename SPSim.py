#!/usr/bin/env python
"""	
This file implements all the GUI for the Solar Panel Simulator 
software using the Python library 'tkinter'

Autor: João Carlos Cerqueira  FEEC/Brazil , CTU/Prague
Email: jc.cerqueira13@gmail.com
Jan/2016 - Prague

Copyright (c) 2016 - João Carlos Cerqueira - jc.cerqueira13@gmail.com
GNU GENERAL PUBLIC LICENSE Version 3.0, June 2007
"""

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog

from matplotlib import style
style.use('ggplot')

from itertools import cycle

import pvspice
import os.path
import numpy as np
import os
import subprocess
import matplotlib.pyplot as plt

class Window: #Main window
	def __init__ (self, master):
		#Internal variable initialization
		self.win_bypass_flag = 0        
		self.win_grid_flag = 0        
		self.win_string_flag = 0
		self.win_panel_flag = 0
		self.win_cell_flag = 0
		self.win_bypasstemp_flag = 0
		self.irradiance_list = []        
		self.diode_list = []
		self.last_applied_diode_list = []
		self.master = master

		print ("Solar Panel Simulator - CVUT v Praze - 2016\n\
This window will show important informations about the software\n\
status and data output. Keep it open during the simulations.\n")

		master.title('Solar Panel Simulator - ČVUT v Praze')

		#Execute Python with the correct directory
		pyfilepath = os.path.dirname(os.path.realpath(sys.argv[0]))
		os.chdir(pyfilepath)
		del pyfilepath
		#Creating the workspace directory
		os.makedirs("workspace", exist_ok = True)
		self.work_abs_path = os.path.abspath('workspace')

		#CVUT icon
		try:
			master.iconbitmap(default='cvut.ico')
		except:
			messagebox.showerror("Error", "Could not find CVUT icon (cvut.ico)")

		#Solar cell image
		try:
			self.cell_photo = PhotoImage(file = 'cell.gif')
			self.hscell_photo = PhotoImage(file = 'hscell.gif')
		except:
			messagebox.showerror("Error","Could not find solar cell gif image")
			self.quit_all
			
		#Menu
		menubar = Menu(master)
		
		#Main sub-menu (save parameters, load parameters, exit)
		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label="Save parameters", command=self.save_parameters)
		filemenu.add_command(label="Load parameters", command=self.load_parameters)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.quit_all)
		menubar.add_cascade(label="File", menu=filemenu)
		
		#Help sub-menu
		helpmenu = Menu(menubar, tearoff=0)
		helpmenu.add_command(label="Help", command=self.help)
		helpmenu.add_command(label="About", command=self.about)
		helpmenu.add_command(label="License", command=self.license)
		menubar.add_cascade(label="Help", menu=helpmenu)

		master.config(menu=menubar)
		
		#Create frame1 (for user input values)
		frame1 = LabelFrame(master, bd = 2, relief = GROOVE, text="Panel Datasheet Values - STC (25°C & 1000 W/m^2)")
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10, ipadx = 10, ipady = 10, sticky=W+E)

		#Create frame3 (for generated values)
		frame3 = LabelFrame(master, bd = 2, relief = GROOVE, text="Panel Simulation Parameters - STC (25°C & 1000 W/m^2)")
		frame3.grid(row = 0, column = 1, padx = 10, pady = 10, ipadx = 10, ipady = 10, sticky=W+E+N+S)
		
		#Create frame4 (for simulations commands)
		frame4 = LabelFrame(master, bd = 2, relief = GROOVE, text="Simulation Options")
		frame4.grid(row = 1, column = 0,  padx = 10, pady = 10, ipadx = 10, ipady = 10, sticky=W+E+N+S)
		
		#Create frame5 (for results)
		frame5 = LabelFrame(master, bd = 2, relief = GROOVE, text="Open Results")
		frame5.grid(row = 1, column = 1,  padx = 10, pady = 10, ipadx = 10, ipady = 10, sticky=W+E+N+S)

		#Labels (used to name the parameter boxes)
		#Frame1 labels, first column
		Label(frame1, text="Number of cells").grid(row = 0, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Open-circuit voltage").grid(row = 1, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Short-circuit current").grid(row = 2, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Peak power voltage").grid(row = 3, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Peak power current").grid(row = 4, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Voltage temp. coeff.").grid(row = 5, column = 0, padx = 10, sticky = E)
		Label(frame1, text="Current temp. coeff.").grid(row = 6, column = 0, padx = 10, sticky = E)
		Label(frame1, text="N° of panels in serie").grid(row = 7, column = 0, padx = 10, pady=3, sticky = E)
		Label(frame1, text="N° of panels in parallel").grid(row = 8, column = 0, padx = 10, sticky = E)
		#Frame1 labels, third colum
		Label(frame1, text="[V]").grid(row = 1, column = 2, sticky = W)
		Label(frame1, text="[A]").grid(row = 2, column = 2, sticky = W)
		Label(frame1, text="[V]").grid(row = 3, column = 2, sticky = W)
		Label(frame1, text="[A]").grid(row = 4, column = 2, sticky = W)
		Label(frame1, text="[V/°C]").grid(row = 5, column = 2, sticky = W)
		Label(frame1, text="[A/°C]").grid(row = 6, column = 2, sticky = W)
		#Frame3 labels, first colum
		Label(frame3, text="Saturation current (Io)").grid(row = 0, column = 0, padx = 10, sticky = E)
		Label(frame3, text="Photovoltaic current (Iph)").grid(row = 1, column = 0, padx = 10, sticky = E)
		Label(frame3, text="Series resistance (Rs)").grid(row = 2, column = 0, padx = 10, sticky = E)  
		Label(frame3, text="Shunt resistance (Rsh)").grid(row = 3, column = 0, padx = 10, sticky = E)  
		Label(frame3, text="Diode ideality constant (A)").grid(row = 4, column = 0, padx = 10, sticky = E)  
		#Frame3 labels, third colum
		Label(frame3, text="[A]").grid(row = 0, column = 2,sticky = W) 
		Label(frame3, text="[A]").grid(row = 1, column = 2, sticky = W)
		Label(frame3, text="[Omhs]").grid(row = 2, column = 2,  sticky = W)
		Label(frame3, text="[Omhs]").grid(row = 3, column = 2, sticky = W)

		#Parameter entry boxes
		#Frame 1 (input values)
		self.e_Ns = Entry(frame1, width = 15)
		self.e_Ns.grid(row=0, column=1, padx = 10, sticky=W)
		self.e_Ns.insert(0, '72')
		
		self.e_Voc = Entry(frame1, width = 15)
		self.e_Voc.grid(row=1, column=1, padx = 10, sticky=W)
		self.e_Voc.insert(0, '43.5')
		
		self.e_Isc = Entry(frame1, width = 15)
		self.e_Isc.grid(row=2, column=1, padx = 10, sticky=W)
		self.e_Isc.insert(0, '3.45')
	   
		self.e_Vmp = Entry(frame1, width = 15)
		self.e_Vmp.grid(row=3, column=1, padx = 10, sticky=W)
		self.e_Vmp.insert(0, '35')   
	   
		self.e_Imp = Entry(frame1, width = 15)
		self.e_Imp.grid(row=4, column=1, padx = 10, sticky=W)
		self.e_Imp.insert(0, '3.15')
		
		self.e_Kv = Entry(frame1, width = 15)
		self.e_Kv.grid(row=5, column=1, padx = 10, sticky=W)
		self.e_Kv.insert(0, '-0.152')
		
		self.e_Ki = Entry(frame1, width = 15)
		self.e_Ki.grid(row=6, column=1, padx = 10, sticky=W)
		self.e_Ki.insert(0, '0.0014')

		self.e_nserie = Entry(frame1, width = 15)
		self.e_nserie.grid(row=7, column=1, padx = 10, sticky=W)
		self.e_nserie.insert(0, '1')

		self.e_nparallel = Entry(frame1, width = 15)
		self.e_nparallel.grid(row=8, column=1, padx = 10, sticky=W)
		self.e_nparallel.insert(0, '1')

		#Frame 3 (generated values)
		self.e_I0 = Entry(frame3, width = 15)
		self.e_I0.grid(row=0, column=1, padx = 10, sticky=W)
		self.e_I0.insert(0, '')
		
		self.e_Iph = Entry(frame3, width = 15)
		self.e_Iph.grid(row=1, column=1, padx = 10, sticky=W)
		self.e_Iph.insert(0, '')
		
		self.e_Rs = Entry(frame3, width = 15)
		self.e_Rs.grid(row=2, column=1, padx = 10, sticky=W)
		self.e_Rs.insert(0, '')
		
		self.e_Rsh = Entry(frame3, width = 15)
		self.e_Rsh.grid(row=3, column=1, padx = 10, sticky=W)
		self.e_Rsh.insert(0, '')
		
		self.e_A = Entry(frame3, width = 15)
		self.e_A.grid(row=4, column=1, padx = 10, sticky=W)
		self.e_A.insert(0, '')

		#Buttons
		#Frame 1
		self.button1 = Button(frame1, text = "Set Bypass Diode", command = self.window_bypass)
		self.button1.grid(row=9, column=0, padx = 10, pady = 5, sticky = W)

		self.button2 = Button(frame1, text = "Create Grid", command = self.datasheet_apply_function)
		self.button2.grid(row=9, column=1, columnspan=2, padx = 10, pady = 5, sticky = E)

		#Frame 3
		self.button3 = Button(frame3, text = "Generate Parameters", command = self.panelparameters_generate_function)
		self.button3.grid(row=6, column=0, padx = 10, pady = 5, sticky = W)

		self.button4 = Button(frame3, text = "Apply Changes", command = self.panelparameters_apply_function)
		self.button4.grid(row=6, column=1, columnspan=2, padx = 10, pady = 5, sticky = E)

		self.button5 = Button(frame3, text = "Customize Grid Panels", command = self.window_grid)
		self.button5.grid(row=7, column=1, columnspan=3, padx = 10, pady = 5, sticky = E)

		self.button6 = Button(frame3, text = "Restore Default Values", command = self.restore_default_values)
		self.button6.grid(row=9, column=1, columnspan = 2, padx = 10, pady = 5, sticky = E)
		
		#Frame 4 BUTTONS, LABELS & ENTRIES
		Label(frame4, text="File name:").grid(row = 0, column = 0, padx = 10, sticky = W)

		self.e_filename = Entry(frame4)
		self.e_filename.grid(row=0, column=2, padx = 10, sticky=W+E)
		self.e_filename.insert(0, 'Grid_1')
	  
		Label(frame4, text="Simulation Precision [V]:").grid(row = 1, column = 0, columnspan=2, padx = 10, sticky = W)
		
		self.e_precision = Entry(frame4)
		self.e_precision.grid(row=1, column=2, padx = 10, sticky=W+E)
		self.e_precision.insert(0, '0.5')

		self.checkbox1 = BooleanVar()
		self.check1 = Checkbutton(frame4, text="Probe strings current", variable=self.checkbox1)
		self.check1.grid(row=2, column=0, columnspan = 2, padx = 10, sticky=W)

		self.checkbox2 = BooleanVar()
		self.check2 = Checkbutton(frame4, text="Probe diodes current", variable=self.checkbox2)
		self.check2.grid(row=3, column=0, columnspan = 2, padx = 10, sticky=W)

		self.button7 = Button(frame4, text = "Simulate", command = self.run_simulation_routine)
		self.button7.grid(row=3, column=2, padx = 10)

		#Frame 5 BUTTONS, LABELS & ENTRIES
		self.button8 = Button(frame5, text = "Open File", command = self.open_result_file)
		self.button8.grid(row=0, column=0, padx = (10,0), pady = 10)

		self.stringvar_opened_file = StringVar()
		Label(frame5, textvariable = self.stringvar_opened_file, bg='white', width=15, relief=RIDGE).grid(
			row = 0, column = 1, padx = (0,10), pady = 10, sticky = N+S)

		self.button8 = Button(frame5, text = "Plot", command = self.plot_new_graphic)
		self.button8.grid(row=0, column=2, padx = 10, pady = 10)

		#Creating listboxes for graphs selection
			# First listbox
		inframe = LabelFrame(frame5, relief = FLAT, text = 'Current')
		inframe.grid(row = 1, column = 0, columnspan=2,  padx = 5, pady = 5, ipadx = 5, ipady = 5, sticky=W+E+N+S)

		scrollbar = Scrollbar(inframe, orient=VERTICAL)
		self.listbox = Listbox(inframe, exportselection=0, height=3, width=15, yscrollcommand=scrollbar.set, selectmode=MULTIPLE)
		scrollbar.config(command=self.listbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.listbox.pack(side=LEFT, fill=BOTH, expand=1)

			# Second listbox
		inframe2 = LabelFrame(frame5, relief = FLAT, text = 'Power')
		inframe2.grid(row = 1, column = 2,  padx = 5, pady = 5, ipadx = 5, ipady = 5, sticky=W+E+N+S)

		scrollbar2 = Scrollbar(inframe2, orient=VERTICAL)
		self.listbox2 = Listbox(inframe2, exportselection=0, height=3, width=12, yscrollcommand=scrollbar2.set, selectmode=MULTIPLE)
		scrollbar2.config(command=self.listbox2.yview)
		scrollbar2.pack(side=RIGHT, fill=Y)
		self.listbox2.pack(side=LEFT, fill=BOTH, expand=1)

	def plot_new_graphic(self):
		#Find which names are selected
		selected = self.listbox.curselection()
		selected2 = self.listbox2.curselection()
		if selected == () and selected2 == ():
			messagebox.showerror("Error", "Select at least one curve")
			return

		print ("\n      -- New plot --\n")
		#Function that returns the value of a picked plot point
		def on_pick(event):
			artist = event.artist
			xmouse, ymouse = event.mouseevent.xdata, event.mouseevent.ydata
			x, y = artist.get_xdata(), artist.get_ydata()
			ind = event.ind
			print ('Artist picked:', event.artist)
			print ('{} vertices picked'.format(len(ind)))
			print ('Pick between vertices {} and {}'.format(min(ind), max(ind)+1))
			print ('x, y of mouse: {:.2f},{:.2f}'.format(xmouse, ymouse))
			print ('Data point:', x[ind[0]], y[ind[0]])
			print ('\n')

		#Variables initialization
		f , ax1 = plt.subplots()
		legend_list = []
		x_values = np.asarray(self.file_output.probe_vbias.values)

		#Plotting the graphs from the first listbox
		if selected != ():
			for idx in selected:
				y_values = np.asarray(self.node_listbox[idx].values)
				ax1.plot(x_values, y_values, self.node_listbox[idx].color, picker=5)
				legend_list.append(self.node_listbox[idx].name + " current")
			
				ax1.set_ylabel('Current [A]')
				
				ax1.set_ylim(ymin=0)

		ax1.set_xlabel('Bias Voltage [V]')
		f.canvas.mpl_connect('pick_event', on_pick)

		#Plotting the graphs from the second listbox
		if selected2 != ():
			if selected != (): ax2 = ax1.twinx()
			else: ax2 = ax1
			for idx in selected2:
				y_values = np.asarray(self.node_listbox2[idx].values) * x_values
				ax2.plot(x_values, y_values, self.node_listbox2[idx].color, picker=5, linestyle='--')
				if selected == (): legend_list.append(self.node_listbox2[idx].name + " power")
				maxidx = np.argmax(y_values)
				print ("Maximum power point of the {}:\nVoltage: {:.1f}V, Current: {:.1f}A, Power: {:.1f}W\n".format(
					self.node_listbox2[idx].name, x_values[maxidx], self.node_listbox2[idx].values[maxidx], y_values[maxidx]))
			ax2.set_ylabel('Power [W]')
			ax2.set_ylim(ymin=0)
		
		ax1.legend(legend_list, loc='lower left')
		f.show()

		# Saving the plotted data as a CSV file (only from the first listbox !)
		if selected != ():
			path = self.raw_abs_path.split('.raw')[0]
			csv_txt_name = path+"_csv"+".txt"
			txtdata = open(csv_txt_name,"w")
			reader = 'Bias Voltage'
			for idx in selected:
				reader = reader + ', ' + str(self.node_listbox[idx].name + ' Current')
			txtdata.write(reader+"\n")
			for i in range(len(self.node_listbox[0].values)):
				line = str(self.file_output.probe_vbias.values[i])
				for idx in selected:
					line = line + ', ' + str(self.node_listbox[idx].values[i])
				txtdata.write(line)
				txtdata.write("\n")
			txtdata.close
			print ("CSV file were generated with the plotted data: {}".format(csv_txt_name))


	def open_result_file(self):
		#Choose file to open from workspace
		self.raw_abs_path = filedialog.askopenfilename(filetypes = [('raw spice files','.raw'), ('all files','.*') ], title = 'Choose Simulation Result File', parent = self.master, initialdir = self.work_abs_path)
		if self.raw_abs_path == '':
			return
		#Open selected file and extract data
		self.file_output = pvspice.extract_raw_file(self.raw_abs_path)

		#Get file name
		self.stringvar_opened_file.set(self.file_output.name)

		#Construct a list to associate each node to its listbox label
		self.node_listbox = []
		self.node_listbox2 = []
		#Create a closed-loop iterator to associate each plot with a color
		colors = cycle(['r','b','y','g','m','c','k'])

	#Add components to the listbox
		self.listbox.delete(0, END)
		self.listbox2.delete(0, END)
		#current name
		this_color = next(colors)
		self.listbox.insert(END, self.file_output.probe_ibias.name)
		self.node_listbox.append(self.file_output.probe_ibias)
		self.node_listbox[-1].color = this_color
		self.listbox2.insert(END, self.file_output.probe_ibias.name)
		self.node_listbox2.append(self.file_output.probe_ibias)	
		self.node_listbox2[-1].color = this_color	
		#string names
		for probe in self.file_output.probe_strings:
			this_color = next(colors)
			self.listbox.insert(END, probe.name)
			self.node_listbox.append(probe)
			self.node_listbox[-1].color = this_color
			self.listbox2.insert(END, probe.name)
			self.node_listbox2.append(probe)
			self.node_listbox2[-1].color = this_color
		#bypass diode names
		for probe in self.file_output.probe_bypass:
			this_color = next(colors)
			self.listbox.insert(END, probe.name)
			self.node_listbox.append(probe)
			self.node_listbox[-1].color = this_color

	#Routine that actually runs the SPICE simulation
	def run_simulation_routine(self):
		try:
			self.grid
		except AttributeError:
			messagebox.showerror("Error", "Create a grid first")
			return
		#Getting the input file name
		filename = str( self.e_filename.get() )
		filename = filename.replace(' ','')
		if filename == '':
			messagebox.showerror("Error", "Choose a file name first")
			return

		#Creating the folder inside the workspace
		filedir = "workspace\{}\\".format(filename)
		os.makedirs("workspace", exist_ok = True)
		os.makedirs( filedir, exist_ok = True)

		#Creating a new netlist to be executed
		new_netlist = pvspice.netlist(filename)
		circuit = new_netlist.defaultRun( self.grid, self.grid.nserie*(self.grid.parameters.Voc + 1), float( self.e_precision.get() ),
						probe_strings = self.checkbox1.get(), probe_bypassdiode = self.checkbox2.get() )

		#Writting the .cir file
		f = open(filedir + filename + ".cir","w")
		for string in circuit:
			f.write(string+"\n")
		f.close()

		print ("Simulation is running...")
		subprocess.call(["scad3", "-ascii", "-b", "-run", "".join([filedir,filename,".cir"])])
		print ("{}.cir were simulated. Output stored in: {} \n".format(filename, filedir))

		del new_netlist
		del circuit

	#Function that creates the grid of panels from the input values and bypass config.
	def datasheet_apply_function(self):  
		try:
			Ns  = int(self.e_Ns.get())
			Voc = float(self.e_Voc.get())
			Isc = float(self.e_Isc.get())
			Vmp = float(self.e_Vmp.get())
			Imp = float(self.e_Imp.get())
			Kv  = float(self.e_Kv.get())
			Ki  = float(self.e_Ki.get())
			nserie = int(self.e_nserie.get())
			nparallel = int(self.e_nparallel.get())
		except ValueError:
			messagebox.showerror("Error", "Invalid input data")
			return

		print ("Grid of panels creation were successful\n")
		self.grid = pvspice.pvgrid(nserie,nparallel,Voc,Isc,Vmp,Imp,Kv,Ki,Ns)
		self.I0, self.Iph, self.Rs, self.Rsh, self.A = self.grid.parameters.get_parameters(25.0)

		self.e_I0.delete(0, END)
		self.e_I0.insert(0, str(self.I0))
		self.e_Iph.delete(0, END)
		self.e_Iph.insert(0, str(self.Iph))        
		self.e_Rs.delete(0, END)
		self.e_Rs.insert(0, str(self.Rs))        
		self.e_Rsh.delete(0, END)
		self.e_Rsh.insert(0, str(self.Rsh))
		self.e_A.delete(0, END)
		self.e_A.insert(0, str(self.A))

		if len(self.diode_list) != Ns:
			self.diode_list = []
		self.grid.setBypassList(self.diode_list)
		self.last_applied_diode_list = self.diode_list

	#Function that substitutes the model parameters by the generated by the algorithm from pvspice.py
	def panelparameters_generate_function(self):
		try:
			self.grid
		except AttributeError:
			messagebox.showerror("Error", "Create a grid first")
			return

		self.grid.parameters.routine() 
		I0, Iph, Rs, Rsh, A = self.grid.parameters.get_parameters(25.0)

		self.e_I0.delete(0, END)
		self.e_I0.insert(0, str(I0))
		self.e_Iph.delete(0, END)
		self.e_Iph.insert(0, str(Iph))        
		self.e_Rs.delete(0, END)
		self.e_Rs.insert(0, str(Rs))        
		self.e_Rsh.delete(0, END)
		self.e_Rsh.insert(0, str(Rsh))
		self.e_A.delete(0, END)
		self.e_A.insert(0, str(A))

	#Function that overwrites the model parameters with user's input values
	def panelparameters_apply_function(self):
		try:
			self.grid
		except AttributeError:
			messagebox.showerror("Error", "Create a grid first")
			return
		try:
			I0  = float(self.e_I0.get())
			Iph = float(self.e_Iph.get())       
			Rs  = float(self.e_Rs.get())       
			Rsh = float(self.e_Rsh.get())
			A   = float(self.e_A.get())
		except ValueError:
			messagebox.showerror("Error", "Invalid input data")
			return

		self.grid.parameters.manualSetting(I0,Iph,Rs,Rsh,A)
		print ("Model parameters were successfully changed\n")

	#######################################################################
	# This section handles the creation of the "Set Bypass Diode" window #
	#######################################################################
	def window_bypass(self):
		if self.win_bypass_flag == 1 or self.win_grid_flag == 1: #Window already exists 
			return 
		self.win_bypass_flag = 1 #Make sure only one window like this exists
		
		try: #Retrieves number of cells of the module
			n = int(self.e_Ns.get())
		except:
			messagebox.showerror("Error", "Please input a valid number of solar cells")
			self.win_bypass_flag = 0
			return
			
		#Variable initialization
		self.diode_remove = 0
		self.diode_insert = 0
		self.cell_list = {}
		
		#List initialization (diode list for customization)
		#If user changed n, list must be destroyed
		if len(self.diode_list) != n:
			self.diode_list = []
		#If there is no such lists, create them
		if self.diode_list == []:
			for i in range(n):
				self.diode_list.append([0,0,0,0])

		#Create new window
		self.new_window = Toplevel()
		self.new_window.title('Set bypass diodes')
		self.new_window.protocol('WM_DELETE_WINDOW', self.turnoff_bypass_cancel)
		self.new_window.grab_set()

		#Create frame1 (for spinboxes)
		frame1 = LabelFrame(self.new_window, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
		
		#Create frame2 (for solar module interaction)
		frame2 = LabelFrame(self.new_window, bd = 0)
		frame2.grid(row = 1, column = 0)
		
		#Create frame3 (for buttons)
		frame3 = LabelFrame(self.new_window, bd = 0)
		frame3.grid(row = 2, column = 0, padx = 10, pady = 10)
		
		#Sets window in insert bypass diode mode
		def bypass_insert():
			if self.diode_remove == 0 and self.diode_insert == 0:
				self.diode_insert = 1
				self.new_window.config(cursor="cross")
				
			elif self.diode_insert != 2:
				self.diode_remove = 0
				self.diode_insert = 0
				self.new_window.config(cursor="arrow")
 
		#Sets window in remove bypass diode mode
		def bypass_remove():
			if self.diode_remove == 0 and self.diode_insert == 0:
				self.diode_remove = 1
				self.new_window.config(cursor="cross")
			
			elif self.diode_insert != 2:
				self.diode_remove = 0
				self.diode_insert = 0
				self.new_window.config(cursor="arrow")  

		#Buttons
		Button(frame1, text = "Insert", command = bypass_insert).grid(row=0, column=4, padx = 5)        
		Button(frame1, text = "Remove", command = bypass_remove).grid(row=0, column=5, padx = 5)        
		
		Button(frame3, text = "   OK   ", command = self.turnoff_bypass_ok).grid(row=0, column=0, padx = 40)        
		Button(frame3, text = " Cancel ", command = self.turnoff_bypass_cancel).grid(row=0, column=1, padx = 40) 
		
		#Labels
		Label(frame1, text="Bypass diodes: ").grid(row = 0, column = 3, sticky = W)
		Label(frame1, text="         ").grid(row = 0, column = 2)
		Label(frame1, text="Triangles are anodes and vertical bars are cathodes of the bypass diodes").grid(row = 1, column = 0, columnspan = 6)
		
		#Canvas for solar module display
		#Calculate canvas size
		x = int(np.ceil(np.sqrt(n)))
		w = x * 85
		h = int(np.ceil(n/x)) * 65
				
		#Create canvas for solar module display
		self.canvas = Canvas(frame2, height = h, width = w)
		
		def create_bypass_cell_function(id_cell): #Create a light increase or decrease function for a specific cell
			return lambda x: self.bypassDiode(id_cell)
		
		#Create initial distribution of cells and its corresponding texts for irradiance
		#Also associating each cell with a function to allow the (in/de)crement of its irradiance value
		for i in range(n):
			coord_x = 45 + 85*int(i % x)
			coord_y = 35 + 65 * int(i / x)
			#Draw wire from across the cell
			self.canvas.create_line(85*int(i % x), 35 + 65 * int(i / x), 85 + 85*int(i % x), 35 + 65 * int(i / x))
			if i!=(n-1) and ((35 + 65*int(i / x)) != (35 + 65*int((i+1) / x))):
				self.canvas.create_line(85+85*int(i%x), 35+65*int(i/x), 85+85*int(i%x), 65+65*int(i/x), 2+85*int((i+1)%x), 65+65*int(i/x), 2+85*int((i+1)%x), 35+65*int((i+1)/x))
			#For each cell create an image of a cell and a corresponding number text on top of it
			id_cell = self.canvas.create_image(45 + 85*int(i % x), 35 + 65 * int(i / x), image = self.cell_photo)
			id_text = self.canvas.create_text(45 + 85*int(i % x), 35 + 65 * int(i / x), text = str(i+1), fill="white")
			
			#Draws bypassed diodes (if there are any)
			if self.diode_list[i][0] > 0:
				self.diode_list[i][2] = self.canvas.create_polygon(coord_x - 40, coord_y - 12, coord_x - 40, coord_y + 12, coord_x - 25, coord_y)
			if self.diode_list[i][1] > 0:
				self.diode_list[i][3] = self.canvas.create_line(coord_x + 30, coord_y - 12, coord_x + 30, coord_y + 12, width = 2)

			#Dictionary associating each cell with its id
			self.cell_list[id_cell] = i
			
			#Associate canvas image and text to respective diode insertion functions
			self.canvas.tag_bind(id_cell,"<Button-1>", create_bypass_cell_function(id_cell))
			self.canvas.tag_bind(id_cell,"<Button-3>", create_bypass_cell_function(id_cell))
			self.canvas.tag_bind(id_text,"<Button-1>", create_bypass_cell_function(id_cell))
			self.canvas.tag_bind(id_text,"<Button-3>", create_bypass_cell_function(id_cell))
			
		self.canvas.grid(row = 0, column = 0, columnspan = 2) 
			
	#Support function for set bypass diode
	#inserts and removes bypass diodes
	def bypassDiode(self,id): #
		#Insert the anode part of the bypass diode
		if self.diode_insert == 1:
			if self.bypassed_cell(id)[0] == True: #If cell is already bypassed, there is nothing to be done
				self.diode_insert = 0
				self.new_window.config(cursor="arrow")
				return
			#Draws diode anode
			coord = self.canvas.coords(id) 
			self.diode_list[self.cell_list[id]][2] = self.canvas.create_polygon(coord[0] - 40, coord[1] - 12, coord[0] - 40, coord[1] + 12, coord[0] - 25, coord[1])
			self.diode_list[self.cell_list[id]][0] = self.cell_list[id]+1 #This cell now has a bypass diode in parallel
			self.last_diode = self.cell_list[id] #Saves this cell for cathode insertion
			self.diode_insert = 2 #Goes to cathode insertion mode
			return
		 
		#Insert the cathode part of the bypass diode   
		elif self.diode_insert == 2:
			#If the user tries to put the cathode in the wrong way, or in a bypassed cell, or around some bypassed cells...
			if self.cell_list[id] < self.last_diode or self.bypassed_cell(id)[0] == True:
				return
			for i in self.diode_list[self.last_diode + 1 : self.cell_list[id]]:
				if i[0] > 0 or i[1] > 0:
					return 
			#Draws diode cathode
			coord = self.canvas.coords(id)
			self.diode_list[self.cell_list[id]][3] = self.canvas.create_line(coord[0] + 30, coord[1] - 12, coord[0] + 30, coord[1] + 12, width = 2)
			self.diode_list[self.cell_list[id]][1] = self.last_diode+1 #This cell (and all cells after last_diode) now has a bypass diode in parallel      
			#Goes back to normal mode
			self.new_window.config(cursor="arrow")
			self.diode_insert = 0
			return
			
		elif self.diode_remove == 1:
			result = self.bypassed_cell(id)
			if result[0] == True: 
				self.canvas.delete(self.diode_list[result[1]][2])
				self.canvas.delete(self.diode_list[result[2]][3])
				self.diode_list[result[1]][0] = 0
				self.diode_list[result[2]][1] = 0
				
			self.diode_remove = 0
			self.new_window.config(cursor="arrow")
			return

	#Verifies whether a cell is in parallel with any bypass diode
	#In other words, verifies whether the cell has been bypassed already
	def bypassed_cell(self, id):
		bypassed = 0
		count = 0
		for i in self.diode_list: #Goes through bypass diode list                       
			if (i[0] == count+1) and bypassed == 0: #Found the beginning of a bypass connection
				bypassed = 1
				anode = count
				
			if (i[0] == count+1) and bypassed == 2 and self.diode_insert == 2: 
				return False, 0, 0
				 
			if (self.cell_list[id] == count) and (bypassed == 1): #Found given cell
				bypassed = 2
				if self.diode_insert == 2 and self.last_diode == count: 
					return False, 0, 0
				
			if i[1] > 0 and bypassed > 0: #Found the end of a bypass connection                    
				if bypassed == 2 or self.cell_list[id] == count:
					return True, anode, count
				bypassed = 0
				
			count += 1
			
		return False, 0, 0 #The cell is not bypassed
			
	def turnoff_bypass_cancel(self): #Exiting function for the "Light and shadow cells" window
		if self.diode_insert == 2:
			return 
		del self.cell_list    #Cell list is meaningless now
		self.diode_list = []
		self.win_bypass_flag = 0
		self.new_window.destroy()
		print ("All diodes have been removed\n")

		
	def turnoff_bypass_ok(self): #Exiting function for the "Light and shadow cells" window 
		if self.diode_insert == 2:
			return
		del self.cell_list    #Cell list is meaningless now
		self.win_bypass_flag = 0
		self.new_window.destroy()
		print ("Diode list have been updated\n")
	#############################################
	# End of "Set Bypass Diode" window section #
	#############################################

	#######################################################################
	# This section handles the creation of the "Customize Grid" window   #
	#######################################################################
	def window_grid(self):
		#Initialization tests (make sure only one window of this type is open)
		if self.win_grid_flag == 1 or self.win_bypass_flag == 1:
			return
		try:
			self.grid
		except AttributeError:
			messagebox.showerror("Error", "Create a grid first")
			return

		self.win_grid_flag = 1          #Make sure only one window is open
		self.master.withdraw()          #Hide the main window
		n_str = len(self.grid.modules)  #Getting the number of strings

		#Create a new window to display all the strings
		self.new_win_grid = Toplevel()
		self.new_win_grid.title('Grid Customization')
		self.new_win_grid.protocol('WM_DELETE_WINDOW', self.turnoff_grid_cancel)

		#Create frame1 (for intro text)
		frame1 = LabelFrame(self.new_win_grid, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
		
		#Create frame2 (for string selection)
		frame2 = LabelFrame(self.new_win_grid, bd = 0, padx = 10)
		frame2.grid(row = 1, column = 0)
		
		#Create frame3 (for buttons)
		frame3 = LabelFrame(self.new_win_grid, bd = 0)
		frame3.grid(row = 2, column = 0, padx = 10, pady = 10)

		#Frame 1 label, entry, button
		Label(frame1, text="Set grid base temperature and irradiance:").grid(row = 0, column = 0, padx = 10, sticky = E)
		Label(frame1, text="°C").grid(row = 0, column = 2, sticky = W) 
		Label(frame1, text="W/m^2").grid(row = 0, column = 4, sticky = W)

		self.e_temp_grid = Entry(frame1, width = 6)
		self.e_temp_grid.grid(row=0, column=1, padx = 10, sticky=W)
		self.e_temp_grid.insert(0, str( self.grid.temperature ))
		self.e_irrad_grid = Entry(frame1, width = 6)
		self.e_irrad_grid.grid(row=0, column=3, padx = 10, sticky=W)
		self.e_irrad_grid.insert(0, str( self.grid.irradiance ))

		def grid_set_button_function():
			if self.win_panel_flag == 1:
				messagebox.showerror("Error", "Close the panel windows first")
				return
			if self.win_string_flag == 1:
				messagebox.showerror("Error", "Close the string windows first")
				return
			e_temp = float( self.e_temp_grid.get() )
			e_irrad = float( self.e_irrad_grid.get() )
			self.grid.changeGridTemp(e_temp)
			self.grid.changeGridIrrad(e_irrad)
			print ("Grid temperature and irradiance have been modified\n")

		Button(frame1, text = "Set", command = grid_set_button_function).grid(row=0, column=5, padx = 10) 

		#Frame 2 buttons 
		def create_function_window_string(number):  #Lambda function to create the button functions
			return lambda: self.window_string(number)

		for n in range(0,n_str):
			row = n // 15
			col = n % 15
			Button(frame2, text = " String {} ".format(n), command = create_function_window_string(n) ).grid(row=row, column=col, padx = 1, pady=10)  

		#Frame 3 button     
		Button(frame3, text = " Close ", command = self.turnoff_grid_cancel).grid(row=0, column=1, padx = 40) 

	#Close window routine
	def turnoff_grid_cancel(self):
		try:
			self.turnoff_string_cancel()
		except:
			pass
		self.win_grid_flag = 0
		self.master.deiconify()
		self.new_win_grid.destroy()
	#############################################
	# End of "Customize Grid" window section    #
	#############################################

	#######################################################################
	# This section handles the creation of the "String N°#" window        #
	#######################################################################
	def window_string(self,stringnum):
		#Initialization tests (make sure only one window of this type is open)
		if self.win_string_flag == 1:
			return

		self.win_string_flag = 1 	#Make sure only one window is opened

		nserie = len(self.grid.modules[0])	#Retrieve number of modules per string

		#Create a new window to display all the modules inside the string n
		self.new_win_string = Toplevel()
		self.new_win_string.title('String N°{}'.format(stringnum))
		self.new_win_string.protocol('WM_DELETE_WINDOW', self.turnoff_string_cancel)

		#Create frame1 (for intro text)
		frame1 = LabelFrame(self.new_win_string, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
		
		#Create frame2 (for string selection)
		frame2 = LabelFrame(self.new_win_string, bd = 0, padx = 10)
		frame2.grid(row = 1, column = 0)
		
		#Create frame3 (for buttons)
		frame3 = LabelFrame(self.new_win_string, bd = 0)
		frame3.grid(row = 2, column = 0, padx = 10, pady = 10)

		#Frame 1 text
		Label(frame1, text="Select the desired panel").grid(row = 0, column = 0, padx = 10)
		Label(frame1, text="(Panels are connected in serie)").grid(row = 1, column = 0, padx = 10)

		def create_function_window_panel(stringnum,panelnum):  #Lambda function to create the button functions
			return lambda: self.window_panel(stringnum,panelnum)

		#Frame 2 label, entry, button
		for panelnum in range(0,nserie):
			row = panelnum // 15
			col = panelnum % 15
			Button(frame2, text = " Panel {} ".format(panelnum), command = create_function_window_panel(stringnum,panelnum) ).grid(row=row, column=col, padx = 1, pady=10)  

		#Frame 3 button     
		Button(frame3, text = " Close ", command = self.turnoff_string_cancel).grid(row=0, column=1, padx = 40)

	#Close window routine
	def turnoff_string_cancel(self):
		try:
			self.turnoff_panel_cancel()
		except:
			pass
		self.win_string_flag = 0
		self.new_win_string.destroy()
	#############################################
	# End of "String N°#" window function       #
	#############################################


	#######################################################################
	# This function handles the creation of the "Panel N°#" window        #
	#######################################################################
	def window_panel(self,stringnum,panelnum):
		#Initialization tests (make sure only one window of this type is open)
		if self.win_panel_flag == 1:
			return
		self.win_panel_flag = 1

		n_cells = len(self.grid.modules[0][0].cells) 	#Retrieve number of cells per module

		#Create a new window to display all the cells inside the module selected
		self.new_win_panel = Toplevel()
		self.new_win_panel.title('Panel N°{} from String N°{}'.format(panelnum,stringnum))
		self.new_win_panel.protocol('WM_DELETE_WINDOW', self.turnoff_panel_cancel)

		#Create frame1 (for temperature and irrad selection)
		frame1 = LabelFrame(self.new_win_panel, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10, sticky=W+E)
		
		#Create frame1 (for solar cell interaction)
		frame2 = LabelFrame(self.new_win_panel, bd = 0)
		frame2.grid(row = 1, column = 0)
		
		#Create frame3 (for buttons)
		frame3 = LabelFrame(self.new_win_panel, bd = 0)
		frame3.grid(row = 2, column = 0, padx = 10, pady = 10)

		#Frame 1 label, entry, button
		Label(frame1, text="Set panel base temperature and irradiance:").grid(row = 0, column = 0, padx = 10, sticky = E)
		Label(frame1, text="°C").grid(row = 0, column = 2, sticky = W) 
		Label(frame1, text="W/m^2").grid(row = 0, column = 4, sticky = W)

		self.e_temp_panel = Entry(frame1, width = 6)
		self.e_temp_panel.grid(row=0, column=1, padx = 10, sticky=W)
		self.e_temp_panel.insert(0, str(self.grid.modules[stringnum][panelnum].temperature) )
		self.e_irrad_panel = Entry(frame1, width = 6)
		self.e_irrad_panel.grid(row=0, column=3, padx = 10, sticky=W)
		self.e_irrad_panel.insert(0, str(self.grid.modules[stringnum][panelnum].irradiance) )

		#Frame 2
		#Canvas for solar module display
		#Calculate canvas size
		x = int(np.ceil(np.sqrt(n_cells)))
		w = x * 85
		h = int(np.ceil(n_cells/x)) * 65

		#Create canvas for solar module display
		self.canvas2 = Canvas(frame2, height = h, width = w)

		#Function that handles individual cell customization window
		def create_cell_function(stringnum,panelnum,cellnum,text_id,cell_id):
			return lambda x: self.window_cell(stringnum,panelnum,cellnum,text_id,cell_id)

		#Create a list to manage the cells text and image information
		self.id_text_list = []		#List created to allow further changes of the displayed texts
		self.id_cell_list = []		#List created to allow further changes of the displayed cell symbol
		#Create initial distribution of cells and its corresponding functions
		#for customization
		for i in range(n_cells):
			#Initialization of useful values
			this_cell = self.grid.modules[stringnum][panelnum].cells[i]
			canvas_text = "{:.1f}".format(this_cell.irradiance) + "\n" + "{:.1f}".format(this_cell.temperature)
			coord_x = 45 + 85*int(i % x)
			coord_y = 35 + 65 * int(i / x)
			#Draw wire from across the cell
			self.canvas2.create_line(85*int(i % x), 35 + 65 * int(i / x), 85 + 85*int(i % x), 35 + 65 * int(i / x))
			if i!=(n_cells-1) and ((35 + 65*int(i / x)) != (35 + 65*int((i+1) / x))):
				self.canvas2.create_line(85+85*int(i%x), 35+65*int(i/x), 85+85*int(i%x), 65+65*int(i/x), 2+85*int((i+1)%x), 65+65*int(i/x), 2+85*int((i+1)%x), 35+65*int((i+1)/x))
			#For each cell create an image of a cell
			id_cell = self.canvas2.create_image(45 + 85*int(i % x), 35 + 65 * int(i / x), image = self.cell_photo)
			id_text = self.canvas2.create_text(45 + 85*int(i % x), 35 + 65 * int(i / x), text = canvas_text, justify=CENTER, fill="white")
			self.id_text_list.append(id_text)
			self.id_cell_list.append(id_cell)
			#Bind every canvas with a function
			self.canvas2.tag_bind(id_cell,"<Button-1>", create_cell_function(stringnum,panelnum,i,id_text,id_cell))
			self.canvas2.tag_bind(id_cell,"<Button-3>", create_cell_function(stringnum,panelnum,i,id_text,id_cell))
			self.canvas2.tag_bind(id_text,"<Button-1>", create_cell_function(stringnum,panelnum,i,id_text,id_cell))
			self.canvas2.tag_bind(id_text,"<Button-3>", create_cell_function(stringnum,panelnum,i,id_text,id_cell))
			#Draws bypassed diodes (if there are any)
			if self.last_applied_diode_list != []:
				if self.last_applied_diode_list[i][0] > 0:
					self.canvas2.create_polygon(coord_x - 40, coord_y - 12, coord_x - 40, coord_y + 12, coord_x - 25, coord_y)
				if self.last_applied_diode_list[i][1] > 0:
					self.canvas2.create_line(coord_x + 30, coord_y - 12, coord_x + 30, coord_y + 12, width = 2)
			#If the cell has Hotspot, changes the canvas image and displayed text
			if this_cell.hotspot:
				new_canvas_text = 'HotS' + "\n" + "{:.1f}".format(this_cell.temperature)
				self.canvas2.itemconfig(id_text, text=new_canvas_text)		
				self.canvas2.itemconfig(id_cell, image = self.hscell_photo)				
		self.canvas2.grid(row = 0, column = 0, columnspan = 2) 

		#Frame 1: SET button and its function
		def panel_set_button_function():
			e_temp = float( self.e_temp_panel.get() )
			e_irrad = float( self.e_irrad_panel.get() )
			self.grid.modules[stringnum][panelnum].changeModuleTemp(e_temp)
			self.grid.modules[stringnum][panelnum].changeModuleIrrad(e_irrad)
			for cell in self.grid.modules[stringnum][panelnum].cells:
				cell.hotspot = False
				cell.piddefect = False
			for idtext in self.id_text_list:
				canvas_text = "{:.1f}".format(e_irrad) + "\n" + "{:.1f}".format(e_temp)
				self.canvas2.itemconfig(idtext, text=canvas_text)
			for idcell in self.id_cell_list:
				self.canvas2.itemconfig(idcell, image=self.cell_photo)
			print ("Panel N°{} from string N°{} have been modified\n".format(panelnum,stringnum))

		Button(frame1, text = "Set", command = panel_set_button_function).grid(row=0, column=5, padx = 10) 

		#Frame 1: Set diode temperature button
		def create_bypasstemp_function(stringnum,panelnum):
			return lambda: self.window_bypasstemp(stringnum,panelnum)

		Button(frame1, text = "Set Bypass Diode Temperature", command = create_bypasstemp_function(stringnum,panelnum)).grid(row=0, column=6, padx = 10, sticky=E+W) 

		#Frame 3 button     
		Button(frame3, text = " Close ", command = self.turnoff_panel_cancel).grid(row=0, column=1, padx = 40) 
	
	#Close window routine
	def turnoff_panel_cancel(self):
		try:
			self.turnoff_cell_cancel()
			self.turnoff_bypasstemp()
		except:
			pass
		self.win_panel_flag = 0
		self.new_win_panel.destroy()

	#############################################
	# End of "Panel N°#" window function        #
	#############################################
	
	#######################################################################
	# This function handles the creation of the "Cell N°#" window         #
	#######################################################################
	def window_cell(self,stringnum,panelnum,cellnum,text_id,cell_id):
		#Initialization tests (make sure only one window of this type is open)
		if self.win_cell_flag == 1:
			return
		self.win_cell_flag = 1

		#Window creation
		self.new_win_cell = Toplevel()
		self.new_win_cell.title('Cell Window')
		self.new_win_cell.protocol('WM_DELETE_WINDOW', self.turnoff_cell_cancel)

		# 'this_cell' and 'this_panel' are renamings to simplify the code
		this_cell = self.grid.modules[stringnum][panelnum].cells[cellnum] 
		this_panel = self.grid.modules[stringnum][panelnum]

		#Create frame1 
		frame1 = LabelFrame(self.new_win_cell, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
		
		#Create frame2
		frame2 = LabelFrame(self.new_win_cell, bd = 2,relief = GROOVE,text='Manual Setting')
		frame2.grid(row = 1, column = 0, padx=10, pady=10, sticky=N+S+E+W, ipadx=5, ipady=5)
		
		#Create frame3
		frame3 = LabelFrame(self.new_win_cell, bd = 2,relief = GROOVE,text='Hotspot Defect')
		frame3.grid(row = 2, column = 0, padx=10, pady=10, sticky=N+S+E+W, ipadx=5, ipady=5)

		#Create frame4
		frame4 = LabelFrame(self.new_win_cell, bd = 2,relief = GROOVE,text='PID Defect')
		frame3.grid(row = 3, column = 0, padx=10, pady=10, sticky=N+S+E+W, ipadx=5, ipady=5)

		#Create frame5 
		frame5 = LabelFrame(self.new_win_cell, bd = 0)
		frame5.grid(row = 4, column = 0, padx = 10, pady = 10)


		#Frame 1 Labels
		Label(frame1, text="Cell N°{} from Panel N°{} & String N°{}".format(cellnum + 1,panelnum,stringnum)).grid(row=0, column=0)

		#Frame 2 Labels
			#1st column
		Label(frame2, text="Cell temperature:").grid(row = 0, column = 0, padx = 10, sticky = E)
		Label(frame2, text="Cell irradiance:").grid(row = 1, column = 0, padx = 10, sticky = E)
			#3rd column
		Label(frame2, text="°C").grid(row = 0, column = 2, sticky = W) 
		Label(frame2, text="W/m^2").grid(row = 1, column = 2, sticky = W)

		#Frame 2 Entry
			#2nd column
		self.e_temp_cell = Entry(frame2, width = 10)
		self.e_temp_cell.grid(row=0, column=1, padx = 10, sticky=E+W)
		self.e_temp_cell.insert(0, str(this_cell.temperature) )

		self.e_irrad_cell = Entry(frame2, width = 10)
		self.e_irrad_cell.grid(row=1, column=1, padx = 10, sticky=E+W)
		self.e_irrad_cell.insert(0, str(this_cell.irradiance) )

		#Frame 3 (hotspot commands)
		def hotspot_function():		#Function associated to the hotspot checkbox
			if self.checkbox_hotspot.get():
				self.e_temp_cell.configure(state='disabled')
				self.e_irrad_cell.configure(state='disabled')
				self.e_hs_temp.configure(state='normal')
			else:
				self.e_temp_cell.configure(state='normal')
				self.e_irrad_cell.configure(state='normal')
				self.e_hs_temp.configure(state='disabled')

		#Hotspot checkbox
		self.checkbox_hotspot = BooleanVar()
		self.check_hotspot = Checkbutton(frame3, text="Hotspot", variable=self.checkbox_hotspot, command=hotspot_function)
		self.check_hotspot.grid(row=0, column=0, columnspan=3, padx = 10, sticky=W)

		#Hotspot labels
		Label(frame3, text="Hotspot temperature:").grid(row = 1, column = 0, padx = 10, sticky = E)
		Label(frame3, text="°C").grid(row = 1, column = 2, sticky = W)
		
		#Hotspot temperature entry
		self.e_hs_temp = Entry(frame3, width = 10)
		self.e_hs_temp.grid(row=1, column=1, padx = 10, sticky=E+W)
		self.e_hs_temp.insert(0, str(this_cell.temperature))
		self.e_hs_temp.configure(state='disabled')

		#Frame 4 Apply button
		def cell_apply_button(cell,text_id):
			this_cell.hotspot = self.checkbox_hotspot.get()			
			if self.checkbox_hotspot.get():
				temperature = float( self.e_hs_temp.get() )
				irradiance = this_panel.irradiance * ( 1 - (np.sqrt( (temperature - this_panel.temperature)/300.0 ) / this_panel.parameters.Isc) )
				this_cell.temperature = temperature
				this_cell.irradiance = irradiance
				canvas_text = 'HotS' + "\n" + "{:.1f}".format(temperature)
				self.canvas2.itemconfig(text_id, text=canvas_text)		
				self.canvas2.itemconfig(cell_id, image = self.hscell_photo)		
			else:
				temperature = float( self.e_temp_cell.get() )
				irradiance = float( self.e_irrad_cell.get() )
				this_cell.temperature = temperature
				this_cell.irradiance = irradiance
				canvas_text = "{:.1f}".format(irradiance) + "\n" + "{:.1f}".format(temperature)
				self.canvas2.itemconfig(text_id, text=canvas_text)	
				self.canvas2.itemconfig(cell_id, image = self.cell_photo)
	
			self.turnoff_cell_cancel()

		def create_cell_apply_button(cell,text_id):
			return lambda: cell_apply_button(cell,text_id)

		Button(frame5, text = "Apply Changes", command = create_cell_apply_button(this_cell,text_id)).grid(row=0, column=0, pady = 10)

		#Refreshing the checkbox in case the cell is already hotspotted
		if this_cell.hotspot==True:
			self.check_hotspot.invoke()
			self.check_hotspot.select()

	def turnoff_cell_cancel(self):
		self.win_cell_flag = 0
		self.new_win_cell.destroy()
	#############################################
	# 	End of "Cell N°#" window function       #
	#############################################

	####################################################################################
	# This function handles the creation of the "Set Bypass Temperature" window        #
	####################################################################################
	def window_bypasstemp(self,stringnum,panelnum):
		if self.win_bypasstemp_flag == 1:
			return
		self.win_bypasstemp_flag = 1

		self.new_win_bypasstemp = Toplevel()
		self.new_win_bypasstemp.title('Bypass Diode Temperature')
		self.new_win_bypasstemp.protocol('WM_DELETE_WINDOW', self.turnoff_bypasstemp)

		this_panel = self.grid.modules[stringnum][panelnum]

		#Create frame1
		frame1 = LabelFrame(self.new_win_bypasstemp, bd = 0)
		frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
		
		#Create frame2
		frame2 = LabelFrame(self.new_win_bypasstemp, bd = 2,relief = GROOVE)
		frame2.grid(row = 1, column = 0, padx=10, pady=10, sticky=N+S+E+W)

		#Create frame3 
		frame3 = LabelFrame(self.new_win_bypasstemp, bd = 0)
		frame3.grid(row = 4, column = 0, padx = 10, pady = 10)

		#Frame2 Labels, list of entries
		e_bypasstemp_list = []
		for idx,j in enumerate(this_panel.diode_temp):
			Label(frame2, text="Bypass number {}:".format(idx)).grid(row = idx, column = 0, padx = 10, sticky = E)
			e_bypasstemp_list.append(Entry(frame2, width = 10))
			e_bypasstemp_list[idx].grid(row=idx, column=1, padx = 10, sticky=E+W)
			e_bypasstemp_list[idx].insert(0, str(this_panel.diode_temp[idx]) )

		#Frame3 apply button
		def bypasstemp_apply_button(panel,entry_list):
			for idx,entry in enumerate(entry_list):
				try:
					new_temp = float( entry.get() )
				except ValueError:
					return
				panel.diode_temp[idx] = new_temp
			self.turnoff_bypasstemp()

		def create_bypasstemp_apply_button(panel,entry_list):
			return lambda: bypasstemp_apply_button(panel,entry_list)

		Button(frame3, text = "Apply Changes", command = create_bypasstemp_apply_button(this_panel,e_bypasstemp_list)).grid(row=0, column=0, pady = 10)		

	def turnoff_bypasstemp(self):
		self.win_bypasstemp_flag = 0
		self.new_win_bypasstemp.destroy()
	##########################################################
	# End of "Set Bypass Temperature" window function        #
	##########################################################

	def restore_default_values(self):
		#Cleaning current grid of panels
		try:
			del self.grid
		except AttributeError:
			pass
		#Cleaning current values
		self.e_Ns.delete(0, END)
		self.e_Voc.delete(0, END)
		self.e_Isc.delete(0, END)
		self.e_Vmp.delete(0, END)
		self.e_Imp.delete(0, END)
		self.e_Kv.delete(0, END)
		self.e_Ki.delete(0, END)
		self.e_nserie.delete(0, END)
		self.e_nparallel.delete(0, END)
		##
		self.e_I0.delete(0, END)
		self.e_Iph.delete(0, END)        
		self.e_Rs.delete(0, END)      
		self.e_Rsh.delete(0, END)
		self.e_A.delete(0, END)
		#Insert default values
		self.e_Ns.insert(0, '72')
		self.e_Voc.insert(0, '43.5')
		self.e_Isc.insert(0, '3.45')
		self.e_Vmp.insert(0, '35')   
		self.e_Imp.insert(0, '3.15')
		self.e_Kv.insert(0, '-0.152')
		self.e_Ki.insert(0, '0.0014')
		self.e_nserie.insert(0, '1')
		self.e_nparallel.insert(0, '1')


	def save_parameters(self): # *** Save current parameters to a file
		os.makedirs("workspace", exist_ok = True)
		f = filedialog.asksaveasfile(mode='w', initialfile='parameters.txt', title="Choose file to save simulations parameters", filetypes=[('all files', '.*'), ('text files', '.txt')], initialdir = self.work_abs_path)
		
		if f == None:
			return
		f.write( 'SolarSim datasheet values file\n' )
		#Save datasheet parameters
		f.write( self.e_Ns.get() + '\n' )
		f.write( self.e_Voc.get() + '\n' )
		f.write( self.e_Isc.get() + '\n' )
		f.write( self.e_Vmp.get() + '\n' )
		f.write( self.e_Imp.get() + '\n' )
		f.write( self.e_Kv.get() + '\n' )
		f.write( self.e_Ki.get() + '\n' )
		f.write( self.e_nserie.get() + '\n' )
		f.write( self.e_nparallel.get() + '\n' )
		#Save bypass diode list
		for element in self.diode_list:
			f.write( str(element) + '\n' )
		#Close file
		f.close()


	def load_parameters(self): # *** Load parameters from a file
		os.makedirs("workspace", exist_ok = True)
		f = filedialog.askopenfile(mode='r', initialfile='parameters.txt', title="Choose file containing simulations parameters", filetypes=[('all files', '.*'), ('text files', '.txt')], initialdir = self.work_abs_path)
		
		if f == None:
			return
		try:    
			line = f.readline().rstrip('\n')
		except:
			messagebox.showerror("Error", "Error reading file.")
			return
			
		if line != 'SolarSim datasheet values file': #Reader is different from what it should be
			messagebox.showerror("Error", "Wrong file type or invalid data")
			return

		#Cleaning current values
		self.e_Ns.delete(0, END)
		self.e_Voc.delete(0, END)
		self.e_Isc.delete(0, END)
		self.e_Vmp.delete(0, END)
		self.e_Imp.delete(0, END)
		self.e_Kv.delete(0, END)
		self.e_Ki.delete(0, END)
		self.e_nserie.delete(0, END)
		self.e_nparallel.delete(0, END)
		
		#Insert default values
		line = f.readline().rstrip('\n')
		self.e_Ns.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Voc.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Isc.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Vmp.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Imp.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Kv.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_Ki.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_nserie.insert(0, line)
		line = f.readline().rstrip('\n')
		self.e_nparallel.insert(0, line)

		#Reading the new diode_list
		self.diode_list = []
		line = f.readline().rstrip('\n') 		#DO
		while line != '':						#WHILE
			line = line.replace('[','')
			line = line.replace(']','')
			line = line.split(',')

			diode_list_line = []
			for charc in line:
				diode_list_line.append(int(charc))
			self.diode_list.append(diode_list_line)

			line = f.readline().rstrip('\n')	#REFRESH

		f.close()

	def about(self): #Information about the developers of the program
		messagebox.showinfo("About", "This program has been developed by João Carlos Cerqueira, \
student of electrical engineering at the State University of Campinas (Unicamp), under guidance of \
Ladislava Černa, PhD student at the photovoltaics lab at the electrotechnology department of \
České Vysoké Učení Technické v Praze (ČVUT). Copyright (c) 2016 - João Carlos Cerqueira - jc.cerqueira13@gmail.com. \n \
The GUI of this software were based on the software SolarSim, developed by Pedro Tabacof (tabacof@gmail.com).")
	
	def license(self): #License: GNU GPL v3.0 (free software)
		messagebox.showinfo("License", "GNU GENERAL PUBLIC LICENSE Version 3.0, June 2007")
	
	def help(self): #Some useful information for a beginner
		messagebox.showinfo("Help", "Read the documentation that comes with the software. If the problem could not be solved, contact the developer through the e-mail: jc.cerqueira13@gmail.com")

	def quit_all(self): #Exiting function for the program
		self.cell.close_figures()
		root.quit()
		exit()

#Start window and enter main loop
root = Tk()
window = Window(root)
root.mainloop()