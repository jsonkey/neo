#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: testing_osinfo.py$
##               $Revision: 1$
##
##  Last Update: $2009-3-25 19:57$
##
##--------------------------------------------------------------------------
##

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
    unittest.main()
