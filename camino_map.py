import os
import json
import sqlite3
import folium
import calendar
import gpxpy
import pandas as pd
import webbrowser
from statistics import mean
from ftplib import FTP
from dotenv import load_dotenv
from collections import OrderedDict
load_dotenv()

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(CURRENT_FOLDER, "camino_map.db")


class CaminoMap:

    def __init__(self, settings='camino_settings.json'):
        """Initialise class variables from json file content

        Args:
            settings (string): path to json file containing all map settings
        """

        with open(settings, 'r') as jf:
            spreadsheet_json = json.loads(jf.read())

            self.sheet_id = spreadsheet_json['sheet_id']
            self.tab_id = spreadsheet_json['tab_id']
            self.stamps_tab_id = spreadsheet_json['stamps_tab_id']
            self.events_csv = os.path.join(CURRENT_FOLDER, spreadsheet_json['events_csv'])
            self.stamps_csv = os.path.join(CURRENT_FOLDER, spreadsheet_json['stamps_csv'])
            self.camino_map_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['camino_map_html'])
            self.table_template = os.path.join(CURRENT_FOLDER, spreadsheet_json['table_template'])
            self.table_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['table_html'])
            self.table_css = os.path.join(CURRENT_FOLDER, spreadsheet_json['table_css'])
            self.popup_contents_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['popup_contents_html'])
            self.stamp_popup_contents_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['stamp_popup_contents_html'])
            self.jpg_web_prefix = spreadsheet_json['jpg_web_prefix']
            self.jpg_folder = os.path.join(CURRENT_FOLDER, spreadsheet_json['jpg_folder'])
            self.gpx_folder = os.path.join(CURRENT_FOLDER, spreadsheet_json['gpx_folder'])
            self.pic_default = spreadsheet_json['pic_default']
            self.stamp_pic_default = spreadsheet_json['stamp_pic_default']
            self.popup_width = spreadsheet_json['popup_width']
            self.popup_height = spreadsheet_json['popup_height']
            self.stamp_popup_width = spreadsheet_json['stamp_popup_width']
            self.stamp_popup_height = spreadsheet_json['stamp_popup_height']
            self.zoom_start = spreadsheet_json['zoom_start']
            self.gpx_weight = spreadsheet_json['gpx_weight']
            self.gpx_opacity = spreadsheet_json['gpx_opacity']
            self.gpx_smoothness = spreadsheet_json['gpx_smoothness']
            self.blog_event_page = spreadsheet_json['blog_event_page']
            self.ftp_dir = spreadsheet_json['ftp_dir']

            print('Json settings loaded successfully')

        # load html popup contents
        with open(self.popup_contents_html) as f:
            self.html_popup = f.read()

        # load stamp popup contents
        with open(self.stamp_popup_contents_html) as f:
            self.stamp_html_popup = f.read()

        # define counters for stats
        self.dist_count = 0
        self.dplus_count = 0
        self.stages_count = 0
        self.stamps_count = 0

    def download_spreadsheet_as_csv(self):
        """Download google spreadsheet as csv file"""

        os.makedirs(os.path.dirname(self.events_csv), exist_ok=True)

        command = f'curl -L "https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?exportFormat=csv" -o {self.events_csv}'
        os.system(command)

        if not os.path.isfile(self.events_csv):
            print(f'Error downloading the spreadsheet at location {self.events_csv}')

    def download_stamps_as_csv(self):
        """Download stamps spreadsheet as csv file"""

        os.makedirs(os.path.dirname(self.stamps_csv), exist_ok=True)

        command = f'curl -L "https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?exportFormat=csv&gid={self.stamps_tab_id}" -o {self.stamps_csv}'
        os.system(command)

        if not os.path.isfile(self.stamps_csv):
            print(f'Error downloading the stamps spreadsheet at location {self.stamps_csv}')

    def load_csv_file(self):
        """Extracts and formats data from the csv file"""

        print('\n' + ' DOWNLOAD AND READ SPREADSHEET '.center(100, '#'))

        # download and update csv file
        self.download_spreadsheet_as_csv()

        # extract camino infos into a panda dataframe
        data = pd.read_csv(self.events_csv).fillna('')

        # store information into lists
        self.date_list = list(data['Date'])
        self.title_list = list(data['Title'])
        self.camino_list = list(data['Camino'])
        self.start_list = list(data['Start'])
        self.start_lat_list = list(data['Start Lat'])
        self.start_lon_list = list(data['Start Lon'])
        self.end_list = list(data['End'])
        self.end_lat_list = list(data['End Lat'])
        self.end_lon_list = list(data['End Lon'])
        self.dist_list = list(data['Distance'])
        self.dplus_list = list(data['D+'])
        self.time_list = list(data['Time'])
        self.notes_list = list(data['Notes'])
        self.color_list = list(data['Color'])
        self.post_list = list(data['Post'])

        # format date as 'Day FullMonthName Year'
        self.dateF_list = []
        for date in self.date_list:
            date = [int(d) for d in date.split('.')]
            date = f'{date[0]} {calendar.month_name[date[1]]} {date[2]}'
            self.dateF_list.append(date)

        # format time entries as 'Xh Ymin Zsec'
        self.timeF_list = []
        for time in self.time_list:
            if len(time.split(':')) == 3:
                time = time.split(':')
                time = f'{time[0]}h {time[1]}min {time[2]}sec'
            self.timeF_list.append(time)

        # get distance list as floats (handle comma as decimal separator)
        self.distF_list = []
        for dist in self.dist_list:
            if isinstance(dist, str):
                dist = dist.replace(',', '.')
            self.distF_list.append(float(dist) if dist else 0.0)

        # list of jpg web links
        self.jpg_links = []
        for jpg in data['Jpg']:
            if jpg:
                self.jpg_links.append(f'{self.jpg_web_prefix}{jpg}')
            else:
                self.jpg_links.append(f'{self.jpg_web_prefix}{self.pic_default}')

        # list of gpx file paths
        self.gpx_files = []
        for gpx_file in data['Gpx']:
            path = os.path.join(self.gpx_folder, gpx_file) if gpx_file else ''
            self.gpx_files.append(path)

    def load_stamps_csv(self):
        """Extracts and formats data from the stamps csv file"""

        print('\n' + ' DOWNLOAD AND READ STAMPS SPREADSHEET '.center(100, '#'))

        # download and update stamps csv file
        self.download_stamps_as_csv()

        # extract stamps infos into a panda dataframe
        data = pd.read_csv(self.stamps_csv).fillna('')

        # store information into lists
        self.stamp_date_list = list(data['Date'])
        self.stamp_place_list = list(data['Place'])
        self.stamp_location_list = list(data['Location'])
        self.stamp_camino_list = list(data['Camino'])
        self.stamp_lat_list = list(data['Lat'])
        self.stamp_lon_list = list(data['Lon'])
        self.stamp_note_list = list(data['Note'])
        self.stamp_link_list = list(data['Link'])

        # format date as 'Day FullMonthName Year'
        self.stamp_dateF_list = []
        for date in self.stamp_date_list:
            date = [int(d) for d in date.split('.')]
            date = f'{date[0]} {calendar.month_name[date[1]]} {date[2]}'
            self.stamp_dateF_list.append(date)

        # list of jpg web links for stamps
        self.stamp_jpg_links = []
        for jpg in data['Jpg']:
            if jpg:
                self.stamp_jpg_links.append(f'{self.jpg_web_prefix}{jpg}')
            else:
                self.stamp_jpg_links.append(f'{self.jpg_web_prefix}{self.stamp_pic_default}')

    def update_database(self, rebuild=False):
        """Update database with new data"""

        print('\n' + ' UPDATE DATABASE '.center(100, '#'))

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # drop table to rebuild a brand new one
        if rebuild:
            cursor.execute("DROP TABLE IF EXISTS camino_map")

        # create database if not available
        cursor.execute("""CREATE TABLE IF NOT EXISTS camino_map(
                       id INTEGER PRIMARY KEY,
                       date TEXT,
                       title TEXT,
                       camino TEXT,
                       start TEXT,
                       start_lt REAL,
                       start_ln REAL,
                       end TEXT,
                       end_lt REAL,
                       end_ln REAL,
                       dist REAL,
                       dplus INT,
                       time TEXT,
                       notes TEXT,
                       post TEXT,
                       jpg TEXT,
                       gpx TEXT,
                       UNIQUE(date, title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx)
                       )
        """)

        # delete from database any entry not in the csv file
        cursor.execute("SELECT date FROM camino_map")
        dates_in_db = [row[0] for row in cursor.fetchall()]

        for date in dates_in_db:
            if date not in self.date_list:
                # entry has been deleted from csv file, remove it from db too
                cursor.execute("DELETE FROM camino_map WHERE date=?", (date,))
                print(f"Deleting from database entry with date {date}: Not in CSV file.")

        # iterate through database, add or update entries
        data_iter = zip(self.date_list, self.title_list, self.camino_list, self.start_list,
                        self.start_lat_list, self.start_lon_list, self.end_list, self.end_lat_list,
                        self.end_lon_list, self.distF_list, self.dplus_list, self.time_list,
                        self.notes_list, self.post_list, self.jpg_links, self.gpx_files)

        for date, title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx in data_iter:
            cursor.execute("SELECT * FROM camino_map WHERE date=?", (date,))
            row = cursor.fetchone()

            # entry already exists -> update it if any change
            if row:
                # unpack row values for comparison
                _, _, title_db, camino_db, start_db, start_lt_db, start_ln_db, end_db, end_lt_db, end_ln_db, dist_db, dplus_db, time_db, notes_db, post_db, jpg_db, gpx_db = row

                # check for a change in the row values
                if (title != title_db or camino != camino_db or start != start_db or
                    start_lt != start_lt_db or start_ln != start_ln_db or end != end_db or
                    end_lt != end_lt_db or end_ln != end_ln_db or dist != dist_db or
                    dplus != dplus_db or time != time_db or notes != notes_db or
                    post != post_db or jpg != jpg_db or gpx != gpx_db):

                    # update the row
                    cursor.execute("""UPDATE camino_map
                                   SET title=?, camino=?, start=?, start_lt=?, start_ln=?, end=?, end_lt=?, end_ln=?, dist=?, dplus=?, time=?, notes=?, post=?, jpg=?, gpx=?
                                   WHERE date=?
                                   """, (title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx, date))

                    print(f"Updating to database entry with date {date}: different values in CSV file.")

            # new entry -> add it
            else:
                cursor.execute("""INSERT INTO camino_map
                               (date, title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                               """, (date, title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx))

                print(f"Adding to database entry with date {date}: New entry.")

        # commit and close
        conn.commit()
        cursor.close()
        conn.close()

        print("Database updated successfully.")
        self.check_database()

    def check_database(self):
        """Check the database properties"""

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # database rows
        cursor.execute("SELECT COUNT(*) FROM camino_map")
        rows = cursor.fetchone()[0]

        # database colums
        cursor.execute("PRAGMA table_info(camino_map)")
        columns = cursor.fetchall()

        print(f"Path: {DATABASE_PATH}")
        print(f"Rows: {rows}")
        print(f"Columns: {len(columns)}")

        cursor.close()
        conn.close()

    def search_database(self, sql_query):
        """Search the database"""

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # print sql query results
        results = cursor.execute(sql_query)

        if results:
            for result in results:
                print(50 * '-')
                for element in result:
                    print(element)
        else:
            print('SQL request returned no result.')

        cursor.close()
        conn.close()

    def generate_map(self):
        """Generates the map as a html file"""

        print('\n' + ' GENERATING HTML MAP '.center(100, '#'))

        # center map based on all location coordinates (start, end points and stamps)
        all_lats = self.start_lat_list + self.end_lat_list + self.stamp_lat_list
        all_lons = self.start_lon_list + self.end_lon_list + self.stamp_lon_list
        # Filter out empty values
        all_lats = [lat for lat in all_lats if lat]
        all_lons = [lon for lon in all_lons if lon]

        start_lat = mean([min(all_lats), max(all_lats)])
        start_lon = mean([min(all_lons), max(all_lons)])

        # create map object
        self.camino_map = folium.Map(location=[start_lat, start_lon], tiles=None, zoom_start=self.zoom_start)

        # Add custom CSS to remove focus outline on paths
        custom_css = """
        <style>
            .leaflet-interactive {
                outline: none !important;
            }
            .leaflet-interactive:focus {
                outline: none !important;
            }
            path.leaflet-interactive:focus {
                outline: none !important;
            }
        </style>
        """
        self.camino_map.get_root().html.add_child(folium.Element(custom_css))

        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
                         attr='Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA,'
                         'ESA, METI, NRCAN, GEBCO, NOAA, iPC', name='Nat Geo Map').add_to(self.camino_map)
        folium.TileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                         attr='Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)',
                         name='OpenTopoMap').add_to(self.camino_map)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                         attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                         name='Satellite').add_to(self.camino_map)
        folium.TileLayer('cartodbpositron', name='CartoDB Positron').add_to(self.camino_map)
        folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(self.camino_map)

        # create feature groups based on unique Camino routes
        legend_txt = '<span style="color: {col};">{txt}</span>'
        feature_groups = OrderedDict()

        # Build a mapping of Camino name to color from the spreadsheet data
        camino_colors = {}
        for camino, color in zip(self.camino_list, self.color_list):
            if camino and camino not in camino_colors:
                camino_colors[camino] = color if color else 'blue'

        # Create feature groups for each Camino route with its color
        for camino in sorted(camino_colors.keys()):
            color = camino_colors[camino]
            feature_groups[camino] = folium.FeatureGroup(name=legend_txt.format(txt=camino, col=color)).add_to(self.camino_map)

        # add markers based on csv file data
        data_iter = zip(self.dateF_list, self.title_list, self.camino_list, self.start_list,
                        self.start_lat_list, self.start_lon_list, self.end_list, self.end_lat_list,
                        self.end_lon_list, self.distF_list, self.dplus_list, self.timeF_list,
                        self.notes_list, self.post_list, self.jpg_links, self.gpx_files, self.color_list)

        for date, title, camino, start, start_lt, start_ln, end, end_lt, end_ln, dist, dplus, time, notes, post, jpg, gpx, color in data_iter:

            print(f'Loading {title}')

            # add distance and dplus to counter
            self.dist_count += dist
            if dplus:
                self.dplus_count += dplus

            # count stages
            self.stages_count += 1

            # use blue as default color
            stage_color = color if color else 'blue'

            # delete the blog post line if link not in csv file
            if not str(post).lower().startswith('http'):
                html_contents = self.html_popup.replace('<a href="{post}" target="_blank">Blog Post</a>', '')
            else:
                html_contents = self.html_popup

            # reformat distance with comma and km suffix
            str_dist = str(dist).replace('.', ',') + ' km'

            # adds D+ to distance if available
            if dplus:
                str_dist += f' | {int(dplus)} D+'

            # create the iFrame popup for marker
            iframe = folium.IFrame(
                width=self.popup_width, height=self.popup_height, html=html_contents.format(
                    title=title, date=date, camino=camino, start=start, end=end,
                    dist=str_dist, time=time, notes=notes, post=post, pic=jpg
                )
            )

            # create custom shell icon using the camino_shell.png image
            shell_icon_url = f'{self.jpg_web_prefix}camino_shell.png'
            shell_icon = folium.CustomIcon(
                icon_image=shell_icon_url,
                icon_size=(32, 32),
                icon_anchor=(16, 16),
                popup_anchor=(0, -16)
            )

            # add marker at START location with shell icon
            folium_marker = folium.Marker(
                location=[start_lt, start_ln],
                tooltip=f"{title}: {start} → {end}",
                popup=folium.Popup(iframe),
                icon=shell_icon
            )

            # process gpx data
            folium_gpx = None
            if gpx:
                points = self.process_gpx_to_df(gpx)
                if points:
                    # Create popup for the GPX trace (same as marker)
                    iframe_gpx = folium.IFrame(
                        width=self.popup_width, height=self.popup_height, html=html_contents.format(
                            title=title, date=date, camino=camino, start=start, end=end,
                            dist=str_dist, time=time, notes=notes, post=post, pic=jpg
                        )
                    )
                    folium_gpx = folium.PolyLine(
                        points,
                        color=stage_color,
                        weight=self.gpx_weight,
                        opacity=self.gpx_opacity
                    )
                    # Add popup and tooltip to the polyline
                    folium_gpx.add_child(folium.Popup(iframe_gpx))
                    folium.Tooltip(f"{title}: {start} → {end}").add_to(folium_gpx)

            # add marker and gpx trace to Feature Groups based on Camino route
            if camino and camino in feature_groups:
                folium_marker.add_to(feature_groups[camino])
                if folium_gpx:
                    folium_gpx.add_to(feature_groups[camino])
            else:
                # Add to map directly if no camino or camino not in feature groups
                folium_marker.add_to(self.camino_map)
                if folium_gpx:
                    folium_gpx.add_to(self.camino_map)

        # Create a feature group for stamps
        legend_txt = '<span style="color: {col};">{txt}</span>'
        stamps_feature_group = folium.FeatureGroup(name=legend_txt.format(txt='Stamps', col='black')).add_to(self.camino_map)

        # Add stamp markers
        stamp_data_iter = zip(self.stamp_dateF_list, self.stamp_place_list, self.stamp_location_list,
                              self.stamp_camino_list, self.stamp_lat_list, self.stamp_lon_list,
                              self.stamp_note_list, self.stamp_link_list, self.stamp_jpg_links)

        for date, place, location, camino, lat, lon, note, link, jpg in stamp_data_iter:
            print(f'Loading stamp: {place}')

            # count stamps
            self.stamps_count += 1

            # create the iFrame popup for stamp marker
            iframe = folium.IFrame(
                width=self.stamp_popup_width, height=self.stamp_popup_height,
                html=self.stamp_html_popup.format(
                    place=place, date=date, location=location, camino=camino,
                    note=note, link=link, pic=jpg
                )
            )

            # create custom stamp icon using the stamp.png image
            stamp_icon_url = f'{self.jpg_web_prefix}stamp.png'
            stamp_icon = folium.CustomIcon(
                icon_image=stamp_icon_url,
                icon_size=(32, 32),
                icon_anchor=(16, 16),
                popup_anchor=(0, -16)
            )

            # add stamp marker with custom stamp icon
            stamp_marker = folium.Marker(
                location=[lat, lon],
                tooltip=place,
                popup=folium.Popup(iframe),
                icon=stamp_icon
            )

            stamp_marker.add_to(stamps_feature_group)

        print(f'Total stamps loaded: {self.stamps_count}')

        # add layer control (legend), each feature group will be a different Camino route
        self.camino_map.add_child(folium.LayerControl(position='topright', collapsed=True, autoZIndex=True))

    def generate_table(self):
        """Generate the html table embebbed on the website"""

        print('\n' + ' GENERATING TABLE HTML FILE '.center(100, '#'))

        if not os.path.isfile(self.table_template):
            print(f'{self.table_template} is not a valid filepath. Skipping this step.')
            return

        with open(self.table_template, 'r', encoding='utf-8') as input_file:
            html_contents = input_file.read()

        html_marker = '<!--InsertNewEvent-->'
        indent = 4 * ' '
        current_year = ''

        if html_marker not in html_contents:
            print('html marker not found in template file. Skipping this step.')
            return

        # create data iterator from spreadsheet
        data_iter = zip(self.date_list, self.camino_list, self.start_list, self.end_list,
                        self.dist_list, self.dplus_list, self.time_list, self.post_list)

        # browse through event_table
        for date, camino, start, end, dist, dplus, time, post in data_iter:

            # create new event to store the corresponding html contents
            new_event = ''

            # Add a year separator
            year = date.split('.')[-1]
            if not current_year:
                current_year = year
            else:
                if current_year != year:
                    new_event += indent + '<tr>\n'
                    new_event += 2 * indent + '<td class="tg-d1kj" colspan="5"></td>'
                    new_event += indent + '</tr>\n'
                    current_year = year

            # build new event html data
            new_event += indent + '<tr>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{date}<br />\n'
            if post:
                new_event += 2 * indent + f'<a href="{post}" target="_blank"><i><u>Review</u></i></a></td>\n'
            else:
                new_event += 2 * indent + '</td>\n'
            new_event += 2 * indent + f'<td class="tg-9hbo">{camino}</td>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{start} → {end}</td>\n'

            # Distance / D+
            dist_str = f'{dist} km'
            if dplus:
                dist_str += f' | {int(dplus)} m'
            new_event += 2 * indent + f'<td class="tg-yw4l">{dist_str}</td>\n'

            new_event += 2 * indent + f'<td class="tg-yw4l">{time}</td>\n'
            new_event += indent + '</tr>\n'

            # add to html file
            html_contents = html_contents.replace(html_marker, new_event + html_marker)

        # write html file
        with open(self.table_html, 'w', encoding='utf-8') as output_file:
            output_file.write(html_contents)

        print(f'Table html file created successfully at location {self.table_html}')

    def save_map(self):
        """Saves the map as html file"""
        print('\n' + ' SAVING HTML MAP '.center(100, '#'))
        self.camino_map.save(self.camino_map_html)
        print(f'Map saved at location {self.camino_map_html}')

    def process_gpx_to_df(self, gpx_file):
        """Parse the gpx data into a dataframe

        Args:
            gpx_file (string): path to gpx file
            step (int): slicing step for storing gpx points to avoid using too much data

        Return:
            (list): list of tuples (lat, long) for each data point
        """

        if not os.path.isfile(gpx_file) or not gpx_file.lower().endswith('.gpx'):
            print(f'Invalid gpx file {gpx_file}')
            return None

        gpx = gpxpy.parse(open(gpx_file))

        # Make points tuple for lines
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points[::self.gpx_smoothness]:
                    points.append(tuple([point.latitude, point.longitude]))

        return points

    def upload_to_ftp(self, html=True, jpg=True, gpx=True, force=False):
        """Uploads map and files to ftp server

        Args:
            html (bool): Upload HTML files
            jpg (bool): Upload JPG files
            gpx (bool): Upload GPX files
            force (bool): Force upload all files, even if they exist on server
        """

        ftp_address = os.getenv('FTP_ADDRESS')
        ftp_user = os.getenv('FTP_USER')
        ftp_pwd = os.getenv('FTP_PWD')

        # Check if all required environment variables are set
        if not all([ftp_address, ftp_user, ftp_pwd]):
            print("❌ Error: Missing FTP environment variables in .env file")
            print("Required variables: FTP_ADDRESS, FTP_USER, FTP_PWD")
            return False

        try:
            print(f"🔄 Connecting to FTP server: {ftp_address}")
            ftp = FTP(ftp_address)

            print("🔄 Logging in...")
            ftp.login(user=ftp_user, passwd=ftp_pwd, acct='')

            # Try to change to directory, create it if it doesn't exist
            print(f"🔄 Changing to directory: {self.ftp_dir}")
            try:
                ftp.cwd(self.ftp_dir)
            except Exception:
                print(f"📁 Directory {self.ftp_dir} doesn't exist, creating it...")
                ftp.mkd(self.ftp_dir)
                ftp.cwd(self.ftp_dir)
            print("✅ FTP connection successful!")

        except Exception as e:
            print(f"❌ FTP connection failed: {str(e)}")
            print("💡 Please check your .env file and FTP credentials.")
            print(f"💡 Make sure the FTP directory {self.ftp_dir} can be created on the server.")
            return False

        def get_ftp_file_list(directory='.'):
            """Get list of files in FTP directory"""
            files = []
            try:
                ftp.cwd(directory)
                ftp.retrlines('NLST', files.append)
            except Exception as e:
                print(f"Warning: Could not list files in {directory}: {e}")
            return files

        def file_needs_upload(filename, ftp_files, force_upload=False):
            """Check if file needs to be uploaded"""
            if force_upload:
                return True
            return filename not in ftp_files

        if html:
            print('\n' + ' TRANSFERING HTML FILES '.center(100, '#'))

            # Get list of files in root directory
            ftp_files = get_ftp_file_list('.')

            # Upload camino_map.html
            with open(self.camino_map_html, 'rb') as file:
                ftp.storbinary('STOR camino_map.html', file)
            print('camino_map.html transfered')

            # Upload camino_table.html
            with open(self.table_html, 'rb') as file:
                ftp.storbinary('STOR camino_table.html', file)
            print('camino_table.html transfered')

            # Upload camino_table.css
            with open(self.table_css, 'rb') as file:
                ftp.storbinary('STOR camino_table.css', file)
            print('camino_table.css transfered')

        # transfer jpg files
        if jpg:
            print('\n' + ' TRANSFERING JPG FILES '.center(100, '#'))
            try:
                try:
                    ftp.cwd('jpg')
                except Exception:
                    print("📁 Creating jpg/ directory...")
                    ftp.mkd('jpg')
                    ftp.cwd('jpg')
                ftp_jpg_files = get_ftp_file_list('.')
                jpg_folder = self.jpg_folder

                if os.path.exists(jpg_folder):
                    local_jpg_files = os.listdir(jpg_folder)
                    uploaded_count = 0
                    skipped_count = 0

                    for jpg_file in local_jpg_files:
                        if file_needs_upload(jpg_file, ftp_jpg_files, force):
                            pic_path = os.path.join(jpg_folder, jpg_file)
                            with open(pic_path, 'rb') as file:
                                ftp.storbinary('STOR {}'.format(jpg_file), file)
                            print('{} transfered'.format(jpg_file))
                            uploaded_count += 1
                        else:
                            skipped_count += 1

                    print(f'JPG transfer complete: {uploaded_count} uploaded, {skipped_count} skipped')
                else:
                    print(f'JPG folder {jpg_folder} does not exist')

                # Return to start directory
                ftp.cwd(self.ftp_dir)
            except Exception as e:
                print(f'Error accessing JPG directory: {e}')
                ftp.cwd(self.ftp_dir)

        # transfer gpx files
        if gpx:
            print('\n' + ' TRANSFERING GPX FILES '.center(100, '#'))
            try:
                try:
                    ftp.cwd('gpx')
                except Exception:
                    print("📁 Creating gpx/ directory...")
                    ftp.mkd('gpx')
                    ftp.cwd('gpx')
                ftp_gpx_files = get_ftp_file_list('.')
                gpx_folder = self.gpx_folder

                if os.path.exists(gpx_folder):
                    local_gpx_files = os.listdir(gpx_folder)
                    uploaded_count = 0
                    skipped_count = 0

                    for gpx_file in local_gpx_files:
                        if file_needs_upload(gpx_file, ftp_gpx_files, force):
                            gpx_path = os.path.join(gpx_folder, gpx_file)
                            with open(gpx_path, 'rb') as file:
                                ftp.storbinary('STOR {}'.format(gpx_file), file)
                            print('{} transfered'.format(gpx_file))
                            uploaded_count += 1
                        else:
                            skipped_count += 1

                    print(f'GPX transfer complete: {uploaded_count} uploaded, {skipped_count} skipped')
                else:
                    print(f'GPX folder {gpx_folder} does not exist')

                # Return to start directory
                ftp.cwd(self.ftp_dir)
            except Exception as e:
                print(f'Error accessing GPX directory: {e}')
                ftp.cwd(self.ftp_dir)

        try:
            ftp.quit()
            print("✅ FTP upload completed successfully!")
            return True
        except Exception as e:
            print(f"Warning: Error closing FTP connection: {e}")
            return True

    def open_blog_page(self):
        """Opens the map on the blog web page"""
        webbrowser.open(self.blog_event_page)

