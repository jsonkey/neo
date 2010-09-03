#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# File: netutil.py
# Date: 2010-09-01
# Author: tommy
#

"""network tools by short connection 
"""

import re
import time
import random
import urllib
import httplib
import traceback
import socket

# set timeout for socket
socket.setdefaulttimeout(30)


#
def client_get(server=None,url=None):
    """GET"""
    if server and url:
        pass
    else:
        return False, "client_get(%s, %s) argvs is unavailable!"%(server, url)
    # now we are safe !
    try:
        try:
            headers = {"Content-Type":"application/x-www-form-urlencoded", "Referer":"http://www.tudou.com", "User-Agent":"tudou MPS-Core client"}
            conn=httplib.HTTPConnection(server)
            conn.request("GET",url)
            resp=conn.getresponse()
            if int(resp.status) == 200:
                return True, resp.read()
            else:
                return False, "client_get(%s, %s) getresponse return %s %s"%(server, url, resp.status, resp.reason)
            #
        finally:
            if conn:
                conn.close()
    except Exception, e:
        return False, "client_get(%s, %s) Exception %s"%(server, url, e)
    #
    # return
    return False, "None"

def client_post(server=None, url=None, obj=None, proxy=None):
    if server and url and obj:
        pass
    else:
        return False, "client_post(%s, %s, %s) argvs is unavailable!"%(server, url, obj)
    if proxy:
        url="%s%s"%(server, url)
        if server.find(r"http://") < 0:
            url="http://%s"%(url)
        server=random.choice(proxy)
        if server.find(r"http://") < 0:
            server="http://%s"%server
        return urllib_client_post(server=server, url=url, obj=obj)
    else:
        return httplib_client_post(server=server, url=url, obj=obj)

def urllib_client_post(server=None, url=None, obj=None):
    headers = {"Content-Type":"application/x-www-form-urlencoded","Referer":"http://www.tudou.com", "User-Agent":"tudou MPS-Core client"}
    proxies = {'http':server}
    try:
        try:
            fd=None
            fd=urllib.urlopen(url=url, data=obj, proxies=proxies)
            return True, fd.read()
        except Exception, e:
            return False, "client_post(%s, %s, %s) Exception %s"%(server, url, obj, e)
    finally:
        if fd:
            fd.close()
        

#
def httplib_client_post(server=None, url=None, obj=None):
    """POST"""
    # OK, now we are safe !
    try:
        try:
            headers = {"Content-Type":"application/x-www-form-urlencoded","Referer":"http://www.tudou.com", "User-Agent":"tudou MPS-Core client"}
            conn=httplib.HTTPConnection(server)
            conn.request("POST", url, body=obj, headers=headers)
            resp=conn.getresponse()
            if int(resp.status) == 200:
                return True, resp.read()
            else:
                return False, "client_post(%s, %s, %s) getresponse return %s %s"%(server, url, obj, resp.status, resp.reason)
        finally:
            if conn:
                conn.close()
    except Exception, e:
        return False, "client_post(%s, %s, %s) Exception %s"%(server, url, obj, e)
    #
    # return
    return False, ""


###############################################
#
# unittest
#
###############################################
import unittest
class clientGETTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGET404(self):
        """
        uri is 404
        """
        self.assertFalse(client_get("www.tudou.com", None)[0])
        self.assertFalse(client_get("www.tudou.com", "/xyz")[0])
        return

    def testGET200(self):
        """
        uri is 200
        """
        code, req=client_get("www.tudou.com", "/")
        self.assertEqual(code, True)
        self.assertEqual(req[0:9]!="client_get", True)
        return

class clientPOSTTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testPOST404(self):
        """
        uri is 404
        """
        self.assertEqual(client_post("www.tudou.com", None, "test")[0],   False)
        self.assertEqual(client_post("www.tudou.com", "/", None)[0],      True)
        self.assertEqual(client_post("www.tudou.com", "/xyz", "test")[0], False)
        return

    def testPOST200(self):
        """
        uri is 200
        """
        code, req=client_post("www.tudou.com", "/", "test")
        self.assertEqual(code, True)
        self.assertEqual(req[0:9]!="client_get", True)
        return

#-----------------------------------------------
#
# main() like C language
#
#-----------------------------------------------
if __name__=='__test__':
    #
    unittest.main()

if __name__=="__main__":
    import json
    import urllib
    server="10.5.16.181:8080"
    url   ="/job_nextjob.do"
    istr={"clientPath":"/home/www/1/", "ip":"10.5.16.223", "clientType":"Core"}
    ss=json.write(istr)
    print "ss :", ss
    obj=urllib.urlencode({"param":"%s"%ss})
    print "obj :", obj
    print client_post(server, url, obj)

