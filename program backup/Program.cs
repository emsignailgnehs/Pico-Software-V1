using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Ports;
using System.Reflection;
using System.Linq;
using System.Threading;

namespace EmStatConsoleExample
{
    class Program
    {
        static string W0File = "SWV_on_10kOhmW0.txt";//"SWV_on_10kOhm.txt";                    //Name of the script file
        static string W1File = "SWV_on_10kOhmW1.txt";                  //Name of the script file for w1
        static string W2File = "SWV_on_10kOhmW2.txt";                  //Name of the script file for w2
        static string FFfile = "FF.txt";
        static string AppLocation = Assembly.GetExecutingAssembly().Location;
        static string FilePath = System.IO.Path.GetDirectoryName(AppLocation) + "\\scripts";         //Location of the script file
        static string FilePathSave = "C:\\Users\\aptitude3\\Desktop\\Tyler Desktop\\Pico Software V1\\MethodSCRIPTExamples_C#\\MSConsoleExample"; //Change this path to where you want to drop the output files 
        


        const string CMD_VERSION = "t\n";                                                            //Version command
        const int BAUD_RATE = 230400;                                                                //Baudrate for EmStat Pico
        const int READ_TIME_OUT = 7000;                                                              //Read time out for the device in ms
        const int PACKAGE_DATA_VALUE_LENGTH = 8;                                                     //Length of the data value in a package
        const int OFFSET_VALUE = 0x8000000;                                                          //Offset value to receive positive values

        // Variables for multi pico multi working electrodes.
        
        static SerialPort SerialPortEsP;
       
        static List<double> CurrentReadings = new List<double>();                                    //Collection of current readings
        static List<double> VoltageReadings = new List<double>();                                    //Collection of potential readings
        static List<string> timestampArray = new List<string>();
        static int numberOfScans = 5; //Change this variable to vary number of scans. 


        static string RawData;
        static int NDataPointsReceived = 0;                                                          //The number of data points received from the measurement

        readonly static Dictionary<string, double> SI_Prefix_Factor = new Dictionary<string, double> //The SI unit of the prefixes and their corresponding factors
                                                          { { "a", 1e-18 },
                                                            { "f", 1e-15 },
                                                            { "p", 1e-12 },
                                                            { "n", 1e-9 },
                                                            { "u", 1e-6 },
                                                            { "m", 1e-3 },
                                                            { " ", 1 },
                                                            { "k", 1e3 },
                                                            { "M", 1e6 },
                                                            { "G", 1e9 },
                                                            { "T", 1e12 },
                                                            { "P", 1e15 },
                                                            { "E", 1e18 }};

        readonly static Dictionary<string, string> MeasurementVariables = new Dictionary<string, string>  //Variable types and their corresponding labels
                                                                            { { "da", "E (V)" },
                                                                              { "ba", "i (A)" },
                                                                              { "dc", "Frequency (Hz)" },
                                                                              { "cc", "Z' (Ohm)" },
                                                                              { "cd", "Z'' (Ohm)" } };
        /// <summary>
        /// All possible current ranges, the current ranges
        /// that are supported by EmStat pico.
        /// </summary>
        private enum CurrentRanges
        {
            cr100nA = 0,
            cr2uA = 1,
            cr4uA = 2,
            cr8uA = 3,
            cr16uA = 4,
            cr32uA = 5,
            cr63uA = 6,
            cr125uA = 7,
            cr250uA = 8,
            cr500uA = 9,
            cr1mA = 10,
            cr5mA = 11,
            hscr100nA = 128,
            hscr1uA = 129,
            hscr6uA = 130,
            hscr13uA = 131,
            hscr25uA = 132,
            hscr50uA = 133,
            hscr100uA = 134,
            hscr200uA = 135,
            hscr1mA = 136,
            hscr5mA = 137
        }

        [Flags]
        private enum ReadingStatus
        {
            OK = 0x0,
            Overload = 0x2,
            Underload = 0x4,
            Overload_Warning = 0x8
        }


        static int dataPoints = 0;

        static bool filledStatus = false;
        static bool continuous = false;

        static int Main(string[] args)
        {

            bool canConvert = true;
            if (canConvert)
            {
                SerialPortEsP = OpenSerialPort();
                if (SerialPortEsP != null)
                {
                    string outputFilePath = "";
                    int numberOfElectrodes = 3;
                    // Full file path to scripts
                    
                    string W0FilePath = Path.Combine(FilePath, W0File);
                    string W1FilePath = Path.Combine(FilePath, W1File);
                    string W2FilePath = Path.Combine(FilePath, W2File);
                    string FFFilePath = Path.Combine(FilePath, FFfile);
                    if (args.Count() > 0)
                    {
                        outputFilePath = args[1];
                        // Full file path to scripts
                        W0FilePath = Path.Combine(outputFilePath, W0File);
                        W1FilePath = Path.Combine(outputFilePath, W1File);
                        W2FilePath = Path.Combine(outputFilePath, W2File);
                        FFFilePath = Path.Combine(outputFilePath, FFfile);
                        // Get number of scans from arguments and Check if continuous scan is running
                        numberOfScans = int.Parse(args[3]);
                        continuous = args[2].Equals("Continuous");
                        // Checks what type of scan is going to run and assign the number of electrods to use accordingly
                        if (args[2].Equals("Three Electrode Scan"))
                        {
                            numberOfElectrodes = 3;
                        }
                        else if(args[2].Equals("One Electrode Scan") || continuous)
                        {
                            numberOfElectrodes = 1;
                        }
                    }
                    Console.WriteLine("\nConnected to EmStat Pico.\n");
                    if (args.Count()>4 && args[4] == "True")
                    {
                        fluidFillDetect(FFFilePath);
                        while (!filledStatus) { }
                    }
                    if (!continuous)
                    {
                        System.Threading.Thread.Sleep(30000); //comment this out if you want to bypass 30s
                    }

                    // Check if directory has previous continuous scanning files so we can add to directory without overwriting
                    string[] dirs = Directory.GetFiles(outputFilePath, "WE1 *");
                    
                    for (int i = 0; i < numberOfScans; i++)
                    {
                        if (numberOfElectrodes == 3)
                        {
                            SendScriptFile(W0FilePath);                  //Sends the script file for SWV measurement to pico
                            ProcessReceivedPackages();

                            SendScriptFile(W1FilePath);
                            ProcessReceivedPackages();

                            SendScriptFile(W2FilePath);
                            ProcessReceivedPackages();
                        }
                        else if (numberOfElectrodes == 1)
                        {
                            SendScriptFile(W1FilePath);
                            ProcessReceivedPackages();
                            if (continuous)
                            {
                                writeCSVPath(int.Parse(args[0]), outputFilePath, numberOfElectrodes,(dirs.Length + i).ToString());
                            }
                        }
                    }
                    // If scanning is not continuous then write csv after all scanning is done.
                    if(!continuous)
                    {
                        dataPoints = (NDataPointsReceived / numberOfElectrodes) / numberOfScans; //To get number of datapoints for one electrode scan. 3 is for number of electrodes.
                        if (args.Count() != 0)
                            writeCSVPath(int.Parse(args[0]), outputFilePath, numberOfElectrodes,"");
                        else
                            writeCSVPath(1, FilePathSave, numberOfElectrodes,"");
                    }

                    SerialPortEsP.Close();
                }
                else
                {
                    Console.WriteLine($"Could not connect. \n");
                }
                
            }
            if (args.Count() != 0)
                return int.Parse(args[0]);
            else
                return 0;
            
        }
        
        static private void writeCSVPath(int picoNumber,string filePath, int numberOfElectrodes, string scanNumber)
        {
            switch (picoNumber)
            {
                case 1:
                    // File path to output csv's pico 1
                    if (numberOfElectrodes == 3)
                    {
                        string WE0csv = Path.Combine(filePath, "WE0.csv");
                        string WE1csv = Path.Combine(filePath, "WE1.csv");
                        string WE2csv = Path.Combine(filePath, "WE2.csv");
                        string WE0Vcsv = Path.Combine(filePath, "WE0V.csv");
                        WriteCSVCurrent(CurrentReadings.ToArray(), WE0csv, WE1csv, WE2csv);
                        WriteCSVVoltage(VoltageReadings.ToArray(), WE0Vcsv);
                    }
                    else if (numberOfElectrodes == 1)
                    {
                        
                        if (continuous)
                        {
                            string WE1csv = Path.Combine(filePath, "WE1 " + scanNumber + ".csv");
                            WriteCSVContinuous(timestampArray.ToArray(), CurrentReadings.ToArray(), VoltageReadings.ToArray(), WE1csv);
                        }
                        else
                        {
                            string WE1csv = Path.Combine(filePath, "WE1.csv");
                            string WE0Vcsv = Path.Combine(filePath, "WE0V.csv");
                            WriteCSVCurrentOneElectrode(CurrentReadings.ToArray(), WE1csv);
                            WriteCSVVoltage(VoltageReadings.ToArray(), WE0Vcsv);
                        }
                        
                    }
                    
                    
                    break;
                case 2:
                    // File path to output csv's pico 2
                    if (numberOfElectrodes == 3)
                    {
                        string WE02csv = Path.Combine(filePath, "WE02.csv");
                        string WE12csv = Path.Combine(filePath, "WE12.csv");
                        string WE22csv = Path.Combine(filePath, "WE22.csv");
                        string WE02Vcsv = Path.Combine(filePath, "WE02V.csv");
                        WriteCSVCurrent(CurrentReadings.ToArray(), WE02csv, WE12csv, WE22csv);
                        WriteCSVVoltage(VoltageReadings.ToArray(), WE02Vcsv);
                    }
                    else if(numberOfElectrodes == 1)
                    {
                        if (continuous)
                        {
                            string WE12csv = Path.Combine(filePath, "WE12 " + scanNumber + ".csv");
                            WriteCSVContinuous(timestampArray.ToArray(), CurrentReadings.ToArray(), VoltageReadings.ToArray(), WE12csv);
                        }
                        else
                        {
                            string WE12csv = Path.Combine(filePath, "WE12.csv");
                            string WE02Vcsv = Path.Combine(filePath, "WE02V.csv");
                            WriteCSVCurrentOneElectrode(CurrentReadings.ToArray(), WE12csv);
                            WriteCSVVoltage(VoltageReadings.ToArray(), WE02Vcsv);
                        }
                    }
                    break;
            }
        }

        static private void fluidFillDetect(string fileScript)
        {

            //double fillThresh = 200e-9;
            double fillThresh = 50 * Math.Pow(10, -9);
            while (!filledStatus)
            {
                SendScriptFile(fileScript);
                ProcessReceivedPackages();

                double sum = 0;
                int istart = 10;
                for (int i = istart; i < NDataPointsReceived; i++)
                    sum += (CurrentReadings[i]);
                double average = Math.Abs(sum) / (NDataPointsReceived - istart);
                filledStatus = average > fillThresh;

                Console.WriteLine(average.ToString());
                Console.WriteLine(fillThresh.ToString());
                Console.WriteLine(filledStatus.ToString());
                //Clear all stored values for next scan
                CurrentReadings.Clear();
                VoltageReadings.Clear();
                NDataPointsReceived = 0;
            }
            Console.WriteLine("Fluid Detected!");
        }

        private static void WriteCSVContinuous(string[] timeArray, double[] currentVector, double[] voltageVector, string we1FilePath)
        {
            TextWriter we1CSV = new StreamWriter(we1FilePath);
            var header = String.Format("{0},{1},{2}",
                   "timestamp", "I", "V");
            we1CSV.WriteLine(header);
            for (int row = 0; row < NDataPointsReceived; row++) //NDataPointsReceived is used here since we are writing only one scan at a time.
            {
                var line = String.Format("{0},{1},{2}",
                   timeArray[row], currentVector[row],
                   voltageVector[row]);
                we1CSV.WriteLine(line);
            }
            we1CSV.Close();
            CurrentReadings.Clear();
            VoltageReadings.Clear();
            timestampArray.Clear();
            NDataPointsReceived = 0;
        }

        private static void WriteCSVCurrentOneElectrode(double[] vector, String we1FilePath)
        {
            double[,] we1 = new double[dataPoints, numberOfScans];

            for (int i = 0; i < numberOfScans; i++)
            {
                for (int j = 0; j < dataPoints; j++)
                {
                    we1[j, i] = vector[j + (dataPoints * i)];
                }
            }
            TextWriter we1CSV = new StreamWriter(we1FilePath);
            for (int row = 0; row < dataPoints; row++)
            {
                var line = String.Format("{0},{1},{2},{3},{4}",
                   we1[row, 0], we1[row, 1],
                   we1[row, 2], we1[row, 3],
                   we1[row, 4]);
                we1CSV.WriteLine(line);

            }
            we1CSV.Close();
        }

        private static void WriteCSVCurrent(double[] vector,String we0FilePath,String we1FilePath,String we2FilePath)
        {
            
            double[,] we0 = new double[dataPoints, numberOfScans];
            double[,] we1 = new double[dataPoints, numberOfScans];
            double[,] we2 = new double[dataPoints, numberOfScans];
            for(int i = 0; i < numberOfScans; i++)
            {
                for(int j = 0; j < dataPoints; j++)
                {
                    we0[j,i] = vector[j + (dataPoints * i * 3)];
                    we1[j,i] = vector[(dataPoints + j) + (dataPoints * i * 3)];
                    we2[j,i] = vector[((dataPoints * 2) + j) + (dataPoints * i * 3)];
                }
            }
            TextWriter we0CSV = new StreamWriter(we0FilePath);
            TextWriter we1CSV = new StreamWriter(we1FilePath);
            TextWriter we2CSV = new StreamWriter(we2FilePath);
            for (int row = 0; row < dataPoints; row++)
            {
                var line = String.Format("{0},{1},{2},{3},{4}",
                    we0[row, 0], we0[row, 1],
                    we0[row, 2], we0[row, 3],
                    we0[row, 4]);
                we0CSV.WriteLine(line);

                line = String.Format("{0},{1},{2},{3},{4}",
                   we1[row, 0], we1[row, 1],
                   we1[row, 2], we1[row, 3],
                   we1[row, 4]);
                we1CSV.WriteLine(line);

                line = String.Format("{0},{1},{2},{3},{4}",
                   we2[row, 0], we2[row, 1],
                   we2[row, 2], we2[row, 3],
                   we2[row, 4]);
                we2CSV.WriteLine(line);
            }
            we0CSV.Close();
            we1CSV.Close();
            we2CSV.Close();
        }

        private static void WriteCSVVoltage(double[] vector, String we0VFilePath)
        {
            //dataPoints = 203;
            double[,] we0 = new double[dataPoints, numberOfScans];
            for (int i = 0; i < numberOfScans; i++)
            {
                for (int j = 0; j < dataPoints; j++)
                {
                    we0[j, i] = vector[j + (dataPoints * i)];
                }
            }
            TextWriter we0CSV = new StreamWriter(we0VFilePath);
            for (int row = 0; row < dataPoints; row++)
            {
                var line = String.Format("{0},{1},{2},{3},{4}",
                    we0[row, 0], we0[row, 1],
                    we0[row, 2], we0[row, 3],
                    we0[row, 4]);
                we0CSV.WriteLine(line);
            }
            we0CSV.Close();
        }

        

        /// <summary>
        /// Opens the serial ports and identifies the port connected to EmStat Pico
        /// </summary>
        /// <returns> The serial port connected to EmStat Pico</returns>
        private static SerialPort OpenSerialPort()
        {
            SerialPort serialPort = null;
            string[] ports = SerialPort.GetPortNames();
            for (int i = 0; i < ports.Length; i++)
            {
                serialPort = GetSerialPort(ports[i]);
                // FIND OUT A WAY TO MAKE THIS APPLICABLE TO N PORTS
                if (SerialPortEsP == null && !serialPort.IsOpen)
                {
                    try
                    {
                        serialPort.Open();                                  //Opens the serial port 
                        if (serialPort.IsOpen)
                        {
                            serialPort.Write(CMD_VERSION);                  //Writes the version command             
                            while (true)
                            {
                                string response = serialPort.ReadLine();    //Reads the response
                                response += "\n";
                                if (response.Contains("espico"))            //Verifies if the device connected is EmStat Pico
                                    serialPort.ReadTimeout = READ_TIME_OUT; //Sets the read time out for the device
                                if (response.Contains("*\n"))
                                    return serialPort;                      //Reads until "*\n" is found and breaks
                            }
                        }
                    }
                    catch (Exception exception)
                    {
                        serialPort.Close();                                 //Closes the serial port in case of exception
                    }
                }
            }
            return serialPort;
        }

        /// <summary>
        /// Fetches a new instance of the serial port with the port name passed to it
        /// </summary>
        /// <param name="port"></param>
        /// <returns></returns>
        private static SerialPort GetSerialPort(string port)
        {
            SerialPort serialPort = new SerialPort(port);
            serialPort.DataBits = 8;
            serialPort.Parity = Parity.None;
            serialPort.StopBits = StopBits.One;
            serialPort.BaudRate = BAUD_RATE;
            serialPort.ReadTimeout = 1000;                  //Initial time out set to 1000ms, upon connecting to EmStat Pico, time out reset to READ_TIME_OUT
            serialPort.WriteTimeout = 2;
            return serialPort;
        }

        /// <summary>
        /// Sends the script file to EmStat Pico
        /// </summary>
        private static void SendScriptFile(string ScriptFilePath)
        {
            string line = "";
            using (StreamReader stream = new StreamReader(ScriptFilePath))
            {
                while (!stream.EndOfStream)
                {
                    line = stream.ReadLine();               //Reads a line from the script file
                    line += "\n";                           //Adds a new line character to the line read
                    SerialPortEsP.Write(line);
                    
                }
                Console.WriteLine("Measurement started.");
            }
        }

        

        /// <summary>
        /// Processes the response packages from the EmStat Pico and stores the response in RawData.
        /// </summary>
        private static void ProcessReceivedPackages()
        {
            string readLine = "";
            Console.WriteLine("\nReceiving measurement response:");
            while (true)
            {
                readLine = ReadResponseLine();
                RawData += readLine;                         //Adds the response to raw data
                if (readLine == "\n")
                    break;
                else if (readLine[0] == 'P')
                {
                    String timeStamp = DateTime.Now.ToString("dd:HH:mm:ss:fff");
                    Console.WriteLine(timeStamp);
                    timestampArray.Add(timeStamp);
                    NDataPointsReceived++;
                    ParsePackageLine(readLine);
                }
            }
            Console.WriteLine("");
            Console.WriteLine($"\nMeasurement completed, {NDataPointsReceived} data points received.");
            
        }

        /// <summary>
        /// Reads characters and forms a line from the data received
        /// </summary>
        /// <returns>A line of response</returns>
        private static string ReadResponseLine()
        {
            string readLine = "";
            int readChar;
            while (true)
            {
                readChar = SerialPortEsP.ReadChar();
                
                if (readChar > 0)                           //Possibility of time out exception if the operation doesn't complete within the read time out; increment READ_TIME_OUT for measurements with long response times
                {
                    readLine += (char)readChar;             //Appends the read character to readLine to form a response line
                    if ((char)readChar == '\n')
                    {
                        return readLine;                    //Returns the readLine when a new line character is encountered
                    }
                }
            }
        }

        /// <summary>
        /// Parses a measurement data package and adds the parsed data values to their corresponding arrays
        /// </summary>
        /// <param name="responsePackageLine">The line from response package to be parsed</param>
        private static void ParsePackageLine(string packageLine)
        {
            string[] variables;
            string variableIdentifier;
            string dataValue;  

            int startingIndex = packageLine.IndexOf('P');                        //Identifies the beginning of the package
            string responsePackageLine = packageLine.Remove(startingIndex, 1);   //Removes the beginning character 'P'

            Console.Write($"\nindex = " + String.Format("{0,3} {1,2} ", NDataPointsReceived, " "));
            variables = responsePackageLine.Split(';');                         //The data values are separated by the delimiter ';'

            foreach (string variable in variables)
            {
                variableIdentifier = variable.Substring(0, 2);                 //The string (2 characters) that identifies the variable type
                dataValue = variable.Substring(2, PACKAGE_DATA_VALUE_LENGTH);
                double dataValueWithPrefix = ParseParamValues(dataValue);      //Parses the data value package and returns the actual values with their corresponding SI unit prefixes 
                switch (variableIdentifier)
                {
                    case "da":                                                  //Potential reading
                        VoltageReadings.Add(dataValueWithPrefix);              //Adds the value to the VoltageReadings list
                        break;
                    case "ba":                                                  //Current reading
                        CurrentReadings.Add(dataValueWithPrefix);              //Adds the value to the CurrentReadings list
                        break;
                }
                Console.Write("{0,4} = {1,10} {2,2}", MeasurementVariables[variableIdentifier], string.Format("{0:0.000E+00}", dataValueWithPrefix).ToString(), " ");
                if(variable.Substring(10).StartsWith(","))                 
                    ParseMetaDataValues(variable.Substring(10));               //Parses the metadata values in the variable, if any
            }
        }

        /// <summary>
        /// Parses the metadata values of the variable, if any.
        /// The first character in each meta data value specifies the type of data.
        /*  1 - 1 char hex mask holding the status (0 = OK, 2 = overload, 4 = underload, 8 = overload warning (80% of max))
         *  2 - 2 chars hex holding the current range index. First bit high (0x80) indicates a high speed mode cr.
         *  4 - 1 char hex holding the noise value */
        /// </summary>
        /// <param name="packageMetaData"></param>
        private static void ParseMetaDataValues(string packageMetaData)
        {
            string[] metaDataValues;
            metaDataValues = packageMetaData.Split(new string[] { "," }, StringSplitOptions.RemoveEmptyEntries);          //The metadata values are separated by the delimiter ','
            byte crByte;
            foreach (string metaData in metaDataValues)
            {
                switch (metaData[0])
                {
                    case '1':
                        GetReadingStatusFromPackage(metaData);
                        break;
                    case '2':
                        crByte = GetCurrentRangeFromPackage(metaData);
                        if(crByte != 0) DisplayCR(crByte);
                        break;
                    case '4':
                        GetNoiseFromPackage(metaData);
                        break;
                }
            }
        }

        /// <summary>
        /// Parses the reading status from the package. 1 char hex mask holding the status (0 = OK, 2 = overload, 4 = underload, 8 = overload warning (80% of max)) 
        /// </summary>
        /// <param name="metaDatastatus"></param>
        private static void GetReadingStatusFromPackage(string metaDatastatus)
        {
            string status = "";
            int statusBits = (Convert.ToInt32(metaDatastatus[1].ToString(), 16));          //One char of the metadata value corresponding to status is retrieved
            if ((statusBits) == (long)ReadingStatus.OK)
                status = nameof(ReadingStatus.OK);
            if ((statusBits & 0x2) == (long)ReadingStatus.Overload)
                status = nameof(ReadingStatus.Overload);
            if ((statusBits & 0x4) == (long)ReadingStatus.Underload)
                status = nameof(ReadingStatus.Underload);
            if ((statusBits & 0x8) == (long)ReadingStatus.Overload_Warning)
                status = nameof(ReadingStatus.Overload_Warning);
            Console.Write(String.Format("Status : {0,-10} {1,2}", status, " "));
        }

        /// <summary>
        /// Parses the bytes corresponding to current range from the package.
        /// </summary>
        /// <param name="metaDataCR"></param>
        /// <returns>The cr byte after parsing</returns>
        private static byte GetCurrentRangeFromPackage(string metaDataCR) 
        {
            byte crByte;
            if (byte.TryParse(metaDataCR.Substring(1, 2), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out crByte)) //Two characters of the metadata value corresponding to current range are retrieved as byte
            {
                return crByte;
            }
            return 0;
        }

        /// <summary>
        /// Displays the string corresponding to the input cr byte
        /// </summary>
        /// <param name="crByte">The crByte value whose string is to be obtained</param>
        private static void DisplayCR(byte crByte)
        {
            string currentRangeStr = "";
            switch (crByte)
            {
                case (byte)CurrentRanges.cr100nA:
                    currentRangeStr = "100nA";
                    break;
                case (byte)CurrentRanges.cr2uA:
                    currentRangeStr = "2uA";
                    break;
                case (byte)CurrentRanges.cr4uA:
                    currentRangeStr = "4uA";
                    break;
                case (byte)CurrentRanges.cr8uA:
                    currentRangeStr = "8uA";
                    break;
                case (byte)CurrentRanges.cr16uA:
                    currentRangeStr = "16uA";
                    break;
                case (byte)CurrentRanges.cr32uA:
                    currentRangeStr = "32uA";
                    break;
                case (byte)CurrentRanges.cr63uA:
                    currentRangeStr = "63uA";
                    break;
                case (byte)CurrentRanges.cr125uA:
                    currentRangeStr = "125uA";
                    break;
                case (byte)CurrentRanges.cr250uA:
                    currentRangeStr = "250uA";
                    break;
                case (byte)CurrentRanges.cr500uA:
                    currentRangeStr = "500uA";
                    break;
                case (byte)CurrentRanges.cr1mA:
                    currentRangeStr = "1mA";
                    break;
                case (byte)CurrentRanges.cr5mA:
                    currentRangeStr = "15mA";
                    break;
                case (byte)CurrentRanges.hscr100nA:
                    currentRangeStr = "100nA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr1uA:
                    currentRangeStr = "1uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr6uA:
                    currentRangeStr = "6uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr13uA:
                    currentRangeStr = "13uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr25uA:
                    currentRangeStr = "25uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr50uA:
                    currentRangeStr = "50uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr100uA:
                    currentRangeStr = "100uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr200uA:
                    currentRangeStr = "200uA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr1mA:
                    currentRangeStr = "1mA (High speed)";
                    break;
                case (byte)CurrentRanges.hscr5mA:
                    currentRangeStr = "5mA (High speed)";
                    break;
            }
            Console.Write(String.Format("CR : {0,-5} {1,2}", currentRangeStr, " "));
        }

        /// <summary>
        /// Parses the noise from the package.
        /// </summary>
        /// <param name="metaDataNoise"></param>
        private static void GetNoiseFromPackage(string metaDataNoise)
        {

        }

        /// <summary>
        /// Parses the data value package and appends the respective SI unit prefixes
        /// </summary>
        /// <param name="paramValueString">The data value package to be parsed</param>
        /// <returns>The actual data value after appending the unit prefix</returns>
        private static double ParseParamValues(string paramValueString)
        {
            char strUnitPrefix = paramValueString[7];                         //Identifies the SI unit prefix from the package at position 8
            string strvalue = paramValueString.Remove(7);                     //Retrieves the value of the variable the package
            int value = Convert.ToInt32(strvalue, 16);                        //Converts the hex value to int
            double paramValue = value - OFFSET_VALUE;                         //Values offset to receive only positive values
            return (paramValue * SI_Prefix_Factor[strUnitPrefix.ToString()]); //Returns the actual data value after appending the SI unit prefix
        }
    }
}
