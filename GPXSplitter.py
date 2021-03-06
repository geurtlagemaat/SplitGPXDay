import os, shutil
import string
from collections import OrderedDict
from glob import glob

from datetime import datetime
from time import sleep

import argparse

import sys
from lxml import etree

GPXDATAPATH = "C:\Projecten\Oriana\Bliknet\SplitGPXDay\gpxdata\/2015"

GPXNAMESPACE_URL = 'http://www.topografix.com/GPX/1/1'
TRACKPOINTEXTENSIONS= 'http://www.garmin.com/xmlschemas/TrackPointExtension/v2'
GPXNAMESPACES = { 'gpx' : GPXNAMESPACE_URL, 'gpxtpx' : TRACKPOINTEXTENSIONS}

GPXXSDLCOATION = "http://www.topografix.com/gpx/1/1/gpx.xsd"

GPXFILETEMPLATE = "<?xml version='1.0' encoding='UTF-8' standalone='no' ?>\
                   <gpx xmlns='http://www.topografix.com/GPX/1/1' \
                        xmlns:gpxtpx='http://www.garmin.com/xmlschemas/TrackPointExtension/v2' \
                        creator='zumo 350' version='1.1' \
                        xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' \
                        xsi:schemaLocation='http://www.topografix.com/GPX/1/1 \
                        http://www.topografix.com/GPX/1/1/gpx.xsd \
                        http://www.garmin.com/xmlschemas/GpxExtensions/v3 \
                        http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd \
                        http://www.garmin.com/xmlschemas/TrackPointExtension/v2 \
                        http://www.garmin.com/xmlschemas/TrackPointExtensionv2.xsd \
                        http://www.garmin.com/xmlschemas/TripExtensions/v1 \
                        http://www.garmin.com/xmlschemas/TripExtensionsv1.xsd'>\
                   </gpx>"



def parseGPXFilesToDict(gpxlocation):
    """
    parse all *.gpx files in gpxlocation (recursive) to a dictionary
    :param gpxlocation: location to GPX Files to be parsed
    :type gpxlocation: string
    :return: dictionary containing trackpoint info
    """
    GPXPoints = {}
    myFiles = [y for x in os.walk(gpxlocation) for y in glob(os.path.join(x[0], '*.gpx'))]
    for myFile in myFiles:
        print "parsing: %s" % myFile
        gpxDom = etree.parse(myFile)
        trkpts = gpxDom.xpath('//gpx:trkpt', namespaces=GPXNAMESPACES)
        # get all trkpt elements and store there data in a dictionary
        for trkpt in trkpts:
            trkptDateTime = trkpt.xpath('gpx:time', namespaces=GPXNAMESPACES)[0]
            readTimeStamp = trkptDateTime.text
            gpxTimestamp = None
            # remove zulu marking (not needed for building correct sequence & sorting
            if readTimeStamp.endswith('Z'):
                readTimeStamp = string.replace(readTimeStamp, 'Z', '')
                gpxTimestamp = datetime.strptime(readTimeStamp, '%Y-%m-%dT%H:%M:%S')
            else:
                gpxTimestamp = datetime.strptime(readTimeStamp, '%Y-%m-%dT%H:%M:%S')
            if gpxTimestamp is not None:
                GPXPoints[gpxTimestamp] = trkptToDics(trkpt=trkpt)  # TODO duplicates will be handled correct? or check differences?
    return OrderedDict(sorted(GPXPoints.items(), key=lambda t: t[0]))

def trkptToDics(trkpt):
    """
    Parses lxml trackpoint element subtree to a dictionary
    :param trkpt: lxml Element using GPX format (See below)
    :return: dict with trackpoint info
    <trkpt lat="52.244421" lon="6.223868">
        <ele>-35.43</ele>
        <time>2013-05-31T09:11:08Z</time>
        <extensions>
            <gpxtpx:TrackPointExtension>
                <gpxtpx:speed>4.12</gpxtpx:speed>
                <gpxtpx:course>163.76</gpxtpx:course>
            </gpxtpx:TrackPointExtension>
        </extensions>
    </trkpt>
    """
    lat = trkpt.get('lat')
    lon = trkpt.get('lon')
    trkptDateTime = trkpt.xpath('gpx:time', namespaces=GPXNAMESPACES)[0].text
    elev = trkpt.xpath('gpx:ele', namespaces=GPXNAMESPACES)[0].text
    myTrkpt = {'lat':lat,'lon':lon, 'time':trkptDateTime,'elev':elev}
    if len(trkpt.xpath('gpx:extensions/gpxtpx:TrackPointExtension/gpxtpx:course', namespaces=GPXNAMESPACES))>0:
        myTrkpt['course']=trkpt.xpath('gpx:extensions/gpxtpx:TrackPointExtension/gpxtpx:course', namespaces=GPXNAMESPACES)[0].text
    if len(trkpt.xpath('gpx:extensions/gpxtpx:TrackPointExtension/gpxtpx:speed', namespaces=GPXNAMESPACES))>0:
        myTrkpt['speed']=trkpt.xpath('gpx:extensions/gpxtpx:TrackPointExtension/gpxtpx:speed', namespaces=GPXNAMESPACES)[0].text
    return myTrkpt

def dictToFile(GPXPoints, datetimeStamp, exportDir):
    """
    Write a dictionary of trackpoints to a file using date as filename
    :param GPXPoints:  trackpoint info
    :type GPXPoints: dictionary
    :param datetimeStamp: datetime with the date of the GPX track
    :type datetimeStamp:: datetime
    :param exportDir: string with the export location
    :type exportDir: string
    :return: nothing
    """

    if len(dayGPXPoints) > 0:
        sortedGPXPoints = OrderedDict(sorted(GPXPoints.items(), key=lambda t: t[0]))
        gpxElem = etree.fromstring(GPXFILETEMPLATE)
        metaDataElem = etree.SubElement(gpxElem, '{%s}metadata' % GPXNAMESPACE_URL)
        timeElem = etree.SubElement(metaDataElem, '{%s}time' % GPXNAMESPACE_URL)
        # 2013-08-14T11:33:29Z
        timeElem.text = datetime.strftime(datetimeStamp, '%Y-%m-%dT%H:%M:%SZ')

        trkElem = etree.SubElement(gpxElem, '{%s}trk' % GPXNAMESPACE_URL)

        nameElem = etree.SubElement(trkElem, '{%s}name' % GPXNAMESPACE_URL)
        dayString = datetime.strftime(datetimeStamp, '%Y-%m-%d')
        nameElem.text = "Logboek: %s." % dayString

        trksegElem = etree.SubElement(trkElem, '{%s}trkseg' % GPXNAMESPACE_URL)

        for datetimeStamp, GPXPoint in sortedGPXPoints.iteritems():
            trkptElem = etree.SubElement(trksegElem, "{%s}trkpt" % GPXNAMESPACE_URL)
            trkptElem.set('lat', GPXPoint['lat'])
            trkptElem.set('lon', GPXPoint['lon'])

            eleElem = etree.SubElement(trkptElem, "{%s}ele"% GPXNAMESPACE_URL)
            eleElem.text = GPXPoint['elev']

            timeElem = etree.SubElement(trkptElem, "{%s}time"% GPXNAMESPACE_URL)
            timeElem.text = GPXPoint['time']
            if 'course' or 'speed' in GPXPoint.keys():
                extensionsElem = etree.SubElement(trkptElem, "{%s}extensions" % GPXNAMESPACE_URL)
                trackPointExtElem = etree.SubElement(extensionsElem, "{%s}TrackPointExtension" % TRACKPOINTEXTENSIONS)
                if 'course' in GPXPoint.keys():
                    courseElem = etree.SubElement(trackPointExtElem, "{%s}course" % TRACKPOINTEXTENSIONS)
                    courseElem.text = GPXPoint['course']
                if 'speed' in GPXPoint.keys():
                    speedElem = etree.SubElement(trackPointExtElem, "{%s}speed" % TRACKPOINTEXTENSIONS)
                    speedElem.text = GPXPoint['speed']

        exportFileName = os.path.join(exportDir, "%s.gpx" % datetime.strftime(datetimeStamp, '%Y%m%d'))
        exportXMLString = etree.tostring(gpxElem, pretty_print=True)
        try:
            with open(exportFileName, "w") as text_file:
                text_file.write(exportXMLString)
                print "save: %s done." % exportFileName
        except:
            print "error writing GPXData to %s." % exportFileName

def daysFromEpoch(date):
    epoch = datetime.utcfromtimestamp(0)
    d = date - epoch
    return d.days

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("gpxlocation", help="The location where the GPX files are located (parsing is recursive)", \
                        type=str)
    args = parser.parse_args()
    gpxlocation = args.gpxlocation
    if not os.path.isdir(gpxlocation):
        print "gpxlocation %s does not exits" % gpxlocation
        sys.exit()
    else:
        exportDir = os.path.join(gpxlocation, 'export')
        if os.path.isdir(exportDir):
            print "Removing existing export location: %s" % exportDir
            shutil.rmtree(exportDir)
            sleep(2) # give some time
        os.makedirs(exportDir)
        gpxPoints = parseGPXFilesToDict(gpxlocation=gpxlocation)

        # create and write GPX file per day
        exportDateTime = None
        dayGPXPoints = {}
        for datetimeStamp, GPXPoint in gpxPoints.iteritems():
            if exportDateTime is None:
                exportDateTime = datetimeStamp
            elif daysFromEpoch(date=datetimeStamp) > daysFromEpoch(date=exportDateTime):
               dictToFile(GPXPoints=dayGPXPoints, datetimeStamp=exportDateTime,exportDir=exportDir)
               # clear dict and start new
               dayGPXPoints.clear()
               exportDateTime=datetimeStamp
            dayGPXPoints[datetimeStamp]=GPXPoint
        # last day
        dictToFile(GPXPoints=dayGPXPoints, datetimeStamp=exportDateTime, exportDir=exportDir)
        dayGPXPoints.clear()
        print "ready!"