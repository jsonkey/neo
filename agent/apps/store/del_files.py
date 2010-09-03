#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: del_files.py$
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
import traceback

# version
VERSION="delete-0.2"

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))


import json

def trace_back():
    return traceback.print_exc()


class delFiles(object):
    """delete file, and then if deleted ok, so del null dirs, until not null.
    """
    def __init__(self):
        self.stdin  =sys.stdin
        self.stdout =sys.stdout
        self.stderr =sys.stderr
        self.job    =None
        self.src    =None
        self.timeout=10*60
        self.msg    =""
    
    def checkArgvs(self):
        """check argvs
        """
        try:
            self.job = json.read(self.stdin.readline().strip())
            self.stdout.write("NEED###%s%s"%(self.job, os.linesep))
            self.stdout.flush()
            self.src    =self.job["src"]
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
        
    def del_dir_by_null(self, path=None):
        try:
            os.removedirs(path)
        except:
            print traceback.print_exc()
        return True
    
    def del_files(self):
        if os.path.isfile(self.src):
            os.remove(self.src)
            self.del_dir_by_null(os.path.dirname(self.src))
        elif os.path.isdir(self.src):
            self.del_dir_by_null(self.src)
        return True

    def _run(self):
        """really to del.
        """
        self.checkArgvs()
        #
        try:
            self.del_files()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":"", "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
        except Exception, e:
            self.stdout.write("RESULT###%s%s"%(json.write({"result":403, "msg":str(e), "aux":{}, "v":VERSION}), os.linesep))
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
    delete=delFiles()
    delete.run()
