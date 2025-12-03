import os
import time

class FileStat:
    def __init__(self, path):
        self.path = path
        try:
            self.stat = os.stat(path)
        except:
            self.stat = None

    @property
    def LASTMODIFIEDDATE(self):
        if self.stat:
            return self.stat.st_mtime
        return 0

def get_module():
    return {
        'STAT': lambda args, interp: FileStat(interp.visit(args[0])),
        # EXISTS is also in core, but maybe here too?
        'EXISTS': lambda args, interp: os.path.exists(interp.visit(args[0]))
    }
