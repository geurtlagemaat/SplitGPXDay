# Split GPX Per Day
Parses a directory with Garmin Zumo GPX track files (tested on Zumo 350),
and writes the trackpoint in daily files (sorted on trackpoint date time and duplicates removed).

Ready for import in Google Maps.

usage
python GPXSplitter.py GPXFilelocation

**Warning**
GPXSplitter will remove (if exists) the "export" folder inside the given GPXFilelocation and create a new one.