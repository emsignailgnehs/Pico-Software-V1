function peakdetectionv2(picoNumber,filepath)

%Where data will be located (will be the same as the visual studio code)
%filepath = "C:\Users\rup96\Desktop\peakProgram\"; 

switch(picoNumber)
    case 1
        we0I = csvread(strcat(filepath,'WE0.csv'));
        we0V = csvread(strcat(filepath,'WE0V.csv'));
        we1I = csvread(strcat(filepath,'WE1.csv'));
        we2I = csvread(strcat(filepath,'WE2.csv'));
    case 2
        we0I = csvread(strcat(filepath,'WE02.csv'));
        we0V = csvread(strcat(filepath,'WE02V.csv'));
        we1I = csvread(strcat(filepath,'WE12.csv'));
        we2I = csvread(strcat(filepath,'WE22.csv'));
end
if ~isfile(strcat(filepath,'SortedData.csv'))
    fid = fopen('SortedData.csv', 'wt');
    fprintf(fid, '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n', 'WE1','','','WE2','','','WE3','','','Chip');
    fprintf(fid, '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n','Avg I (nA)','Avg Baseline (nA)','Avg V (V)'...
        ,'Avg I (nA)','Avg Baseline (nA)','Avg V (V)',...
        'Avg I (nA)','Avg Baseline (nA)','Avg V (V)','Avg I (nA)','Avg Baseline (nA)','Avg V (V)');
    fclose(fid);
end

if ~isfile(strcat(filepath,'BaselinePeak.csv'))
    fid = fopen('BaselinePeak.csv', 'wt');
    fprintf(fid, '%s,%s,%s,%s,%s,%s,%s\n', 'WE1', '','','WE2','','','WE3');
    fprintf(fid, '%s,%s,%s,%s,%s,%s,%s,%s,%s\n','Peak I (A)','Baseline (A)','Peak V (V)'...
        ,'Peak I (A)','Baseline (A)','Peak V (V)','Peak I (A)','Baseline (A)','Peak V (V)');
    fclose(fid);
end
baselinePeakCSV = [];
figure(picoNumber)
for i = 1:5
    
    we0 = [we0V(:,i), we0I(:,i)];
    %we1 = [we0V(:,i), we1I(:,i)];
    %we2 = [we0V(:,i), we2I(:,i)];
    nstd = 3.1;
    peakwidth = 0.25;%not used any more - taken care of automatically in fitpeak
    minpot = -1; % not necessary any more - peakfitting is robust enough to not require chopping of the edges
    maxpot = .1; % not necessary any more - peakfitting is robust enough to not require chopping of the edges
    
    %% WE0
    %fit peak
    
    [xnotjunk, ynotjunk, xforfit, gauss, baseline, peakcurrent, peakvoltage, fiterror] =...
        fitPeak(we0,nstd,peakwidth,minpot,maxpot);
    baselineatpeak = baseline(ceil(end/2));
    
    baselinerowWE0 = [peakcurrent baselineatpeak peakvoltage];
    plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,...
    [peakvoltage,peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent]);
    hold on
    %annotate peak
    x = peakvoltage;
    y = baselineatpeak+peakcurrent;
    text(x,y,num2str(peakcurrent));
    %% WE1
    %fit peak
    [xnotjunk, ynotjunk, xforfit, gauss, baseline, peakcurrent, peakvoltage, fiterror] =...
        fitPeak(we1,nstd,peakwidth,minpot,maxpot);
    
    baselineatpeak = baseline(ceil(end/2));
    
    baselinerowWE1 = [peakcurrent baselineatpeak peakvoltage];
    plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,...
    [peakvoltage,peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent]);
    
    %annotate peak
    x = peakvoltage;
    y = baselineatpeak+peakcurrent;
    text(x,y,num2str(peakcurrent));
   
    %% WE2
    %fit peak
    [xnotjunk, ynotjunk, xforfit, gauss, baseline, peakcurrent, peakvoltage, fiterror] =...
        fitPeak(we2,nstd,peakwidth,minpot,maxpot);
    
    baselineatpeak = baseline(ceil(end/2));
    
    baselinerowWE2 = [peakcurrent baselineatpeak peakvoltage];
    plot(xnotjunk,ynotjunk,xforfit,gauss,xforfit,baseline,...
    [peakvoltage,peakvoltage],[baselineatpeak,baselineatpeak+peakcurrent]);

    %annotate peak
    x = peakvoltage;
    y = baselineatpeak+peakcurrent;
    text(x,y,num2str(peakcurrent));
    %store peak value for writecsv
    %% Append to matrix
    baselinePeakCSV = [baselinePeakCSV; baselinerowWE0 baselinerowWE1 baselinerowWE2];
end
%% Sort data and store. Then write to each csv.
scale = 1e9;
% Avg peak current for each electrode (takes last three out of 5 scans)

avgPeakCurrent0 = sum(baselinePeakCSV((end-2:end),1))/3;
avgPeakCurrent1 = sum(baselinePeakCSV((end-2:end),4))/3;
avgPeakCurrent2 = sum(baselinePeakCSV((end-2:end),7))/3;

% Avg Baseline for each electrode (takes last three out of 5 scans)
avgbaseline0 = sum(baselinePeakCSV((end-2:end),2))/3;
avgbaseline1 = sum(baselinePeakCSV((end-2:end),5))/3;
avgbaseline2 = sum(baselinePeakCSV((end-2:end),8))/3;

% Avg peak voltage for each electrode (takes last three out of 5 scans)
avgPeakVoltage0 = sum(baselinePeakCSV((end-2:end),3))/3;
avgPeakVoltage1 = sum(baselinePeakCSV((end-2:end),6))/3;
avgPeakVoltage2 = sum(baselinePeakCSV((end-2:end),9))/3;

% Make row vector for each electrode
e0 = [avgPeakCurrent0*scale avgbaseline0*scale avgPeakVoltage0];
e1 = [avgPeakCurrent1*scale avgbaseline1*scale avgPeakVoltage1];
e2 = [avgPeakCurrent2*scale avgbaseline2*scale avgPeakVoltage2];

% Avg chip current, baseline, and voltage

chipCurrent = (sum(e0(1)+e1(1)+e2(1))/3);
chipBaseline = (sum(e0(2)+e1(2)+e2(2))/3);
chipVoltage = (sum(e0(3)+e1(3)+e2(3))/3);

% Make row vector for chip
chip = [chipCurrent chipBaseline chipVoltage];

% Add electrode and chip averages to matrix
sortedCSV = [e0 e1 e2 chip];
hold off
%write data to end of file
dlmwrite('SortedData.csv',sortedCSV,'-append');
dlmwrite('BaselinePeak.csv',baselinePeakCSV,'-append');

end