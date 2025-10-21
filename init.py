import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from os import getenv
import json
import csv
from datetime import datetime
import time

load_dotenv()

def get_all_saved_tracks(spotify):
    tracks = []
    offset = 0
    limit = 50  # Maximum allowed by Spotify API
    total = None
    
    print("Starting to fetch Spotify library...")
    
    while True:
        try:
            # Fetch a batch of tracks
            results = spotify.current_user_saved_tracks(limit=limit, offset=offset)
            
            # On first iteration, get the total count
            if total is None:
                total = results['total']
                print(f"Total tracks in library: {total}")
            
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
            print(f"Fetched {min(offset, total)} / {total} tracks ({(min(offset, total) / total * 100):.1f}%)")
            

            if results['next'] is None:
                break
            
            time.sleep(0.1)
            
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:  # Rate limit exceeded
                retry_after = int(e.headers.get('Retry-After', 5))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                print(f"Spotify API error: {e}")
                break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return tracks

def save_to_json(tracks, filename=None):
    if filename is None:
        filename = f"spotify_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(tracks)} tracks to {filename}")
    return filename

def save_to_csv(tracks, filename=None):
    if filename is None:
        filename = f"spotify_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if not tracks:
        print("No tracks to save!")
        return
    
    # Define the CSV columns
    fieldnames = [
        'name', 'artist', 'album', 'release_date'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(tracks)
    
    print(f"Saved {len(tracks)} tracks to {filename}")
    return filename

def print_library_stats(tracks):
    """Print some interesting statistics about the library."""
    if not tracks:
        return
    
    print("\n" + "="*50)
    print("LIBRARY STATISTICS")
    print("="*50)
    
    # Basic stats
    print(f"Total tracks: {len(tracks)}")
    
    # Find unique artists and albums
    unique_artists = set(track['artist'] for track in tracks)
    unique_albums = set(track['album'] for track in tracks)
    print(f"Unique artists: {len(unique_artists)}")
    print(f"Unique albums: {len(unique_albums)}")

def main():
    client_id = getenv("SPOTIFY_CLIENT_ID")
    client_secret = getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID and secret must be set in environment variables.")
    
    # Create auth manager with headless-friendly settings
    auth_manager = SpotifyOAuth(
        scope="user-library-read",
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        open_browser=False,
        cache_path=".spotify_cache"
    )
    
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        
        user = spotify.current_user()
        print(f"Authenticated as: {user['display_name']}")
        print("-" * 50)
        
        start_time = time.time()
        tracks = get_all_saved_tracks(spotify)
        elapsed_time = time.time() - start_time
        
        if tracks:
            print(f"\nSuccessfully fetched {len(tracks)} tracks in {elapsed_time:.1f} seconds")
            
            # Save to both formats
            print("\nSaving to files...")
            json_file = save_to_json(tracks)
            csv_file = save_to_csv(tracks)
            
            # Print statistics
            print_library_stats(tracks)
            
            print(f"\nYour library has been exported to:")
            print(f"  - JSON: {json_file}")
            print(f"  - CSV: {csv_file}")
            
        else:
            print("No tracks found in your library.")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nIf you're seeing authentication issues:")
        print("1. The script will provide a URL - copy it")
        print("2. Open it in your Windows browser")
        print("3. After authorizing, copy the ENTIRE redirect URL")
        print("4. Paste it back in this terminal")

if __name__ == "__main__":
    main()