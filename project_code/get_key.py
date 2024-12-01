import os

# Global variable to store the API key
_cached_api_key = None

def get_api_key():
    """
    Fetches and caches the API key.
    If the API key has already been loaded, returns the cached version.
    If not, reads it from the file called api_key in the project and caches it.
    """
    global _cached_api_key

    if _cached_api_key is not None:
        return _cached_api_key

    file_path = os.path.join(os.path.dirname(__file__), '..', 'api_key.txt')

    with open(file_path, 'r') as file:
        _cached_api_key = file.read()

    return _cached_api_key
