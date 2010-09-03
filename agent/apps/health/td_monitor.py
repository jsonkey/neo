#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
#vim:sw=4:tw=4:ts=4:ai:expandtab
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: td_zombie.py$
##               $Revision: 1$
##
##  Last Update: $2009-3-25 19:57$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import time
import commands
import traceback
from signal import SIGTERM 

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))


def trace_back():
    return traceback.print_exc()


class Monitor:
    """monitor Process.
    """
    def __init__(self, timeout=6*60*60):
        self.timeout    =6*60*60
        self.men        =60
        self.mzombieName=("mencoder", "ffmpeg", "mplayer", "lame", "mp4creator", "yamdi", "codewav", "codevideo")
        self.kill_pid   =[]

    
    def time2sec(self, mytime) :
        #time must be 03:34:33.2 format
        m = mytime.split(':')
        if m[0].find("-") >= 0:
            tmp=m[0].split("-")
            m[0]=int(tmp[0])*24*60*60 + int(tmp[1])*60*60
        else:
            m[0]=int(m[0])*60*60
        return int((m[0]) + int(m[1]) * 60 + float(m[2]))
    
    def kill(self, pid):
        # Try killing the daemon process
        try:
            os.system("kill -9 %s"%pid)
        except OSError, err:
            print str(err)
            return False
    
    def filter_need(self, program=None):
        if not program:
            return False
        if re.search(r"[a-zA-Z]+", program).group().lower() in self.mzombieName:
            return True
        else:
            return False
        
    
    def filter_timeout(self, pid=None, timestr=None):
        if not timestr:
            return
        t = self.time2sec(timestr)
        if t >= self.timeout:
            return pid 
    
    def filter_men(self, pid=None, men=None):
        if not men:
            return
        if float(men) >= self.men:
            return pid 
    
    def filter_zombie(self, pid=None, ppid=None):
        if not ppid:
            return
        if int(ppid) == 1:
            return pid 
            
    def get_zombie(self):
        #28236 28746 mps      python          00:00:00  0.3
        #28746 28756 mps      python          00:00:00  0.2
        #18572 29604 mps      ps              00:00:00  0.0
        process_list = commands.getoutput("ps -eo ppid,pid,user,comm,time,%mem | grep -v grep").split("\n")
        process_list.pop(0)
        for i in process_list:
            i = i.strip().split()
            ppid, pid, user, program, timestr, men = i[0], i[1], i[2], i[3], i[4], i[5]
            if not self.filter_need(program):
                continue
            print "i   :", i
            # ok, need to filter.
            if self.filter_men(pid, men) or self.filter_timeout(pid, timestr) or self.filter_zombie(pid, ppid):
                self.kill_pid.append(pid)
        print self.kill_pid
        return True
                
    #checks the return value of an API function printing error information on
    #failure. usage checksc(funcname,sc)
    def checkcode(self, func, code):
        if code:
            print "%s ok: code=%s"%(func, code)
        else:
            print "%s fail: code=%s" % (func, code)
            raise Exception(func + code)
    
    def run(self):
        self.get_zombie()
        [self.kill(e) for e in self.kill_pid]
         

if __name__ == '__main__' :
    #monitor()
    monitor=Monitor()
    monitor.run()
