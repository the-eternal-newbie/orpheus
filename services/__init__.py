import importlib
from functools import lru_cache

class Service:
    SERVICES = {
        "spotify": {"services.spotify", "SpotifyService"},
        "apple_music": {"services.apple_music", "AppleMusicService"},
        "youtube_music": {"services.youtube_music", "YouTubeMusicService"},
    }
    
    @classmethod
    @lru_cache(maxsize=None)
    def load(cls, service_name, **config):
        if service_name not in cls.SERVICES:
            raise ValueError(f"Service '{service_name}' is not recognized.")
        
        module_path, class_name = cls.SERVICES[service_name]
        module = importlib.import_module(module_path)
        service_class = getattr(module, class_name)

        return service_class(**config)