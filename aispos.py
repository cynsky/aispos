#!/usr/bin/env python

import serial
import ais
import re
import json
import math

ser = serial.Serial("/dev/ttyUSB0", 38400)
serout = serial.Serial("/dev/ttyUSB1", 4800)

while(True):
    line = ser.readline()
    line = line.decode('ISO-8859-1')
    if re.match("\!AIVDM,1", line):
        try:
            aismsg = line.split(',')
            aisdata = ais.decode(aismsg[5], int(aismsg[6][:1]))
            #aisdata = ais.decode(aismsg[5], 0)
            if aisdata['mmsi'] == 258968000:
                lat = aisdata['y']
                lon = aisdata['x']
                dlat = str(math.floor(lat)).zfill(2)
                mlat = str((((lat - math.floor(lat)) *60 ) % 60)).zfill(2)
                dlon = str(math.floor(lon)).zfill(2)
                mlon = str((((lon - math.floor(lon)) *60 ) % 60)).zfill(2)
                outstring = "$GPGGA,131313.13," + dlat+mlat + ",N," + dlon+mlon + ",E,1,08,0.9,5,M\r\n"
                serout.write(bytes(outstring, "UTF-8")) 
                print(outstring)

        except:
            pass
