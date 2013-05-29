import os
import sys
import web
import gzip
import json
import config
import logging
import pygeoip
import memcache
import operator
import subprocess

from time import time, sleep
from math import radians, cos, sin, asin, sqrt
from urllib import urlretrieve

shoal_list = {}

"""
    Helper functions to get, set and delete the list of tracked Squid servers.
    Will try and use memcache first if available, then fallback on global shoal_list variable
"""
def get_shoal():
    if config.memcached:
        memc = memcache.Client([config.memcached])
        data = memc.get('shoal')
        if data:
            return data
        else:
            memc.set('shoal', {})
            return {}
    else:
        return shoal_list

def set_shoal(val):
    if config.memcached:
        memc = memcache.Client([config.memcached])
        memc.set('shoal', val)
    else:
        global shoal_list
        shoal_list = val

def delete_shoal():
    set_shoal({})

"""
    Given an IP return all its geographical information (using GeoLiteCity.dat)
"""
def get_geolocation(ip):
    geolite_db = os.path.join(config.geolitecity_path, "GeoLiteCity.dat")
    try:
        gi = pygeoip.GeoIP(geolite_db)
        return gi.record_by_addr(ip)
    except pygeoip.socket.error as e:
        return
    except (IOError, pygeoip.GeoIPError) as e:
        logging.error(e)
        sys.exit(1)

"""
    Given an IP return `count` IP's of nearest Squid servers.
"""
def get_nearest_squids(ip, count=10):
    request_data = get_geolocation(ip)
    try:
        r_lat = request_data['latitude']
        r_long = request_data['longitude']
    except KeyError as e:
        logging.error("Invalid request, unable to generate geolocation data for IP: {0}".format(ip))
        return

    nearest_squids = []
    shoal_list = get_shoal()

    for squid in shoal_list:
        s_lat = float(shoal_list[squid]['geo_data']['latitude'])
        s_long = float(shoal_list[squid]['geo_data']['longitude'])
        distance = haversine(r_lat,r_long,s_lat,s_long)
        nearest_squids.append((shoal_list[squid],distance))

    squids = sorted(nearest_squids, key=lambda k: (k[1], k[0]['load']))
    return squids[:count]

"""
    Calculate distance between two points using Haversine Formula.
"""
def haversine(lat1,lon1,lat2,lon2):
    r = 6371 #radius of earth
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return round((r * c),2)

"""
    Function to generate data for the /nearest URL.
"""
def generate_nearest(ip, count):
    try:
        count = int(count)
    except (ValueError, TypeError):
        count = 5

    squids = get_nearest_squids(ip, count)
    # Could fix this logic, get_nearest_squid returns an array of tuples, and converts to dictionary.
    if squids:
        squid_json = {}
        for i,squid in enumerate(squids):
            squid_json[i] = squid[0]
            squid_json[i]['distance'] = squid[1]
        return json.dumps(squid_json)
    else:
        return json.dumps(None)

"""
    Function to generate data for the /wpad.dat URL.
"""
def generate_wpad(ip):
    squids = get_nearest_squids(ip)
    if squids:
        proxy_str = ''
        for squid in squids:
            try:
                proxy_str += "PROXY http://{0}:{1};".format(squid[0]['hostname'],squid[0]['squid_port'])
            except TypeError as e:
                continue
        return proxy_str
    else:
        return

"""
    Function to check if geolitecity database needs updating.
"""
def check_geolitecity_need_update():
    curr = time()
    geolite_db = os.path.join(config.geolitecity_path,"GeoLiteCity.dat")
    # check if GeoLiteCity database is older than 30 days.
    outdated = 30 * 24 * 60 * 60 # 30 days in seconds.

    if os.path.exists(geolite_db):
        if curr - os.path.getmtime(geolite_db) < outdated:
            return False
        else:
            return True
    else:
        return True

"""
    Function to download geolitecity database from URL.
"""
def download_geolitecity():
    geolite_db = os.path.join(config.geolitecity_path,"GeoLiteCity.dat")
    geolite_url = config.geolitecity_url

    try:
        urlretrieve(geolite_url,geolite_db + '.gz')
    except Exception as e:
        logging.error("Could not download the database. - {0}".format(e))
        sys.exit(1)
    try:
        content = gzip.open(geolite_db + '.gz').read()
    except Exception as e:
        logging.error("GeoLiteCity.dat file was not properly downloaded. Check contents of {0} for possible errors.".format(geolite_db + '.gz'))
        sys.exit(1)

    with open(geolite_db,'w') as f:
        f.write(content)

    if check_geolitecity_need_update():
        logging.error('GeoLiteCity database failed to update.')
        sys.exit(1)
