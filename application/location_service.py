from flask import current_app, url_for, Markup
from googlemaps import Client
from flask_googlemaps import Map


geo_location_markers_icons = {
    'start': 'twotone-room-24px.svg',
    'end': 'twotone-flag-24px.svg',
    'hotel': 'baseline-hotel-24px.svg'
}


class Geolocation():
    def __init__(self, place):
        geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
        geocode_result = geolocation.geocode(place)
        self.lat = geocode_result[0]['geometry']['location']['lat']
        self.lng = geocode_result[0]['geometry']['location']['lng']
        self.fmt_addr = geocode_result[0]['formatted_address']


def map_a_story(story):
    geopoints = story.get_geo_points()
    if geopoints is None:
        map = None
        return map
    bounds = not len(geopoints) == 1
    markers = set_geo_markers(geopoints)
    map = Map(identifier="sndmap",
              style="width:100%;height:100%;margin:0;",
              lat=geopoints[0]['lat'],
              lng=geopoints[0]['lng'],
              fit_markers_to_bounds=bounds,  # True
              markers=markers)
    return map


def set_geo_markers(geopoints):
    markers = []
    start_list = min(len(geopoints) - 1, 1)
    for geopoint in geopoints[start_list:]:
        marker = {
            'icon': Markup(url_for('static',
                                   filename='images/' +
                                   geo_location_markers_icons[geopoint['category']]
                                   )),
            'lat': geopoint['lat'],
            'lng': geopoint['lng'],
            'infobox': "<b>Hello World</b>",
            'id': geopoint['type']
        }
        markers.append(marker)
    return markers