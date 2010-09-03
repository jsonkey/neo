#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: baby_sitter.py$
##               $Revision: 1$
##
##  Last Update: $2010-3-3 11:24$
##
##--------------------------------------------------------------------------
##

#---------------------------------------------------------------------------
#
# tmp_queue=Queue(0)
#
# log_queue=Queue(0)
#
#---------------------------------------------------------------------------

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
import daemon
import netutil
import uuid
import processing
from processing import Queue, Lock
import processing, logging
processing.enableLogging(level=logging.INFO)


# logging
import td_logging
if not os.path.exists(os.path.join(curpath, "logs/")):
    os.makedirs(os.path.join(curpath, "logs/"))
log=td_logging.mini_logging(os.path.join(curpath, "logs/", "access"))
GenLog=log.GenLog

#
tmp_queue=Queue(0)
log_queue=Queue(0)

# cpuCount
cpuCount = int(processing.cpuCount())


# pid
daemon_pid = os.path.join("/tmp", curpath.split("/")[-1] + ".pid")


# reload
_mtimes = {}
_win = True and (sys.platform == "win32") or False

#
G_process={}

# min_space_left_in_giga
min_space_left_in_giga=setting.min_space_left_in_giga
# storage root
STORAGE_ROOT=setting.STORAGE_ROOT #{"/tudou/0":500, "/tudou/1":500}
dplayer_SERVER=setting.dplayer_SERVER

#
def check_disk(STORAGE_ROOT=None):
    keys=STORAGE_ROOT.keys()
    keys.sort()
    return [STORAGE_ROOT[e] for e in keys]
#
#
Health={'load': '0.00', 'server': 1, 'disk':check_disk(STORAGE_ROOT), 'cpu':0,'freemem':0}
TIMEOUT=setting.TIMEOUT # timeout for cmdStatus
VISIT_TIME=setting.VISIT_TIME
N=0 #report times n += 1

#
process_lock  =Lock()

import logging

log = logging.getLogger("gearman")


# tools
def trace_back():
    return traceback.print_exc()

def no_left_storage():
    global log_queue
    global STORAGE_ROOT
    if len([k for k in STORAGE_ROOT if int(STORAGE_ROOT[k]) - min_space_left_in_giga <= 0]) == len(STORAGE_ROOT): # no space left.
        log.error("dplayer disk no left [%s] , so we not to access to server [%s]"%(STORAGE_ROOT, "%s:%s%s"%(setting.HOSTNAME, setting.PORT, setting.BASEURI_NEWJOB)))
        time.sleep(120)
        sys.exit(0)

new_process={"pid":0,\
             "cid":0,\
             "progress":0,\
             "result":0,\
             "msg":"",\
             "aux":{},\
             }

def check_load_limit(job=None):
    if (len([e for e in processing.activeChildren() if e.getName().split("_")[1] in setting.LIMIT_CPU]) >= cpuCount) and (job["type"] in setting.LIMIT_CPU):
        return True  # load >= limit, we can not fore more worker.
    else:
        return False # load < limit, we can fork more worker.

def code_changed():
    """check modes' is change, should reload modes
    """
    global _mtimes, _win
    for filename in filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values())):
        if filename.endswith(".pyc") or filename.endswith(".pyo"):
            filename = filename[:-1]
        if not os.path.exists(filename):
            continue # File might be in an egg, so it can't be reloaded.
        stat = os.stat(filename)
        mtime = stat.st_mtime
        if _win:
            mtime -= stat.st_ctime
        if filename not in _mtimes:
            _mtimes[filename] = mtime
            continue
        if mtime != _mtimes[filename]:
            print "file :", filename
            print "new time:", mtime
            print "old time:", _mtimes[filename]
            if os.path.basename(filename).find(r'sitter.py') >= 0:
                _mtimes[filename] = mtime
                continue
            try:
                _filename, ext = os.path.splitext(os.path.basename(filename))
                if ext.lower() != ".py":
                    continue
                if sys.modules.has_key(_filename):
                    mod = sys.modules[_filename]
                    reload(mod)
                else:
                    mod = __import__(_filename)
                #reload(mod[os.path.basename(filename).split(".")[0]])
            except:
                print "[reload()]" + trace_back()
            _mtimes[filename] = mtime
            continue
    
     
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


#---------------------------------------------------------------------------
#
# Communication
#
#---------------------------------------------------------------------------
class Communication:
    """
    Communication server and client.
    """
    def __init__(self, cmdStatus={}):
        self.cmdStatus=cmdStatus
     
    def check_arguments(self, i):
        #i = {"cid":1234,\
        #"type":"encode",\
        #"param":'{"src_path":"/home/tudou/0/a/b/c.flv","dest_path":"/home/tudou/0/a/b/desc_c.flv","encode_type":"www_flv","timeout":1000}',\
        # }
        # cmd={
        #"cid":1234,
        #"progress":0--100,
        #"result":-2, -1, 0, 1,
        #"msg":"",
        #"aux":"",
        #}
        tmp=copy.deepcopy(new_process)
        if not i.has_key("cid"):
            _put(log_queue, "[get-new-job-err] job, %s , is not have cid keyword."%i)
        tmp["cid"]=i["cid"]
        if not i.has_key("tid"):
            _put(log_queue, "[get-new-job-err] job, %s , is not have tid keyword."%i)
        tmp["tid"]=i["tid"]
        if not i.has_key("type"):
            _put(log_queue, "[get-new-job-err] job, %s , is not have type keyword."%i)
            tmp.update({"progress":0,\
                        "result":400,\
                        "msg":"job, %s , is not have type keyword."%i,\
                        "aux":{},\
                        })
            return False, tmp
        tmp["type"]=i["type"]
        App=setting.App
        if i["type"] not in App.keys():
            _put(log_queue, "[get-new-job-err] Client not support this type %s"%i["type"])
            tmp.update({"progress":0,\
                        "result":405,\
                        "msg":"Client not support this type %s"%i["type"],\
                        "aux":{},\
                        })
            return False, tmp
        for ex in App[i["type"]].split():
            if os.path.exists(ex) and not os.access(ex, os.R_OK|os.X_OK):
                try:
                    os.chmod(ex, stat.S_IREAD|stat.S_IEXEC)
                except:
                    pass
            if not os.path.exists(ex) or not os.access(ex, os.R_OK|os.X_OK):
                _put(log_queue, "[get-new-job-err] Client App %s is not exists or not execute authority."%i["type"])
                tmp.update({"progress":0,\
                            "result":406,\
                            "msg":"Client App %s is not exists or not execute authority."%i["type"],\
                            "aux":{},\
                            })
                try:
                    os.chmod(ex, stat.S_IREAD|stat.S_IEXEC)
                except:
                    pass
                return False, tmp
        tmp["app"]=App[i["type"]]
        if not i.has_key("param"):
            _put(log_queue, "[get-new-job-err] job, %s , is not have param keyword."%i)
            tmp.update({"progress":0,\
                        "result":400,\
                        "msg":"job, %s , is not have param keyword."%i,\
                        "aux":{},\
                        })
            return False, tmp
        try:
            tmp["param"]=i["param"]
        except:
            _put(log_queue, "[get-new-job-err] job, %s ,param is not a json type."%i)
            tmp.update({"progress":0,\
                        "result":400,\
                        "msg":"job, %s ,param is not a json type."%i,\
                        "aux":{},\
                        })
            return False, tmp
        if not i.has_key("timeout"):
            _put(log_queue, "[get-new-job-err] job, %s , is not have timeout keyword."%i)
            tmp.update({"progress":0,\
                        "result":400,\
                        "msg":"job, %s , is not have timeout keyword."%i,\
                        "aux":{},\
                        })
            return False, tmp
        if i.has_key("cookie"):
            tmp["cookie"]=i["cookie"]
        # timestamp
        tmp["timestamp"]=time.time()
        tmp["timeout"]=i["timeout"]
        tmp["param"]["timeout"]=i["timeout"]
        if not tmp["param"].has_key("core"):
            tmp["param"]["core"]=1
        tmp["core"]=tmp["param"]["core"]
        tmp["param"]["tmp"]=os.path.join(curpath, "__TMP", str(i["cid"]))
        # public
        tmp["param"]["storage_root"]=STORAGE_ROOT
        tmp["param"]["SYNC"]=setting.SYNC
        tmp["param"]["DEV"] =setting.DEV
        tmp["param"]["dplayer_server"]=setting.dplayer_SERVER
        return True, tmp
    
    def new_worker(self, njob):
        global tmp_queue
        global log_queue
        try:
            t=worker(njob)
            t.setName("%s_%s"%(str(njob["cid"]), njob["type"]))
            t.setDaemon(1)
            t.start()
            _put(log_queue, "[fork-new-process] %s"%njob)
        except:
            njob.update({"progress":100,\
                        "result":410,\
                        "msg":"start worker error. %s"%traceback.print_exc(),\
                        "aux":{},\
                        })
            _put(tmp_queue, njob)
    
    def reset_finaly_arguments(self, job=None):
        global VISIT_TIME
        global min_space_left_in_giga
        try:
            if job["global"].has_key("min_space_left_in_giga"):
                min_space_left_in_giga = job["global"]["min_space_left_in_giga"]
            if job["global"].has_key("t"):
                VISIT_TIME=int(job["global"]["t"])/1000
        except:
            print traceback.print_exc()
            return
        return True

    def clear_msg(self, tmp=None):
        #{\'result\': 1,
        # \'app\': \'/usr/bin/python /home/tommy/Client/app/ls/listDir.py\',
        # \'pid\': 25296,
        # \'cid\': 1478,
        # \'aux\': \'{"result":1,"msg":""}\',
        # \'progress\': 100,
        # \'msg\': \'child_returncode=0\\n\\n\', 
        # \'param\': {\'tmp\': \'/home/tommy/Client/__TMP/1478\', \'path\': \'/home\', \'timeout\':600 }
        # }
        if tmp["result"] in (-1, 0, 1):
            tmp["msg"]=""
        req={"cid"        :tmp["cid"],\
                "tid"     :tmp["tid"],\
                "core"    :tmp["core"],\
                "result"  :tmp["result"],\
                "progress":tmp["progress"],\
                "aux"     :tmp["aux"],\
                "msg"     :tmp["msg"],\
                "type"    :tmp["type"],\
                }
        # cookie
        # app version number
        [req.update({k:tmp[k]}) for k in ("cookie", "v") if tmp.has_key(k)]
        return req
    
    def dict_2_list(self):
        return [self.clear_msg(self.cmdStatus[k]) for k in self.cmdStatus.keys() if int(k) not in  (-100,)]
    
    def get_request_body(self):
        global Health
        global N # ++N
        N += 1
        body={"v":setting.versions,\
              "n":N,\
              "health":copy.deepcopy(Health),\
              "status":self.dict_2_list(),\
              }
        return body
    
    def inject_special_job(self, job):
        global min_space_left_in_giga
        try:
            #if job["global"].has_key("h") and int(job["global"]["h"]) == 1: # need health check.
            if N%3 == 0:
                if not self.cmdStatus.has_key(-100) or ((time.time() - self.cmdStatus[-100]["timestamp"]) >= TIMEOUT):
                    job["cmds"].append({"cid":-100,"tid":0, "core":1, "type":"health","timeout":60,"param":{"timeout":60, "storage_root":STORAGE_ROOT},})
            for e in job["cmds"]:
                if e["type"] == "kill":
                    job["cmds"]["param"]["pid"]=self.cmdStatus[e["cid"]]["pid"]
        except:
            pass
    
    def set_busy_job(self, job=None, msg=None):
        global tmp_queue
        if not job.has_key("core"):
            job["core"]=1
        _put(tmp_queue,  {"cid":job["cid"],\
                          "tid":job["tid"],\
                          "core":job["core"],\
                          "result":413,\
                          "progress":100,\
                          "aux":{},\
                          "msg":msg,\
                          "type":job["type"],\
                          }
        )
    
    def dispense_job_2_worker(self, job=None):
        global tmp_queue
        if not job:
            return
        for i in job["cmds"]:
            if len(processing.activeChildren()) >= setting.MAX_PROCESS:
                print "xxxx : process numbers is very big.", processing.activeChildren()
                print "xxxx : numbers cmds.", job["cmds"]
                self.set_busy_job(i, "Client is busy now: jobs(all) numbers >= max_process(%s)."%setting.MAX_PROCESS)
                continue
            elif check_load_limit(i):
                print "xxxx : process numbers is very big.", processing.activeChildren()
                print "xxxx : numbers cmds.", job["cmds"]
                self.set_busy_job(i, "Client is busy now: jobs(encoder) numbers >= CPUS(%s)."%cpuCount)
                continue
            ccode, creq=self.check_arguments(i)
            # add new job to cmdStatus
            _put(tmp_queue, creq)
            if ccode:# ok
                # start new process do this.
                self.new_worker(creq)
    
    def report_server(self):
        global log_queue
        # sleep
        time.sleep(VISIT_TIME)
        # dplayer check storage left. 
        no_left_storage()
        # reload
        code_changed()
        # request body
        new_job_request_body=self.get_request_body()
        istr=urllib.urlencode(new_job_request_body)
        hostname, port, baseuri, proxy=setting.HOSTNAME, setting.PORT, setting.BASEURI_NEWJOB, setting.PROXY
        server = hostname + ":" + str(port)
        print "======"*20
        print "server :", server
        print "baseuri:", baseuri
        print "new_job_request_body:",new_job_request_body
        print "======"*20
        _put(log_queue, "[send-request-ok] server=%s baseuri=%s body=%s"%(server, baseuri, new_job_request_body))
        req_code, req =netutil.client_post(server, baseuri, istr, proxy)
        _put(log_queue, "[processing.activeChildren()] %s"%(processing.activeChildren()))
        # test ls
        #req_code, req=True, json.write({"global":{"touch_interval":5,"health_report_interval":20},"cmds":[{"cid":N, "tid":0,"type":"ls","param":{"path":"/home", "timeout":10*60}),} ],}
        # test pic
        #req_code, req=True, json.write({"global":{"touch_interval":5,"health_report_interval":20},"cmds":[{"cid":N,"tid":0,"type":"pic","param":{"path":"/home/mps-test/core/v2-mps/encoder/benchmark/src.flv", "desc_dir":"/home/tommy/Client/__TMP/pic_%s"%Tid, "pic_type":"normal", "timeout":10*60},} ],})
        # test analyze_src
        #req_code, req=True, json.write({"global":{"touch_interval":5,"health_report_interval":20},"cmds":[{"cid":N,"tid":0,"type":"analyze_src","param":{"src":"/home/mps-test/core/v2-mps/encoder/benchmark/src.flv", "timeout":600},} ],})
        # test delete_file
        #req_code, req=True, json.write({"global":{"touch_interval":5,"health_report_interval":20},"cmds":[{"cid":N,"tid":0,"type":"delete_file","param":{"path":"/home/mps-test/core/v2-mps/encoder/benchmark/src.flv", "timeout":600},} ],})
        if not req_code:
            print "%s getjobs Error."%time.ctime()
            _put(log_queue, "[get-new-job-error] %s"%req)
            return
        try:
            job=json.read(req)
            _put(log_queue, "[get-new-job-ok] %s"%req)
        except Exception, e:
            _put(log_queue, "[get-new-job-error] json.read(%s) Exception, %s"%(req, e))
            return
        #
        #http response:
        #{
        #    "global":{},
        #    "cmds":[{}, {}],
        #}
        #
        #{ "t":5, //in second "health_report_interval":20 //in second
        #  "h":1/0   //ask for health
        #}
        # reset vist_time
        self.reset_finaly_arguments(job)
        # if job["global"]["h"] == 1
        self.inject_special_job(job)
        # hand out new jobs to different worker to do.
        self.dispense_job_2_worker(job)
        #
        return True
    
    def update_cmdStatus(self):
        global tmp_queue
        while not tmp_queue.empty():
            try:
                req=None
                req=_get_nowait(tmp_queue)
                if req:
                    if self.cmdStatus.has_key(req["cid"]):
                        self.cmdStatus[req["cid"]].update(req)
                    else:
                        self.cmdStatus[req["cid"]]=req
            except:
                pass
    
    def filter_special_job(self, k=None):
        global Health
        global STORAGE_ROOT
        if int(k) == -100:
            if self.cmdStatus[k]["aux"].has_key("storage_root"):
                STORAGE_ROOT=self.cmdStatus[k]["aux"]["storage_root"]
                #del self.cmdStatus[k]["storge_root"]
            Health=self.cmdStatus[k]["aux"] or Health
    
    def check_finished(self):
        finished=""
        for k in self.cmdStatus.keys():
            # filter
            self.filter_special_job(k)
            if int(self.cmdStatus[k]["result"]) not in (-1, 0):
                print "finihed key :", k
                finished = "%s%s%s"%(finished, os.linesep, self.cmdStatus[k])
                del self.cmdStatus[k]
            elif self.cmdStatus[k].has_key("timestamp") and (time.time() - self.cmdStatus[k]["timestamp"]) > TIMEOUT:
                print "TIMEOUT key :", k
                finished = "%s%s[timeout] %s"%(finished, os.linesep, self.cmdStatus[k])
                del self.cmdStatus[k]
        if finished:
            _put(log_queue, "[finished-job] %s"%finished)

    def run(self):
        # update job, flush new finished job to cmdStatus
        self.update_cmdStatus()
        # report to server
        if self.report_server():
            # report ok
            # check, del finished and reported job,
            # or, server is busy, so we keep the results , try send times as we can.
            # so, we will not lost results.
            self.check_finished()


#---------------------------------------------------------------------------
#
# logging
#
#---------------------------------------------------------------------------
class log(processing.Process):
    """log all.
    """
    def __init__(self):
        processing.Process.__init__(self)
    
    def run(self):
        global log_queue
        while True:
            try:
                req=None
                req=_get(log_queue)
                if req:
                    GenLog("INFO", req)
            except:
                pass

#---------------------------------------------------------------------------
#
# monitor
#
#---------------------------------------------------------------------------
class monitor(processing.Process):
    """monitor all.
    """
    def __init__(self):
        processing.Process.__init__(self)
    
    def run(self):
        global log_queue
        while True:
            try:
                code_changed()
                monitor=setting.App["monitor"]
                os.system(monitor)
            except Exception, e:
                _put(log_queue, "process monitor Exception:%s"%str(e))
            time.sleep(random.randint(10, 60))


############################################################################
#
# process produce
#
############################################################################
def new_one_process(m_class, m_name):
    """process produce.
    """
    global G_process
    if m_class and m_name:
        pass
    else:
        msg="new_one_process(m_class, m_name) argv, m_class or m_name is None."
        GenLog("DEBUG", msg)
        return False
    # OK,
    t=m_class()
    t.setName(m_name)
    t.setDaemon(1)
    t.start()
    try:
        try:
            process_lock.acquire()
            if G_process.has_key(m_name):
                if G_process[m_name]:
                    G_process[m_name].join(3)
                    del G_process[m_name]
            G_process[m_name]=t
        finally:
            process_lock.release()
    except:
        GenLog("ERROR", "new_one_process(m_class, %s) Exception, %s"%(m_name, trace_back()))
        return False
    # return
    return True

############################################################################
#
# control
#
############################################################################
def control():
    """
    """
    # init env
    clear_env()
    # do
    # loop check which thrad die, and than to start new thread, OK
    new_one_process(log, "log_process")
    new_one_process(monitor, "monitor_process")
    cmdStatus={}
    while True:
        print "#######"*20
        print "cmdStatus :", cmdStatus
        print "#######"*20
        Communication(cmdStatus).run()
        print "activeChildren :", processing.activeChildren()
        [e.join(0.1) for e in processing.activeChildren()]
        for p in ("log_process", "monitor_process"):
            if not G_process[p].isAlive():
                GenLog("ERROR", "%s exit."%p)
                sys.exit()


################################################################################
#
#
# main
#
################################################################################
#if __name__ == "__main__":
#    control()



class MyDaemon(daemon.Daemon):
    def run(self):
        try:
            control()
        except Exception, e:
            msg="test_control() Exception, %s"%e
            GenLog("DEBUG", msg)
            return False
        # return
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Unknown command"
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
    if sys.argv[1] == "-d":
        control()
    if len(sys.argv) == 2:
        daemon = MyDaemon(daemon_pid)
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
