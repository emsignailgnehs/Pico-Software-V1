from picoLibrary import *

settings = {
    'E Begin': 0,
    'E End': -600,
    'E Step': 5,
    'E Amp': 10,
    'Frequency': 100,
    'Wait time': 0,
    'CurrentRange Min': '100 uA',
    'CurrentRange Max': '100 nA',
    'repeats': 5
}

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
    setPin = channel_to_pin(channel)
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
    duration = settings['Duration(s)']
    script = eval('f'+repr(covid_trace_template))
    return {'interval':interval,'repeats':repeats,
        'script':script , 'duration':duration , 'autoERange':autoERange,
        'E_begin': settings['E Begin'] ,'E_end':settings['E End'] }