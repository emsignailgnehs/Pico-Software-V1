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
    
    we0I = numpy.loadtxt(open(filepath+"WE0"+str(picoNumber)+".csv", "rb"), delimiter=",",usecols=range(numberOfScans))
    we0V = numpy.loadtxt(open(filepath+"WE"+str(picoNumber)+"V.csv", "rb"), delimiter=",",usecols=range(numberOfScans))
    we2I = numpy.loadtxt(open(filepath+"WE2"+str(picoNumber)+".csv", "rb"), delimiter=",",usecols=range(numberOfScans))
    if not Path(filepath+"SortedDataTwoE.csv").is_file():
        with open(filepath+'SortedDataTwoE.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE1','','','WE3','','','Chip'])
            header.writerow(['Avg I (nA)','Avg Baseline (nA)','Avg V (V)','Avg I (nA)','Avg Baseline (nA)','Avg V (V)'
            ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)'])

    if not Path(filepath+"BaselinePeakTwoE.csv").is_file():
        with open(filepath+'BaselinePeakTwoE.csv', 'w', newline='') as csvfile:
            header = csv.writer(csvfile, delimiter=',')
            header.writerow(['WE1','','','WE3'])
            header.writerow(['Peak I (A)','Baseline (A)','Peak V (V)','Peak I (A)','Baseline (A)','Peak V (V)'])

    plt.ion()
    baselinePeakCSV = []
    plt.figure(picoNumber)
    plt.title("IV Curve: Pico " + str(picoNumber))
    for i in range(0,numberOfScans):
        we0 = numpy.array([we0V[:,i], we0I[:,i]])
        we2 = numpy.array([we0V[:,i], we2I[:,i]])

        nstd = 3.1
        peakwidth = 0.25; #not used any more - taken care of automatically in fitpeak
        minpot = -1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        maxpot = .1; # not necessary any more - peakfitting is robust enough to not require chopping of the edges
        
        ''' WE0 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = myfit.myfitpeak(we0)
        
        baselineatpeak = getBaselinePeak(xforfit,baseline,peakvoltage)
        baselinerowWE0 = [peakcurrent,baselineatpeak,peakvoltage]
        
        # Plot and annotate 
        plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
        [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
        plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))
        plt.pause(0.05)
        plt.draw()

        ''' WE2 '''
        xnotjunk,ynotjunk,xforfit,gauss,baseline,peakcurrent,peakvoltage,fiterror = myfit.myfitpeak(we2)
        
        baselineatpeak = getBaselinePeak(xforfit,baseline,peakvoltage)
        baselinerowWE2 = [peakcurrent,baselineatpeak,peakvoltage]

        # Plot and annotate 
        plt.plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,
        [peakvoltage, peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent])
        plt.annotate(str(peakcurrent),(peakvoltage,baselineatpeak+peakcurrent))

        # Append to matrix
        baselinePeakCSV.append(baselinerowWE0+baselinerowWE2)
        plt.pause(0.05)
        plt.draw()

    '''Sort data and store. Then write to each csv. '''
    scale = 10**9
    baseSort = numpy.array(baselinePeakCSV)
   
    # AVG peak current, baseline, and peak voltage
    # for each electrode (takes last three out of 5 scans)
    avgPeakCurrent0 = sum(baseSort[len(baseSort)-3:len(baseSort),0])/3
    avgPeakCurrent2 = sum(baseSort[len(baseSort)-3:len(baseSort),3])/3

    avgbaseline0 = sum(baseSort[len(baseSort)-3:len(baseSort),1])/3
    avgbaseline2 = sum(baseSort[len(baseSort)-3:len(baseSort),4])/3

    avgPeakVoltage0 = sum(baseSort[len(baseSort)-3:len(baseSort),2])/3
    avgPeakVoltage2 = sum(baseSort[len(baseSort)-3:len(baseSort),5])/3

    # Make row vector  for each electrode
    e0 = [avgPeakCurrent0*scale, avgbaseline0*scale, avgPeakVoltage0]
    e2 = [avgPeakCurrent2*scale, avgbaseline2*scale, avgPeakVoltage2]
    
    # Avg chip current, baseline, and voltage
    chipCurrent = ((e0[0]+e2[0])/3)
    chipBaseline = ((e0[1]+e2[1])/3)
    chipVoltage = ((e0[2]+e2[2])/3)

    # Make row vector for chip
    chip = [chipCurrent, chipBaseline, chipVoltage]

    sortedCSV = [e0+ e2 + chip]

    with open(filepath+'SortedDataTwoE.csv', 'a', newline='') as csvfile:
            data = csv.writer(csvfile)
            data.writerows(sortedCSV)

    with open(filepath+'BaselinePeakTwoE.csv', 'a', newline='') as csvfile:
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
    
#peakDetection(1,"C:\\Users\\rup96\\Desktop\\Aptitude\\Pico\\Pico Lab\\Software\\peakProgram\\",5)