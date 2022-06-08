import numpy
import fitPeak
from pathlib import Path
import csv
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import time
from PIL import Image
import random
import os

def peakDetection(picoNumber,filepath,numberOfScans):

    if not Path(filepath+"SortedDataContinuous.csv").is_file():
        with open(filepath+'SortedDataContinuous.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['','WE2','','','Chip'])
            header.writerow(['Time','Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
            ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

    if not Path(filepath+"BaselinePeakContinuous.csv").is_file():
        with open(filepath+'BaselinePeakContinuous.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['','WE2','',''])
            header.writerow(['Time','Peak I (A)','Baseline (A)','Peak V (V)'])
    # Check if previous raw files exist 
    files = [i for i in os.listdir(filepath) if os.path.isfile(os.path.join(filepath,i)) and \
         'WE1 ' in i]
    
    plt.ion()
    baselinePeakCSV = []
    timeTracker = []
    plt.figure(picoNumber)
    plt.title("IV Curve: Pico " + str(picoNumber))
    for i in range(len(files),len(files)+numberOfScans):
        V = None
        I = None
        
        while(not Path(filepath+"WE"+str(picoNumber)+" "+str(i)+".csv").is_file()):
            pass
        electrode = numpy.genfromtxt(open(filepath+"WE"+str(picoNumber)+" "+str(i)+".csv"), dtype=None,names = ['timestamp','I','V'],delimiter=",",skip_header=1)
        
        timeStamp = electrode['timestamp']
        I = electrode['I']
        V = electrode['V']  
        
        we1 = numpy.array([V, I])
        nstd = 3.1
        peakwidth = 0.25; #not used any more - taken care of automatically in fitpeak
        minpot = -1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        maxpot = .1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges

        ''' WE1 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = fitPeak.fitpeak(we1,nstd,peakwidth,minpot,maxpot)
        
        baselineatpeak = baseline[math.ceil((len(baseline)-1)/2)]
        baselinerowWE1 = [timeStamp[-1].decode("utf-8"),peakcurrent[0],baselineatpeak,peakvoltage]

        # Plot and annotate 
        timeTracker.append(timeStamp[-1].decode("utf-8"))
        plt.plot(i-len(files),peakcurrent,'ro')
        plt.xticks(range(i-len(files)+1),timeTracker)
        #plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))
        plt.pause(0.05)
        plt.draw()

        # Append to matrix
        baselinePeakCSV.append(baselinerowWE1)
        
        with open(filepath+'BaselinePeakContinuous.csv', 'a', newline='') as csvfile:
                data = csv.writer(csvfile)
                
                data.writerow(baselinerowWE1) #use row here because baselinePeakCSV is used for sorted data at end of scans

    '''Sort data and store. Then write to each csv. '''
    scale = 10**9
    baseSort = numpy.array(baselinePeakCSV)
    # AVG peak current, baseline, and peak voltage
    # for each electrode (takes last three out of 5 scans)
    avgPeakCurrent1 = sum([float(i) for i in baseSort[len(baseSort)-3:len(baseSort),1]])/3

    avgbaseline1 = sum([float(i) for i in baseSort[len(baseSort)-3:len(baseSort),2]])/3

    avgPeakVoltage1 = sum([float(i) for i in baseSort[len(baseSort)-3:len(baseSort),3]])/3

    # Make row vector  for each electrode
    e1 = [timeStamp[-1].decode("utf-8"), avgPeakCurrent1*scale, avgbaseline1*scale, avgPeakVoltage1]

    sortedCSV = [e1]

    with open(filepath+'SortedDataContinuous.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(sortedCSV)

           
    # Plot curves
    plt.show()

#peakDetection(1,"C:\\Users\\rup96\\Desktop\\peakProgram\\",5)