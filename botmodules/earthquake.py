import urllib.request, urllib.error, urllib.parse
import json
import datetime


def get_quake(self, e):
    #returns the latest earthquake on USGS

    updated, quakestring = get_quake_data()
    e.output = quakestring
    return e
get_quake.command = "!q"
get_quake.helptext = "Usage: !q\nShows the latest earthquake larger than M2.5 and how long ago it occured"


def quake_alert():
    #returns a new get_quake_data only if it hasn't returned it before - for use in alerts
    try: #it's possible for there to be nothing in the json file, so check for it.
        updated, quakestring = get_quake_data()
    except:
        return

    try: #if a filter is set
        if quakestring.find(quake_alert.filter) != -1:
            return
    except:
        pass


    if not quake_alert.lastquakecheck:
        quake_alert.lastquakecheck = updated
    if updated > quake_alert.lastquakecheck:
        quake_alert.lastquakecheck = updated
        return quakestring


quake_alert.lastquakecheck = ""
quake_alert.alert = True


def get_quake_data():
    #Altername URLS for intensities: http://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
    request = urllib.request.urlopen("http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson")
    quake = json.loads(request.read().decode())
    request.close()
    quake = quake['features'][0] #select the latest quake
    qtitle = quake['properties']['title']
    updated = round(quake['properties']['time'] / 1000)
    updated = datetime.datetime.fromtimestamp(updated)
    ago = round((datetime.datetime.now() - updated).seconds / 60)
    depth = quake['geometry']['coordinates'][2]
    depthmi = '{0:.2f}'.format(depth / 1.61)
    elevation = "%s km (%s mi)" % (depth, depthmi)
    tsunami = ""
    if quake['properties']['tsunami']:
        tsunami = " - Tsunami Warning!"
    alert = ""
    if quake['properties']['alert']:
        alert = " - Alert level: %s" % quake['properties']['alert']

    quakestring = "Latest Earthquake: %s - Depth: %s (%s minutes ago)%s%s" % (qtitle, elevation, ago, tsunami, alert)

    return updated, quakestring

