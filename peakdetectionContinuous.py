import numpy
import myfit
from pathlib import Path
import csv
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import time
import random
import os
import asyncio
import sys

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

def peakdetectionContinuous(picoNumber,filepath,numberOfScans):
    print(picoNumber)
    picoNumber = int(picoNumber)
    numberOfScans = int(numberOfScans)
    if not Path(filepath+"SortedDataContinuous.csv").is_file():
        with open(filepath+'SortedDataContinuous.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['','WE2','',''])
            header.writerow(['Time','Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

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
            continue
        time.sleep(0.01)
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
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = myfit.myfitpeak(we1)
        
        baselineatpeak = getBaselinePeak(xforfit,baseline,peakvoltage)
        baselinerowWE1 = [timeStamp[-1].decode("utf-8"),peakcurrent,baselineatpeak,peakvoltage]

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


def main():
    peakdetectionContinuous(sys.argv[1],sys.argv[2],sys.argv[3])

if __name__ == "__main__":
    main()
#peakDetection(1,"C:\\Users\\rup96\\Desktop\\peakProgram\\",5)