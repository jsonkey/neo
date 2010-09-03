#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Cncodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: setting.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 12:20$
##
##--------------------------------------------------------------------------
##

#DEV=True
DEV=False

#
if DEV: # testing env
    # proxy
    PROXY=None
    # server info
    HOSTNAME="localhost"
    PORT    ="8080"
    BASEURI_NEWJOB = "/mps/InspectSyncerServlet?hostname=%s"%(socket.gethostname()) # for main
    # version
    versions="0.1"
    min_space_left_in_giga=50 # G
    STORAGE_ROOT=[
            "/data/0",\
            "/data/1",\
            "/data/2",\
            "/data/3",\
            "/data/4",\
            "/data/5",\
            "/data/6",\
            "/data/7",\
            "/data/8",\
            "/data/9",\
            ] # dplayer storage root mount point.
else: # on line
    # proxy
    PROXY=["10.24.26.201:3128", "10.24.26.202:3128"]
    # server info
    HOSTNAME="ulpc.cncodec.com"
    PORT    ="80"
    BASEURI_NEWJOB = "/mps3/InspectSyncerServlet?hostname=%s"%(socket.gethostname()) # for main
    # version
    versions="0.1"
    min_space_left_in_giga=50 # G
    STORAGE_ROOT=[
            "/data/0",\
            "/data/1",\
            "/data/2",\
            "/data/3",\
            "/data/4",\
            "/data/5",\
            "/data/6",\
            "/data/7",\
            "/data/8",\
            "/data/9",\
            ] # dplayer storage root mount point.
