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
            we0I = numpy.loadtxt(open(filepath+"WE0.csv", "rb"), delimiter=",")
            we0V = numpy.loadtxt(open(filepath+"WE0V.csv", "rb"), delimiter=",")
            we1I = numpy.loadtxt(open(filepath+"WE1.csv", "rb"), delimiter=",")
            we2I = numpy.loadtxt(open(filepath+"WE2.csv", "rb"), delimiter=",")
            
    elif(picoNumber == 2):
            we0I = numpy.loadtxt(open(filepath+"WE02.csv", "rb"), delimiter=",")
            we0V = numpy.loadtxt(open(filepath+"WE02V.csv", "rb"), delimiter=",")
            we1I = numpy.loadtxt(open(filepath+"WE12.csv", "rb"), delimiter=",")
            we2I = numpy.loadtxt(open(filepath+"WE22.csv", "rb"), delimiter=",")

    if not Path(filepath+"SortedData.csv").is_file():
        with open(filepath+'SortedData.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE1','','','WE2','','','WE3','','','Chip'])
            header.writerow(['Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
            ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)','Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
            ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

    if not Path(filepath+"BaselinePeak.csv").is_file():
        with open(filepath+'BaselinePeak.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE1', '','','WE2','','','WE3'])
            header.writerow(['Peak I (A)','Baseline (A)','Peak V (V)','Peak I (A)',
            'Baseline (A)','Peak V (V)','Peak I (A)','Baseline (A)','Peak V (V)'])

    plt.ion()
    baselinePeakCSV = []
    plt.figure(picoNumber)
    plt.title("IV Curve: Pico " + str(picoNumber))
    for i in range(0,numberOfScans):
        we0 = numpy.array([we0V[:,i], we0I[:,i]])
        we1 = numpy.array([we0V[:,i], we1I[:,i]])
        we2 = numpy.array([we0V[:,i], we2I[:,i]])
        nstd = 3.1
        peakwidth = 0.25; #not used any more - taken care of automatically in fitpeak
        minpot = -1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        maxpot = .1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        
        ''' WE0 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = fitPeak.fitpeak(we0,nstd,peakwidth,minpot,maxpot)
        
        baselineatpeak = baseline[math.ceil((len(baseline)-1)/2)]
        baselinerowWE0 = [peakcurrent[0],baselineatpeak,peakvoltage]
        
        # Plot and annotate 
        plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
        [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
        plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))
        plt.pause(0.05)
        plt.draw()
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
        ''' WE2 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = fitPeak.fitpeak(we2,nstd,peakwidth,minpot,maxpot)
        
        baselineatpeak = baseline[math.ceil((len(baseline)-1)/2)]
        baselinerowWE2 = [peakcurrent[0],baselineatpeak,peakvoltage]

        # Plot and annotate 
        plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
        [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
        plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))

        # Append to matrix
        baselinePeakCSV.append(baselinerowWE0+baselinerowWE1+baselinerowWE2)
        plt.pause(0.05)
        plt.draw()

    '''Sort data and store. Then write to each csv. '''
    scale = 10**9
    baseSort = numpy.array(baselinePeakCSV)
    # AVG peak current, baseline, and peak voltage
    # for each electrode (takes last three out of 5 scans)
    avgPeakCurrent0 = sum(baseSort[len(baseSort)-3:len(baseSort),0])/3
    avgPeakCurrent1 = sum(baseSort[len(baseSort)-3:len(baseSort),3])/3
    avgPeakCurrent2 = sum(baseSort[len(baseSort)-3:len(baseSort),6])/3

    avgbaseline0 = sum(baseSort[len(baseSort)-3:len(baseSort),1])/3
    avgbaseline1 = sum(baseSort[len(baseSort)-3:len(baseSort),4])/3
    avgbaseline2 = sum(baseSort[len(baseSort)-3:len(baseSort),7])/3

    avgPeakVoltage0 = sum(baseSort[len(baseSort)-3:len(baseSort),2])/3
    avgPeakVoltage1 = sum(baseSort[len(baseSort)-3:len(baseSort),5])/3
    avgPeakVoltage2 = sum(baseSort[len(baseSort)-3:len(baseSort),8])/3

    # Make row vector  for each electrode
    e0 = [avgPeakCurrent0*scale, avgbaseline0*scale, avgPeakVoltage0]
    e1 = [avgPeakCurrent1*scale, avgbaseline1*scale, avgPeakVoltage1]
    e2 = [avgPeakCurrent2*scale, avgbaseline2*scale, avgPeakVoltage2]
    
    # Avg chip current, baseline, and voltage
    chipCurrent = ((e0[0]+e1[0]+e2[0])/3)
    chipBaseline = ((e0[1]+e1[1]+e2[1])/3)
    chipVoltage = ((e0[2]+e1[2]+e2[2])/3)

    # Make row vector for chip
    chip = [chipCurrent, chipBaseline, chipVoltage]

    sortedCSV = [e0 + e1 + e2 + chip]

    with open(filepath+'SortedData.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(sortedCSV)

    with open(filepath+'BaselinePeak.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(baselinePeakCSV)
            
    # Plot curves
    plt.show()
    ##randNum = random.randint(0,10000)
    #savedFigure = filepath+"Pico"+str(picoNumber)
    #plt.savefig(savedFigure)
    
    #plt.close()
    #im = Image.open(savedFigure+".png")
    #im.show()
    
#peakDetection(1,"C:\\Users\\rup96\\Desktop\\peakProgram\\")