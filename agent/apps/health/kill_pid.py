#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: kill_pid.py$
##               $Revision: 1$
##
##  Last Update: $DateTue Feb 24 15:51:10 CST 2010$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import time
import signal
import traceback

# version
VERSION="kill-0.2"

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))


import json

def trace_back():
    return traceback.print_exc()


class killPid(object):
    """kill by pid.
    """
    def __init__(self):
        self.stdin  =sys.stdin
        self.stdout =sys.stdout
        self.stderr =sys.stderr
        self.job    =None
        self.pid    =None
        self.timeout=10*60
        self.msg    =""
    
    def checkArgvs(self):
        """check argvs
        """
        try:
            # {"pid":1005, "timeout":60}
            self.job = json.read(self.stdin.readline().strip())
            self.stdout.write("NEED###%s%s"%(self.job, os.linesep))
            self.stdout.flush()
            self.pid    =self.job["pid"]
            self.timeout=self.job["timeout"]
        except:
            self.msg="check argument error. %s"%trace_back()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":400, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg) 
        #
        #if not os.path.exists(self.src):
        #    self.msg="%s is not exists."%self.src
        #    self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":self.msg, "aux":{}}), os.linesep))
        #    self.stdout.flush()
        #    raise Exception(self.msg) 
        #
        return True, "ok"
        
    def send_signal(self, sig):
        """Send a signal to the process
        """
        os.kill(self.pid, sig)
         
    def terminate(self):
        """Terminate the process with SIGTERM
        """
        self.send_signal(signal.SIGTERM)
        
    def kill(self):
        """Kill the process with SIGKILL
        """
        self.send_signal(signal.SIGKILL)

    def _run(self):
        """really to del.
        """
        self.checkArgvs()
        #
        try:
            self.kill()
            self.terminate()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":"", "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
        except Exception, e:
            self.stdout.write("RESULT###%s%s"%(json.write({"result":401, "msg":str(e), "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
        return True
    
    def run(self):
        try:
            return self._run()
        except:
            pass

#-----------------------------------------
#main()
#-----------------------------------------
if  __name__ == '__main__':
    pid=killPid()
    pid.run()
