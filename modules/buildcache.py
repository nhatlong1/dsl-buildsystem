import os
import json

CACHE_FILE = ".buildcache"

class BuildCache:
    def __init__(self):
        self.cache = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
            except:
                pass

    def get_entry(self, path):
        return self.cache.get(path, {})

    def update_entry(self, path, timestamp):
        self.cache[path] = {'LASTMODIFIEDDATE': timestamp}

    def save(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

class CacheEntry:
    def __init__(self, data):
        self.data = data

    @property
    def LASTMODIFIEDDATE(self):
        return self.data.get('LASTMODIFIEDDATE', 0)

_global_cache = BuildCache()

def get_module():
    return {
        'CACHE': lambda args, interp: CacheEntry(_global_cache.get_entry(interp.visit(args[0]))),
        'WRITEBUILDCACHE': lambda args, interp: _global_cache.save()
    }
