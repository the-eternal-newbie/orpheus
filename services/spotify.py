import spotipy

from os import getenv
from spotipy.oauth2 import SpotifyOAuth
from utils import logger
from utils.files_manager import FilesManager

import time
from utils.logger import RadLogger, SpinnerStyle

class SpotifyService:
    def __init__(self, verbose=False, **kwargs):
        self.log = RadLogger(
            name="SpotifyService", 
            show_timestamp=True,
            show_emoji=True,
            colored=True,
            log_file="spotify_service.log"
        )
        
        self.client_id = kwargs.get("client_id", getenv("SPOTIFY_CLIENT_ID"))
        self.client_secret = kwargs.get("client_secret", getenv("SPOTIFY_CLIENT_SECRET"))
        self.redirect_uri = kwargs.get("redirect_uri", "http://127.0.0.1:8888/callback")

        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify client ID and secret must be set in environment variables.")
        
        auth_manager = SpotifyOAuth(
            scope="user-library-read",
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            open_browser=False,
            cache_path=".spotify_cache"
        )
        
        self.client = spotipy.Spotify(auth_manager=auth_manager)
        self.verbose = verbose
        self.kwargs = kwargs
        
        
        if self.verbose:
            self.log.success("Initialized SpotifyService")

    def __get_all_saved_tracks(self):
        tracks = []
        offset = 0
        limit = 50  # Maximum allowed by Spotify API
        total = None
        
        if (self.verbose):
            self.log.section("Fetching Spotify library")
        
        while True:
            try:
                # Fetch a batch of tracks
                results = self.client.current_user_saved_tracks(limit=limit, offset=offset)

                # On first iteration, get the total count
                if total is None:
                    total = results['total']
                    self.log.info(f"Total tracks in library: {total}")
                
                # Process each track in this batch
                for item in results['items']:
                    track = item['track']
                    
                    # Extract relevant information
                    track_info = {
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'release_date': track['album']['release_date'],
                    }
                    tracks.append(track_info)
                
                offset += limit
                self.log.progress_bar(
                    offset,
                    total,
                    prefix="Fetched",
                    suffix=f"{min(offset, total)} / {total} tracks"
                )
                

                if results['next'] is None:
                    break
            
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:  # Rate limit exceeded
                    retry_after = int(e.headers.get('Retry-After', 5))
                    self.log.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                else:
                    self.log.error(f"Spotify API error: {e}")
                    break
            except Exception as e:
                self.log.error(f"Unexpected error: {e}")
                break
        
        self.log.end_section()
        
        return tracks

    def execute(self):
        try:    
            self.log.section("Spotify Library Exporter")
            self.log.spinner("Authenticating with Spotify...", SpinnerStyle.MUSIC)            
            user = self.client.current_user()
            self.log.stop_spinner(f"Authenticated as: {user['display_name']}", success=True)
            
            start_time = time.time()
            tracks = self.__get_all_saved_tracks()
            elapsed_time = time.time() - start_time
            
            if tracks:
                self.log.success(f"\nSuccessfully fetched {len(tracks)} tracks in {elapsed_time:.1f} seconds")
                
                files_manager = FilesManager(verbose=self.verbose)
                csv_file, json_file = files_manager.save_tracks(tracks)
                
            else:
                self.log.warning("No tracks found in your library.")
                
        except Exception as e:
            self.log.stop_spinner(f"Error: {e}", success=False)
            self.log.info("\nIf you're seeing authentication issues:")
            self.log.info("1. The script will provide a URL - copy it")
            self.log.info("2. Open it in your Windows browser")
            self.log.info("3. After authorizing, copy the ENTIRE redirect URL")
            self.log.info("4. Paste it back in this terminal")