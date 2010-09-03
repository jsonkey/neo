#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: td_queue.py$
##               $Revision: 1$
##
##  Last Update: $2010-3-3 11:26$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import time

def _put():
    pass


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
