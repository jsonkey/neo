#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: dispatcher.py$
##               $Revision: 1$
##
##  Last Update: $2010-09-01 12:26$
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
import netutil
import uuid
import processing
from processing import Queue, Lock
import processing, logging
processing.enableLogging(level=logging.INFO)


# cpuCount
cpuCount = int(processing.cpuCount())

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

import logging
log = logging.getLogger("dispatcher")


#---------------------------------------------------------------------------
#
# Communication
#
#---------------------------------------------------------------------------
class Communication:
    """ Communication server and client.
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
