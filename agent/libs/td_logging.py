#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: td_logging.py
# Date: 2010-09-01
# Author: tommy

import os
import re
import logging
import logging.handlers
import time




class mini_logging:
    """mini logging's class
    """
    def __init__(self, logname):
        """logging
        """
        self.filename=logname 
        #logging.basicConfig(\
        #                    level = logging.DEBUG,\
        #                    format  = '[%(asctime)s] [%(levelname)-5s] %(message)s',\
        #                    datefmt = '%Y-%m-%d %H:%M:%S',\
        #                    filename= self.filename,\
        #                    filemode= 'a',\
        #                    )
        # set another log handler for the console.
        #console = logging.StreamHandler()
        #console.setLevel(logging.DEBUG)
        # set a format whitch is simpler for console use
        #formatter = logging.Formatter('[%(asctime)s] [%(levelname)-5s] %(message)s', '%Y-%m-%d %H:%M:%S')
        # tell the handler to use this format
        #console.setFormatter(formatter)
        #logging.getLogger('').addHandler(console)
        #
        # supports rotation of disk log files at certain timed intervals
        #TimedRotating=logging.handlers.TimedRotatingFileHandler(self.filename, "midnight", 1, 7)
        # add the handler to the root logger
        # note that you must remove it before the function end.
        #logging.getLogger('').addHandler(TimedRotating)
        logging.getLogger().setLevel(logging.DEBUG)
        #
        #logfile = logging.handlers.TimedRotatingFileHandler(self.filename , 'H', 12, backupCount=14)
        logfile = logging.handlers.RotatingFileHandler(self.filename, maxBytes=10*1024*1024, backupCount=30)
        logfile.setLevel(logging.DEBUG)
        #logfile.setFormatter(logging.Formatter('%(asctime) s %(levelname)-8s %(module)s: %(message)s'))
        #formatter = logging.Formatter('[%(asctime)s] [%(levelname)-5s] %(message)s')
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)-5s] [%(process)d] %(message)s', '%Y-%m-%d %H:%M:%S')
        logfile.setFormatter(formatter)
        logging.getLogger().addHandler(logfile)
        #
        self.td_error_logging=logging.error
        self.td_warning_logging=logging.warning
        self.td_debug_logging=logging.debug
        self.td_info_logging=logging.info
        
        
    def GenLog(self, logType, logContent):
        """set the basiconfig for the log. It's a file log."""
        #logContent= "[%s] %s"%(time.strftime("%Y-%m-%d %X", time.localtime(time.time())), _logContent)
        # parse the log type
        if logType == "ERROR":
            self.td_error_logging(logContent)
        elif logType == "WARNING":
            self.td_warning_logging(logContent)
        elif logType == "DEBUG":
            self.td_debug_logging(logContent)
        else:
            self.td_info_logging(logContent)
        #
        return True



#
if __name__ == '__main__':
    log_dirs  =os.path.join(re.sub(r"\/\w+$", "/", os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))), "logs/", "access")
    td_log=mini_logging(log_dirs)
    td_log.GenLog("INFO", "This is a INFO info")
    time.sleep(2)
    td_log.GenLog("DEBUG", "This is a DEBUG info")
    time.sleep(2)
    td_log.GenLog("ERROR", "This is a ERROR info")
    time.sleep(2)
    td_log.GenLog("WARNING", "This is a WARNING info")
