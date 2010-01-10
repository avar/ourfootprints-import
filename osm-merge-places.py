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

# places = [ 'hamlet', 'village', 'region', 'town', 'city', 'locality' ]

def distance(id, lat, lon):
    return math.hypot(pts[id]['lat'] - lat, pts[id]['lon'] - lon)

def mexpand(piece):
    if piece in [ u'kol', u'kol.' ]:
        return u'kolonia'
    if piece in [ u'pierwszy', u'pierwsze', u'pierwsza', u'1' ]:
        return u'i'
    if piece in [ u'drugi', u'drugie', u'druga', u'2' ]:
        return u'ii'
    if piece in [ u'trzeci', u'trzecie', u'trzecia', u'3' ]:
        return u'iii'
    if piece in [ u'wlk.', u'wielkie', u'wielka', u'wielki' ]:
        return u'wlk'
    if piece in [ u'dz.', u'duze', u'duza', u'duzy', u'duże', u'duża', u'duży' ]:
        return u'dz'
    if piece in [ u'ml.', u'male', u'mala', u'maly', u'małe', u'mała', u'mały' ]:
        return u'ml'
    if piece in [ u'str.', u'stare', u'stara', u'stary', u'st', u'str' ]:
        return u'str'
    if piece in [ u'nw.', u'nowe', u'nowa', u'nowy', u'n', u'n.' ]:
        return u'nw'
    if piece in [ u'dln.', u'dolne', u'dolna', u'dolny', u'dol', u'dol.' ]:
        return u'dln'
    if piece in [ u'grn.', u'gorne', u'gorna', u'gorny', u'gor', u'gor.',
            u'gór', u'gór.', u'górne', u'górna', u'górny' ]:
        return u'grn'
    if piece in [ u'k.', u'k', u'koło' ]:
        return u'kolo'
    if piece in [ u'maz', u'maz.', u'mazowieckie', u'mazowiecka' ]:
        return u'mazowiecki'
    if piece in [ u'wlkp', u'wlkp.', u'wielkopolskie', u'wielkopolska' ]:
        return u'wielkopolski'
    if piece in [ u'sl', u'sl.', u'śl', u'śl.', u'slaskie', u'slaska',
            u'śląskie', u'śląska', u'śląski' ]:
        return u'slaski'
    return piece.replace(u'ó', 'o').replace(u'ł', 'l').replace(u'ź', 'z').\
            replace(u'ż', 'z').replace(u'ą', 'a').replace(u'ę', 'e').\
            replace(u'ć', 'c').replace(u'ś', 's').replace(u'ń', 'n')

def msplit(name):
    split = name.lower().replace('-', ' ').split(' ')
    split = [ mexpand(n.strip()) for n in split if n.strip() != '' ]
    return split

def mnamematch(a, b):
    # TODO generate the splits on load
    a = msplit(a)
    b = msplit(b)
    for n in a:
        if n not in b:
            return 0
    for n in b:
        if n not in a:
            return 0
    return 1

def isround(num):
    (num, dummy) = math.modf(num * 10.0)
    epsilon = 0.00001
    for i in [ 0.0, 0.166667, 0.333333, 0.5, 0.666667, 0.833333 ]:
        if num >= i - epsilon and num <= i + epsilon:
            return 1
    return 0

def trydelete(name, lat, lon, place, id):
    for osmid in pts:
        if mnamematch(pts[osmid]['att']['name'], name):
            if distance(osmid, lat, lon) < maxdist:
                pts[osmid]['matches'] = 1
                pts[osmid]['newpos'] = (lat, lon, id)
                if not isround(pts[osmid]['lat']):
                    pts[osmid]['dont'] = 3
                if not isround(pts[osmid]['lon']):
                    pts[osmid]['dont'] = 3
                if pts[osmid]['att']['name'] != name:
                    pts[osmid]['dont'] = 1
                if pts[osmid]['att']['place'] != place:
                    pts[osmid]['dont'] = 1

import locale, codecs
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
encoding = locale.getlocale()[1]
sys.stdout = codecs.getwriter(encoding)(sys.stdout, errors = "replace")
sys.stderr = codecs.getwriter(encoding)(sys.stderr, errors = "replace")

afile = codecs.open(sys.argv[1], "r", "utf-8")
bfile = codecs.open(sys.argv[2], "r", "utf-8")
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
            if 'name' not in attrs:
                sys.stderr.write("No name for node " + str(id) + "\n")
                continue
            pts[id] = {
                'c':   0,
                'id':  id,
                'lat': float(lat),
                'lon': float(lon),
                'att': attrs
            }
            for key in attrs:
                if key not in ignore:
                    pts[id]['dont'] = 2

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
            if 'name' not in attrs:
                sys.stderr.write("No name for node " + id + "\n")
                continue
            trydelete(attrs['name'], float(lat), float(lon), attrs['place'], id)

afile.close()
bfile.close()

afile = codecs.open(sys.argv[1], "r", "utf-8")
state = 0
out = 1
newline = ""
deleteme = {}
for line in afile:
    if state == 0 and line.find("<node") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("id=") + 1]
        lat = el.index("lat=") + 1
        lon = el.index("lon=") + 1
        state = 1
        if line.find(" />") > -1:
            state = 0

        elif id in pts:
            if 'matches' in pts[id]:
                if 'dont' in pts[id]:
                    if pts[id]['dont'] == 2:
                        if el.count('action='):
                            pass
                        else:
                            line = line.replace('<node',
                                            "<node action='modify'", 1)
                        line = line.replace("lat='" + el[lat],
                                        "lat='" + str(pts[id]['newpos'][0]))
                        line = line.replace("lon='" + el[lon],
                                        "lon='" + str(pts[id]['newpos'][1]))
                        deleteme[pts[id]['newpos'][2]] = 1
                    elif pts[id]['dont'] == 3:
                        if el.count('action='):
                            pass
                        else:
                            line = line.replace('<node',
                                            "<node action='modify'", 1)
                        vlat = float(el[lat])
                        vlat += 0.3 * (pts[id]['newpos'][0] - vlat)
                        vlon = float(el[lon])
                        vlon += 0.3 * (pts[id]['newpos'][1] - vlon)
                        line = line.replace("lat='" + el[lat],
                                        "lat='" + str(vlat))
                        line = line.replace("lon='" + el[lon],
                                        "lon='" + str(vlon))
                        deleteme[pts[id]['newpos'][2]] = 1
                    else:
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

bfile = codecs.open(sys.argv[2], "r", "utf-8")
state = 0
out = 1
for line in bfile:
    if state == 0 and line.find("<node") > -1:
        el = line.replace("'", ' ').split()
        id = el[el.index("id=") + 1]
        state = 1
        if line.find(" />") > -1:
            state = 0

        elif id in deleteme:
            out = 0

    if out:
        sys.stdout.write(line)
    sys.stdout.write(newline)

    if state == 1 and line.find("</node") > -1:
        state = 0
        out = 1

bfile.close()

#for pt in pts:
#    print "(%s, %s) is from %s\n" % (pt[0], pt[1], pts[pt])
