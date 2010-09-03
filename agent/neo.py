#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: neo.py$
##               $Revision: 1$
##
##  Last Update: $2010-3-3 11:24$
##
##--------------------------------------------------------------------------
##

#---------------------------------------------------------------------------
#
# tmp_queue=Queue(0)
#
# log_queue=Queue(0)
#
#---------------------------------------------------------------------------

import os
import re
import sys
import stat
import time
import copy
import shlex
import random
import signal
import urllib
import traceback
import subprocess

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))
#

def append_path(path=None):
    """append to sys.path list
    if this path is exists in sys.path's list, we do nothing!
    else, append to sys.path
    """
    if not os.path.exists(path):
        raise "%s is not exists!"%path
    if path in sys.path:
        print "%s has exists! in sys.path, so we do nothing."%path
        return True
    else:
        sys.path.append(path)
        return True
    return

[append_path(e) for e in (os.path.join(curpath, "lib"),\
                          os.path.join(curpath, "config"),\
                          os.path.join(curpath, "app"))]


import setting
import json
import daemon
import netutil
import uuid
import processing
from processing import Queue, Lock
import processing, logging
processing.enableLogging(level=logging.INFO)


# logging
import td_logging
if not os.path.exists(os.path.join(curpath, "logs/")):
    os.makedirs(os.path.join(curpath, "logs/"))
log=td_logging.mini_logging(os.path.join(curpath, "logs/", "access"))
GenLog=log.GenLog

#
tmp_queue=Queue(0)
log_queue=Queue(0)

# cpuCount
cpuCount = int(processing.cpuCount())

# reload
_mtimes = {}
_win = True and (sys.platform == "win32") or False

#
G_process={}

# min_space_left_in_giga
min_space_left_in_giga=setting.min_space_left_in_giga
# storage root
STORAGE_ROOT=setting.STORAGE_ROOT #{"/tudou/0":500, "/tudou/1":500}
dplayer_SERVER=setting.dplayer_SERVER

#
def check_disk(STORAGE_ROOT=None):
    keys=STORAGE_ROOT.keys()
    keys.sort()
    return [STORAGE_ROOT[e] for e in keys]
#
#
Health={'load': '0.00', 'server': 1, 'disk':check_disk(STORAGE_ROOT), 'cpu':0,'freemem':0}
VISIT_TIME=setting.VISIT_TIME
N=0 #report times n += 1

#
process_lock  =Lock()

import logging

log = logging.getLogger("gearman")


# tools
def trace_back():
    return traceback.print_exc()


#---------------------------------------------------------------------------
#
# monitor
#
#---------------------------------------------------------------------------
class monitor(processing.Process):
    """monitor all.
    """
    def __init__(self):
        processing.Process.__init__(self)
    
    def run(self):
        global log_queue
        while True:
            try:
                code_changed()
                monitor=setting.App["monitor"]
                os.system(monitor)
            except Exception, e:
                _put(log_queue, "process monitor Exception:%s"%str(e))
            time.sleep(random.randint(10, 60))


############################################################################
#
# process produce
#
############################################################################
def new_one_process(m_class, m_name):
    """process produce.
    """
    global G_process
    if m_class and m_name:
        pass
    else:
        msg="new_one_process(m_class, m_name) argv, m_class or m_name is None."
        GenLog("DEBUG", msg)
        return False
    # OK,
    t=m_class()
    t.setName(m_name)
    t.setDaemon(1)
    t.start()
    try:
        try:
            process_lock.acquire()
            if G_process.has_key(m_name):
                if G_process[m_name]:
                    G_process[m_name].join(3)
                    del G_process[m_name]
            G_process[m_name]=t
        finally:
            process_lock.release()
    except:
        GenLog("ERROR", "new_one_process(m_class, %s) Exception, %s"%(m_name, trace_back()))
        return False
    # return
    return True

############################################################################
#
# control
#
############################################################################
def control():
    """
    """
    # init env
    clear_env()
    # do
    # loop check which thrad die, and than to start new thread, OK
    new_one_process(log, "log_process")
    new_one_process(monitor, "monitor_process")
    cmdStatus={}
    while True:
        print "#######"*20
        print "cmdStatus :", cmdStatus
        print "#######"*20
        Communication(cmdStatus).run()
        print "activeChildren :", processing.activeChildren()
        [e.join(0.1) for e in processing.activeChildren()]
        for p in ("log_process", "monitor_process"):
            if not G_process[p].isAlive():
                GenLog("ERROR", "%s exit."%p)
                sys.exit()


################################################################################
#
#
# main
#
################################################################################
#if __name__ == "__main__":
#    control()



class MyDaemon(daemon.Daemon):
    def run(self):
        try:
            control()
        except Exception, e:
            msg="test_control() Exception, %s"%e
            GenLog("DEBUG", msg)
            return False
        # return
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Unknown command"
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
    if sys.argv[1] == "-d":
        control()
    if len(sys.argv) == 2:
        daemon = MyDaemon(daemon_pid)
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
