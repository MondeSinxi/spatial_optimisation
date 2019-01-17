import sys
import gmaps
import requests
import json
import re
import numpy as np
import urllib.parse
import itertools
import shutil

addresses = ["115 St Andrew’s Drive, Durban North, KwaZulu-Natal, South Africa",
             "67 Boshoff Street, Pietermaritzburg, KwaZulu-Natal, South Africa",
             "4 Paul Avenue, Fairview, Empangeni, KwaZulu-Natal, South Africa",
             "166 Kerk Street, Vryheid, KwaZulu-Natal, South Africa",
             "9 Margaret Street, Ixopo, KwaZulu-Natal, South Africa",
             "16 Poort Road, Ladysmith, KwaZulu-Natal, South Africa"
            ]

access_token="pk.eyJ1IjoibWF0dGZpY2tlIiwiYSI6ImNqNnM2YmFoNzAwcTMzM214NTB1NHdwbnoifQ.Or19S7KmYPHW8YjRz82v6g"

def get_geocodes_mapbox(addresses):
    """
    call to mapbox api converts addresses to coordinates.
    Function takes an array of addresses and returns an array of coordinates
    """
    geo_locations = []
    for add in addresses:
        add = re.sub(r" ",r"%20",add) # format spaces for url
        geocode_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json?access_token={}&cachebuster=1547705050308&autocomplete=true".format(add, access_token)
        res = requests.get(geocode_url).content
        form_res = json.loads(res)
        geo_locations.append(form_res['features'][0]['geometry']['coordinates'])
    return geo_locations

def destination_matrix(geo_locs):
    """
    takes an array of coordinates [lattitude,longitude] and returns an nxn matrix via
    call to mapbox API.
    """
    s = str(geo_locs) # convert array to string
    s = s.replace(' ', '').replace('],',';').replace('[','').replace(']]','') # formatting; remove spaces, add semi-colon and remove brackets
    route_url = "https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{}?&annotations=distance,duration&access_token={}".format(s, access_token)
    res  =requests.get(route_url).content
    json_matrix = json.loads(res)
    durations = json_matrix['durations']
    return durations


def total_duration(durations):
    """
    takes an array of tuples and duration matrix to calculate total duration for each permutation 
    """
    durations = np.array(durations)
    l = durations.shape[0] # number of locations
    it = itertools.permutations(range(l))
    route_duration = []
    for i in it:
        d = 0
        for j in range(1, l):
            d += durations[i[j-1]][i[j]]
        route_duration.append([d, i])
    return min(route_duration, key=lambda x: x[0])

def map_path(route, geo_locs):
    route_string = ''
    for r in route:
        route_string += str(geo_locs[r]).replace(' ','').replace('[','').replace(']','') + ';'
    route_string = route_string[:-1]
    url_route = "https://api.mapbox.com/directions/v5/mapbox/driving/{}?geometries=polyline&access_token={}".format(route_string, access_token)
    res = requests.get(url_route).content
    j_path = json.loads(res)
    return j_path

def draw_map(path, geo_locs, route):
    """
    will make a call to static API of mapbox generate map and save image
    """
    path = urllib.parse.quote(str(path['routes'][0]['geometry']))
    center_image = str(geo_locs[0]).replace('[','').replace(']','').replace(' ','') # e.g '-22.4,33.9'
    zoom_level = '8'
    url_static = "https://api.mapbox.com/v4/mapbox.streets/path-5+f44-0.5({})/{},{}/1000x1000.png?access_token={}".format(path, center_image,zoom_level,access_token)
    res = requests.get(url_static, stream=True)
    with open('img.png', 'wb') as out_file: # https://stackoverflow.com/questions/13137817/how-to-download-image-using-requests
        shutil.copyfileobj(res.raw, out_file)
        del res
    return

def run():
    geo_locs = get_geocodes_mapbox(addresses)
    durations = destination_matrix(geo_locs)
    total_time, route = total_duration(durations)
    path = map_path(route, geo_locs)
    draw_map(path, geo_locs, route)
    best_route_addr = [addresses[r] for r in route]
    print('The optimimal route is as follows:')
    for i, ba in enumerate(best_route_addr):
          print(i,+ 1':' , ba)
    print('Expected travel time for the optimal tour: {} units'.format(total_time)) # mapbox time units not documented

if __name__ == "__main__":
	run()
