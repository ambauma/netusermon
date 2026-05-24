import subprocess
import threading

# Simple in-memory cache for UID to username mappings
_uid_cache = {}
_cache_lock = threading.Lock()

def get_username_from_uid(uid):
    """
    Returns the username associated with a UID.
    Uses an in-memory cache to minimize subprocess overhead.
    """
    with _cache_lock:
        if uid in _uid_cache:
            return _uid_cache[uid]

    try:
        # Use id command to get username from UID
        result = subprocess.run(['id', '-nu', str(uid)], capture_output=True, text=True, check=True)
        username = result.stdout.strip()
        
        with _cache_lock:
            _uid_cache[uid] = username
            
        return username
    except subprocess.CalledProcessError:
        return "unknown"
