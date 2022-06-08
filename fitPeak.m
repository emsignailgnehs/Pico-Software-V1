function [xnotjunk, ynotjunk, xforfit, gauss, baseline, peakcurrent, peakvoltage, fiterror] = fitPeak(xydataIn, nstd, peakwidth, minpot, maxpot)
% Gives me the peak current from a scan
%     fits the data to a polynomial and a gaussian, then subtracts the
%     xydataIn this is the current and voltage data set for one scan
%     nstd = 3.5  this is normally obtained from the user - the number of standard deviations to look
%     peakwidth = 0.2 %% this is the peakwidth of the gaussianpolynomial to find peak current on a scan by scan basis

    


    %% assign voltage and current data
    x = xydataIn(:,1); %voltage
    y = xydataIn(:,2); %current
    
    %% Cut out the bad data  
    [truncx, truncy] = truncEdges(x,y,minpot,maxpot); %cut out the bad data from the edges
 
    %% Normalize the current by the average current value
    norm = mean(truncy); % for normalizing the current
    truncy = truncy/norm; % normalize by the mean
  
    
    %% Apply butterfilter
    voltageinterval = abs(truncx(2)-truncx(1));
    fs = 1/voltageinterval; % Sampling rate
    fc = 0.1*fs; % Cut off frequency  ***We made up this scale factor based on limited emperical data***
    
    [filt_b,filt_a] = butter(1,fc/(fs/2)); % Butterworth filter of order 1
    truncy = filter(filt_b,filt_a,truncy); % Will be the filtered signal
 

    %% Overide values
    nstd = 4.5; %4 is good
    peakwidthscalefactor = 4; %3.1 is good    
    
    %% Find the peak location and its height
    %MinPeakProminence can cause issues if peak is too small, if getting
    %"Matrix dimensions must agree error" on line 54 (baseMask 0
    %(truncx...), decrease MinPeakProminenece
    [peakHeights,centerlocs,peakWidths] = findpeaks(truncy);
    
    if length(peakHeights) > 10
        prom = 0;
        while length(peakHeights) > 2
            prom = prom + .01;
            [peakHeights,centerlocs,peakWidths] = findpeaks(truncy,'MinPeakProminence',prom);
        end
    end
    
    %Remove false peaks at extreme voltages
     edge = 0.015; %%Emperically chosen cut off value in Volts
     for i = 1:length(centerlocs)
         if truncx(centerlocs(i)) > max(truncx)-edge || truncx(centerlocs(i)) < min(truncx)+edge
             centerlocs(i) = 0;
         end
     end
     peakHeights(centerlocs == 0) = [];  % Need to cut out all elements peak height, width, centerlocs where we are outside of edge
     peakWidths(centerlocs == 0) = [];
     centerlocs(centerlocs == 0) = [];
     %%
    peakHeight = max(peakHeights);
    centerloc = centerlocs(peakHeights==peakHeight);
    peakwidth = peakWidths(peakHeights==peakHeight);
    
    
    if length(centerloc) > 1
        centerloc = min(centerloc);
        peakwidth = sum(peakWidths(peakHeights==peakHeight));
        peakHeight = truncy(centerloc);
    end
    
    
    
    %%%peakwidth*(voltageinterval)
     
     
     
        center = truncx(centerloc);
    peakwidth = peakwidthscalefactor*peakwidth*(voltageinterval);%convert peakwidth to voltage and scale
    %**scale value is arbitrary, was 4 previously

%     
%     try
%         center = findPeakLoc(truncx, truncy);  %gets the peak location
%         peakHeight = max(truncy(truncx==center)); %gets the peak height
%         
%     catch err
%         peakHeight = max(truncy); % if the above fails this takes the max for the peak height
%         center = max(truncx(truncy==peakHeight)); % if the above fails it grabs the center at that max
%                        
%         print('Error fitting'); % don't know what this does
%         rethrow(err);  % don't know what this does
%     end

    %Fail Gracefully - Identify lack of peaks and output flagging function values 
    if isempty(centerloc) == 1
        xnotjunk = truncx;
        ynotjunk = truncy*norm;
        xforfit = 0;
        gauss = 0;
        baseline = 0;
        peakcurrent = 0;
        peakvoltage = 0;
        fiterror = -0.001; % increase so that it can be seen
        
    else

    %% Now we find the regions of the data for determining the baseline and the reduction peak (peak)
    baseMask = (truncx > (center + peakwidth/2.5)) | (truncx < (center - peakwidth/2.5)); % Gets the portion of the data that's (1/4 of the peakwidth) either side of the center. 1/8 samples more of the peak, 1/2.5 samples less of the peak
    peakMask = (truncx > (center - peakwidth/1.5)) & (truncx < (center + peakwidth/1.5)); %Gets the portion aroud the center (1/2 peak width) that's the gaussian
	
    %% Isolates the data to consider for the baseline fit
    xbase = truncx(baseMask & peakMask); % Finds the intersection of these to consider for the baseline fit
    ybase = truncy(baseMask & peakMask); % Corresponding y data
    
    %%  Get liner least squares fit for baseline data
    vp = polyfit(xbase,ybase,1); % Do least squares fit for baseline - vp = [slope, intercept]

    %%  Get reasonable guessess for non-linear regression
    % 	v = [slope, int, log height, center, stdevs]
    v0 = [vp(1), vp(2), log(peakHeight-linFit(vp,center)),center,peakwidth/6];  %give reasonable starting values for non-linear regression  
 
    %%  Run minimization of fitting error to get optimal values for the fitting parameters v
    options=optimset('Display','off');
    v = fminsearch(@getFillFitError,v0,options,truncx,truncy);
    fiterrornorm = getFillFitError(v,truncx, truncy); %Gets the error for the particualar fit
    
    
    ip = (gaussAndLinFit(v,v(4))-linFit(v,v(4)));  %find the max value of the gaussian peak (minus the polynomial)
    potp = v(4);
    
%     if ip > max(truncy)
%          ip = 0;
%     end
    

    peakMask = (truncx>(v(4)-nstd*v(5)))& (truncx<(v(4)+nstd*v(5)));
    full = gaussAndLinFit(v,truncx(peakMask));
    base = linFit(v,truncx(peakMask));  
  

    %% Outputs
    xnotjunk = truncx;
    ynotjunk = truncy*norm;
    xforfit = truncx(peakMask);
    gauss = full*norm;
    baseline = base*norm;
    peakcurrent = ip*norm;
    peakvoltage = potp;
    fiterror = fiterrornorm*norm*100; % increase so that it can be seen
    
    if isempty(gauss) == 1
        xnotjunk = truncx;
        ynotjunk = truncy*norm;
        xforfit = 0;
        gauss = 0;
        baseline = 0;
        peakcurrent = 0;
        peakvoltage = 0;
        fiterror = -0.002; % increase so that it can be seen
    end
    
%     if fiterror*1000 > 10
%         xnotjunk = truncx;
%         ynotjunk = truncy*norm;
%         xforfit = 0;
%         gauss = 0;
%         baseline = 0;
%         peakcurrent = 0;
%         peakvoltage = 0;
%         fiterror = -0.002; % increase so that it can be seen
%     end
    
    %plot(truncx,truncy*norm,'o', xforfit,baseline,'g', xforfit,gauss,'r');
    

% 	if flag == 0: return x,y,full*norm,base*norm,ip*norm,passingx[PeakMask]
         
    end


    %% Nested functions
    
    function y = linFit(v, x)
    %linear portion of fit 
    %   This function attempts to describe current (y) as a function of voltage
    %   (x). That function captures the linear portion
    %   Fitting parameters are handed by the arrary (v),
    %   where v = [slope intercept]
        y = v(1)*x + v(2);
    end

    function y = gaussNormFit(v, x)
    %linear portion of fit 
    %   This function attempts to describe current (y) as a function of voltage
    %   (x). That function captures the gaussian portion
    %   Fitting parameters are handed by the arrary (v),
    %   where v = [y-intecept, slope, Gaussian scalar, Gaussian mean, SD]
        y = exp(-(((x-v(4)).^2)/(2*v(5).^2)));
    end

    function y = gaussAndLinFit(v, x)
    %Gaussian on a lienar baseline
    %   This function attempts to describe current (y) as a function of voltage
    %   (x).  That function is a combination of gaussian on a cosh baseline.
    %   Fitting parameters are handed by the arrary (v),
    %   where v = [slope, y-intecept, Gaussian scalar, Gaussian mean, SD]    
        y = v(1)*x + v(2) + exp(v(3))*exp(-(((x-v(4)).^2)/(2*v(5).^2)));
    end

        
%     function peakLocOut = findPeakLoc(xp,yp)
%     
%         peaknotfound = 1;
%         spacing = abs(xp(1)-xp(2));  % determine the step size in x
%         
%         while peaknotfound > 0.1
%             i = 0;
%             peakheight = max(yp); % finds the max y value
%             peakLocOut = min(xp(yp==peakheight)); %finds the x value at the max y value (Takes the min if there are multiple maxes)
%             left = mean(yp((xp>peakLocOut)&(xp<(peakLocOut+5.5*spacing)))); % finds the average of 5 the y values to the to the left (negative) of the peak
%             right = mean(yp((xp<peakLocOut)&(xp>(peakLocOut-5.5*spacing))));% finds the average of 5 the y values to the to the right (positive) of the peak
%         
%             if (size(left)>0)&(size(right)>0)&(left<peakheight)&(right<peakheight)
%                 peaknotfound = 0;
%             else
% 				mask = xp==peakLocOut;
% 				xp = xp(~mask);
% 				yp = yp(~mask);
% 				i = i+1;
%             end
%             
%             if i > 100
%                 peaknotfound = 0;
%             end
%         
%         end % while
%      
%     end % peakLocOut 
    
  
    function sse = getFillFitError(v,x,y)
        % This function fits the peak only within the numer of standard deviations (nSD) of the peak in a weighted manner   
        peakmask = (x > (v(4) - 2.5 * v(5)))  & (x < (v(4) + 2.5 * v(5)));
        basemask = (x > (v(4) - nstd * v(5))) & (x < (v(4) + nstd * v(5))) & (~peakmask);
        
        Error_Vector  = (gaussAndLinFit(v, x(basemask)) - y(basemask))/sqrt(sum(basemask));
        
        %Peak error is weighted by exp(-distance from peak)
        Error_Vector  = [Error_Vector ; ((gaussAndLinFit(v, x(peakmask)) - y(peakmask))/sqrt(sum(peakmask)) .* gaussNormFit(v,x(peakmask)))]; % Ensure the curve does not disappear
        
        
        % When curvefitting, a typical quantity to
        % minimize is the sum of squares error
        sse = sum(Error_Vector.^2);
        % You could also write sse as
        % sse=Error_Vector(:)'*Error_Vector(:);
    end
 
    
end %fitPeak



function [truncxOut, truncyOut] = truncEdges(x, y, min, max)
%removes outlier portion of fit of known bad signal from a scan data
%   

    %%eliminate the values that are outside of the desired range
    truncxOutTemp = zeros(1, length(x)); % initilize lists
    truncyOutTemp = zeros(1, length(x));

    count = 0;
    for j = 1:length(x)
        if x(j) >= min && x(j) <= max
            count = count + 1;
            truncxOutTemp(count) = x(j);
            truncyOutTemp(count) = y(j);
        end
    end
    
  
    %% trim the padded zeros off the vectors
    truncxOut = zeros(1, count);
    truncyOut = zeros(1, count);
    
    for j = 1:count
        truncxOut(j) = truncxOutTemp(j);
        truncyOut(j) = truncyOutTemp(j);
    end
    
    %% Turn into column vectors for output
    truncxOut = truncxOut';
    truncyOut = truncyOut';
    
        
end % truncEdges


    