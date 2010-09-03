#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCode Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: add_file.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 12:26$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import time
import random
import urllib
import socket
import traceback
import subprocess

import json
import td_shell

# set timeout for socket
socket.setdefaulttimeout(30)

# version
VERSION="download-0.2"

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))

def trace_back():
    return traceback.print_exc()


class addFile(td_shell.subwork):
    """add file, download remote url to host disk.
    """
    def __init__(self):
        td_shell.subwork.__init__(self)
        self.stdin  =sys.stdin
        self.stdout =sys.stdout
        self.stderr =sys.stderr
        self.outcome  =None
        self.job      =None
        self.storage_root=None
        self.www_root =None
        self.ip       =None
        self.cmd      =None
        self.src      =None
        self.dest_path=None
        self.check_url=None
        self.dst      =None
        self.tmp      =None
        self.cwd      =curpath
        self.md5      =None
        self.proxy    =None
        self.thread   =5
        self.timeout  =10*60
        self.time_tag =1
        self.speed    =10 # default 10s
        self.www_root =None
        self.msg      =""
        
    def checkArgvs(self):
        """check argvs
        """
        try:
            #{
            #"src":"http://xxxx",
            #"dest_path":"/home/tudou/0/a/b/c.flv",
            #"md5":"21345",
            #"proxy":"1.2.3.4:7080",
            #"threads":5
            #}
            self.job = json.read(self.stdin.readline().strip())
            self.stdout.write("NEED###%s%s"%(self.job, os.linesep))
            self.stdout.flush()
            self.src      =self.job["src"]
            self.storage_root=self.set_storage_root()
            self.dest_path=self.set_dest_path()
            self.www_root =self.set_www_root()
            self.ip       =self.set_ip()
            self.dst      =self.set_dst()
            self.tmp      =self.job["tmp"]
            self.md5      =self.job["md5"]
            if self.job.has_key("proxy"):
                self.proxy=self.job["proxy"]
            if self.job.has_key("thread"):
                self.thread=self.job["thread"] or self.thread
            if self.job.has_key("check_url"):
                self.check_url=self.job["check_url"]
            self.timeout=self.job["timeout"]
            self.outcome=os.path.join(self.tmp, "speeds.txt")
        except Exception, e:
            self.msg="check argument error. %s"%e
            self.stdout.write("RESULT###%s%s"%(json.write({"result":400, "msg":self.msg, "aux":self.get_aux_by_null(), "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg) 
        # check output file.
        if not os.path.exists(os.path.dirname(self.dst)):
            try:
                os.makedirs(os.path.dirname(self.dst))
            except:
                self.msg="os.makedirs(%s) Exception. %s"%(os.path.dirname(self.dst), trace_back())
                self.stdout.write("RESULT###%s%s"%(json.write({"result":407, "msg":self.msg, "aux":self.get_aux_by_null(), "v":VERSION}), os.linesep))
                self.stdout.flush()
                raise Exception(self.msg)
        # outfile is W_OK.
        if not os.access(os.path.dirname(self.dst), os.W_OK):
            self.msg="%s is not write authority."%os.path.dirname(self.dst)
            self.stdout.write("RESULT###%s%s"%(json.write({"result":403, "msg":self.msg, "aux":self.get_aux_by_null(), "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        # return
        return True
    
    def set_dest_path(self):
        if self.job["dest_path"][0] == "/":
            return self.job["dest_path"][1:]
        else:
            return self.job["dest_path"]
    
    def set_storage_root(self):
        return dict([(e, self.job["storage_root"][e]) for e in self.job["storage_root"] if int(self.job["storage_root"][e]) != -1])
    
    def set_www_root(self):
        import random
        return random.choice(self.storage_root.keys())
    
    def set_ip(self):
        return self.job["dplayer_server"][self.www_root]
    
    def set_dst(self):
        return os.path.join(self.www_root, self.dest_path)
    
    def get_base_url(self):
        return self.dest_path
    
    def get_full_url(self):
        if self.ip[-1] != "/":
            self.ip="%s/"%self.ip
        return "%s%s"%(self.ip, self.get_base_url())
        
    def check_md5(self, path=None, md5=None):
        if not path or not md5:
            raise Exception("check_md5() path or md5 is None.")
        if self.get_md5sum(path) == md5:
            return True
        else:
            raise Exception('src(%s) != dst(%s).'%(self.get_md5sum(path), md5))
    
    def del_dir_by_null(self, path=None):
        try:
            os.removedirs(path)
        except:
            print traceback.print_exc()
        return True
    
    def del_files(self, path=None):
        if os.path.isfile(path):
            os.remove(path)
            self.del_dir_by_null(os.path.dirname(path))
        elif os.path.isdir(path):
            self.del_dir_by_null(path)
        return True
    
    def make_dirs(self):
        if not os.path.exists(os.path.dirname(self.dst)):
            os.makedirs(os.path.dirname(self.dst))
        return True

    def move_file(self):
        self.make_dirs()
        shutil.move(self.src, self.dst)
    
    def get_progress(self, fout=None):
        if not fout:
            return False
        #time,speed,have,all
        #1270007465,67676,155927742,155927742
        _time, _speed, _have, _all = [e.strip().split(",") for e in fout.readlines() if e.find(r":") < 0][-1]
        if _time and _speed and _have and _all:
            self.stdout.write("%sPROGRESS###%s%s"%(json.write({"check_result":0, "speed":_speed, "full_url":self.get_full_url()}), int(100*(float(_have)/int(_all))), os.linesep))
            self.stdout.flush()
            self.speed=_speed
        return True
    
    def check_timeout(self):
        if (time.time() - self.start_time) >= self.timeout:#timeout
            self.msg="Client execute child process timeout, %s"%self.msg
            self.stdout.write("RESULT###%s%s"%(json.write({"result":408, "msg":self.msg, "aux":self.get_aux_old_by_404(), "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
    
    def check_poll(self):
        if self.Popen.poll() != 0: # chile process return code is not 0
            self.msg="child process execute exception, %s"%self.Popen.poll()
            self.stdout.write("RESULT###%s%s"%(json.write({"result":401, "msg":self.msg, "aux":self.get_aux_old_by_404(), "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
    
    def engine_get_http_file(self):
        import stat
        path=os.path.join(curpath, "engine", "get_http_file")
        if not os.access(path, os.R_OK|os.X_OK):
            os.chmod(path, stat.S_IREAD|stat.S_IEXEC)
        return path
    
    def get_url_by_proxy(self):
        req={"_http":self.src,\
             "_proxy":self.proxy and "::%s"%self.proxy or "",\
             }
        return "%(_http)s%(_proxy)s"%req
    
    def set_cmd(self):
        #get_http_file -s  http://222.73.82.5/mp4/021/167/406/21167406.f4v?20004 -thread 6 -timeout 70 -speed 10 ./b.f4v
        req={"_get_http_file":self.engine_get_http_file(),\
             "_uri":self.get_url_by_proxy(),\
             "_dst":self.dst,\
             "_thread":self.thread,\
             "_timeout":int(self.timeout)/60,\
             "_speed":self.speed,\
             }
        self.cmd='%(_get_http_file)s -s %(_uri)s  -thread %(_thread)s -timeout %(_timeout)s -speed %(_speed)s  %(_dst)s'%req
        self.stdout.write("NEED###%s%s"%(self.cmd, os.linesep))
        self.stdout.flush()
    
    def shell(self):
        code = True
        try:
            fout=open(self.outcome, "a+")
            _fout=open(self.outcome, "r")
            print "cmd :", self.cmd
            self.Popen = subprocess.Popen(args=self.cmd.split(), stdin=None, stdout=fout, stderr=None, cwd=self.cwd)
            self.pid   = self.Popen.pid
#                new_process={"pid":0,\
#                             "app":"",\
#                             "cid":0,\
#                             "progress":0,\
#                             "result":-1,\
#                             "msg":"",\
#                             "aux":"",\
#                             }
            self.start_time = time.time()
            while self.Popen.poll() == None and (time.time() - self.start_time) < self.timeout :
                time.sleep(random.randint(1, 2))
                try:
                    self.get_progress(_fout)
                except:
                    print trace_back()
        except:
            # system error. result=-2
            self.msg="%s%s"%(self.msg, trace_back())
            self.stdout.write("RESULT###%s%s"%(json.write({"result":410, "msg":self.msg, "aux":self.get_aux_old_by_404(), "v":VERSION}), os.linesep))
            self.stdout.flush()
            raise Exception(self.msg)
        # check returncode
        self.check_poll()
        # check timeout
        self.check_timeout()
        # free child process
        self.free_child()
        # close open file
        if fout:
            fout.close()
    
    def download(self):
        # first check, my be have download before. safe time.
        try:
            self.check_md5(self.dst, self.md5)
            return True
        except:
            print trace_back()
        # clear dst
        self.del_files(self.dst)
        # realy to downlaod
        # set cmd
        self.set_cmd()
        # download
        self.shell()
        # check
        self.check_md5(self.dst, self.md5)
        # return
        return True
    
    def check_old_url_200(self):
        if not self.check_url:
            return True
        # self.check_url = "http://origin-player0145.tudou.com/mp4/021/181/199/21181199.f4v"
        # if 404
        try:
            fd = None
            file_size=0
            try:
                if self.proxy:
                    proxies = {'http':"http://%s"%self.proxy}
                    fd=urllib.urlopen(url=self.check_url, proxies=proxies)
                else:
                    fd = urllib.urlopen(self.check_url)
                file_size=int(fd.info().getheaders("Content-Length")[0])
            except:
                return True
            if file_size >= 50*1024: # >= 50k
                self.msg="check_url(%s) has exists."%self.check_url
                self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":self.msg, "aux":self.get_aux_old_by_200(), "v":VERSION}), os.linesep))
                self.stdout.flush()
                raise Exception(self.msg)
        finally:
            if fd:
                fd.close()
        #
        return
    
    def get_aux_by_null(self):
        return {}
    
    def get_aux_old_by_404(self):
        return {"check_result":0, "speed":self.speed, "full_url":self.get_full_url()}
    
    def get_aux_old_by_200(self):
        return {"check_result":1}

    def _run(self):
        """really to do.
        """
        self.checkArgvs()
        # check old url if exists (http-200).
        self.check_old_url_200()
        #
        try:
            self.download()
            self.msg=""
            self.stdout.write("RESULT###%s%s"%(json.write({"result":1, "msg":self.msg, "aux":self.get_aux_old_by_404(), "v":VERSION}), os.linesep))
            self.stdout.flush()
        except Exception, e:
            self.msg = "%s %s"%(self.msg, str(e))
            self.del_files(self.dst)
            self.stdout.write("RESULT###%s%s"%(json.write({"result":401, "msg":self.msg, "aux":self.get_aux_old_by_404(), "v":VERSION}), os.linesep))
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
    #{"src":"http://10.5.16.59:8080/21180485.mp4", "dest_path":"/home/mps/Client/__TMP/download/test.flv", "md5":"a6f6616510acc9883a7c8341495351a0", "tmp":"/home/mps/Client/__TMP/-10", "timeout":600}
    add=addFile()
    add.run()
