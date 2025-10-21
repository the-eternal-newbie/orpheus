import csv
import json
import time

from datetime import datetime
from utils.logger import RadLogger, SpinnerStyle

class FilesManager:
    filename = None
    root = './data/'
    csv_fieldnames = ['name', 'artist', 'album', 'release_date']

    def __init__(self, verbose=False, filename=None):
        self.log = RadLogger(
            name="SpotifyService", 
            show_timestamp=True,
            show_emoji=True,
            colored=True,
            log_file="spotify_service.log"
        )
        self.verbose = verbose
        self.filename = filename

    def __save_to_json(self, tracks):
        if self.filename is None:
            self.filename = f"spotify_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(self.root + self.filename, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)

        if self.verbose:
            self.log.info(f"Saved {len(tracks)} tracks to:")
            self.log.file_operation("write", self.filename, success=True)

        return self.filename

    def __save_to_csv(self, tracks):
        if self.filename is None:
            self.filename = f"spotify_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(self.root + self.filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(tracks)
        
        
        if self.verbose:
            self.log.info(f"Saved {len(tracks)} tracks to:")
            self.log.file_operation("write", self.filename, success=True)
        
        return self.filename
    
    def save_tracks(self, tracks, formats=('csv', 'json')):
        if self.verbose:
            self.log.section("Saving tracks to files")

        if not tracks:
            self.log.warning("No tracks to save!")
            return None, None

        self.log.spinner("Writing to disk...", SpinnerStyle.DOTS2)

        csv_file = self.__save_to_csv(tracks) if 'csv' in formats else None
        time.sleep(0.5)
        json_file = self.__save_to_json(tracks) if 'json' in formats else None
        
        if self.verbose:
            self.log.stop_spinner("Files saved successfully!", success=True)
            self.log.end_section()

        return csv_file, json_file