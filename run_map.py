import os
import json
import folium
import calendar
import gpxpy
import pandas as pd
import webbrowser
from statistics import mean
from ftplib import FTP
from dotenv import load_dotenv
load_dotenv()

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))


class RunMap:

    def __init__(self, settings='settings.json'):
        """Initialise class variables from json file content

        Args:
            json_file (string): path to json file containing all map settings
        """

        with open(settings, 'r') as jf:
            spreadsheet_json = json.loads(jf.read())

            self.sheet_id = spreadsheet_json['sheet_id']
            self.tab_id = spreadsheet_json['tab_id']
            self.events_csv = os.path.join(CURRENT_FOLDER, spreadsheet_json['events_csv'])
            self.run_map_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['run_map_html'])
            self.events_table_template = os.path.join(CURRENT_FOLDER, spreadsheet_json['events_table_template'])
            self.events_table_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['events_table_html'])
            self.events_table_css = os.path.join(CURRENT_FOLDER, spreadsheet_json['events_table_css'])
            self.eventometer_template = os.path.join(CURRENT_FOLDER, spreadsheet_json['eventometer_template'])
            self.eventometer_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['eventometer_html'])
            self.popup_contents_html = os.path.join(CURRENT_FOLDER, spreadsheet_json['popup_contents_html'])
            self.jpg_web_prefix = spreadsheet_json['jpg_web_prefix']
            self.jpg_folder = os.path.join(CURRENT_FOLDER, spreadsheet_json['jpg_folder'])
            self.gpx_folder = os.path.join(CURRENT_FOLDER, spreadsheet_json['gpx_folder'])
            self.pic_default = spreadsheet_json['pic_default']
            self.popup_width = spreadsheet_json['popup_width']
            self.popup_height = spreadsheet_json['popup_height']
            self.zoom_start = spreadsheet_json['zoom_start']
            self.gpx_weight = spreadsheet_json['gpx_weight']
            self.gpx_opacity = spreadsheet_json['gpx_opacity']
            self.gpx_smoothness = spreadsheet_json['gpx_smoothness']
            self.map_colors = spreadsheet_json['map_colors']
            self.blog_event_page = spreadsheet_json['blog_event_page']

            print('Json settings loaded successfully')

        # load html popup contents
        with open(self.popup_contents_html) as f:
            self.html_popup = f.read()

        # define counters for the eventometer
        self.dist_count = 0
        self.dplus_count = 0
        self.halfs_count = 0
        self.marathons_count = 0
        self.ultras_count = 0

    def download_spreadsheet_as_csv(self):
        """Download google spreadsheet as csv file"""

        print('\n' + ' DOWNLOAD SPREADSHEET AS CSV FILE '.center(100, '#'))

        command = f'curl -L "https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?exportFormat=csv" -o {self.events_csv}'
        os.system(command)

        if not os.path.isfile(self.events_csv):
            print(f'Error downloading the spreadsheet at location {self.events_csv}')

    def read_csv_file(self):
        """Extracts and formats data from the csv file"""

        # extract race infos into a panda dataframe
        data = pd.read_csv(self.events_csv).fillna('')

        # store information into lists
        self.date_list = list(data['Date'])
        self.race_list = list(data['Race'])
        self.loc_list = list(data['Location'])
        self.lat_list = list(data['Latitude'])
        self.lon_list = list(data['Longitude'])
        self.type_list = list(data['Type'])
        self.notes_list = list(data['Notes'])
        self.dist_list = list(data['Distance'])
        self.dplus_list = list(data['D+'])
        self.time_list = list(data['Time'])
        self.link_list = list(data['Link'])
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

        # get distance list as floats
        self.distF_list = [float(dist) for dist in self.dist_list]

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
            path = os.path.join(CURRENT_FOLDER, self.gpx_folder, gpx_file) if gpx_file else ''
            self.gpx_files.append(path)

    def generate_map(self):
        """Generates the map as a html file"""

        print('\n' + ' GENERATING HTML MAP '.center(100, '#'))

        # read csv file
        self.read_csv_file()

        # center map based on race locations
        start_lat = mean([min(self.lat_list), max(self.lat_list)])
        start_lon = mean([min(self.lon_list), max(self.lon_list)])

        # create map object
        self.run_map = folium.Map(location=[start_lat, start_lon], tiles=None, zoom_start=self.zoom_start)

        folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(self.run_map)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
                         attr='Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA,'
                         'ESA, METI, NRCAN, GEBCO, NOAA, iPC', name='Nat Geo Map').add_to(self.run_map)

        # create feature groups and add them to the map
        legend_txt = '<span style="color: {col};">{txt}</span>'
        fg_misc = folium.FeatureGroup(name=legend_txt.format(txt='Misc', col=self.map_colors['misc'])).add_to(self.run_map)
        fg_10k = folium.FeatureGroup(name=legend_txt.format(txt='10k', col=self.map_colors['10k'])).add_to(self.run_map)
        fg_half = folium.FeatureGroup(name=legend_txt.format(txt='Halfs', col=self.map_colors['half'])).add_to(self.run_map)
        fg_marathon = folium.FeatureGroup(name=legend_txt.format(txt='Marathons', col=self.map_colors['marathon'])).add_to(self.run_map)
        fg_ultra = folium.FeatureGroup(name=legend_txt.format(txt='Ultras', col=self.map_colors['ultra'])).add_to(self.run_map)

        # add markers based on csv file data
        data_iter = zip(self.dateF_list, self.race_list, self.loc_list, self.lat_list, self.lon_list,
                        self.type_list, self.distF_list, self.dplus_list, self.timeF_list, self.notes_list,
                        self.link_list, self.post_list, self.jpg_links, self.gpx_files)

        for date, race, loc, lt, ln, typ, dist, dplus, time, notes, link, post, jpg, gpx in data_iter:

            print(f'Loading {race}')

            # add distance and dplus to counter
            self.dist_count += dist
            if dplus:
                self.dplus_count += dplus

            # define race_color icon and title based on the distance
            str_dist = str(dist)

            if dist == 10:
                race_color = self.map_colors['10k']
            elif 21 <= dist <= 22:
                race_color = self.map_colors['half']
                self.halfs_count += 1
            elif 42 <= dist <= 43:
                race_color = self.map_colors['marathon']
                self.marathons_count += 1
            elif dist > 43:
                race_color = self.map_colors['ultra']
                self.ultras_count += 1
            else:
                race_color = self.map_colors['misc']

            # delete the blog post line if link not in csv file
            if not str(post).lower().startswith('http'):
                html_contents = self.html_popup.replace(' | <a href="{post}" target="_blank">Blog Post</a>', '')
            else:
                html_contents = self.html_popup

            # reformat distance with comma and km suffix
            str_dist = str_dist.replace('.', ',') + ' km'

            # adds D+ to distance if available
            if dplus:
                str_dist += f' | {int(dplus)} D+'

            # create the iFrame popup
            iframe = folium.IFrame(
                width=self.popup_width, height=self.popup_height, html=html_contents.format(
                    race=race, date=date, loc=loc, typ=typ, dist=str_dist, time=time,
                    notes=notes, link=link, post=post, pic=jpg, race_clr=race_color
                )
            )

            # add marker to feature groups
            folium_marker = folium.Marker(location=[lt, ln], tooltip=race, popup=folium.Popup(iframe),
                                          icon=folium.Icon(color=race_color))

            # process gpx data
            folium_gpx = None
            if gpx:
                points = self.process_gpx_to_df(gpx)
                folium_gpx = folium.PolyLine(points, color=race_color, weight=self.gpx_weight,
                                             opacity=self.gpx_opacity).add_to(self.run_map)

            # add markers and gpx traces to Feature Groups
            if dist == 10:
                folium_marker.add_to(fg_10k)
                if folium_gpx:
                    folium_gpx.add_to(fg_10k)
            elif 21 <= dist <= 22:
                folium_marker.add_to(fg_half)
                if folium_gpx:
                    folium_gpx.add_to(fg_half)
            elif 42 <= dist <= 43:
                folium_marker.add_to(fg_marathon)
                if folium_gpx:
                    folium_gpx.add_to(fg_marathon)
            elif dist > 43:
                folium_marker.add_to(fg_ultra)
                if folium_gpx:
                    folium_gpx.add_to(fg_ultra)
            else:
                folium_marker.add_to(fg_misc)
                if folium_gpx:
                    folium_gpx.add_to(fg_misc)

        # add layer control (legend), each feature group will be a different category
        self.run_map.add_child(folium.LayerControl(position='topright', collapsed=True, autoZIndex=True))

    def generate_events_table(self):
        """Generate the html events table embebbed on the website"""

        print('\n' + ' GENERATING EVENTS TABLE HTML FILE '.center(100, '#'))

        if not os.path.isfile(self.events_table_template):
            print(f'{self.events_table_template} is not a valid filepath. Skipping this step.')
            return

        with open(self.events_table_template, 'r', encoding='utf-8') as input_file:
            html_contents = input_file.read()

        html_marker = '<!--InsertNewEvent-->'
        indent = 4 * ' '
        current_year = ''

        if html_marker not in html_contents:
            print('html marker not found in template file. Skipping this step.')
            return

        # create data iterator from spreadsheet
        data_iter = zip(self.date_list, self.race_list, self.loc_list, self.type_list, self.dist_list,
                        self.dplus_list, self.time_list, self.link_list, self.post_list)

        # browse through event_table
        for date, race, loc, typ, dist, dplus, time, link, post in data_iter:

            # create new event to store the corresponding html contents
            new_event = ''

            # Add a year separator
            year = date.split('.')[-1]
            if not current_year:
                current_year = year
            else:
                if current_year != year:
                    new_event += indent + '<tr>\n'
                    new_event += 2 * indent + '<td class="tg-d1kj" colspan="6"></td>'
                    new_event += indent + '</tr>\n'
                    current_year = year

            # build new event html data
            new_event += indent + '<tr>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{date}<br />\n'
            if post:
                new_event += 2 * indent + f'<a href="{post}" target="_blank"><i><u>Review</u></i></a></td>\n'
            new_event += 2 * indent + f'<td class="tg-9hbo"><a de="" en="" href="{link}" https:="" target="_blank">{race}</a></td>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{loc}</td>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{typ}</td>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{dist} km<br />\n'
            if dplus:
                new_event += 2 * indent + f'{int(dplus)} m</td>\n'
            new_event += 2 * indent + f'<td class="tg-yw4l">{time}</td>\n'
            new_event += indent + '</tr>\n'

            # add to html file
            html_contents = html_contents.replace(html_marker, new_event + html_marker)

        # write html file
        with open(self.events_table_html, 'w', encoding='utf-8') as output_file:
            output_file.write(html_contents)

        print(f'Events table html file created successfully at location {self.events_table_html}')

    def generate_eventometer(self):
        """Generates the html event-o-meter embebbed as iframe on the main page"""

        with open(self.eventometer_template, 'r') as input_file:
            html_contents = input_file.read()
            html_contents = html_contents.replace('<!--dist-->', str(int(self.dist_count)))
            html_contents = html_contents.replace('<!--dplus-->', str(round(self.dplus_count / 1000, 2)).replace('.', ','))
            html_contents = html_contents.replace('<!--H-->', str(self.halfs_count))
            html_contents = html_contents.replace('<!--M-->', str(self.marathons_count))
            html_contents = html_contents.replace('<!--U-->', str(self.ultras_count))

        # write html file
        with open(self.eventometer_html, 'w', encoding='utf-8') as output_file:
            output_file.write(html_contents)
            print(f'Eventometer html file created successfully at location {self.eventometer_template}')

    def save_map(self):
        """Saves the map as html file"""
        print('\n' + ' SAVING HTML MAP '.center(100, '#'))
        self.run_map.save(self.run_map_html)
        print(f'Map saved at location {self.run_map_html}')

    def process_gpx_to_df(self, gpx_file):
        """Parse the gpx data into a dataframe

        Args:
            gpx_file (string): path to gpx file
            step (int): slicing step for storing gpx points to avoid using too much data

        Return:
            (list): list of tuples (lat, long) for each data point
        """

        if not os.path.isfile(gpx_file) and not gpx_file.lower().endswith('.gpx'):
            print(f'Invalid gpx file {gpx_file}')
            return

        gpx = gpxpy.parse(open(gpx_file))
        track = gpx.tracks[0]
        segment = track.segments[0]

        # Make points tuple for lines
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points[::self.gpx_smoothness]:
                    points.append(tuple([point.latitude, point.longitude]))

        return points

    def upload_to_ftp(self, html=True, jpg=True, gpx=True):
        """Uploads map and files to ftp server"""

        ftp_address = os.getenv('FTP_ADDRESS')
        ftp_user = os.getenv('FTP_USER')
        ftp_pwd = os.getenv('FTP_PWD')
        ftp_start_dir = os.getenv('FTP_START_DIR')

        ftp = FTP(ftp_address)
        ftp.login(user=ftp_user, passwd=ftp_pwd, acct='')
        ftp.cwd(ftp_start_dir)

        if html:
            print('\n' + ' TRANSFERING HTML MAP '.center(100, '#'))
            with open(self.run_map_html, 'rb') as file:
                ftp.storbinary('STOR run_map.html', file)
            print('run_map.html transfered')

            print('\n' + ' TRANSFERING HTML EVENTS TABLE '.center(100, '#'))
            with open(self.events_table_html, 'rb') as file:
                ftp.storbinary('STOR events_table.html', file)
            print('events_table.html transfered')
            with open(self.events_table_css, 'rb') as file:
                ftp.storbinary('STOR events_table.css', file)
            print('events_table.css transfered')

            print('\n' + ' TRANSFERING HTML EVENT-O-METER '.center(100, '#'))
            with open(self.eventometer_html, 'rb') as file:
                ftp.storbinary('STOR eventometer.html', file)
            print('eventometer.html transfered')

        # transfer jpg files
        if jpg:
            ftp.cwd('jpg')
            jpg_folder = os.path.join(CURRENT_FOLDER, 'jpg')

            print('\n' + ' TRANSFERING JPG FILES '.center(100, '#'))
            for jpg in os.listdir(jpg_folder):
                pic_path = os.path.join(jpg_folder, jpg)
                with open(pic_path, 'rb') as file:
                    ftp.storbinary('STOR {}'.format(jpg), file)
                    print('{} transfered'.format(jpg))

        # transfer gpx files
        if gpx:
            ftp.cwd('../gpx')
            gpx_folder = os.path.join(CURRENT_FOLDER, 'gpx')

            print('\n' + ' TRANSFERING GPX FILES '.center(100, '#'))
            for gpx in os.listdir(gpx_folder):
                gpx_path = os.path.join(gpx_folder, gpx)
                with open(gpx_path, 'rb') as file:
                    ftp.storbinary('STOR {}'.format(gpx), file)
                    print('{} transfered'.format(gpx))

        ftp.quit()

    def open_blog_page(self):
        """Opens the map on the blog web page"""
        webbrowser.open(self.blog_event_page)
