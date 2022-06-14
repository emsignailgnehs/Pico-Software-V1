from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import Checkbutton
import picoScript
import threading
from threading import Thread
import GUIconfig
from pathlib import Path
    
root_folder = Path(__file__).parent.absolute()
class Root(Tk):

    def __init__(self):
        super(Root, self).__init__()
        self.title("Python Tkinter Dialog Widget")
        self.minsize(640, 400)
        self.config = GUIconfig.load_dict(f'{root_folder}/config.json')
 
        # Create frames and place grids for labels and entries
        self.gridLayout()

        self.labelFrame = LabelFrame(self, text = "Open File")
        self.labelFrame.grid(column = 1, row = 9, padx = 20, pady = 20)
        self.button()
        
        self.electrodeOption()
        self.scans()
        self.fluidFillButton()
    
    def load_config(self):
        filename = filedialog.askopenfilename(initialdir = root_folder, title = 'Select the ".json" config file', filetype = [('json file', '*.json')])
        self.config = GUIconfig.load_dict(filename)
        self.update_fields()

    def save_config(self):
        savename = filedialog.asksaveasfilename(initialdir = root_folder, title = 'Save the config as json file', filetype = [('json file', '*.json')])
        savename = savename.replace('.json', '') + '.json'
        GUIconfig.save_dict(savename, self.config)

    def update_fields(self):
        self.E1.delete(0, END)
        self.E2.delete(0, END)
        self.E3.delete(0, END)
        self.E4.delete(0, END)
        self.E5.delete(0, END)
        self.E6.delete(0, END)

        self.E1.insert(0, self.config["t equilibration"])
        self.E2.insert(0, self.config["E begin"])
        self.E3.insert(0, self.config["E end"])
        self.E4.insert(0, self.config["E step"])
        self.E5.insert(0, self.config["Amplitude"])
        self.E6.insert(0, self.config["Frequency"])
    
    def gridLayout(self):
        # Create each label and entry we want
        self.L1 = Label(self, text="t equilibration")
        self.L1.grid(row=0, sticky="E")
        self.E1 = Entry(self, bd =5)
        self.E1.grid(column=1, row=0)

        self.L2 = Label(self, text="E begin")
        self.L2.grid(row=1, sticky="E")
        self.E2 = Entry(self, bd =5)
        self.E2.grid(column=1, row=1)

        self.L3 = Label(self, text="E end")
        self.L3.grid(row=2, sticky="E")
        self.E3 = Entry(self, bd =5)
        self.E3.grid(column=1, row=2)

        self.L4 = Label(self, text="E step")
        self.L4.grid(row=3, sticky="E")
        self.E4 = Entry(self, bd =5)
        self.E4.grid(column=1, row=3)

        self.L5 = Label(self, text="Amplitude")
        self.L5.grid(row=4, sticky="E")
        self.E5 = Entry(self, bd =5)
        self.E5.grid(column=1, row=4)

        self.L6 = Label(self, text="Frequency")
        self.L6.grid(row=5, sticky="E")
        self.E6 = Entry(self, bd =5)
        self.E6.grid(column=1, row=5)
        
        self.filepath = ""
        self.btn = Button(self,text="Write File!", command=self.writeFile)
        self.btn.grid(column=0, row=6, columnspan=2)

        self.update_btn = Button(self,text="Load Config", command=self.load_config)
        self.update_btn.grid(column=0, row=7, columnspan=2)

        self.saveconfig_btn = Button(self,text="Save Config", command=self.save_config)
        self.saveconfig_btn.grid(column=0, row=8, columnspan=2)

        self.L7 = Label(self, text="Enter Number of Picos")
        self.L7.grid(row=6,column=2, sticky="NSWE")
        self.PicoNumber = Entry(self, bd=5)
        self.PicoNumber.grid(column=3, row=6)
        self.PicoNumber.insert(END,"1")

        self.Run = Button(self,text="Run",command=lambda: self.runScript(self.PicoNumber.get(),
        self.filepath,self.var.get(),self.numberOfScans.get(),self.FFVar.get()),height = 1, width = 10)
        self.Run.grid(column=4,row=6,columnspan=2)

        self.update_fields()     
 
    def button(self):
        self.button = Button(self.labelFrame, text = "Browse Directory",command = self.fileDialog)
        self.button.grid(column = 1, row = 1)

    def electrodeOption(self):
        self.var = StringVar(self)
        self.var.set("One Electrode Scan") # Default value
        self.electrodeOptionMenu = OptionMenu(self, self.var,"One Electrode Scan", "Three Electrode Scan", 
        "Continuous","Two Electrode Scan","Two Electrode Scan (Alternating)")
        self.electrodeOptionMenu.grid(column=2,row=1,columnspan=2)
    
    def scans(self):
        self.scanLabel = Label(self, text="Enter Number of Scans")
        self.scanLabel.grid(column=2,row=2)

        self.numberOfScans = Entry(self, bd=5)
        self.numberOfScans.insert(END, "5")
        self.numberOfScans.grid(column=3,row=2)

    def fluidFillButton(self):
        self.FFVar = BooleanVar()
        self.FFButton = Checkbutton(self, text="9 Chip Fluid Fill", variable=self.FFVar).grid(column=2,row=3, sticky=W)

    def fileDialog(self):
        self.filepath = filedialog.askdirectory(title = "Select A Directory")
        self.label = Label(self.labelFrame, text = "")
        self.label.grid(column = 1, row = 2)
        self.label.configure(text = self.filepath)

    def writeFile(self):
        if(self.filepath != ""):
            fileFF = open(self.filepath+"\\FF.txt",'w')
            header = ["e\n","var c\n","var p\n","var f\n","var g\n","set_pgstat_chan 0\n","set_pgstat_mode 0\n","set_pgstat_chan 1\n","set_pgstat_mode 3\n"]

            bw = "set_max_bandwidth " + str(int(self.E6.get())*8) #bandwidth
            pr = "set_pot_range " + self.pot_range_helper(int(self.E2.get()),int(self.E3.get()),int(self.E5.get())) #potential range
            cr = "set_cr 7375n" #current range set to default
            ar = "set_autoranging 7375n 7375n" #autoranging set to defualt
            cell_on = "cell_on"

            measurementSeq = "meas_loop_swv p c f g " + self.E2.get() +"m " + self.E3.get() + "m " + self.E4.get() + "m " \
                + self.E5.get() + "m " + self.E6.get() # Sequence for measurement
            body = [bw+"\n",pr+"\n",cr+"\n",ar+"\n",cell_on+"\n", measurementSeq+"\n"]

            footer = ["pck_start\n", "pck_add p\n", "pck_add c\n", "pck_end\n", "endloop\n", "on_finished:\n","cell_off\n\n"]
            fileFF.writelines(header)
            fileFF.writelines(body)
            fileFF.writelines(footer)
            fileFF.close() 

            for WE in range(0,3):
                if(WE == 0):
                    file1 = open(self.filepath+"\\SWV_on_10kOhmW0.txt",'w') 
                elif(WE == 1):
                    file1 = open(self.filepath+"\\SWV_on_10kOhmW1.txt",'w') 
                else:
                    file1 = open(self.filepath+"\\SWV_on_10kOhmW2.txt",'w') 
                # write header, body, and footer to file
                header = ["e\n","var c\n","var p\n","var f\n","var g\n","set_pgstat_chan 1\n","set_pgstat_mode 0\n","set_pgstat_chan 0\n","set_pgstat_mode 3\n"]

                if(WE == 0):
                    gpioCFG = "set_gpio_cfg 96 1\nset_gpio 0i" #WE0
                elif(WE == 1):
                    gpioCFG = "set_gpio_cfg 96 1\nset_gpio 32i" #WE1
                else:
                    gpioCFG = "set_gpio_cfg 96 1\nset_gpio 64i" #WE2
                
                body = [bw+"\n",pr+"\n",cr+"\n",ar+"\n",gpioCFG+"\n",cell_on+"\n", measurementSeq+"\n"]

                file1.writelines(header)
                file1.writelines(body)
                file1.writelines(footer)
                file1.close() 
            messagebox.showinfo("Complete", "Scripts written!")
        else:
            messagebox.showerror("Error", "Valid Directory Must Be Set!")

    def pot_range_helper(self, begin, end, amplitude):
        '''
            This function will get the proper potential range from
            the given begin, end, and amplitude voltages (all in millivolts)
            and return the string contained the range.

        '''
        pr=""
        if(begin > end):
            y = -2*amplitude + end
            if y == 0:
                pr = "0 " + str(begin) + "m"
            else:
                pr = str(y) + "m " + str(begin) + "m"
        elif(end > begin):
            y = 2*amplitude + end
            if y == 0:
                pr = str(begin) + "m 0"
            else:
                pr = str(begin) + "m " + str(y) + "m"

        return pr
    
    def runScript(self, numberOfPicos, filepath, electrodeOption, numberOfScans,FF):
        self.config = GUIconfig.save_dict(f'{root_folder}/config.json', self.config)
        picoScript.script(numberOfPicos,filepath+"/",electrodeOption,numberOfScans,str(FF))

root = Root()
root.mainloop()