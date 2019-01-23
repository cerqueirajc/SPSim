"""	
This file is a macro for running simulations
on the software LTSpice oriented to PV cells.

Autor: João Carlos Cerqueira  FEEC/Brazil , CTU/Prague
Email: jc.cerqueira13@gmail.com
Jan/2016 - Prague

Copyright (c) 2016 - João Carlos Cerqueira - jc.cerqueira13@gmail.com
GNU GENERAL PUBLIC LICENSE Version 3.0, June 2007
"""

from os import system
import os.path
import numpy as np

""" class gausspv: 
		 	Implementation of an algorithm for estimation of the PV panel
		equivalent circuit (one diode, with series and shunt resistances), based
		on the article "Gauss-Seidel Iteration Based Parameter Estimation for a 
		Single Diode Model of a PV Module", S. Shongwe, M. Hanif.
			The model follows the equation bellow:

		I = Iph - I0*[exp( (V+Rs*I)/(Ns*Vt) ) - 1] - (V+Rs*I)/(Rsh)
				where: Vt = A*k*T/q
					   k = Boltzmann's constant
					   q = electron charge
					   T = temperature (K)
					   A = diode ideality constant  """
class gausspv:
	def __init__(self,Voc,Isc,Vmp,Imp,Kv,Ki,Ns,stdtemp):	#All the input values must be STC datasheet values
		#Physical constants
		self.k = 1.38064852e-23		#Boltzmann constant
		self.q = 1.60217662e-19		#Electron charge
		self.kelvin = 273.15		#Celsius to Kelvin

		#Datasheet values
		self.Voc  = Voc
		self.Isc  = Isc
		self.Vmp  = Vmp
		self.Imp  = Imp
		self.Kv   = Kv
		self.Ki	  = Ki
		self.Pmax  = Vmp*Imp
		self.Ns   = Ns
		self.stdtemp = stdtemp + self.kelvin
		self.stdtempC = stdtemp

		#Execution of the routine to calculate the parameters
		self.routine()

	def manualSetting(self,I0,Iph,Rs,Rsh,A):			#function used to set the values manually
		self.I0 = I0
		self.Iph = Iph
		self.Rs = Rs
		self.Rsh = Rsh
		self.Rsh2 = Rsh
		self.Vt = A*self.k*self.stdtemp/self.q
		self.parameters_dic = {}

	def calcExpression(self,V,I):
		I2 = self.Iph - self.I0*( np.exp((V+I*self.Rs)/(self.Ns*self.Vt)) - 1 ) - (V + I*self.Rs)/(self.Rsh)
		return I2

	def iterVt(self,Voc,Isc,Vmp,Imp,Rs,Rsh,Ns):			#evaluation of expression (20)
		try:
			ln2 = np.log( (Isc*Rsh + Isc*Rs - Voc - Vmp - Imp*Rs - Imp*Rsh)/(Isc*Rsh + Isc*Rs - Voc) )
			Vt2 = ( Vmp + Imp*Rs - Voc )/( Ns*ln2 )
		except:
			Vt2 = 0.032
		return Vt2

	def iterRs(self,Voc,Isc,Vmp,Imp,Rs,Rsh,Ns,Vt):		#evaluation of expression (23)
		ln1 = np.log( (Ns*Vt*Rsh*Imp - Ns*Vt*Vmp + Ns*Vt*Imp*Rs)/(Vmp*Isc*Rsh + Vmp*Isc*Rs - Vmp*Voc + Imp*Rs*Voc - Imp*Rs*Isc*Rs - Imp*Rs*Rsh*Isc) )
		Rs2 = ( Voc - Vmp + Ns*Vt*ln1 )/Imp
		return Rs2

	def iterRsh(self,Voc,Isc,Vmp,Imp,Rs,Rsh,Ns,Vt):		#evaluation of expression (26)
		Rsh2 = ( Ns*Vt*Rsh + (Rs*Isc*Rsh + Rs*Isc*Rs - Rs*Voc)*np.exp( (Isc*Rs - Voc)/(Ns*Vt) ) + Ns*Vt*Rs ) / ( (Isc*Rsh + Isc*Rs - Voc)*np.exp( (Isc*Rs - Voc)/(Ns*Vt) ) + Ns*Vt )
		return Rsh2

	def iterI0(self,Voc,Isc,Rs,Rsh,Ns,Vt):				#evaluation of expression (14)
		I02 = ( Isc*Rsh + Isc*Rs - Voc )/(Rsh*np.exp( Voc/(Ns*Vt) ))
		return I02

	def iterIph(self,Voc,Rsh,Ns,Vt,I0):					#evaluation of expression (3)
		Iph2 = I0*( np.exp(Voc/(Ns*Vt)) - 1 ) + Voc/Rsh
		return Iph2

	#  The following function is a second way to evaluate Rsh, used to improve the algorithm,
	#used only on the end of the iterative part of the algorithm
	def iterRsh2(self,Vmp,Imp,Rs,Ns,Vt,I0,Iph,Pmax):	
		d = Vmp*Iph - Vmp*I0*np.exp( (Vmp + Imp*Rs)/(Ns*Vt) ) + Vmp*I0 - Pmax
		n = Vmp*( Vmp + Imp*Rs )
		Rsh3 = n/d
		return Rsh3

	def calcError(self):								#function used to determine a stop criteria
		errorVt = (self.Vt - self.VtA)/self.Vt
		errorRs = (self.Rs - self.RsA)/self.Rs
		errorRsh = (self.Rsh - self.RshA)/self.Rsh

		self.RsA  = self.Rs
		self.VtA  = self.Vt
		self.RshA = self.Rsh

		if (errorVt < 0.000001) and (errorRs < 0.000001) and (errorRsh < 0.000001):
			return True
		else:
			return False

	def routine(self):				#iterative routine
		#Parameters to be estimated:
		self.Rs   = 0
		self.Rsh  = 5000
		self.Vt   = self.iterVt(self.Voc,self.Isc,self.Vmp,self.Imp,self.Rs,self.Rsh,self.Ns)
		self.Io   = None
		self.Iph  = None

		#Initialization of convergence check variables:
		self.RsA  = self.Rs
		self.VtA  = self.Vt
		self.RshA = self.Rsh

		#Refreshing dictionary
		self.parameters_dic = {}

		niter = 100000
		for i in range(niter):
						
			self.Rsh = self.iterRsh(self.Voc,self.Isc,self.Vmp,self.Imp,self.Rs,self.Rsh,self.Ns,self.Vt)
			self.Rs = self.iterRs(self.Voc,self.Isc,self.Vmp,self.Imp,self.Rs,self.Rsh,self.Ns,self.Vt)
			self.Vt = self.iterVt(self.Voc,self.Isc,self.Vmp,self.Imp,self.Rs,self.Rsh,self.Ns)

			if self.calcError() == True:
				self.I0 = self.iterI0(self.Voc,self.Isc,self.Rs,self.Rsh,self.Ns,self.Vt)
				self.Iph = self.iterIph(self.Voc,self.Rsh,self.Ns,self.Vt,self.I0)
				self.Rsh2 = self.iterRsh2(self.Vmp,self.Imp,self.Rs,self.Ns,self.Vt,self.I0,self.Iph,self.Pmax)
				return True

		self.I0 = self.iterI0(self.Voc,self.Isc,self.Rs,self.Rsh,self.Ns,self.Vt)
		self.Iph = self.iterIph(self.Voc,self.Rsh,self.Ns,self.Vt,self.I0)
		self.Rsh2 = self.iterRsh2(self.Vmp,self.Imp,self.Rs,self.Ns,self.Vt,self.I0,self.Iph,self.Pmax)
		return False

	# This is the function used to retrieve the circuit parameters for any desired temperature
	def get_parameters(self,temp):
		temperature = temp + self.kelvin

		if temperature in self.parameters_dic:
			return self.parameters_dic[temperature]
		else:
			Vt2  = self.Vt * temperature / self.stdtemp
			Iph2 = self.Iph +  self.Ki * (temperature - self.stdtemp)
			
			Voc2 = self.Voc + self.Kv * (temperature - self.stdtemp)
			Isc2 = self.Isc + self.Ki * (temperature - self.stdtemp)
			I02 = self.iterI0(Voc2,Isc2,self.Rs,self.Rsh,self.Ns,Vt2)
			A = Vt2*self.q/(self.k*self.stdtemp)

			self.parameters_dic[temperature] = [I02, Iph2, self.Rs, self.Rsh2, A]
			
			return [I02, Iph2, self.Rs, self.Rsh2, A]

""" class pvcell is the class that represents each cell. It has its own temperature and irradiance,
	problems (hotspot, PID), reference number (number within module, module's number, string's number),
	positive and negative nodes. """
class pvcell:
	def __init__(self,param_source,row,column,number):
		#Cell parameters
		self.parameters = param_source
		self.temperature = self.parameters.stdtempC
		self.irradiance = 1000.0
		self.Ns = self.parameters.Ns
		self.hotspot = False
		self.piddefect = False

		#Circuit references
		self.row = row
		self.column = column
		self.number = number
		self.node0 = "S{}P{}N{}".format(self.row, self.column, self.number)
		self.node1 = "S{}P{}N{}".format(self.row, self.column, self.number + 1)
		self.cell_name = "S{}P{}N{}".format(self.row, self.column, self.number)

	def changeCellTemp(self,new_temp):		#method used to change the cell temperature
		self.temperature = new_temp

	def writeCommandLine(self):				#method used to obtain the SPICE equivalent circuit with the cell's conditions
		self.I0, self.Iph, Rs, Rsh, self.A = self.parameters.get_parameters(self.temperature) # <-- usage of the "get_parameters" method
		self.Rs = Rs / self.Ns
		self.Rsh = Rsh / self.Ns
		cellcircuit = ( "xcell{cellname} {node0} {node1} cell_py params: irrad={irrad} i0={i0} iph={iph} rs={rs} rsh={rsh} a={a} ktq={ktq} ns={ns}".format(
					cellname = self.cell_name,
					node0 = self.node0,
					node1 = self.node1,
					irrad = self.irradiance,
					i0 = self.I0,
					iph = self.Iph,
					rs = self.Rs,
					rsh = self.Rsh,
					a = self.A,
					ktq = 1.0,
					ns = 1.0 ) )
		return cellcircuit

""" class pvmodule is the class that represents each module. It has its own reference number 
	(module's number, string's number), positive and negative nodes, list of bypass diode, list
	of bypass diode's temperature and a list containing its cells. Note that it has a reference
	temperature	and irradiance, although each cell may have its individual values. """
class pvmodule:
	def __init__(self,param_source,row,column):
		self.parameters = param_source
		self.row = row
		self.column = column
		self.cells = []
		self.temperature = self.parameters.stdtempC
		self.irradiance = 1000.0
		self.diode_list = None
		self.diode_temp = []

		#Creating the module's cells
		for i in range(self.parameters.Ns):
			self.cells.append(pvcell(self.parameters,self.row,self.column,i))

		self.node0 = None
		self.node1 = None

	def set_node0(self,n0):			#method used to set the first node of the module
		self.cells[0].node0 = n0
		self.node0 = n0

	def set_node1(self,n1):			#method used to set the second node of the module
		self.cells[-1].node1 = n1
		self.node1 = n1

	def changeModuleTemp(self,new_temp):	#method used to set the module's temperature (and its bypasses and cells)
		self.temperature = new_temp
		for cell in self.cells:
			cell.changeCellTemp(new_temp)
		for i in range(len(self.diode_temp)):
			self.diode_temp[i] = new_temp  

	def changeModuleIrrad(self,new_irrad):	#method used to set the module's irradiance	(changing all its cells)
		self.irradiance = new_irrad
		for cell in self.cells:
			cell.irradiance = new_irrad

	def writeDiodeCircuit(self,probebypass):	#method used to write the bypass diode spice circuit
		if self.diode_list == None or len(self.diode_list) != len(self.cells):
			return []
		else:
			diode_circuit = []
			i = 0
			num = 0
			node_a = None
			node_b = None
			for diode in self.diode_list:
				if diode[0]>0:
					node_a = i
				if diode[1]>0:
					node_b = i
					new_line = "dbypass_S{row}P{column}N{number} {node0} {node1} Dbypass temp={diodetemp}".format(
						number = num,
						column = self.column,
						row = self.row,
						node0  = self.cells[node_a].node0,
						node1  = self.cells[node_b].node1,
						diodetemp = self.diode_temp[num] )
					diode_circuit.append(new_line)
					if probebypass:
						probe_line = ".probe I(dbypass_S{}P{}N{})".format(self.row,self.column,num)
						diode_circuit.append(probe_line)
					num = num + 1
				i = i + 1
			return diode_circuit
	
	def writeModuleCircuit(self,probebypass):  	#	  Method used to obtain the module's spice circuit. Note that this function 
		modulecircuit = []						#	basically calls the method "writeCommandLine(self)" for each of its cells
		for cell in self.cells:					#	and adds the bypass diodes
			modulecircuit.append( cell.writeCommandLine() )
		modulecircuit = modulecircuit + self.writeDiodeCircuit(probebypass)
		return modulecircuit


""" class pvgrid is the class that represents the whole PV system. It has its own reference temperature and irradiance,
	a list of modules, the number of modules in parallel and in series. It also initializes the parameters object from 
	the	"gausspv" class. It always initializes on the STC (25°C 1000W/m^2) """
class pvgrid:
	def __init__(self,nserie,nparallel,Voc,Isc,Vmp,Imp,Kv,Ki,Ns):
		self.nserie = nserie
		self.nparallel = nparallel
		self.modules = []
		self.irradiance = 1000.0
		self.temperature = 25.0

		self.parameters = gausspv(Voc,Isc,Vmp,Imp,Kv,Ki,Ns,self.temperature)


		#Creating the grid's modules
		for i in range(self.nparallel):
			self.modules.append([])
			for j in range(self.nserie):
				self.modules[i].append(pvmodule(self.parameters,i,j))

		#Setting the correct nodes
		for i in range(nparallel):
			for j in range(nserie-1):
				node = "Grid_{}_{}".format(i,j+1)
				self.modules[i][j].set_node1(node)
				self.modules[i][j+1].set_node0(node)
			self.modules[i][0].set_node0("Grid_{}_{}".format(i,0))
			self.node0 = "0"
			self.node1 = "Vb"
			self.modules[i][-1].set_node1(self.node1)

	def changeGridTemp(self,temp):		#method used to change the grid temperature (including panels and its cells)
		self.temperature = temp 
		for string in self.modules:
			for module in string:
				module.changeModuleTemp(temp)

	def changeGridIrrad(self,new_irrad):	#method used to change the grid irradiance (including panels and its cells)
		self.irradiance = new_irrad 
		for string in self.modules:
			for module in string:
				module.changeModuleIrrad(new_irrad)

	def setBypassList(self, diodelist):	#method used to set the bypass list of all the grid's modules
		count = 0
		for element in diodelist:
			if element != [0,0,0,0]:
				count = count+1
		diodecount = int(count / 2)

		self.diode_list = diodelist
		for string in self.modules:
			for module in string:
				module.diode_list = diodelist
				module.diode_temp.clear()
				for i in range(diodecount):
					module.diode_temp.append(module.temperature)

	def writeAllComponents(self,probebypass,probestrings):  #method that returns the spice circuit of the whole grid
		components = []		#Initializing the output circuit text
		for idx, string in enumerate(self.modules):
		#Adding a small series resistance to be able to probe the strings current			
			components.append("rprobe_S{string} {node0} {node1} 0.000001".format(
					string= idx,
					node0= 0,
					node1= self.modules[idx][0].node0) )
			if probestrings:
				components.append(".probe I(rprobe_S{})".format(idx))
		#Writing for each module the correspondent circuit text
			for module in string:		
				components = components + module.writeModuleCircuit(probebypass)
			components.append("")
		return components


""" This is the class that implements a netlist object, which contains the SPICE circuit that will be simulated.
	The circuit is composed of each of the module's cells, the bypass diodes, the bias voltage source, resistances
	in series with the strings for measurements, and also the simulation commands that will be executed, such as 
	voltage precision, which currents and voltages will be probed, and so on. The netlist is divided in three: 
	reader, components and dot commands """
class netlist:
	def __init__(self,filename):
		self.filename = filename
		self.reader = []

		self.reader.append("* This file was generated by the simulation tool PVPY")
		self.reader.append("* File name: {}".format(filename) )
		self.reader.append("*   The circuit temperature config from LTspice is always set to 25° since the temperature effects")
		self.reader.append("*  have already been taken into account during the parameters generation.\n")
		self.reader.append(".include cell_component_py.lib")

		self.component = []
		self.dcommands = []

	def addComponent(self,comp):
		if type(comp) == type(" "):
			self.component.append(comp)
		if type(comp) == type([" "]):
			self.component = self.component + comp

	def addDotCommand(self,command,*argv):
		self.dcommands.append( ".{}".format(command) )
		for argm in argv:
			argument = " {}".format(argm)
			self.dcommands[-1] = "".join([self.dcommands[-1], argument])

	def clearComponent(self):
		self.component = []

	def clearDotCommand(self):
		self.dcommands = []

	def buildNetlist(self):
		list1 = self.reader + [""] + self.component + [""] + self.dcommands
		list1.append(".end")
		return list1

	def defaultRun(self,grid,upperv,precision, probe_strings=True, probe_bypassdiode=True):
		self.clearComponent()
		self.clearDotCommand()

		self.addComponent(grid.writeAllComponents(probe_bypassdiode,probe_strings))
		self.addComponent("vbias {node1} {node0} {value}".format( node1 = grid.node1, node0 = grid.node0, value = "0" ) )
		
		""" The temperature of the circuit is always kept on 25°C since the temp effects has already been considered during
		the parameters generation of each cell, and the temperature of each bypass diode are configured one by one during
		its declaration. """	
		self.addDotCommand("temp","25")			

		""" Dbypass is the name given to the model of the bypass diode. The information that follows are the configurations
		of an schottky diode, usually used as bypass diodes for PV modules. Parameters may be adapted to different models
		if the values are known """
		self.addDotCommand("model","Dbypass","D(IS=3.47597e-05 RS=0.00960369 N=1.28962 EG=0.428428 XTI=5 BV=45 IBV=0.0002 CJO=1e-11 VJ=0.7 M=0.5 FC=0.5 TT=0 KF=0 AF=1)")
		
		""" I(Vbias) is the current that flows through the bias voltage souce"""
		self.addDotCommand("probe", "I(Vbias)")
		self.addDotCommand("dc","vbias",0,str(upperv),str(precision))

		txt = self.buildNetlist()
		return txt

""" This is a class associated to the extract_raw_file. It is a container for the data extracted from the
	simulation output. The values are store in the "self.values" attribute"""
class node_value_class:
	def __init__(self,name,node_type,node_number):
		self.name = name
		self.node_type = node_type
		self.node_number = node_number
		self.values = []
		self.get_node_unit()
		self.color = 'b'

	def get_node_unit(self):
		if "current" in self.node_type:
			self.unit = "A"
		elif "voltage" in self.node_type:
			self.unit = "V"


""" Reads in the .raw file and collects the value info, storing them indiciviually in a 
	node value class. It divides the data in four different kinds: the bias voltage, the current
	of the bias voltage source, string current and the bypass diode current.
		This class has four important attributes as output:
		self.probe_vbias, self.probe_ibias, self.probe_strings, self.probe_bypass  """
class extract_raw_file:	
	def __init__(self,raw_filepath):
		self.nodes = []
		self.raw_filepath = raw_filepath

		#Open file for reading
		f = open(self.raw_filepath,"r")
		self.raw_file_lines = f.readlines()
		self.name = os.path.basename(f.name)  #Get file name without path
		f.close()

		#Check if file is ok
		try:
			("LTspice" in self.raw_file_lines[7])
		except:
			raise TypeError('The choosen file is not LTspice output')

		# Execute the two routines associated with the data reading. For futher understandment, see a .raw output
		#file from any simulation done by the software.
		self.get_data()
		self.sort_node_type()


	def get_data(self):
		#Getting number of variables
		words = self.raw_file_lines[4].split()
		self.num_var = words[2]
		#Getting number of points
		words = self.raw_file_lines[5].split()
		self.num_points = words[2]
		#Getting variable names, types and values
		Variables = False
		Values = False
		for line in self.raw_file_lines[8:]:
			if "Values" in line:
				Values = True
				Variables = False
				continue	#exits the loop to read next line

			if "Variables" in line:
				Values = False
				Variables = True
				continue	#exits the loop to read next line

			if Variables == True:
				number, name, node_type = line.split()
				self.nodes.append( node_value_class( name.lower(), node_type.lower(), int(number) ) )			

			if Values == True:
				words = line.split()
				if len(words) == 2:
					self.nodes[0].values.append( float(words[1]) )
					count = 1
				else:
					self.nodes[count].values.append( float(words[0]) )
					count = count + 1

	# 	Identification and sorting of the different types of data 
	#(four types: bias voltage, grid current, string's currents and bypasses' current)
	def sort_node_type(self):
		self.probe_strings = []
		self.probe_bypass = []

		### inside-method function
		def find_string_number(name):
			split1 = name.split('s')[1]
			str_n = split1.split(')')[0]
			return int(str_n)
		### inside-method function
		def find_bypass_number(name):
			split1 = name.split('s')[-1]
			str_n = split1.split('p')[0]
			split2 = split1.split('p')[1]
			panel_n = split2.split('n')[0]
			split3 = split2.split('n')[1]
			bypass_n = split3.split(')')[0]
			return int(str_n),int(panel_n),int(bypass_n)
		
		for node in self.nodes:
			name = node.name.lower()
			if "i(v" in name:
				self.probe_ibias = node
				self.probe_ibias.name = 'Grid'
			elif "vbias" in name:
				self.probe_vbias = node
			elif "rprobe" in name:
				self.probe_strings.append(node)
				str_n = find_string_number(name)
				self.probe_strings[-1].name = 'String n°{}'.format(str_n)
			elif "i(d" in name:
				self.probe_bypass.append(node)
				str_n, panel_n, bypass_n = find_bypass_number(name)
				self.probe_bypass[-1].name = 'Bypass N°{} from S.{},P.{}'.format(bypass_n,str_n,panel_n)
		del self.nodes

### END OF CLASSES ###


if __name__ == "__main__":
	nserie = 1
	nparallel = 1
	Voc = 43.5
	Isc = 3.45
	Vmp = 35
	Imp = 3.15
	Kv = -0.152
	Ki = 0.0014
	Ns = 72
	temp = 25

	grid1 = pvgrid(nserie,nparallel,Voc,Isc,Vmp,Imp,Kv,Ki,Ns,temp)
	grid1.setBypassList(diodelist1)
	nl = netlist("teste5")
	grid1.changeGridTemp(60)
	grid1.changeGridIrrad(800)

	circuit = nl.defaultRun(grid1,nserie*(Voc+1),nserie*(Voc+1)/100)
	#print (circuit)
	print ( grid1.parameters.get_parameters(temp) )
	print ( grid1.parameters.get_parameters(60) )
	print ( grid1.modules[0][0].cells[0].Rs )
	"""
	grid1.cells[0][0].irradiance = 1000
	grid1.cells[0][0].changeTemp(50)
	grid1.cells[0][1].changeTemp(50)
	grid1.cells[1][0].changeTemp(50)
	grid1.cells[1][1].changeTemp(50)
	nl = netlist("teste4")
	circuit = nl.defaultRun(grid1,nserie*(Voc+1),0.1)
	"""
	f = open("teste7.cir","w")
	for string in circuit:
		f.write(string+"\n")
	f.close


	"""
	grid1 = cellgrid(2,1,1,2,3,4,5,6,7,8,9)
	nl1 = netlist("test1")
	line1 = grid1.cells[0][0].writeCommandLine()
	print (line1)

	#nl1.addDotCommand("dc",0,0.7,0.01)
	#nl1.addComponent(grid1.writeAllComponents())
	list1 = nl1.defaultRun(grid1,2,0.01)
	print (list1)
	f = open("test2.cir","w")
	for string in list1:
		f.write(string+"\n")
	f.close
	"""
	#system("scad3.exe -ascii -b -run teste3.cir")