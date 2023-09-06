# Download google spreadsheet as csv file
import os
sheet_url = 'https://docs.google.com/spreadsheets/d/1FXP3QcYiCeogYNgArd5mPY109RgAOhP6FKQDWqgV4YU/export?exportFormat=csv'
current_folder = os.path.dirname(os.path.abspath(__file__))
csv_filepath = os.path.join(current_folder, 'run_events.csv')
command = f'curl -L {sheet_url} -o {csv_filepath}'
os.system(command)

# Load CSV data
import pandas as pd
data = pd.read_csv(csv_filepath)

# Filter just the Berlin Marathon for this examble
berlin_marathon_df = data[data['Race'] == '41. Berlin Marathon']
race = berlin_marathon_df['Race'].iloc[0]
lat = berlin_marathon_df['Latitude'].iloc[0]
lon = berlin_marathon_df['Longitude'].iloc[0]
link = berlin_marathon_df['Link'].iloc[0]

# create map object centered on our event
import folium
run_map = folium.Map(location=[lat, lon], tiles=None, zoom_start=12)

# add map layer
folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(run_map)

# add feature group for Marathons
fg_marathons = folium.FeatureGroup(name='Marathons').add_to(run_map)

# create marker and add it to marathon feature group. Add pop-up with html link to event page.
folium_marker = folium.Marker(location=[lat, lon], tooltip=race, popup=folium.Popup(f'<a href="{link}">Event Link</a>'), icon=folium.Icon(color='red'))
folium_marker.add_to(fg_marathons)

# create gpx trace
import gpxpy
gpx_file = 'berlin_marathon_2014.gpx'
gpx = gpxpy.parse(open(gpx_file))
track = gpx.tracks[0]
segment = track.segments[0]

points = []
for track in gpx.tracks:
    for segment in track.segments:
        step = 10
        for point in segment.points[::step]:
            points.append(tuple([point.latitude, point.longitude]))

folium_gpx = folium.PolyLine(points, color='red', weight=5, opacity=0.85).add_to(run_map)
folium_gpx.add_to(fg_marathons)

# create legend
run_map.add_child(folium.LayerControl(position='topright', collapsed=False, autoZIndex=True))

# save and open map
run_map.save('run_map.html')

import webbrowser
webbrowser.open('run_map.html')
