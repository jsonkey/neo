#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Cncodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: osinfo.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 19:57$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import time
import urllib
import statvfs
import commands
import traceback


import json
import td_osinfo

def trace_back():
    return traceback.print_exc()


#
class OSstatus(object):
    """result = report client status.
    """
    def __init__(self):
        self.stdin =sys.stdin
        self.stdout=sys.stdout
        self.stderr=sys.stderr
        self.job   =None
    
    def check_argvs(self):
        """check argvs
        """
        try:
            self.job = json.read(self.stdin.readline().strip())
            self.stdout.write("NEED###%s%s"%(self.job, os.linesep))
            self.stdout.flush()
        except:
            self.msg="check argument error. %s"%trace_back()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":400, "msg":self.msg, "aux":{}}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg) 
        #
        return True, "ok"
        
    def run(self):
        """really to do.
        """
        self.check_argvs()
        try:
            code, info=td_osinfo.OSstatus(self.job).run()
            if code:
                self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":"", "aux":info}), os.linesep))
                self.stdout.flush()
            else:
                self.stdout.write("RESULT###%s%s"%(json.write({"result":401, "msg":"", "aux":info}), os.linesep))
                self.stdout.flush()
        except Exception, e:
            self.stdout.write("RESULT###%s%s"%(json.write({"result":402, "msg":str(e), "aux":{}}), os.linesep))
            self.stdout.flush()
        return True
    
###############################################
#
# unittest
#
###############################################
import unittest
class clientTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_func(self):
        osinfo=OSstatus(2)
        self.assertEqual(osinfo.read_tcps("/tmp/%s"%time.time()), 0)
        os.system("echo '100'>/tmp/read_func")
        self.assertEqual(osinfo.read_tcps("/tmp/read_func"), 100)
        so.system("rm -fr /tmp/read_func")

    def test_cpu(self):
        """
        cpu
        """
        osinfo=OSstatus(2)
        print osinfo.get_cpu_usage()
        self.assertEqual(type(osinfo.get_cpu_usage()), float)
        return

    def test_mem(self):
        """
        mem
        """
        osinfo=OSstatus(2)
        self.assertEqual(type(osinfo.get_mem_usage()), float)
        return
    
    def test_load(self):
        """
        load
        """
        osinfo=OSstatus(2)
        self.assertEqual(type(osinfo.get_5m_load()), float)
        return

    def test_all(self):
        """
        load
        """
        osinfo=OSstatus()
        self.assertEqual(type(osinfo.get_os_info()), dict)
        return

if __name__=='__main__':
    #unittest.main()
    info=OSstatus()
    info.run()
