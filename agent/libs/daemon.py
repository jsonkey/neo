#!/usr/bin/env python

import sys, os, time, atexit
import re
import commands
from signal import SIGTERM 

#curpath=os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))

curpath=os.path.join(re.sub(r'\/\w+$', '', os.path.normpath(os.path.join(os.getcwd(),os.path.dirname(__file__)))))

class Daemon:
    """
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile="/tmp/daemon-example.pid", stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin   = stdin
        self.stdout  = stdout
        self.stderr  = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
            
        # decouple from parent environment
        os.chdir(curpath) 
        os.setsid() 
        os.umask(0) 
        
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
            
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        _fd=open(self.pidfile,'w')
        _fd.write("%s\n" % pid)
        _fd.close()
        
    def delpid(self):
        os.remove(self.pidfile)


    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except:
            pid = None
        if pid:
            #
            try:
                ps=commands.getoutput("ps -ef")
            except:
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            #if re.search(r'\ %s\ '%(str(pid)), ps):
            if re.search(r'\W+\ {1,50}%s\ '%str(pid), ps):
                try:
                    print "pid :", re.search(str(pid), ps).group()
                except:
                    pass
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            else:
                self.delpid()
        # Start the daemon
        self.daemonize()
        self.run()
        
    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
            
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart
        
        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
        try:
            os.system("killall python")
        except:
            pass

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()
        
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
