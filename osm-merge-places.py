#!/usr/bin/env python
# vim: set fileencoding=utf-8 et :
# txt2osm, an UnofficialMapProject .txt to OpenStreetMap .osm converter.
# Copyright (C) 2008  Mariusz Adamski, rhn
# Copyright (C) 2009  Andrzej Zaborowski
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import sys
import time
import math
from xml.sax import saxutils

__version__ = '0.1.1'

# Main program.

pts = {}

maxdist = 0.10 # degree

# places = [ 'hamlet', 'village', 'region', 'town', 'city' ]

def distance(id, lat, lon):
    return math.hypot(pts[id]['lat'] - lat, pts[id]['lon'] - lon)

def trydelete(name, lat, lon, place):
    for osmid in pts:
        if pts[osmid]['att']['name'] == name:
            if distance(osmid, lat, lon) < maxdist:
                pts[osmid]['matches'] = 1
                if pts[osmid]['att']['place'] != place:
                    pts[osmid]['dont'] = 1

afile = open(sys.argv[1], "r")
bfile = open(sys.argv[2], "r")
lat = ""
lon = ""
id = 0
ignore = [ 'is_in', 'name', 'place', 'created_by', 'source' ]
attrs = {}
state = 0
for line in afile:
    if state == 0 and line.find("<node") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("id=") + 1]
        lat = el[el.index("lat=") + 1]
        lon = el[el.index("lon=") + 1]
        attrs = {}
        state = 1
        if line.find(" />") > -1:
            state = 0
    elif state == 1 and line.find("k='") > -1:
        el = line.split("'")
        attrs[el[1]] = el[el.index(" v=") + 1]
    elif state == 1 and line.find("</node") > -1:
        state = 0
        if 'place' in attrs:
            pts[id] = {
                'c':   0,
                'id':  id,
                'lat': float(lat),
                'lon': float(lon),
                'att': attrs
            }
            for key in attrs:
                if key not in ignore:
                    pts[id]['dont'] = 1

    if state == 0 and line.find("<way") > -1:
        state = 2
    elif state == 2 and line.find("</way") > -1:
        state = 0
    elif state == 2 and line.find("<nd") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("ref=") + 1]
        if id in pts:
            pts[id]['att']['dont'] = 1;

    if state == 0 and line.find("<relation") > -1:
        state = 3
    elif state == 3 and line.find("</relation") > -1:
        state = 0
    elif state == 3 and line.find("<member type='node'") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("ref=") + 1]
        if id in pts:
            pts[id]['att']['dont'] = 1;

state = 0
for line in bfile:
    if state == 0 and line.find("<node") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("id=") + 1]
        lat = el[el.index("lat=") + 1]
        lon = el[el.index("lon=") + 1]
        attrs = {}
        state = 1
        if line.find(" />") > -1:
            state = 0
    elif state == 1 and line.find("k='") > -1:
        el = line.split("'")
        attrs[el[1]] = el[el.index(" v=") + 1]
    elif state == 1 and line.find("</node") > -1:
        state = 0
        if 'place' in attrs:
            trydelete(attrs['name'], float(lat), float(lon), attrs['place'])

afile.close()
bfile.close()

afile = open(sys.argv[1], "r")
state = 0
out = 1
newline = ""
for line in afile:
    if state == 0 and line.find("<node") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("id=") + 1]
        state = 1
        if line.find(" />") > -1:
            state = 0

        elif id in pts:
            if 'matches' in pts[id]:
                if 'dont' in pts[id]:
                    newline = "    <tag k='mergeme' v='yes' />\n"
                elif int(id) < 0:
                    out = 0
                elif el.count('action='):
                    if el[el.index('action=') + 1] == 'modify':
                        line = line.replace('modify', 'delete', 1)
                    elif el[el.index('action=') + 1] == 'delete':
                        pass
                    else:
                        throw
                else:
                    line = line.replace('<node', "<node action='delete'", 1)

    if out:
        sys.stdout.write(line)
    sys.stdout.write(newline)
    newline = ""

    if state == 1 and line.find("</node") > -1:
        state = 0
        out = 1

afile.close()

#for pt in pts:
#    print "(%s, %s) is from %s\n" % (pt[0], pt[1], pts[pt])
