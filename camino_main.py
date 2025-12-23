from camino_map import CaminoMap

if __name__ == '__main__':

    camino_map = CaminoMap()
    camino_map.load_csv_file()
    camino_map.update_database()
    camino_map.generate_map()
    camino_map.generate_table()
    camino_map.save_map()
    ftp_success = camino_map.upload_to_ftp(html=True, jpg=True, gpx=True, force=False)

    if ftp_success:
        camino_map.open_blog_page()
    else:
        print("Skipping blog page opening due to FTP upload failure.")

