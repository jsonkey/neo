#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Cncodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: app_setting.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 12:20$
##
##--------------------------------------------------------------------------
##

import os
import setting

# curpath
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))

def get_storage_left(storage_root=None):
    import os
    import statvfs
    #STORAGE_ROOT={"/tudou/0":500, "/tudou/1":500}
    G=lambda path: os.statvfs(path)[statvfs.F_BAVAIL]*os.statvfs(path)[statvfs.F_BSIZE]/(1024*1024*1024)
    return dict([(e, G(e)) for e in storage_root])
    

app_dir=re.sub(r'\/\w+$', '', curpath)

# proxy
PROXY=setting.PROXY
# server info
HOSTNAME=setting.HOSTNAME
PORT    =setting.PORT
BASEURI_NEWJOB = setting.BASEURI_NEWJOB    # for main
# version
version=setting.version
# sleep n , for post to server
VISIT_TIME=5              # vist server by time.
TIMEOUT=24*60*60          # when report results error, so keep tasks in client time.
MAX_PROCESS=200           # MAX process
LIMIT_CPU  =("encode",)   # limit cpu used.
min_space_left_in_giga=setting.min_space_left_in_giga # G
dplayer_STORAGE_ROOT=setting.dplayer_STORAGE_ROOT # dplayer storage root path by G.
STORAGE_ROOT = get_storage_left(dplayer_STORAGE_ROOT)
#
App={"ls":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "ls", "listDir.py")),\
        "analyze_src":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "encoder", "encoder", "check_type.py")),\
        "delete":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "store", "del_files.py")),\
        "move":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "store", "move_file.py")),\
        "download":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "store", "add_files.py")),\
        "health":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "health", "osinfo.py")),\
        "kill":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "health", "kill_pid.py")),\
        "monitor":"/usr/bin/python %s"%(os.path.join(app_dir, "app", "health", "td_monitor.py")),\
        }
