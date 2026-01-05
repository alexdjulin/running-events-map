from run_map import RunMap

if __name__ == '__main__':

    run_map = RunMap()
    run_map.load_csv_file()
    run_map.update_database()
    run_map.generate_map()
    run_map.generate_events_table()
    run_map.generate_eventometer()
    run_map.save_map()
    ftp_success = run_map.upload_to_ftp(html=True, jpg=True, gpx=True, force=False)
    
    if ftp_success:
        run_map.open_blog_page()
    else:
        print("Skipping blog page opening due to FTP upload failure.")

