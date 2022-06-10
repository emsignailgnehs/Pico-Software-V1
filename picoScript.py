import subprocess
import peakdetection
import peakdetectionOneElectrode
import peakdetectionContinuous
import peakdetectionTwoElectrode
import time
import asyncio
import os
from multiprocessing import Process
'''
    This script will run the measurement .exe and plot via matlab.

    To run this script:
    1. You can find python versions here: https://www.python.org/downloads/ NOTE: The python used in this
    script is 3.6.8. Run the .exe and it will prompt you to install. Before clicking install, please check
    the box that says "add to PATH". 

    2. Download python extension for visual studio code (not necessary if you do not care to have an IDE)

    3. Open MATLAB and run the command matlabroot in the command window. At a Windows operating system prompt
    type the following two commands: (NOTE: You will insert your matlabroot path)
    cd "<matlabroot>\extern\engines\python"
    python setup.py install

    4. Go back to your MATLAB instance and type matlab.engine.shareEngine in MATLAB command window (NOTE:
    Do not terminate MATLAB) NOTE: Skip this step if you will not be using matlab for data processing.

    5. Change path in visual studio measurement code (this is only done in initial setup).
    Change exePath and filePath as specified below

    6. Either click green button on upper right to run script or cd to the path where this file resides and
    type: python picoScipt.py
'''
#NOTE: If you want to make changes to measurement program then you must change in visual studio and run program
#  (note: you do not have to perform an actual measurement just let the program run through to the end)
#NOTE: before running the program open matlab and run command matlab.engine.shareEngine in matlab terminal

def wait_task(task):
    task.wait()

def kill_task(task):
    task.kill()

def script(numberOfPicos, filePath, electrodeOption, numberOfScans, FF):
    # You will only change exePath during inital setup
    exePath = "C:\\Users\\aptitude\\Desktop\\Pico Software V1\\MethodSCRIPTExamples_C#\\MSConsoleExample\\bin\\Debug\\MSConsoleExample.exe"
    # CHANGE filePath TO THE FOLDER YOU WANT TO DROP THE RAW FILES 
    #filePath = "C:\\Users\\rup96\\Desktop\\peakProgram\\"

    tasks = []
    for i in range(1, int(numberOfPicos) + 1):
        # This path is for the .exe of the measurement code
        tasks.append(subprocess.Popen([exePath,str(i),filePath,electrodeOption, numberOfScans,FF]))
        time.sleep(0.10)
    # output = subprocess.Popen([exePath,numberOfPicos,filePath,electrodeOption, numberOfScans,FF]) # last process to start (hopefully)

    # If continuous scan then we bypass waiting for all scans to finish so we can plot in realtime 
    if(not(electrodeOption=="Continuous")):
        wait_proccesses = [Process(target = wait_task, args = (tasks[i], )) for i in range(1, int(numberOfPicos) + 1)]
        for proc in wait_proccesses:
            proc.start()
        for proc in wait_proccesses:
            proc.join()
        kill_proccesses = [Process(target = kill_task, args = (tasks[i], )) for i in range(1, int(numberOfPicos) + 1)]
        for proc in kill_proccesses:
            proc.start()
        for proc in kill_proccesses:
            proc.join()
    # if int(numberOfPicos)>1:
    #     if(not(electrodeOption=="Continuous")):
    #         out.wait() # If last pico finishes before any pico before it then this will prevent data extraction below until all picos are done.
    #         out.kill()

    #time.sleep(1) #not sure if i need this right now. added in for continuous scan
    
    print("Electrode option: " + electrodeOption)
    print("Number of Scans: " + numberOfScans)
    print("Analyzing Data...")
    # Comment/uncomment out this for loop to disable/enable python peak detection
    cont_tasks = []
    for i in range(1,int(numberOfPicos)+1):
        if(electrodeOption == "Three Electrode Scan"):
            peakdetection.peakDetection(i,filePath,int(numberOfScans)) 
        elif(electrodeOption =="Two Electrode Scan" or electrodeOption == "Two Electrode Scan (Alternating)"):
            peakdetectionTwoElectrode.peakDetection(i,filePath,int(numberOfScans))
        elif(electrodeOption == "One Electrode Scan"):
            peakdetectionOneElectrode.peakDetection(i,filePath,int(numberOfScans))
        elif(electrodeOption == "Continuous"):
             cont_tasks.append(subprocess.Popen(["python","C:\\Users\\aptitude\Desktop\\Pico Software V1\\peakdetectionContinuous.py",str(i),filePath,numberOfScans]))
            #peakdetectionContinuous.peakDetection(i,filePath,int(numberOfScans))
        if (electrodeOption=="Continuous"):
            wait_proccesses_cont = [Process(target = wait_task, args = (cont_tasks[i], )) for i in range(1, int(numberOfPicos) + 1)]
            for proc in wait_proccesses_cont:
                proc.start()
            for proc in wait_proccesses_cont:
                proc.join()
    print("Finished!") 
    
    # Uncomment/comment below to enable/disable matlab peak detection.
    '''if(output.returncode == int(numberOfPicos)):
        names = matlab.engine.find_matlab()
        eng = matlab.engine.connect_matlab(names[0])
        for i in range(1,int(numberOfPicos)+1):
            eng.peakdetectionv2(float(i),filePath,nargout=0)
        eng.quit()'''
