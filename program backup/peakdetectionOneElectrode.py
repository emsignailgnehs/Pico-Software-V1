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

def peakDetection(picoNumber,filepath,numberOfScans):
    if(picoNumber == 1):
            we0V = numpy.loadtxt(open(filepath+"WE0V.csv", "rb"), delimiter=",")
            we1I = numpy.loadtxt(open(filepath+"WE1.csv", "rb"), delimiter=",")
            
    else:
            we0V = numpy.loadtxt(open(filepath+"WE0"+str(picoNumber)+"V.csv", "rb"), delimiter=",")
            we1I = numpy.loadtxt(open(filepath+"WE1"+str(picoNumber)+".csv", "rb"), delimiter=",")

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
        nstd = 3.1
        peakwidth = 0.25; #not used any more - taken care of automatically in fitpeak
        minpot = -1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        maxpot = .1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges

        ''' WE1 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = fitPeak.fitpeak(we1,nstd,peakwidth,minpot,maxpot)
        
        baselineatpeak = baseline[math.ceil((len(baseline)-1)/2)]
        baselinerowWE1 = [peakcurrent[0],baselineatpeak,peakvoltage]

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
    