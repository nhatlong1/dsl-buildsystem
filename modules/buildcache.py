import os
import json
from typing import Dict, Any, Union, Callable, List
from src.protocols import InterpreterProtocol
from src.types import ASTNode

CACHE_FILE = ".buildcache"

class BuildCache:
    """
    Manages the build cache file.

    Attributes
    ----------
    cache : Dict[str, Any]
        The in-memory cache data.
    """
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
            except:
                pass

    def get_entry(self, path: str) -> Dict[str, Any]:
        """
        Retrieves a cache entry for a given path.

        Parameters
        ----------
        path : str
            The file path.

        Returns
        -------
        Dict[str, Any]
            The cache entry or empty dict.
        """
        return self.cache.get(path, {})

    def update_entry(self, path: str, timestamp: Union[int, float]) -> None:
        """
        Updates the cache entry for a given path.

        Parameters
        ----------
        path : str
            The file path.
        timestamp : Union[int, float]
            The modification timestamp.
        """
        self.cache[path] = {'LASTMODIFIEDDATE': timestamp}

    def save(self) -> None:
        """
        Saves the cache to the file.
        """
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

class CacheEntry:
    """
    Represents a single cache entry.

    Parameters
    ----------
    data : Dict[str, Any]
        The entry data.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    @property
    def LASTMODIFIEDDATE(self) -> Union[int, float]:
        """
        Returns the last modified date from the cache entry.
        """
        return self.data.get('LASTMODIFIEDDATE', 0)

_global_cache = BuildCache()

def update_cache(args: List[ASTNode], interp: InterpreterProtocol) -> None:
    """
    Updates the cache entry for a file with its current modified time.
    """
    path = str(interp.visit(args[0]))
    try:
        timestamp = os.path.getmtime(path)
        _global_cache.update_entry(path, timestamp)
    except Exception as e:
        print(f"Warning: Could not update cache for {path}: {e}")

def get_module() -> Dict[str, Callable]:
    """
    Returns the module definition for BUILDCACHE.
    """
    return {
        'CACHE': lambda args, interp: CacheEntry(_global_cache.get_entry(str(interp.visit(args[0])))),
        'WRITEBUILDCACHE': lambda args, interp: _global_cache.save(),
        'UPDATE': update_cache
    }
