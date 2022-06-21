import socket
import sys
import glob
import serial
import json
import re

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def write_port(ser, message):
    ser.write(bytes(message, 'ascii'))

def read_port(ser):
    return ser.read_until(bytes("*\n", 'ascii'))

def list_to_json(list):
    return json.dumps(list)

def parse_feedback(pattern, msg):
    return re.findall(pattern, msg)

def run_swv(ser):
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
    script = eval('f'+repr(fibronogen_trace_template))
    write_port(ser, script)

settings = {
    'E Begin': 0,
    'E End': -0.6,
    'E Step': 0.005,
    'E Amp': 0.010,
    'Frequency': 100,
    'Wait time': 10,
    'CurrentRange Min': '100 uA',
    'CurrentRange Max': '100 nA',
    'Total Scans': 5,
    'Interval': 0.01,
}

fibronogen_trace_template="""e
var c
var p
var f
var r
set_pgstat_chan 0
set_pgstat_mode 3
set_max_bandwidth {Freq*4}
set_autoranging {crMin} {crMax}
set_e {E_begin}
cell_on
wait {waitTime}
meas_loop_swv p c f r {E_begin} {E_end} {E_step} {E_amp} {Freq}
	pck_start
	pck_add p
	pck_add c
	pck_end
endloop
on_finished:
cell_off

"""

if __name__ == '__main__':
    from pyMeasurementScript import *
    from matplotlib import pyplot as plt

    all_ports = serial_ports()
    print(all_ports)

    for port in all_ports:
        bdrate = 230400
        ser = serial.Serial(port, baudrate = bdrate, timeout = 11)
        write_port(ser, 'G04\n')
        run_swv(ser)
        opt_lines = GetResults(ser)
        result = GetValueMatrix(opt_lines)[0]
        voltage = [e[0] for e in result]
        current = [e[1] for e in result]
        # print(voltage)
        # print(current)
        plt.plot(voltage, current)
        plt.show()
        ser.close()