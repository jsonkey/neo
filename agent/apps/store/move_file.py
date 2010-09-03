#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: move_file.py$
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
import shutil
import traceback

# version
VERSION="move-0.2"

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))


import json

def trace_back():
    return traceback.print_exc()


class moveFile(object):
    """move file.
    """
    def __init__(self):
        self.stdin  =sys.stdin
        self.stdout =sys.stdout
        self.stderr =sys.stderr
        self.job    =None
        self.src    =None
        self.dst    =None
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
            self.dst    =self.job["dest"]
            self.timeout=self.job["timeout"]
        except:
            self.msg="check argument error. %s"%trace_back()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":400, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg) 
        # outfile is exists.
        if os.path.exists(self.dst) and not os.path.exists(self.src): 
            self.msg="dst(%s) has exists."%self.dst
            self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        # check exists.
        if not os.path.exists(self.src):
            self.msg="%s is not exists."%self.src
            self.stdout.write("RESULT###%s%s"%(json.write({"result":404, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        if not os.access(self.src, os.R_OK):
            self.msg="%s is not read authority."%self.src
            self.stdout.write("RESULT###%s%s"%(json.write({"result":403, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        # check output file dirs.
        if not os.path.exists(os.path.dirname(self.dst)):
            try:
                os.makedirs(os.path.dirname(self.dst))
            except:
                self.msg="os.makedirs(%s) Exception. %s"%(os.path.dirname(self.dst), trace_back())
                self.stdout.write("RESULT###%s%s"%(json.write({"result":407, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
                self.stdout.flush()
                raise Exception(self.msg)
        # outfile is W_OK.
        if not os.access(os.path.dirname(self.dst), os.W_OK):
            self.msg="%s is not write authority."%os.path.dirname(self.dst)
            self.stdout.write("RESULT###%s%s"%(json.write({"result":403, "msg":self.msg, "aux":{}, "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        # return
        return True
        
    def make_dirs(self):
        if not os.path.exists(os.path.dirname(self.dst)):
            os.makedirs(os.path.dirname(self.dst))
        return True
    
    def move_file(self):
        self.make_dirs()
        shutil.move(self.src, self.dst)
    
    def _run(self):
        """really to del.
        """
        self.checkArgvs()
        #
        try:
            self.move_file()
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
    move=moveFile()
    move.run()
