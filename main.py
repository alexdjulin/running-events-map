from run_map import RunMap

if __name__ == '__main__':

    run_map = RunMap()
    run_map.download_spreadsheet_as_csv()
    run_map.generate_map()
    run_map.generate_events_table()
    run_map.generate_eventometer()
    run_map.save_map()
    run_map.upload_to_ftp(html=True, jpg=True, gpx=True)
    run_map.open_blog_page()
