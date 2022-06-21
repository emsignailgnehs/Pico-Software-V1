from picoLibrary import *

settings = {
    'E Begin': 0,
    'E End': -0.6,
    'E Step': 0.005,
    'E Amp': 0.010,
    'Frequency': 100,
    'Wait time': 0,
    'CurrentRange Min': '100 uA',
    'CurrentRange Max': '100 nA',
    'Total Scans': 5,
    'Interval': 0.01,
}

def GetResults(ser):
    "return results as a list of lines"
    results = []
    while 1:
        res = ser.readline()
        strline = res.decode('ascii')
        results.append(strline)
        if strline == '\n' or '!' in strline:
            break
    return results

def ValConverter(value,sip):
    return sip_factor.get(sip,np.nan) * value

def ParseVarString(varstr):
    SIP = varstr[7]                 #get SI Prefix
    varstr = varstr[:7]             #strip SI prefix from value
    val = int(varstr,16)            #convert the hexdecimal number to an integer
    val = val - 2**27               #substract the offset binary part to make it a signed value
    return ValConverter(val,SIP)    #return the converted floating point value

def ParseResultsFromLine(res_line):
    lval= list()                            #Create a list for values
    lvt= list()                             #Create a list for values
    if res_line.startswith('P'):            #data point start with P
        pck = res_line[1:len(res_line)]     #ignore last and first character
        for v in pck.split(';'):            #value fields are seperated by a semicolon
            str_vt = v[0:2]                 #get the value-type
            str_var = v[2:2+8]              #strip out value type
            val = ParseVarString(str_var)   #Parse the value
            lval.append(val)                #append value to the list
            lvt.append(str_vt)
    return lval,lvt

def GetValueMatrix(content):
    val_array=[[]]
    j=0
    for resultLine in content:
        #check for possible end-of-curve characters
        if resultLine.startswith('*') or resultLine.startswith('+') or resultLine.startswith('-'):
            j = len(val_array) #step to next section of values

        else:
            #parse line into value array and value type array
            vals,_ = ParseResultsFromLine(resultLine)
            #Ignore lines that hold no actual data package
            if len(vals) > 0:
                #If we're here we've found data for this curve, so check that space in allocated for this curve
                #This way we don't allocate space for empty curves (for example when a loop has no data packages)
                if j >= len(val_array):
                    val_array.append([])
                #Add values to value array
                val_array[j].append(vals)
    return val_array

def convert_voltage(v):
    assert (v>=-1.61 and v<=1.81) , 'Potential out of range'
    return f"{v*1000:.0f}m"

def convert_currange_range(r):
    "'100 nA','1 uA','10 uA','100 uA','1 mA','5 mA'"
    n,u = r.split(' ')
    return n+u[0]

def fib_constructScript(settings):
    """
    use channel info to set pins.
    construct method script from settings
    covid-trace method format: {
        'script': method script to send.
        'interval': interval
        'repeats' : repeat how many times
        'duration' : total last measurement time. # whichever happens first.
    }
    """
    
    autoERange = settings.get('Auto E Range',False)
    E_begin = convert_voltage(settings['E Begin'])
    E_end = convert_voltage(settings['E End'])
    if autoERange:
        E_begin = "{E_begin}"
        E_end = "{E_end}"
    # setPin = channel_to_pin(channel)
    assert (settings['E Step']>=0.001 and settings['E Step']<=0.1) ,'E step out of range'
    E_step = convert_voltage(settings['E Step'])
    assert (settings['E Amp']>0.001 and settings['E Amp']<=0.25 ), 'E Amp out of range.'
    E_amp = convert_voltage(settings['E Amp'])
    Freq = int(settings['Frequency'])
    waitTime = convertUnit(max(settings['Wait time'],1e-6))
    assert (Freq<999 and Freq>5) , "Frequency out of range."
    crMin = convert_currange_range(settings['CurrentRange Min'])
    crMax = convert_currange_range(settings['CurrentRange Max'])
    repeats = settings['Total Scans']
    interval = settings['Interval']
    assert (interval > 0) , 'Interval too small for pico.'
    # duration = settings['Duration(s)']
    script = eval('f'+repr(fibronogen_trace_template))
    return {'interval':interval,
            'repeats':repeats,
            'script':script,
            # 'duration':duration,
            'autoERange':autoERange,
            'E_begin': settings['E Begin'],
            'E_end':settings['E End']
            }

if __name__ == '__main__':
    output = fib_constructScript(settings)['script']
    print(output)