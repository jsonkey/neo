#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) Tudou Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: osinfo.py$
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
import socket
import urllib
import statvfs
import commands
import traceback

socket.setdefaulttimeout(20)

import json

def trace_back():
    return traceback.print_exc()

upload_max_idel=5*60

# globa re
re_meminfo_parser = re.compile(r'^(?P<key>\S*):\s*(?P<value>\d*)\s*kB')

#
class OSstatus(object):
    """result = report client status.
    """
    def __init__(self, job=None):
        self.job         =job
        self.storage_root=None
        self.SYNC        =None
        self.msg         =""
        self.sleep       =2
    
    def checkArgvs(self):
        """check argvs
        """
        try:
            self.storage_root=self.job["storage_root"]
            self.SYNC        =self.job["SYNC"]
            self.timeout     =self.job["timeout"]
        except:
            self.msg="check argument error. %s"%trace_back()
            raise Exception(self.msg) 
        #
        return True, "ok"
        
    def _get_mem_usage(self):
        """get mem used by percent
        self.result = falot
        """
        return 100 - int(str(100.0*[int(e.split()[2])/float(e.split()[3]) for e in commands.getoutput("free -m ").split(os.linesep) if e.find(r"buffers")>=0 and e.find(r"cache:") >= 0][0]).split(".")[0])

    def get_mem_usage(self):
        """safe to call _get_memused()
        self.result = falot
        """
        try:
            return self._get_mem_usage()
        except Exception, e:
            print "_get_mem_usage(self) Exception, %s"%e
            return 0

    def get_5m_load(self):
        """get 5 mines avg load
        self.result = float
        """
        try:
            return int("%.0f"%((os.getloadavg())[2]))
        except Exception, e:
            print "_get_5m_load(self) Exception, %s"%e
            return 0
    
    def _read_cpu_usage(self):
        """Read the current system cpu usage from /proc/stat."""
        l=[]
        try:
            fd = open("/proc/stat", 'r')
            lines = fd.readlines()
        finally:
            if fd:
                fd.close()
        for line in lines:
            l = line.split()
            if len(l) < 5:
                continue
            if l[0].startswith('cpu'):
                return l
        return []

    def get_cpu_usage(self):
        """get cpu avg used by percent
        """
        cpustr=self._read_cpu_usage()
        if not cpustr:
            return 0
        #cpu usage=[(user_2 +sys_2+nice_2) - (user_1 + sys_1+nice_1)]/(total_2 - total_1)*100
        usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])
        usn1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])
        #usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[4])
        time.sleep(self.sleep)
        cpustr=self._read_cpu_usage()
        if not cpustr:
            return 0
        usni2=long(cpustr[1])+long(cpustr[2])+float(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])
        usn2=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])
        cpuper=(usn2-usn1)/(usni2-usni1)
        return int("%.0f"%(100*cpuper))
        
    def touch_file(self, path=None):
        #STORAGE_ROOT={"/tudou/0":500, "/tudou/1":500}
        G=lambda path: os.statvfs(path)[statvfs.F_BAVAIL]*os.statvfs(path)[statvfs.F_BSIZE]/(1024*1024*1024)
        try:
            tmp=os.path.join(path, "test.txt")
            fd=open(tmp, "w")
            fd.write("testing.")
            fd.close()
            os.remove(tmp)
            return G(path)
        except:
            return -1
        return -1 
    
    def _check_storge(self):
        return dict([(e, self.touch_file(e)) for e in self.storage_root])
    
    def check_storge(self):
        self.storage_root=self._check_storge()
        return True
    
    def check_disk(self):
        keys=self.storage_root.keys()
        keys.sort()
        return [self.storage_root[e] for e in keys]
    
    def check_lighttpd(self):
        import httplib
        import socket
        # set timeout for socket
        socket.setdefaulttimeout(20)
        # now we are safe !
        try:
            try:
                conn=None
                headers = {"Content-Type":"application/x-www-form-urlencoded", "Referer":"http://www.tudou.com", "User-Agent":"check_http/python osinfo.py"}
                if self.SYNC:
                    url="localhost:80"
                else:
                    url="localhost:8080"
                conn=httplib.HTTPConnection(url)
                conn.request("GET","/index.html", headers=headers)
                resp=conn.getresponse()
                if int(resp.status) == 200:
                    return 1
                else:
                    print "client_get(%s, /index.html) getresponse return %s %s"%(url, resp.status, resp.reason)
                    return 0
            except:
                print trace_back()
                return 0
        finally:
            if conn:
                conn.close()
        return 0

    def check_if_live(self, rep=None):
        if not rep:
            return -1
        # 1273562742,200,1
        timestamp, tcps, all=rep.split(",")
        if int(time.time()) - int(timestamp) >= upload_max_idel:
            return -1
        else:
            return int(tcps)

    def read_tcps(self, path=None):
        fd=None
        try:
            try:
                fd=open(path, "r")
                return self.check_if_live(fd.read().strip())
            except:
                print trace_back()
                return 0
        finally:
            if fd:
                fd.close()

    def webup_url(self, url=None):
        fd=None
        try:
            try:
                fd=urllib.urlopen(url)
                data=json.read(fd.read())
                if isinstance(data, list):
                    return len(data)
                else:
                    print "webuploading data is not list."
                    return -1
            except:
                print trace_back()
                return -1
        finally:
            if fd:
                fd.close()
    
    def get_webup(self):
        return self.webup_url("http://127.0.0.1:8081/status")
    
    def get_itudouup(self):
        return self.read_tcps("/tmp/itudouuploading")

    def get_os_info(self):
        """overide all functions.
        """
        return {"cpu"         :self.get_cpu_usage(),
                "freemem"     :self.get_mem_usage(),
                "load"        :self.get_5m_load(),
                "webup"       :self.get_webup(),
                "itudouup"    :self.get_itudouup(),
                "lighttpd"    :self.check_lighttpd(),
                "disk"        :self.check_storge() and self.check_disk() or [],
                "storage_root":self.storage_root,
                }
    
    def run(self):
        """really to do.
        """
        self.checkArgvs()
        #
        try:
            return True, self.get_os_info()
        except:
            print False, trace_back()
    

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
    info=OSstatus({'tmp': '/home/mps/Client/__TMP/-100', 'core': 1, 'storage_root': {'/tudou/2': 0, '/tudou/1': 0, '/tudou/0': 0}, 'dplayer_server': {'/tudou': 'http://origin-player0001.tudou.com/'}, 'SYNC': False, 'DEV': True, 'timeout': 60})
    print info.run()
