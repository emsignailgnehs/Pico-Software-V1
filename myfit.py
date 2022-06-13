import numpy as np
from scipy import signal
"""
my fit for echem data.
it's ~ 6.6 fold faster than fitpeak2; 180 fold faster than oldmethod.
TODO:
1. test on more messy data.
2. heuristic for finding tangent.
3. ways to measure fitting error by the angle between tangent line and curve slope at contact point.
update 6/9:
change intercept to account for min(0,) in whole
change peak finding prominence requirements.
"""

def smooth(x,windowlenth=11,window='hanning'):
    "windowlenth need to be an odd number"
    s = np.r_[x[windowlenth-1:0:-1],x,x[-2:-windowlenth-1:-1]]
    w = getattr(np,window)(windowlenth)
    return np.convolve(w/w.sum(),s,mode='valid')[windowlenth//2:-(windowlenth//2)]


def intercept(x, x1, x2, whole=False):
    """
    determine whether the line that cross x1 and x2 and x[x1],x[x2] will intercept x.
    if whole == False, will only consider one side.
    Only consider the direction from x2 -> x1,
    that is:
    if x1 > x2; consider the right side of x2
    if x1 < x2; consider the left side of x2
    """
    # set tolerance to be 1/1e6 of the amplitude
    xtol = - (x.max() - x.min())/1e6
    y1 = x[x1]
    y2 = x[x2]
    k = (y2-y1)/(x2-x1)
    b = -k*x2 + y2
    maxlength = len(x)
    res = x - k*(np.array(range(maxlength)))-b
    if whole:
        return np.any(res[max(0, x1 - maxlength//20 - 5):x2 + maxlength//20 + 5] < xtol)
    if x1 > x2:
        return np.any(res[x2: x1 + maxlength//20 + 5] < xtol)
    else:
        # only consider extra half max width; make sure at least 5 points
        return np.any(res[max(0, x1 - maxlength//20 - 5):x2] < xtol)



def sway(x,center,step,fixpoint):
    if center==0 or center==len(x):
        return center

    if not intercept(x,center,fixpoint):
        return center
    return sway(x,center+step,step,fixpoint)

def find_tangent(x,center):
    left = center - 1
    right = center + 1
    while intercept(x,left,right,True):
        if intercept(x,left,right):
            newleft = sway(x,left,-1,right)
        if intercept(x,right,left):
            newright = sway(x,right,1,newleft)
        if newleft == left and newright == right:
            break
        left = newleft
        right = newright
    return left,right

def pickpeaks(peaks,props,totalpoints):
    """
    The way to pick a peak
    20220609: add a potential range for peak location
    """
    if len(peaks) == 1:
        return peaks[0]
    # scores = np.zeros(len(peaks))
    # heights = np.sort(props['peak_heights'])
    # prominences = np.sort(props['prominences'])
    # widths = np.sort(props['widths'])
    normheights = props['peak_heights']/(props['peak_heights']).sum()
    normprominences = props['prominences']/(props['prominences']).sum()
    normwidths = props['widths']/(props['widths']).sum()
    bases = ( (props['left_bases'] == props['left_bases'].min() ) &
              (props['right_bases'] == props['right_bases'].max()) )
    scores = normheights + normprominences + normwidths - 2*bases
    topick = scores.argmax()
    return   peaks[topick]


def myfitpeak(xydataIn, truncate = 0.025):
    x = xydataIn[0,:] #voltage
    y = xydataIn[1,:] #current
    sy = smooth(y)
    prange_flag = ((x.min() + truncate) < x)*((x.max() - truncate) > x)
    sy_for_fit = sy[prange_flag]
    x_for_fit = x[prange_flag]

    noise = np.absolute(y - sy)

    # limit peak width to 1/50 of the totoal scan length to entire scan.
    # limit minimum peak height to be over 0.05 percentile of all original - smoothed
    heightlimit = np.quantile(noise, 0.95) * 3

    # heightlimit = np.absolute(y[0:-1] - y[1:]).mean() * 3
    # set height limit so that props return limits
    peaks, props = signal.find_peaks(
        sy_for_fit, height=heightlimit, prominence=heightlimit, width=len(sy_for_fit) / 30, rel_height=0.5)

    # return if no peaks found.
    if len(peaks) == 0:
        return x,sy,0,0,0,0,0,-1

    peak = pickpeaks(peaks,props,len(sy_for_fit))

    # find tagent to 3X peak width window
    x1,x2 = find_tangent(sy_for_fit,peak)

    y1=sy_for_fit[x1]
    y2=sy_for_fit[x2]
    k=(y2-y1)/(x2-x1)
    b = -k*x2 + y2

    peakcurrent = sy_for_fit[peak] - (k*peak + b)
    peakvoltage = x_for_fit[peak]

    twopointx = np.array([x_for_fit[x1],x_for_fit[x2]])
    twopointy = np.array([sy_for_fit[x1],sy_for_fit[x2]])

    # for compatibility return the same length tuple of results.
    # currently, no error is calculated.
    return x,y,twopointx,twopointy,twopointy,peakcurrent,peakvoltage,0

if __name__ == '__main__':
    import pandas as pd
    from matplotlib import pyplot as plt

    cfile = r'C:\Users\Public\Documents\SynologyDrive\Users\Sheng\SideProjects\Pico Software V1\test\Ch 4_ForSheng\Ch 4\WE1.csv'
    pfile = r'C:\Users\Public\Documents\SynologyDrive\Users\Sheng\SideProjects\Pico Software V1\test\Ch 4_ForSheng\Ch 4\WE1V.csv'
    cdf = pd.read_csv(cfile, header = None).drop(columns= 5)
    pdf = pd.read_csv(pfile, header = None).drop(columns= 5)

    for i in range(len(pdf.columns)):
        x = np.array(pdf[i])
        y = np.array(cdf[i])
        x,y,twopointx,twopointy,twopointy,peakcurrent,peakvoltage,err = myfitpeak(np.array([x, y]))
        clr = ['red', 'orange', 'green', 'blue', 'magenta']
        plt.plot(x, y, color = clr[i])
        plt.plot(twopointx, twopointy, marker = 'x', linestyle = '--', color = clr[i])
        vline_x = np.array([peakvoltage] * 2)
        base_y = twopointy[0] + (twopointy[1] - twopointy[0])*(peakvoltage - twopointx[0])/(twopointx[1] - twopointx[0])
        vline_y = np.array([base_y, base_y + peakcurrent])
        plt.plot(vline_x, vline_y, color = clr[i])
    plt.show()
