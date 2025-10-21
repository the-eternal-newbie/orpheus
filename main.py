from dotenv import load_dotenv
from services import Service
from utils.logger import RadLogger


load_dotenv()


def main():
    log = RadLogger(name="Main", show_timestamp=True, show_emoji=True, colored=True)

    try:
        log.clear_screen()
        log.create_ascii_art_from_file("logo")

        music_service = Service.load("spotify", verbose=True)
        music_service.execute()
    except Exception as e:
        log.error(f"Failed to load or execute the music service: {e}")


if __name__ == "__main__":
    main()
