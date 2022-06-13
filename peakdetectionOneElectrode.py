import numpy
import myfit
from pathlib import Path
import csv
import math
import matplotlib
import matplotlib.pyplot as plt
import time
import random
import tkinter as tk
from tkinter import filedialog
matplotlib.use("TkAgg")

def slope_intercept(x1,y1,x2,y2):
    a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1
    return a,b

def getBaselinePeak(baselineX, baselineY,xaty):
    if(type(baselineX) == int):
        return 0
    slope,intercept = slope_intercept(baselineX[0],baselineY[0],baselineX[1],baselineY[1])
    y = slope*xaty + intercept
    return y

def peakDetection(picoNumber,filepath,numberOfScans):
    we0V = numpy.loadtxt(open(filepath+"WE"+str(picoNumber)+"V.csv", "rb"), delimiter=",",usecols=range(numberOfScans))
    we1I = numpy.loadtxt(open(filepath+"WE"+str(picoNumber)+".csv", "rb"), delimiter=",",usecols=range(numberOfScans))

    if not Path(filepath+"SortedDataOneE.csv").is_file():
        with open(filepath+'SortedDataOneE.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE2','','','Chip'])
            header.writerow(['Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
            ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

    if not Path(filepath+"BaselinePeakOneE.csv").is_file():
        with open(filepath+'BaselinePeakOneE.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE2','',''])
            header.writerow(['Peak I (A)','Baseline (A)','Peak V (V)'])

    plt.ion()
    baselinePeakCSV = []
    plt.figure(picoNumber)
    plt.title("IV Curve: Pico " + str(picoNumber))
    for i in range(0,numberOfScans):
        we1 = numpy.array([we0V[:,i], we1I[:,i]])

        ''' WE1 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = myfit.myfitpeak(we1)

        baselineatpeak = getBaselinePeak(xforfit,baseline,peakvoltage)
        baselinerowWE1 = [peakcurrent,baselineatpeak,peakvoltage]
        # Plot and annotate
        plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
        [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
        plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))
        plt.pause(0.05)
        plt.draw()

        # Append to matrix
        baselinePeakCSV.append(baselinerowWE1)

    '''Sort data and store. Then write to each csv. '''
    scale = 10**9
    baseSort = numpy.array(baselinePeakCSV)
    # AVG peak current, baseline, and peak voltage
    # for each electrode (takes last three out of 5 scans)
    avgPeakCurrent1 = sum(baseSort[len(baseSort)-3:len(baseSort),0])/3

    avgbaseline1 = sum(baseSort[len(baseSort)-3:len(baseSort),1])/3

    avgPeakVoltage1 = sum(baseSort[len(baseSort)-3:len(baseSort),2])/3

    # Make row vector  for each electrode
    e1 = [avgPeakCurrent1*scale, avgbaseline1*scale, avgPeakVoltage1]

    sortedCSV = [e1]

    with open(filepath+'SortedDataOneE.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(sortedCSV)

    with open(filepath+'BaselinePeakOneE.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(baselinePeakCSV)

    # Plot curves
    plt.show()

if __name__ == '__main__':
    import re

    def ui_getfilenames(_filetype = ''):
        """
        _filetype is "a list" of "tuples":

        [
        ('filetype1', '*.extension'),
        ('filetype2', '*.extension'), ...
        ]

        """
        root = tk.Tk() # pointing root to Tk() to use it as Tk() in program.
        root.withdraw() # Hides small tkinter window.
        root.attributes('-topmost', True) # Opened windows will be active. above all windows despite of selection.

        if _filetype == '':
            filez = filedialog.askopenfilenames(parent=root, title='Choose all the files to read')
        else:
            filez = filedialog.askopenfilenames(parent=root, title='Choose all the files to read', filetypes = _filetype)

        # return [repr(filename) for filename in filenames]
        return list(root.tk.splitlist(filez))

    filenames = ui_getfilenames([('comma separated values', '*.csv')])
    filepath = '/'.join(filenames[0].split('/')[:-1]) + '/'

    sorted_files = {}
    for filename in filenames:
        file_id = re.findall(r'.*/(WE\d)[V]*\.csv', filename)[0]
        try:
            sorted_files[file_id] += [filename]
        except KeyError:
            sorted_files[file_id] = [filename]

    for key in sorted_files.keys():
        file = sorted_files[key]
        numberOfScans = 5

        we0V = numpy.loadtxt(open(file[1], "rb"), delimiter=",",usecols=range(numberOfScans))
        we1I = numpy.loadtxt(open(file[0], "rb"), delimiter=",",usecols=range(numberOfScans))

        if not Path(filepath+"SortedDataOneE.csv").is_file():
            with open(filepath+'SortedDataOneE.csv', 'w', newline='') as csvfile:
                header = csv.writer(csvfile, delimiter=',')
                header.writerow(['WE2','','','Chip'])
                header.writerow(['Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
                ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

        if not Path(filepath+"BaselinePeakOneE.csv").is_file():
            with open(filepath+'BaselinePeakOneE.csv', 'w', newline='') as csvfile:
                header = csv.writer(csvfile, delimiter=',')
                header.writerow(['WE2','',''])
                header.writerow(['Peak I (A)','Baseline (A)','Peak V (V)'])

        plt.ion()
        baselinePeakCSV = []
        plt.figure(key)
        plt.title("IV Curve: Pico " + str(key))
        for i in range(0,numberOfScans):
            we1 = numpy.array([we0V[:,i], we1I[:,i]])

            ''' WE1 '''
            xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = myfit.myfitpeak(we1)

            baselineatpeak = getBaselinePeak(xforfit,baseline,peakvoltage)
            baselinerowWE1 = [peakcurrent,baselineatpeak,peakvoltage]
            # Plot and annotate
            plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
            [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
            plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))
            plt.pause(0.05)
            plt.draw()

            # Append to matrix
            baselinePeakCSV.append(baselinerowWE1)

        '''Sort data and store. Then write to each csv. '''
        scale = 10**9
        baseSort = numpy.array(baselinePeakCSV)
        # AVG peak current, baseline, and peak voltage
        # for each electrode (takes last three out of 5 scans)
        avgPeakCurrent1 = sum(baseSort[len(baseSort)-3:len(baseSort),0])/3

        avgbaseline1 = sum(baseSort[len(baseSort)-3:len(baseSort),1])/3

        avgPeakVoltage1 = sum(baseSort[len(baseSort)-3:len(baseSort),2])/3

        # Make row vector  for each electrode
        e1 = [avgPeakCurrent1*scale, avgbaseline1*scale, avgPeakVoltage1]

        sortedCSV = [e1]

        with open(filepath+'SortedDataOneE.csv', 'a', newline='') as csvfile:
                data = csv.writer(csvfile)
                data.writerows(sortedCSV)

        with open(filepath+'BaselinePeakOneE.csv', 'a', newline='') as csvfile:
                data = csv.writer(csvfile)
                data.writerows(baselinePeakCSV)

        # Plot curves
        plt.show()
        plt.savefig(filepath + key + '.svg')
#peakDetection(1,"C:\\Users\\rup96\\Desktop\\Aptitude\\Pico\\Pico Lab\\Software\\peakProgram\\",5)
