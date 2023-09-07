### GET DATA FROM SPREADSHEET ###
# download google doc as a csv file
import os
sheet_url = 'https://docs.google.com/spreadsheets/d/1WghWJbxdCeKpbi3-H_6FmBAv_jILD_1_woRhuKGJ190/export?exportFormat=csv'
current_folder = os.path.dirname(os.path.abspath(__file__))
csv_filepath = os.path.join(current_folder, 'run_events.csv')
command = f'curl -L {sheet_url} -o {csv_filepath}'
os.system(command)

# load CSV data into a dict
import pandas as pd
data = pd.read_csv(csv_filepath).to_dict(orient='records')[0]

### CREATE HTML MAP ###
# create map object and center it on our event
import folium
run_map = folium.Map(location=[data['Latitude'], data['Longitude']], tiles=None, zoom_start=12)

# add Openstreetmap layer
folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(run_map)

# add feature group for Marathons
fg_marathons = folium.FeatureGroup(name='Marathons').add_to(run_map)

### ADD EVENT MARKER ###
# create an iframe pop-up for the marker
popup_html = f"<b>Date:</b> {data['Date']}<br/>"
popup_html += f"<b>Race:</b> {data['Race']}<br/>"
popup_html += f"<b>Time:</b> {data['Time']}<br/>"
popup_html += '<b><a href="{}" target="_blank">Event Page</a></b>'.format(data['Link'])
popup_iframe = folium.IFrame(width=200, height=110, html=popup_html)

# create marker and add it to marathon feature group
folium_marker = folium.Marker(location=[data['Latitude'], data['Longitude']], tooltip=data['Race'], popup=folium.Popup(popup_iframe), icon=folium.Icon(color='red'))
folium_marker.add_to(fg_marathons)

### CREATE GPX TRACE ###
# parse gpx file
import gpxpy
gpx_file = 'berlin_marathon_2014.gpx'
gpx = gpxpy.parse(open(gpx_file))
track = gpx.tracks[0]
segment = track.segments[0]

# load coordinate points
points = []
for track in gpx.tracks:
    for segment in track.segments:
        step = 10
        for point in segment.points[::step]:
            points.append(tuple([point.latitude, point.longitude]))

# add segments to the map
folium_gpx = folium.PolyLine(points, color='red', weight=5, opacity=0.85).add_to(run_map)

# add the gpx trace to our marathon group so it inherits the color
folium_gpx.add_to(fg_marathons)

### ADD LEGEND IN MAP CORNER ###
run_map.add_child(folium.LayerControl(position='topright', collapsed=False, autoZIndex=True))

### SAVE AND OPEN MAP ###
run_map.save('run_map.html')
import webbrowser
webbrowser.open('run_map.html')
