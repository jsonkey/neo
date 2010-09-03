#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: worker.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 12:25$
##
##--------------------------------------------------------------------------
##

import os
import re
import sys
import stat
import time
import copy
import shlex
import random
import signal
import urllib
import traceback
import subprocess

#
curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))
#

def append_path(path=None):
    """append to sys.path list
    if this path is exists in sys.path's list, we do nothing!
    else, append to sys.path
    """
    if not os.path.exists(path):
        raise "%s is not exists!"%path
    if path in sys.path:
        print "%s has exists! in sys.path, so we do nothing."%path
        return True
    else:
        sys.path.append(path)
        return True
    return

[append_path(e) for e in (os.path.join(curpath, "lib"),\
                          os.path.join(curpath, "config"),\
                          os.path.join(curpath, "app"))]


import setting
import json
import uuid
import processing
from processing import Queue, Lock
import processing, logging
processing.enableLogging(level=logging.INFO)


#---------------------------------------------------------------------------
#
# new process
#
#---------------------------------------------------------------------------
class worker(processing.Process):
    def __init__(self, job=None):
        processing.Process.__init__(self)
        self.job       = job
        self.stdin     = None
        self.stdout    = None
        self.stderr    = None
        self.cmd       = None
        self.cwd       = curpath
        self.Popen     = None
        self.pid       = None
        self.returncode= None
        self.timeout   = int(job["timeout"])
        self.start_time= None
        self.msg       = ''

    
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
    
    def wait(self):
        """ wait child exit signal,
        """
        self.Popen.wait()

    def free_child(self):
        """ kill process by pid
        """
        try:
            self.terminate()
            self.kill()
            self.wait()
        except:
            pass
    
    def get_tmp_dir(self):
        tmp_dir=os.path.join(curpath, "__TMP", str(self.job["cid"]))
        if os.path.exists(tmp_dir):
            del_dir_fource(tmp_dir)
        #
        os.makedirs(tmp_dir)
        return tmp_dir
    
    def set_std(self):
        tmp_dir=self.get_tmp_dir()
        assert tmp_dir, "tmp_dir is None."
        #
        only=uuid.uuid4()
        self.stdin =os.path.join(tmp_dir, "stdin_%s"%only)
        self.stdout=os.path.join(tmp_dir, "stdout_%s"%only)
        self.stderr=os.path.join(tmp_dir, "stderr_%s"%only)
        fin =open(self.stdin, 'a+')
        fin.write("%s%s"%(json.write(self.job["param"]), os.linesep))
        fin.flush()
        fin.seek(0)
        fin.close()
        if not os.path.exists(self.stdin):
            time.sleep(random.randint(2, 6))
        assert os.path.exists(self.stdin), "%s has not write to disk."%self.stdin
        self.timeout=int(self.job["param"]["timeout"])
        self.cmd=self.job["app"]
        
    def set_stdout_result(self):
        if not os.path.exists(self.stdout) or int(os.path.getsize(self.stdout)) > 10*1024*1024:
            return
        try:
            fout=None
            fout=open(self.stdout, "r")
            need=''
            for i in fout.readlines():
                if i.find(r"NEED###") >= 0:#need
                    need="%s%s%s"%(need, os.linesep, i.strip().split("###")[1])
                elif i.find(r"RESULT###") >= 0:
                    up=json.read(i.strip().split("###")[1])
                    up["progress"]=100
                    self.job.update(up)
                    log.info("cid=%s%sstderr%s%s"%(self.job["cid"], os.linesep, os.linesep, self.job))
            log.info("cid=%s%sstdout%s%s"%(self.job["cid"], os.linesep, os.linesep, need))
        finally:
            if fout:
                fout.close()
        return
        
    def get_progress(self, fout=None):
        global tmp_queue
        if not fout:
            return False
        # "511PROGRESS###50\n".strip().split("PROGRESS###")
        aux, progress=None, None
        aux, progress=[e.strip().split("PROGRESS###") for e in fout.readlines() if e.find(r"PROGRESS###") >= 0][-1]
        self.job["progress"]=progress or self.job["progress"]
        self.job["aux"]     =json.read(aux) or self.job["aux"]
        _put(tmp_queue, self.job)
    
    def check_timeout(self):
        if (time.time() - self.start_time) >= self.timeout:#timeout
            up={"result":408, "msg":"Client execute child process timeout, %s"%self.msg, "progress":100,}
            self.job.update(up)
    
    def check_poll(self):
        if self.Popen.poll() != 0: # chile process return code is not 0
            up={"result":401, "msg":"child process execute exception, %s"%self.Popen.poll(), "progress":100,}
            self.job.update(up)
    
    def report_results_2_tmp_queue(self):
        global tmp_queue
        _put(tmp_queue, self.job)
            
    def run(self):
        """run cmd """
        global tmp_queue
        code = True
        try:
            self.set_std()
            fin =open(self.stdin, "a+")
            fout=open(self.stdout, "a+")
            ferr=open(self.stderr, "a+")
            _fout=open(self.stdout, "a+")
            print "cmd :", shlex.split(self.cmd)
            self.Popen = subprocess.Popen(args=shlex.split(self.cmd), close_fds=True, stdin=fin, stdout=fout, stderr=ferr, cwd=self.cwd)
            self.pid   = self.Popen.pid
#                new_process={"pid":0,\
#                             "app":"",\
#                             "cid":0,\
#                             "progress":0,\
#                             "result":-1,\
#                             "msg":"",\
#                             "aux":"",\
#                             }
            self.job["pid"]=self.pid
            self.job["progress"]=5
            self.job["result"]=0 # doing
            _put(tmp_queue, self.job)
            self.start_time = time.time()
            while self.Popen.poll() == None and (time.time() - self.start_time) < self.timeout:
                time.sleep(random.randint(1, 2))
                try:
                    self.get_progress(_fout)
                except:
                    pass
                print "running... %s, %s, %s" % (self.Popen.poll(), time.time() - self.start_time, self.timeout)
        except Exception, e:
            # system error. result=-2
            self.msg="%s%s"%(self.msg, str(e))
            up={"result":410, "msg":"Client execute child process error [subwork]!!error in Popen, %s"%self.msg, "progress":100,}
            self.job.update(up)
        # check returncode
        self.check_poll()
        # check timeout
        self.check_timeout()
        # set stdout msg.
        self.set_stdout_result()
        # report results
        self.report_results_2_tmp_queue()
        # free child process
        self.free_child()
        try:
            fin.close()
            fout.close()
            ferr.close()
            _fout.close()
            os.system("rm -fr %s"%os.path.dirname(self.stdin))
        except:
            pass
