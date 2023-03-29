import time
from datetime import datetime
from threading import Thread

from blinker import Signal


class _TimeAdapter(Thread):
    tick = Signal("tick")
    def __init__(self):
        super().__init__()
        self._tick = 0
        
    @staticmethod
    def user_readable(timestamp: int):
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%m/%d/%Y, %H:%M:%S")
    
    def run(self) -> None:
        
        while True:
            self._tick = int(time.mktime(datetime.utcnow().timetuple()))
            _TimeAdapter.tick.send(self._tick)
            time.sleep(1)
        
    
TimeAdapter = _TimeAdapter()
TimeAdapter.daemon = True
TimeAdapter.start()
