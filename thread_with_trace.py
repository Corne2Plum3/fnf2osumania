"""
Code from geeksforgeeks.org (edited)
Full link to the code: https://www.google.com/amp/s/www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/amp
"""

from crash_window import Crash_window
import sys
import traceback
import trace
import threading

class Thread_with_trace(threading.Thread):
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False
 
    def start(self):
        try:
            self.__run_backup = self.run
            self.run = self.__run         
            threading.Thread.start(self)
        except:  # to show an error message if something wrong happens here
            error_window = Crash_window(traceback.format_exc())
            error_window.openWindow()
 
    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
 
    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None
 
    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace
 
    def kill(self):
      self.killed = True