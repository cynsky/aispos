#!/usr/bin/env python

import serial
import ais
import re
import json
import math
import datetime
from queue import Queue
from threading import Thread
from time import sleep


ser = serial.Serial("/dev/ttyUSB0", 38400)
serout = serial.Serial("/dev/ttyUSB1", 4800)

dataq = Queue(maxsize=0)

def checksum(sentence):
    calc_chksum = 0
    for s in sentence:
        calc_chksum ^= ord(s)
    return '*'+hex(calc_chksum)[-2:].upper()

def newpos(lat,lon,d,a):
    R = 6378.1 
    brng = math.radians(a)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    lat2 = math.asin(math.sin(lat1)*math.cos(d/R)+math.cos(lat1)*math.sin(d/R)*math.cos(brng))
    lon2 = lon1+math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),math.cos(d/R)-math.sin(lat1)*math.sin(lat2))
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    return lat2,lon2

def bearingdistance(lat1,lon1,lat2,lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1,lat1,lon2,lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = 6378.1 * c
    bearing = math.atan2(math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1),math.sin(lon2-lon1)*math.cos(lat2))
    bearing = math.degrees(bearing)+180
    return bearing,distance

def serialhandle():
    while(True):
        line = ser.readline()
        line = line.decode('ISO-8859-1')
        if re.match("\!AIVDM,1", line):
            aismsg = line.split(',')
            aisdata = ais.decode(aismsg[5], int(aismsg[6][:1]))
            if aisdata['mmsi'] == 258968000:
                lat = aisdata['y']
                lon = aisdata['x']
                now = datetime.datetime.now()
                dataq.put([lat,lon,now])

def datahandle():
    gotpos = False
    lastlat = 0
    lastlon = 0
    lasttime = 0
    timer = 0
    bearing = 0
    distance = 0
    counter = 1
    ddist = 0
    while(True):
        while not dataq.empty():
            if(gotpos):
                timer = ((time - lasttime).total_seconds())
                lastlat = lat
                lastlon = lon
                lasttime = time
            lat,lon,time = dataq.get()
            bearing,distance = bearingdistance(lastlat,lastlon,lat,lon)
            counter = 1
            if timer > 0:
                ddist = distance / timer 
            if not gotpos:
                gotpos = True 
                lastlat = lat
                lastlon = lon
                lasttime = time
                timer = ((time - lasttime).total_seconds())
        if(gotpos):
            lastlat,lastlon = newpos(lat,lon,ddist*counter,bearing)
            ns = 'N' if lat > 0 else 'S'
            we = 'E' if lat > 0 else 'W'
            dlat = str(math.floor(lastlat)).zfill(2)
            mlat = str("%.5f" % (((lastlat - math.floor(lastlat)) *60 ) % 60)).zfill(2)
            dlon = str(math.floor(lon)).zfill(2)
            mlon = str("%.5f" % (((lastlon - math.floor(lastlon)) *60 ) % 60)).zfill(2)
            outstring = "$GPGGA,"+time.strftime('%H%M%S')+"," + dlat+mlat + ","+ns+"," + dlon+mlon + ","+we+",1,08,0.9,5,M,,"
            chk = checksum(outstring[1:])
            outstring = outstring + chk + '\r\n'
            serout.write(bytes(outstring, "UTF-8")) 
            print(outstring.replace('\n',''))
            #print(bearingdistance(lastlat,lastlon,lat,lon))
            #print(ddist)
            #print(ddist,counter,bearing,outstring)
            #print(lastlat,lastlon)
            sleep(1)
            counter += 1
        
serialt = Thread(target=serialhandle)
serialt.start()
datat = Thread(target=datahandle)
datat.start()
