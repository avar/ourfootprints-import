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

pline_types = {
    0x1:  [ "highway",  "motorway" ],
    0x2:  [ "highway",  "trunk" ],
    0x3:  [ "highway",  "primary" ],
    0x4:  [ "highway",  "secondary" ],
    0x5:  [ "highway",  "tertiary" ],
    0x6:  [ "highway",  "residential" ],
    0x7:  [ "highway",  "living_street" ],
    0x8:  [ "highway",  "primary_link" ],
    0x9:  [ "highway",  "secondary_link" ],
    0xa:  [ "highway",  "unclassified", "surface", "unpaved" ],
    0xb:  [ "highway",  "trunk_link" ],
    0xc:  [ "junction", "roundabout" ],
    0xd:  [ "highway",  "cycleway" ],
    0xe:  [ "highway",  "service", "tunnel", "yes" ],
    0x14: [ "railway",  "rail" ],
    0x16: [ "highway",  "track" ],
    0x18: [ "waterway", "stream" ],
    0x19: [ "_rel",     "restriction" ],
    0x1a: [ "route",    "ferry" ],
    0x1b: [ "route",    "ferry" ],
    0x1c: [ "boundary", "administrative", "admin_level", "8" ],
    0x1d: [ "boundary", "administrative", "admin_level", "4" ],
    0x1e: [ "boundary", "administrative", "admin_level", "2" ],
    0x1f: [ "waterway", "canal" ],
    0x20: [ "barrier",  "wall" ],
    0x21: [ "barrier",  "wall" ],
    0x22: [ "barrier",  "city_wall" ],
    0x23: [ "highway",  "track", "note", "fixme" ],
    0x24: [ "highway",  "road" ],
    0x25: [ "barrier",  "retaining_wall" ],
    0x26: [ "waterway", "drain" ],
    0x27: [ "aeroway",  "runway" ],
    0x28: [ "man_made", "pipeline" ],
    0x29: [ "power",    "line", "barrier", "retaining_wall",
            "note",     "fixme: choose one" ],
    0x2a: [ "note",     "fixme" ],
    0x2c: [ "boundary", "historical", "admin_level", "2" ],
    0x44: [ "boundary", "administrative", "admin_level", "9" ],
    0x4b: [ "note",     "fixme" ],

    0xe00: [ "highway", "footway", "ref", "Czerwony szlak",
             "marked_trail_red", "yes" ],
    0xe01: [ "highway", "footway", "ref", "Żółty szlak",
             "marked_trail_yellow", "yes" ],
    0xe02: [ "highway", "footway", "ref", "Zielony szlak",
             "marked_trail_green", "yes" ],
    0xe03: [ "highway", "footway", "ref", "Niebieski szlak",
             "marked_trail_blue", "yes" ],
    0xe04: [ "highway", "footway", "ref", "Czarny szlak",
             "marked_trail_black", "yes" ],
    0xe07: [ "highway", "footway", "ref", "Szlak", "note", "TODO" ],
    0xe08: [ "highway", "cycleway", "ref", "Czerwony szlak",
             "marked_trail_red", "yes" ],
    0xe09: [ "highway", "cycleway", "ref", "Żółty szlak",
             "marked_trail_yellow", "yes" ],
    0xe0a: [ "highway", "cycleway", "ref", "Zielony szlak",
             "marked_trail_green", "yes" ],
    0xe0b: [ "highway", "cycleway", "ref", "Niebieski szlak",
             "marked_trail_blue", "yes" ],
    0xe0c: [ "highway", "cycleway", "ref", "Czarny szlak",
             "marked_trail_black", "yes" ],
    0xe0f: [ "highway", "cycleway", "ref", "Szlak", "note", "TODO" ],

    0xe10: [ "railway", "tram" ],
    0xe11: [ "railway", "abandoned" ],

    0x6702: [ "highway", "track" ]
}
shape_types = {
    0x1:  [ "landuse",  "residential" ],
    0x2:  [ "landuse",  "residential" ],
    0x3:  [ "highway",  "pedestrian", "area", "yes" ],
    0x4:  [ "landuse",  "military" ],
    0x5:  [ "amenity",  "parking" ],
    0x6:  [ "amenity",  "parking", "building", "garage" ],
    0x7:  [ "building", "terminal", "fixme", "Tag manually!" ],
    0x8:  [ "landuse",  "retail", "building", "shops", "shop", "fixme",
            "fixme",    "Tag manually!" ],
    0x9:  [ "leisure",  "marina" ], # a wild guess
    0xa:  [ "amenity",  "school", "building", "hall" ],
    0xb:  [ "amenity",  "hospital", "building", "hall" ],
    0xc:  [ "landuse",  "industrial" ], # a wild guess
    0xd:  [ "landuse",  "construction" ],
    0xe:  [ "aeroway",  "aerodrome" ],
    0x13: [ "building", "yes" ],
    0x14: [ "military", "barracks", "natural", "wood",
            "note",     "TODO: fixme - choose one" ], # usage varies :(
    0x15: [ "natural",  "wood" ],
    0x16: [ "natural",  "wood" ],
    0x17: [ "leisure",  "park" ],
    0x18: [ "leisure",  "pitch", "sport", "tennis" ],
    0x19: [ "leisure",  "pitch" ], # or stadium...
    0x1a: [ "landuse",  "cemetery" ],
    0x1e: [ "landuse",  "forest", "leisure", "nature_reserve" ],
    0x1f: [ "landuse",  "forest", "leisure", "nature_reserve" ],
    0x20: [ "tourism",  "attraction" ], # a wild guess (forest?)
    0x28: [ "natural",  "coastline" ],
    0x29: [ "natural",  "water" ],
    0x32: [ "natural",  "coastline" ],
    0x3b: [ "natural",  "water" ], # how does this differ from 0x40?
    0x3c: [ "natural",  "water" ], # how does this differ from 0x40?
    0x3d: [ "natural",  "water" ], # how does this differ from 0x40?
    0x3e: [ "natural",  "water" ], # how does this differ from 0x40?
    0x3f: [ "natural",  "water" ], # how does this differ from 0x40?
    0x40: [ "natural",  "water" ],
    0x41: [ "natural",  "water", "amenity", "fountain" ],
    0x42: [ "landuse",  "reservoir" ], # how does this differ from 0x40?
    0x43: [ "landuse",  "reservoir" ], # how does this differ from 0x40?
    0x44: [ "landuse",  "reservoir" ], # how does this differ from 0x40?
    0x45: [ "landuse",  "reservoir" ], # how does this differ from 0x40?
    0x46: [ "waterway", "riverbank" ],
    0x47: [ "waterway", "riverbank" ], # how does this differ from 0x46?
    0x48: [ "waterway", "riverbank" ], # how does this differ from 0x46?
    0x49: [ "waterway", "riverbank" ], # how does this differ from 0x46?
    0x4a: [ "highway",  "residential", "oneway", "yes" ],
    0x4c: [ "natural",  "water" ], # how does this differ from 0x40?
    0x4d: [ "natural",  "glacier" ],
    0x4e: [ "landuse",  "allotments" ],
    0x4f: [ "landuse",  "farm" ],
    0x50: [ "natural",  "wood" ],
    0x51: [ "natural",  "wetland" ],
    0x52: [ "leisure",  "garden", "tourism", "zoo" ],
    0x53: [ "landuse",  "landfill" ],
}
poi_types = {
    0x04:   [ "place",    "city" ],
    0x05:   [ "place",    "city" ],
    0x06:   [ "place",    "city" ],
    0x07:   [ "place",    "city" ],
    0x08:   [ "place",    "town" ],
    0x08:   [ "place",    "town" ],
    0x09:   [ "place",    "town" ],
    0x0a:   [ "place",    "town" ],
    0x0b:   [ "place",    "town" ],
    0x0c:   [ "place",    "village" ],
    0x0d:   [ "place",    "village" ],
    0x0e:   [ "place",    "village" ],
    0x2d:   [ "amenity",  "townhall" ],

    0x0100: [ "place",    "city" ],
    0x0200: [ "place",    "city" ],
    0x0300: [ "place",    "city" ],
    0x0400: [ "place",    "city" ],
    0x0500: [ "place",    "city" ],
    0x0600: [ "place",    "city" ],
    0x0700: [ "place",    "city" ],
    0x0800: [ "place",    "city" ],
    0x0900: [ "place",    "city" ],
    0x0a00: [ "place",    "town" ],
    0x0b00: [ "place",    "town" ],
    0x0c00: [ "place",    "town" ],
    0x0d00: [ "place",    "town" ],
    0x0e00: [ "place",    "village" ],
    0x0f00: [ "place",    "village" ],
    0x1000: [ "place",    "village" ],
    0x1100: [ "place",    "village" ],
    0x1200: [ "bridge",   "yes" ],
    0x1500: [ "place",    "locality" ],
    0x1600: [ "man_made", "lighthouse" ],
    0x1602: [ "note",     "fixme" ],
    0x1605: [ "amenity",  "citymap_post", "tourism", "information" ],
    0x1606: [ "man_made", "beacon", "mark_type", "buoy" ],
    0x1607: [ "man_made", "beacon", "mark_type", "safe_water" ],
    0x1608: [ "man_made", "beacon", "mark_type", "lateral_left" ],
    0x1609: [ "man_made", "beacon", "mark_type", "lateral_right" ],
    0x160a: [ "man_made", "beacon", "mark_type", "isolated_danger" ],
    0x160b: [ "man_made", "beacon", "mark_type", "special" ],
    0x160c: [ "man_made", "beacon", "mark_type", "cardinal" ],
    0x160d: [ "man_made", "beacon", "mark_type", "other" ],
    0x160e: [ "amenity",  "signpost" ],
    0x160f: [ "man_made", "beacon", "mark_type", "white" ],
    0x1610: [ "man_made", "beacon", "mark_type", "red" ],
    0x1611: [ "man_made", "beacon", "mark_type", "green" ],
    0x1612: [ "man_made", "beacon", "mark_type", "yellow" ],
    0x1613: [ "man_made", "beacon", "mark_type", "orange" ],
    0x1614: [ "man_made", "beacon", "mark_type", "magenta" ],
    0x1615: [ "man_made", "beacon", "mark_type", "blue" ],
    0x1616: [ "man_made", "beacon", "mark_type", "multicolored" ],
    0x1708: [ "shop",     "fixme" ],
    0x1709: [ "bridge",   "yes" ],
    0x1710: [ "barrier",  "gate" ],
    0x1712: [ "landuse",  "construction" ],
    0x170a: [ "fixme",    "deleteme" ],
    0x170d: [ "fixme",    "deleteme" ],
    0x190b: [ "highway",  "construction" ],
    0x1a10: [ "man_made", "beacon" ],
    0x1b00: [ "note",     "fixme" ],
    0x1b02: [ "natural",  "peak" ],
    0x1b05: [ "amenity",  "signpost" ],
    0x1b0f: [ "aeroway",  "taxiway" ],
    0x1c00: [ "barrier",  "obstruction" ],
    0x1c01: [ "man_made", "ship_wreck" ],
    0x1c07: [ "barrier",  "obstruction", "visibility", "no" ],
    0x1c09: [ "note",     "fixme" ],
    0x1e00: [ "place",    "region" ],
    0x1f00: [ "place",    "region" ],
    0x2000: [ "highway",  "motorway_junction" ],
    0x2100: [ "highway",  "motorway_junction", "amenity", "parking" ],
    0x2110: [ "highway",  "motorway_junction", "amenity", "parking" ],
    0x2200: [ "highway",  "motorway_junction" ],
    0x2500: [ "highway",  "motorway_junction", "barrier", "toll_booth" ],
    0x2600: [ "bridge",   "yes" ],
    0x2700: [ "highway",  "motorway_junction" ],
    0x2800: [ "place",    "region" ], # Seems to be used villages though
    0x2900: [ "landuse",  "commercial" ],
    0x2a:   [ "amenity",  "restaurant" ],
    0x2a00: [ "amenity",  "restaurant" ],
    0x2a01: [ "amenity",  "restaurant", "cuisine", "american" ],
    0x2a02: [ "amenity",  "restaurant", "cuisine", "asian" ],
    0x2a03: [ "amenity",  "restaurant", "cuisine", "barbecue" ],
    0x2a04: [ "amenity",  "restaurant", "cuisine", "chinese" ],
    0x2a05: [ "shop",     "bakery" ],
    0x2a06: [ "amenity",  "pub" ],
    0x2a07: [ "amenity",  "fast_food",  "cuisine", "burger" ],
    0x2a08: [ "amenity",  "restaurant", "cuisine", "italian" ],
    0x2a09: [ "amenity",  "restaurant", "cuisine", "mexican" ],
    0x2a0a: [ "amenity",  "restaurant", "cuisine", "pizza" ],
    0x2a0b: [ "amenity",  "restaurant", "cuisine", "sea_food" ],
    0x2a0c: [ "amenity",  "restaurant", "cuisine", "grill" ],
    0x2a0d: [ "amenity",  "restaurant", "cuisine", "bagel" ], # bagle?
    0x2a0e: [ "amenity",  "cafe" ],
    0x2a0f: [ "amenity",  "restaurant", "cuisine", "french" ],
    0x2a10: [ "amenity",  "restaurant", "cuisine", "german" ],
    0x2a11: [ "amenity",  "restaurant", "cuisine", "british" ],
    0x2a12: [ "amenity",  "fast_food",  "cuisine", "international" ],
    0x2a13: [ "amenity",  "restaurant", "cuisine", "international" ],
    0x2a14: [ "amenity",  "restaurant", "cuisine", "regional" ],
    0x2b00: [ "tourism",  "hotel" ],
    0x2b01: [ "tourism",  "motel" ],
    0x2b02: [ "tourism",  "hostel" ],
    0x2b03: [ "tourism",  "camp_site" ],
    0x2b04: [ "tourism",  "hotel" ],
    0x2c00: [ "landuse",  "retail", "note", "fixme" ],
    0x2c01: [ "tourism",  "attraction", "leisure", "park" ],
    0x2c02: [ "tourism",  "museum" ],
    0x2c03: [ "amenity",  "library" ],
    0x2c04: [ "tourism",  "viewpoint" ],
    0x2c05: [ "amenity",  "school" ],
    0x2c06: [ "leisure",  "park" ],
    0x2c07: [ "tourism",  "zoo" ],
    0x2c08: [ "leisure",  "sports_centre" ],
    0x2c09: [ "amenity",  "theatre", "note", "fixme" ],
    0x2c0a: [ "amenity",  "restaurant", "cuisine", "wine_bar" ],
    0x2c0b: [ "amenity",  "place_of_worship" ],
    0x2c0c: [ "natural",  "spring", "amenity", "spa" ],
    0x2d00: [ "leisure",  "track" ],
    0x2d01: [ "amenity",  "theatre" ],
    0x2d02: [ "amenity",  "fast_food" ],
    0x2d03: [ "amenity",  "cinema" ],
    0x2d04: [ "amenity",  "nightclub" ],
    0x2d05: [ "sport",    "golf", "leisure", "golf_course" ],
    0x2d06: [ "sport",    "skiing" ],
    0x2d07: [ "sport",    "9pin" ],
    0x2d08: [ "sport",    "skating" ],
    0x2d09: [ "sport",    "swimming" ],
    0x2d0a: [ "leisure",  "stadium" ],
    0x2d0b: [ "sport",    "sailing" ],
    0x2e:   [ "shop",     "stationery" ],
    0x2e00: [ "shop",     "mall" ],
    0x2e01: [ "shop",     "department_store" ],
    0x2e02: [ "shop",     "grocery" ],
    0x2e03: [ "shop",     "fixme" ],
    0x2e04: [ "shop",     "supermarket" ],
    0x2e05: [ "amenity",  "pharmacy" ],
    0x2e06: [ "shop",     "convenience" ],
    0x2e07: [ "shop",     "clothes" ],
    0x2e08: [ "shop",     "garden_centre" ],
    0x2e09: [ "shop",     "furniture" ],
    0x2e0a: [ "shop",     "special_retail", "note", "fixme" ],
    0x2e0b: [ "shop",     "computer" ],
    0x2e0c: [ "shop",     "pets" ],
    0x2f00: [ "amenity",  "miscellaneous" ],
    0x2f01: [ "amenity",  "fuel" ],
    0x2f02: [ "amenity",  "car_rental" ],
    0x2f03: [ "shop",     "car_repair" ],
    0x2f04: [ "aeroway",  "aerodrome" ],
    0x2f05: [ "amenity",  "post_office" ],
    0x2f06: [ "amenity",  "bank" ], # Also used with amenity=bureau_de_change
    0x2f07: [ "shop",     "car" ],
    0x2f08: [ "amenity",  "bus_station" ],
    0x2f09: [ "waterway", "boatyard" ],
    0x2f0a: [ "shop",     "car_wrecker" ],
    0x2f0b: [ "amenity",  "parking" ],
    0x2f0c: [ "amenity",  "toilets" ],
    0x2f0d: [ "amenity",  "automobile_club" ],
    0x2f0e: [ "shop",     "car_wash" ],
    0x2f0f: [ "shop",     "outdoor", "operator", "Garmin" ],
    0x2f10: [ "amenity",  "personal_service" ],
    0x2f11: [ "amenity",  "public_building" ],
    0x2f13: [ "shop",     "bicycle" ],
    0x2f12: [ "amenity",  "wifi" ],
    0x2f14: [ "amenity",  "public_building" ],
    0x2f15: [ "amenity",  "public_building" ],
    0x2f16: [ "amenity",  "parking", "truck_stop", "yes" ],
    0x2f17: [ "amenity",  "travel_agency" ],
    0x3000: [ "amenity",  "public_building" ],
    0x3001: [ "amenity",  "police" ],
    0x3002: [ "amenity",  "hospital" ],
    0x3003: [ "amenity",  "public_building" ],
    0x3004: [ "amenity",  "courthouse" ],
    0x3005: [ "amenity",  "nightclub" ],
    0x3006: [ "amenity",  "border_station" ],
    0x3007: [ "amenity",  "townhall" ],
    0x3008: [ "amenity",  "fire_station" ],
    0x4000: [ "leisure",  "golf_course" ],
    0x4100: [ "landuse",  "reservoir" ],
    0x4200: [ "man_made", "ship" ],
    0x4300: [ "leisure",  "marina" ],
    0x4400: [ "amenity",  "fuel" ],
    0x4500: [ "amenity",  "restaurant" ],
    0x4600: [ "amenity",  "fast_food" ],
    0x4800: [ "tourism",  "camp_sire" ],
    0x4900: [ "leisure",  "park" ],
    0x4700: [ "waterway", "dock" ],
    0x4a00: [ "tourism",  "picnic_site" ],
    0x4b00: [ "amenity",  "hospital" ],
    0x4c00: [ "tourism",  "information" ],
    0x4d00: [ "amenity",  "parking" ],
    0x4e00: [ "amenity",  "toilets" ],
    0x5700: [ "amenity",  "police_car" ], # Fixme
    0x5000: [ "amenity",  "drinking_water" ],
    0x5100: [ "amenity",  "telephone" ],
    0x5200: [ "tourism",  "viewpoint" ],
    0x5300: [ "sport",    "skiing" ],
    0x5400: [ "sport",    "swimming" ],
    0x5500: [ "waterway", "dam" ], # Map_Features requires a way
    0x5600: [ "barrier",  "gate" ],
    0x5800: [ "amenity",  "prison" ],
    0x5900: [ "aeroway",  "aerodrome" ],
    0x5901: [ "aeroway",  "aerodrome" ],
    0x5902: [ "aeroway",  "aerodrome" ],
    0x5903: [ "aeroway",  "aerodrome" ],
    0x5904: [ "aeroway",  "helipad" ],
    0x5905: [ "aeroway",  "aerodrome" ],
    0x593f: [ "aeroway",  "aerodrome" ],
    0x5a00: [ "amenity",  "signpost" ],
    0x5c00: [ "place",    "hamlet" ],
    0x5d00: [ "tourism",  "information" ],
    0x5f00: [ "natural",  "scree" ],
    0x6100: [ "amenity",  "shelter", "building", "residential" ],
    0x6200: [ "depth",    "_name" ],
    0x6300: [ "ele",      "_name" ],
    0x6400: [ "man_made", "fixme" ],
    0x6401: [ "bridge",   "yes" ],
    0x6402: [ "landuse",  "industrial" ],
    0x6403: [ "landuse",  "cemetery" ],
    0x6404: [ "amenity",  "place_of_worship", "religion", "christrian" ],
    0x6405: [ "amenity",  "public_building" ],
    0x6406: [ "amenity",  "ferry_terminal" ],
    0x6407: [ "waterway", "dam" ], # Map_Features requires a way
    0x6408: [ "amenity",  "hospital" ],
    0x6409: [ "man_made", "water_works" ], # random pick from Map_Features
    0x640a: [ "amenity",  "signpost" ],
    0x640b: [ "landuse",  "military" ],
    0x640c: [ "landuse",  "industrial", "amenity",  "mine" ],
    0x640d: [ "man_made", "works", "waterway", "oil_platform" ],
    0x640e: [ "leisure",  "park" ],
    0x6410: [ "amenity",  "school" ],
    0x6411: [ "man_made", "tower" ],
    0x6412: [ "highway",  "marked_trail", "note", "fixme" ],
    0x6413: [ "tunnel",   "yes", "layer", "-1" ], # or Cave Entrance
    0x6414: [ "amenity",  "drinking_water" ],
    0x6415: [ "historic", "ruins" ],
    0x6416: [ "tourism",  "hotel" ],
    0x6500: [ "waterway", "other" ],
    0x6502: [ "highway",  "ford" ],
    0x6503: [ "natural",  "bay" ],
    0x6504: [ "natural",  "water", "waterway", "bend" ],
    0x6505: [ "waterway", "lock_gate" ],
    0x6507: [ "natural",  "spring", "man_made", "water_works" ],
    0x6508: [ "waterway", "waterfall" ],
    0x6509: [ "amenity",  "fountain", "note", "fixme" ],
    0x650b: [ "waterway", "dock" ],
    0x650c: [ "natural",  "land" ],        # Island as a POI
    0x650d: [ "natural",  "water" ],       # Lake as a POI
    0x650e: [ "natural",  "spring" ],
    0x650f: [ "natural",  "water" ],       # Pond as a POI
    0x6511: [ "natural",  "spring" ],
    0x6512: [ "waterway", "stream" ],
    0x6513: [ "natural",  "water" ],       # Swamp as a POI
    0x6600: [ "place",    "locality", "note", "fixme (kurhan?)" ],
    0x6601: [ "barrier",  "sally_port" ],
    0x6602: [ "landuse",  "commetcial" ],
    0x6603: [ "natural",  "bay" ],
    0x6604: [ "natural",  "beach" ],
    0x6605: [ "lock",     "yes" ],
    0x6606: [ "place",    "locality", "locality_type", "cape" ],
    0x6607: [ "natural",  "cliff" ],       # Cliff as a POI
    0x6608: [ "natural",  "peak" ],
    0x6609: [ "natural",  "plain" ],
    0x660a: [ "landuse",  "forest" ],      # Forest as a POI
    0x660b: [ "place",    "locality", "note", "fixme" ],
    0x660e: [ "natural",  "volcano" ],
    0x660f: [ "amenity",  "signpost" ],
    0x6610: [ "mountain_pass", "yes" ],
    0x6611: [ "man_made", "tower" ],
    0x6612: [ "amenity",  "watersports_rental" ],
    0x6613: [ "natural",  "peak", "place", "region" ],
    0x6614: [ "natural",  "scree" ],
    0x6616: [ "natural",  "peak" ],
    0x6617: [ "place",    "locality", "natural",  "valley" ],
    0x6618: [ "natural",  "wood" ],        # Wood as a POI

    0x6701: [ "highway",  "footway", "ref", "Zielony szlak",
              "marked_trail_green", "yes" ],
    0x6702: [ "highway",  "footway", "ref", "Czerwony szlak",
              "marked_trail_red", "yes" ],
    0x6703: [ "highway",  "footway", "ref", "Niebieski szlak",
              "marked_trail_blue", "yes" ],
    0x6704: [ "highway",  "footway", "ref", "Żółty szlak",
              "marked_trail_yellow", "yes" ],
    0x6705: [ "highway",  "footway", "ref", "Czarny szlak",
              "marked_trail_black", "yes" ],
    0x6707: [ "highway",  "cycleway", "ref", "Żółty szlak",
              "marked_trail_yellow", "yes" ],
    0x6708: [ "highway",  "cycleway", "ref", "Czerwony szlak",
              "marked_trail_red", "yes" ],
    0x6709: [ "highway",  "cycleway", "ref", "Niebieski szlak",
              "marked_trail_blue", "yes" ],
    0x670a: [ "highway",  "cycleway", "ref", "Zielony szlak",
              "marked_trail_green", "yes" ],
    0x670b: [ "highway",  "cycleway", "ref", "Czarny szlak",
              "marked_trail_black", "yes" ],
}
interp_types = { "o": "odd", "e": "even", "b": "all" }
levels = { 1: "residential", 2: "tertiary", 3: "secondary", 4: "trunk" }
maxspeeds = {
    '0':  '8', '1': '20', '2':  '40', '3':  '56',
    '4': '72', '5': '93', '6': '108', '7': '128',
}
exceptions = [
    'emergency', # Found nothing better in Map_Features
    'goods',
    'motorcar',
    'psv',
    'taxi', # Found nothing better in Map_Features
    'foot',
    'bicycle',
    'hgv',
]
reftype = {
    0x02: 'ref',
    0x05: 'ref',
    0x1d: 'loc_name', # Abbrevations
    0x1f: 'ele',
    0x2a: 'int_ref', # FIXME: should differentate the types
    0x2b: 'int_ref',
    0x2c: 'int_ref',
    0x2d: 'ref',
    0x2e: 'ref',
    0x2f: 'reg_ref',
}

class Mylist(object):
    k = {}
    v = [] #
    def __len__(self):
        return len(self.k)
    def __getitem__(self, key):
        return self.v[key] #
        for k in self.k:
            if self.k[k] == key:
                return k;
    def index(self, value):
        return self.k[value]
    def __setitem__(self, key, value): #
        if key in v: #
            del self.k[self.v[key]] #
        self.k[value] = key #
        self.v[key] = value #
    def __contains__(self, value):
        return value in self.k
    def append(self, value):
        self.v.append(value) #
        self.k[value] = len(self.k)
    def __iter__(self):
        return self.v.__iter__() #
        return self.k.__iter__()
# Lines with a # above can be removed to save half of the memory used
# (but some look-ups will be slower)

points = Mylist()
pointattrs = []
ways = []
relations = []

maxtypes = []
turnrestrictions = []
# FIXME: should use the timestamp of the cvs checkout from src/CVS
source = "http://ump.waw.pl/ retrieved " + time.strftime('%X %x')
srcidx = 0

borders = None
borders_resize = 1

class Features: # fake enum
    poi, polyline, polygon = range(3)

class ParsingError(Exception):
    pass

def index_to_nodeid(index):
    return -index - 1

def index_to_wayid(index):
    return index_to_nodeid(len(points) + index)

def index_to_relationid(index):
    return index_to_wayid(len(ways) + index)

def xmlize(str):
    return saxutils.escape(str, { '\'': '&apos;' })

def print_point(point, index, argv):
    """Prints a pair of coordinates and their ID as XML"""
    if '_out' in pointattrs[index]:
        return
    head = ''.join(("<node id='", str(index_to_nodeid(index)),
            "' visible='true' lat='", str(point[0]),
            "' lon='", str(point[1]), "'>"))
    print head
    src = pointattrs[index].pop('_src')
    for key in pointattrs[index]:
        try:
            print "\t<tag k='%s' v='%s' />" % \
                (key, xmlize(pointattrs[index][key]))
        except:
           sys.stderr.write("converting key " + key + ": " +
                           str(pointattrs[index][key]) + " failed\n")
    print "\t<tag k='source' v='%s (%s)' />" % (source, argv[src])
    print "</node>"

def print_way(way, index, argv):
    """Prints a way given by way together with its ID to stdout as XML"""
    if way.pop('_c') <= 0:
        return
    print "<way id='%d' visible='true'>" % index_to_wayid(index)
    for nindex in way.pop('_nodes'):
        print "\t<nd ref='%d' />" % index_to_nodeid(nindex)

    src = way.pop('_src')
    for key in way:
        print "\t<tag k='%s' v='%s' />" % (key, xmlize(way[key]))
    print "\t<tag k='source' v='%s (%s)' />" % (source, argv[src])
    print "</way>"

def print_relation(rel, index, argv):
    """Prints a relation given by rel together with its ID to stdout as XML"""
    if rel.pop('_c') <= 0:
        return
    if not rel.has_key("_members"):
        sys.stderr.write( "warning: Unable to print relation not having memebers: %r\n" % (rel,) )
        return
    print "<relation id='%i' visible='true'>" % index_to_relationid(index)
    for role, (type, members) in rel.pop('_members').items():
        for member in members:
            if type == "node":
                id = index_to_nodeid(member)
            elif type == "way":
                id = index_to_wayid(member)
            else:
                id = index_to_relationid(member)
            print "\t<member type='%s' ref='%i' role='%s' />" % (type, id, role)

    src = rel.pop('_src')
    for key in rel:
        print "\t<tag k='%s' v='%s' />" % (key, xmlize(rel[key]))
    print "\t<tag k='source' v='%s (%s)' />" % (source, argv[src])
    print "</relation>"

def points_append(node, attrs):
    global borders
    lat = float(node[0])
    lon = float(node[1])
    if borders_resize:
        if borders is None:
            borders = [ lat, lon, lat, lon ]
        else:
            if lat < borders[0]:
                borders[0] = lat
            if lon < borders[1]:
                borders[1] = lon
            if lat > borders[2]:
                borders[2] = lat
            if lon > borders[3]:
                borders[3] = lon
    elif borders is None or \
         lat < borders[0] or lon < borders[1] or \
         lat > borders[2] or lon > borders[3]:
        attrs['_out'] = 1

    attrs['_src'] = srcidx
    points.append(node)
    maxtypes.append(0x100)
    pointattrs.append(attrs)

def prepare_line(nodes_str, closed):
    """Appends new nodes to the points list"""
    nodes = []
    for element in nodes_str.split(','):
        element = element.strip('()')
        nodes.append(element)

    lats = nodes[::2]
    longs = nodes[1::2]

    nodes = zip(lats, longs)

    for node in nodes:
        if node not in points:
            points_append(node, {})
    try:
        node_indices = map(points.index, nodes)
    except:
        print points
        print nodes
        raise ParsingError('Can\'t map node indices')
    pts = 0
    for node in node_indices:
        if '_out' not in pointattrs[node]:
            pts += 1
    if closed:
        node_indices.append(node_indices[0])
    return (pts, node_indices)

def tag(way, pairs):
    for key, value in zip(pairs[::2], pairs[1::2]):
        way[key] = value

def convert_tag(way, key, value, feat):
    if key.lower() in [ 'label', 'lable', 'lablel' ]:
        label = value
        refpos = label.find("~[")
        if refpos > -1:
            try:
                ## refstr, sep, right = label[refpos + 2:].partition(' ')            # py_ver >= 2.5 version
                label_split = label[refpos + 2:].split(' ',1)                        # above line in py_ver = 2.4
                if len(label_split) == 2:
                    refstr,right = label[refpos + 2:].split(' ',1)
                else:
                    refstr = label_split[0]
                    right = ""
                    
                code, ref = refstr.split(']')
                label = (label[:refpos] + right).strip(' \t')
                way[reftype[int(code, 0)]] = ref.replace("/", ";")
            except:
                if code.lower() == '0x06':
                    pass
                elif code.lower() == '0x1b':
                    way['loc_name'] = right
                elif code.lower() == '0x1c':
                    way['loc_name'] = ref
                else:
                    raise ParsingError('Problem parsing label ' + value)
                label = ref + label
        if 'name' not in way and label != "":
            way['name'] = label
    elif key.lower() in [ 'label2', 'lanel2', 'lable2', 'level2', 'lbel2' ]:
        way['name'] = value
    elif key.lower() == 'label3':
        way['loc_name'] = value
    elif key == 'DirIndicator':
        way['oneway'] = value
    elif key in [ 'Data0',  'Data1', 'Data2', 'Data3', 'Data4' ]:
        if '_nodes' in way:
            sys.stderr.write("warning: Way " + str(way) + " has multiple "
                             "polylines/polygons, some will be discarded!\n")
        way['_c'], way['_nodes'] = prepare_line(value, feat == Features.polygon)
        # way['layer'] = data[4:] ??
    elif key == 'Type':
        if feat == Features.polygon:
            tag(way, shape_types[int(value, 0)])
        elif feat == Features.polyline:
            tag(way, pline_types[int(value, 0)])
        else:
            tag(way, poi_types[int(value, 0)])
    elif key in [ 'EndLevel', 'Level', 'Levles' ]:
        # if 'highway' not in way:
        #     way['highway'] = levels[int(value, 0)]
        # way['layer'] = str(value) ??
        pass
    elif key.lower() == 'miasto' or key.lower() == 'miato':
        way['addr:city'] = value
    elif key == 'StreetDesc':
        way['addr:street'] = value
    elif key == 'RouteParam':
        params = value.split(',')
        if params[0] != '0':
            way['maxspeed'] = maxspeeds[params[0]] # Probably useless
        if params[2] == '1':
            way['oneway'] = 'yes'
        if params[3] == '1':
            way['toll'] = 'yes'
        for i, val in enumerate(params[4:]):
            if val == '1':
                way[exceptions[i]] = 'no'
    elif key == 'RestrParam':
        params = value.split(',')
        excpts = []
        for i, val in enumerate(params[4:]):
            if val == '1':
                excpts.append(exceptions[i])
        way['except'] = ','.join(excpts)
    elif key == 'HLevel0':
        if feat != Features.polyline:
            raise ParsingError('HLevel0 used on a polygon')
        curlevel = 0
        curnode = 0
        list = []
        for level in value.split(')'):
            if level == "":
                break
            pair = level.strip(', ()').split(',')
            start = int(pair[0], 0)
            level = int(pair[1], 0)
            if start > curnode and level != curlevel:
                list.append((curnode, start, curlevel))
                curnode = start
            curlevel = level
        list.append((curnode, -1, curlevel))
        way['_levels'] = list
    elif key == 'Szlak':
        ref = []
        for colour in value.split(','):
            if colour.lower() == 'zolty':
                ref.append('Żółty szlak')
                way['marked_trail_yellow'] = 'yes'
            elif colour.lower() == 'zielony':
                ref.append('Zielony szlak')
                way['marked_trail_green'] = 'yes'
            elif colour.lower() == 'czerwony':
                ref.append('Czerwony szlak')
                way['marked_trail_red'] = 'yes'
            elif colour.lower() == 'niebieski':
                ref.append('Niebieski szlak')
                way['marked_trail_blue'] = 'yes'
            else:
                ref.append(colour)
                sys.stderr.write("warning: Unknown 'Szlak' colour: " +
                                 colour + "\n")
        way['ref'] = ";".join(ref)
    elif key.startswith('NumbersExt'):
        sys.stderr.write("warning: " + key + " tag discarded\n")
    elif key.startswith('Numbers'):
        unused = int(key[7:], 0)
        value = value.split(',')
        if len(value) < 7:
            raise ParsingError("Bad address info specification")
        if '_addr' not in way:
            way['_addr'] = {}
        way['_addr'][int(value[0], 0)] = value[1:]
    elif key.lower() == 'rampa':
        way['bridge'] = 'yes'
    elif key == 'Highway':
        way['ref'] = value
    elif key.startswith('Exit'):
        way[key.lower()] = value
    elif key == 'OvernightParking':
        way['overnight_parking'] = 'yes'
    elif key == 'Phone':
        way['phone'] = value
    elif key == 'HouseNumber':
        way['addr:housenumber'] = value
    elif key == 'KodPoczt':
        way['addr:postcode'] = value
    elif key == 'Time':
        way['hour_on'] = value
    else:
        if key.lower() in [ 'levels', 'lavels', 'city', 'typ', 'plik' ]:
            pass # Known typo
        else:
            raise ParsingError("Unknown key " + key + " in polyline / polygon")

# Mercator
def projlat(lat):
    lat = math.radians(lat)
    return math.degrees(math.log(math.tan(lat) + 1.0 / math.cos(lat)))
def projlon(lat, lon):
    return lon
def unproj(lat, lon):
    lat = math.radians(lat)
    return (math.degrees(math.atan(math.sinh(lat))), lon)
#def unproj(lat, lon):
#    return (lat, lon / math.cos(lat / 180.0 * math.pi))
#def projlat(lat):
#    return lat
#def projlon(lat, lon):
#    return lon * math.cos(lat / 180.0 * math.pi)

def add_addrinfo(nodes, addrs, street, city, right, count):
    prev_house = "xx"
    prev_node = None
    attrs = { 'addr:street': street }
    if city:
        attrs['addr:city'] = city
    for n, node in enumerate(nodes[:-1]):
        if n in addrs and node != nodes[n + 1]:
            type = addrs[n][right * 3 + 0].lower()
            if type not in interp_types:
                continue
            type = interp_types[type]
            low = addrs[n][right * 3 + 1]
            hi = addrs[n][right * 3 + 2]

            dist = 0.0002 # degrees
            lat = projlat(float(points[node][0]))
            lon = projlon(lat, float(points[node][1]))
            nlat = projlat(float(points[nodes[n + 1]][0]))
            nlon = projlon(nlat, float(points[nodes[n + 1]][1]))
            dlen = math.hypot(nlat - lat, nlon - lon)
            normlat = (nlat - lat) / dlen * dist
            normlon = (nlon - lon) / dlen * dist
            if right:
                dlat = -normlon
                dlon = normlat
            else:
                dlat = normlon
                dlon = -normlat
            if dlen > dist * 5:
                shortlat = normlat * 2
                shortlon = normlon * 2
            elif dlen > dist * 3:
                shortlat = normlat
                shortlon = normlon
            else:
                shortlat = 0
                shortlon = 0

            if 0: #prev_house == low:
                low_node = prev_node
            elif low == hi:
                shortlat = (nlat - lat) / 2
                shortlon = (nlon - lon) / 2
                pt0 = 0
            else:
                pt0 = len(points)
                low_node = unproj(lat + dlat + shortlat, lon + dlon + shortlon)
                while low_node in points:
                    low_node = (low_node[0] + normlat / 10,
                                low_node[1] + normlon / 10)
                attrs['addr:housenumber'] = low
                points_append(low_node, attrs.copy())

            pt1 = len(points)
            hi_node = unproj(nlat + dlat - shortlat, nlon + dlon - shortlon)
            while hi_node in points:
                hi_node = (hi_node[0] - normlat / 10, hi_node[1] - normlon / 10)
            attrs['addr:housenumber'] = hi
            points_append(hi_node, attrs.copy())

            if len(addrs[n]) >= 8:
                if addrs[n][6] != "-1":
                    pointattrs[pt0]['addr:postcode'] = addrs[n][6]
                if addrs[n][7] != "-1":
                    pointattrs[pt1]['addr:postcode'] = addrs[n][7]
            if len(addrs[n]) >= 14:
                if addrs[n][8] != "-1":
                    pointattrs[pt0]['addr:city'] = addrs[n][8]
                if addrs[n][9] != "-1":
                    pointattrs[pt0]['addr:region'] = addrs[n][9]
                if addrs[n][10] != "-1":
                    pointattrs[pt0]['addr:country'] = addrs[n][10]
                if addrs[n][11] != "-1":
                    pointattrs[pt1]['addr:city'] = addrs[n][11]
                if addrs[n][12] != "-1":
                    pointattrs[pt1]['addr:region'] = addrs[n][12]
                if addrs[n][13] != "-1":
                    pointattrs[pt1]['addr:country'] = addrs[n][13]

            way = {
                '_nodes': [pt0, pt1],
                'addr:interpolation': type,
                '_c': count,
                '_src': srcidx,
            }
            if low != hi:
                ways.append(way)

            prev_house = hi
            prev_node = hi_node
        else:
            prev_house = "xx"


class NodesToWayNotFound(ValueError):
    """
    Raised when way of two nodes can not be found
    """
    def __init__(self,node_a,node_b):
        self.node_a = node_a
        self.node_b = node_b
        
    def __str__(self):
        return "<NodesToWayNotFound %r,%r>" % (self.node_a,self.node_b,)
    
def nodes_to_way(a, b):
    for way in ways:
        ## print "DEBUG: way['_nodes']: %r" % (way['_nodes'],)
        if a in way['_nodes'] and b in way['_nodes']:
            # Hopefully there's only one
            return way
            
    raise NodesToWayNotFound(a,b)
    
    for way in ways:
        way_nodes = way['_nodes']
        if a in way_nodes:
            print "DEBUG: node a: %r found in way: %r" % (a,way)
        if b in way_nodes:
            print "DEBUG: node b: %r found in way: %r" % (b,way)
            
    ## print "DEBUG: no way nodes: a: %r b: %r" % (a,b,)
    raise NodesToWayNotFound(a,b)

def signbit(x):
    if x > 0:
        return 1
    if x < 0:
        return -1

def next_node(pivot, dir):
    way = nodes_to_way(dir, pivot)['_nodes']
    pivotidx = way.index(pivot)
    return way[pivotidx + signbit(way.index(dir) - pivotidx)]

def split_way(way, node):
    l = len(way['_nodes'])
    i = way['_nodes'].index(node)
    if i == 0 or i == l - 1:
        return
    newway = way.copy()
    ways.append(newway)
    newway['_nodes'] = way['_nodes'][:i + 1]
    way['_nodes'] = way['_nodes'][i:]

def preprepare_restriction(rel):
    rel['_nodes'][0] = next_node(rel['_nodes'][1], rel['_nodes'][0])
    rel['_nodes'][-1] = next_node(rel['_nodes'][-2], rel['_nodes'][-1])

def prepare_restriction(rel):
    fromnode = rel['_nodes'][0]
    fromvia = rel['_nodes'][1]
    tonode = rel['_nodes'][-1]
    tovia = rel['_nodes'][-2]
    split_way(nodes_to_way(fromnode, fromvia), fromvia)
    split_way(nodes_to_way(tonode, tovia), tovia)

def make_restriction(rel):
    nodes = rel.pop('_nodes')
    rel['_members'] = {
        'from': ('way', [ ways.index(nodes_to_way(nodes[0], nodes[1])) ]),
        'via':  ('node', nodes[1:-1]),
        'to':   ('way', [ ways.index(nodes_to_way(nodes[-2], nodes[-1])) ]),
    }

    rel['_c'] = ways[rel['_members']['from'][1][0]]['_c'] + \
                ways[rel['_members']['to'][1][0]]['_c']
    if rel['_c'] > 0:
        ways[rel['_members']['from'][1][0]]['_c'] += 1
        ways[rel['_members']['to'][1][0]]['_c'] += 1

    # Try to suss out the type of restriction.. needs to be checked manually
    if 'name' in rel:
        if rel['name'].find('<<') != -1:
            rel['restriction'] = 'no_u_turn'
        elif rel['name'].find('<') != -1:
            rel['restriction'] = 'no_left_turn'
        elif rel['name'].find('>') != -1:
            rel['restriction'] = 'no_left_turn'

    # Multiple via nodes are not approved by OSM anyway
    if 'restriction' not in rel and len(nodes) == 3:
        # No projection needed
        alat = float(points[nodes[0]][0])
        alon = float(points[nodes[0]][1])
        blat = float(points[nodes[1]][0])
        blon = float(points[nodes[1]][1])
        clat = float(points[nodes[2]][0])
        clon = float(points[nodes[2]][1])
        # Vector dot product (?)
        angle = (blat - alat) * (clon - blon) - (blon - alon) * (clat - blat)

        if angle > 0.0:
            rel['restriction'] = 'no_right_turn'
        else:
            rel['restriction'] = 'no_left_turn'

def recode(line):
    try:
        return unicode(line, "cp1250").encode("UTF-8")
    except:
        sys.stderr.write("warning: couldn't recode " + line + " in UTF-8!\n");
        return line

def parse_txt(infile):
    polyline = None
    feat = None
    miasto = None
    comment = None
    for line in infile:
        if line == "[POLYLINE]\n":
            polyline = {}
            feat = Features.polyline
        elif line == "[POLYGON]\n":
            polyline = {}
            feat = Features.polygon
        elif line == "[POI]\n":
            polyline = {}
            feat = Features.poi
        elif line == '[END]\n':
            way = { '_src': srcidx }
            for key in polyline:
                convert_tag(way, key, polyline[key], feat)
            if comment is not None:
                way['note'] = comment
            comment = None
            if 'Type' in polyline:
                highway = int(polyline['Type'], 0)
                for i in way['_nodes']:
                    if maxtypes[i] > highway:
                        maxtypes[i] = highway
            polyline = None

            if '_addr' in way:
                addrinfo = way.pop('_addr')
                try:
                    street = way['name']
                except:
                    street = 'fixme'
                add_addrinfo(way['_nodes'], addrinfo,
                                street, miasto, 0, way['_c'])
                add_addrinfo(way['_nodes'], addrinfo,
                                street, miasto, 1, way['_c'])
            if 'ele' in way and way['ele'] == '_name':
                way['ele'] = way.pop('name').replace(',', '.')
            if 'depth' in way and way['depth'] == '_name':
                way['depth'] = way.pop('name').replace(',', '.')

            if feat == Features.poi:
                # execution order shouldn't matter here, unlike in C
                pointattrs[way.pop('_nodes')[0]] = way
                if not way.pop('_c'):
                    way['_out'] = 1
            else:
                ways.append(way)
        elif polyline is not None:
            try:
                key, value = line.split('=', 1)
            except:
                print line
                raise ParsingError('Can\'t split the thing')
            polyline[key.strip()] = recode(value).strip()
        elif line.startswith(';'):
            strn = recode(line[1:].strip(" \t\n"))
            if comment is not None:
                comment = comment + " " + strn
            else:
                comment = strn
        elif line.startswith('Miasto='):
            miasto = recode(line[7:].strip(" \t\n"))
        elif line != '\n':
            raise ParsingError('Unhandled line ' + line)

def parse_pnt(infile):
#   raise ParsingError('No?')
    pass

# Main program.

if len(sys.argv) < 2 or sys.argv[1] == "--help":
    print "Usage: txt2osm [files...]"
    print "Example:"
    print "\t ./txt2osm.py UMP-Warszawa/src/WOLOMIN*.txt -- UMP-Warszawa/src/*.txt > wolomin.osm"
    sys.exit()
for n, f in enumerate(sys.argv[1:]):
    srcidx = n + 1
    if f == '--':
        borders_resize = 0
        continue
    if f in sys.argv[1:srcidx]:
        continue
    try:
        infile = open(f, "r")
    except IOError:
        sys.stderr.write("Can't open file " + f + "!\n")
        sys.exit()
    sys.stderr.write("Loading " + f + "\n")

    if f.endswith("pnt") or f.endswith("pnt.txt"):
        parse_pnt(infile)
    elif f.endswith("txt"):
        parse_txt(infile)
    infile.close()

# Roundabouts:
# Use the road class of the most important (lowest numbered) road
# that meets the roundabout.
for way in ways:
    if 'junction' in way and way['junction'] == 'roundabout':
        maxtype = 0x7 # service
        for i in way['_nodes']:
            if maxtypes[i] < maxtype:
                maxtype = maxtypes[i]
        tag(way, pline_types[maxtype])
        if 'oneway' in way:
            del way['oneway']
        # TODO make sure nodes are ordered counter-clockwise

# Relations:
# find them, remove from /ways/ and move to /relations/
#
# For restriction relations: locate members and split member ways
# at the "via" node as required by
# http://wiki.openstreetmap.org/wiki/Relation:restriction
relations = [rel for rel in ways if '_rel' in rel]
for rel in relations:
    rel['type'] = rel.pop('_rel')
    ways.remove(rel)

for rel in relations:
    if rel['type'] == 'restriction':
        try:
            preprepare_restriction(rel)
            ## print "DEBUG: preprepare_restriction(rel:%r) OK." % (rel,)
        except NodesToWayNotFound,ntwnf:
            sys.stderr.write( "warning: Unable to find nodes to preprepare restriction from rel: %r\n" % (rel,) )

# Way level:  split ways on level changes
# TODO: possibly emit a relation to group the ways
levelledways = [way for way in ways if '_levels' in way]
for way in levelledways:
    ways.remove(way)
    if '_levels' in way:
        nodes = way['_nodes']
        levels = way.pop('_levels')
        for segment in levels:
            subway = way.copy()
            if segment[1] == -1:
                subway['_nodes'] = nodes[segment[0]:]
            else:
                subway['_nodes'] = nodes[segment[0]:segment[1] + 1]
            if segment[2] != 0:
                subway['layer'] = str(segment[2])
            if segment[2] > 0:
                subway['bridge'] = 'yes'
            else:
                subway['tunnel'] = 'yes'
            ways.append(subway)

for rel in relations:
    if rel['type'] == 'restriction':
        try:
            prepare_restriction(rel)
        except NodesToWayNotFound,ntwnf:
            sys.stderr.write( "warning: Unable to find nodes to preprepare restriction from rel: %r\n" % (rel,) )
for rel in relations:
    if rel['type'] == 'restriction':
        try:
            make_restriction(rel)
        except NodesToWayNotFound,ntwnf:
            sys.stderr.write( "warning: Unable to find nodes to preprepare restriction from rel: %r\n" % (rel,) )

for way in ways:
    if way['_c'] > 0:
        for node in way['_nodes']:
            if '_out' in pointattrs[node]:
                del pointattrs[node]['_out']

print "<?xml version='1.0' encoding='UTF-8'?>"
print "<osm version='0.5' generator='txt2osm %s converter for UMP-PL'>" \
    % __version__

for index, point in enumerate(points):
    print_point(point, index, sys.argv)

for index, way in enumerate(ways):
    print_way(way, index, sys.argv)

for index, rel in enumerate(relations):
    print_relation(rel, index, sys.argv)

print "</osm>"
