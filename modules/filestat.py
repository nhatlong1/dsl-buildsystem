import os
import time
from typing import Dict, Any, Callable, Optional, Union
from src.protocols import InterpreterProtocol

class FileStat:
    """
    Wraps os.stat information for a file.

    Parameters
    ----------
    path : str
        The file path.

    Attributes
    ----------
    path : str
        The file path.
    stat : Optional[os.stat_result]
        The stat result.
    """
    def __init__(self, path: str):
        self.path = path
        try:
            self.stat: Optional[os.stat_result] = os.stat(path)
        except:
            self.stat = None

    @property
    def LASTMODIFIEDDATE(self) -> float:
        """
        Returns the last modified time.
        """
        if self.stat:
            return self.stat.st_mtime
        return 0.0

def get_module() -> Dict[str, Callable]:
    """
    Returns the module definition for FILESTAT.
    """
    return {
        'STAT': lambda args, interp: FileStat(str(interp.visit(args[0]))),
        # EXISTS is also in core, but maybe here too?
        'EXISTS': lambda args, interp: os.path.exists(str(interp.visit(args[0])))
    }
