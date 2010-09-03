#!/usr/bin/python -u
#-*- coding: UTF-8 -*-
# vi:ts=4:et
##==========================================================================
##
##  Copyright (c) CnCodec Inc. All Rights Reserved.
##
##--------------------------------------------------------------------------
##
##  File:        $Workfile: new_process.py$
##               $Revision: 1$
##
##  Last Update: $2010-3-3 11:26$
##
##--------------------------------------------------------------------------
##

import logging
log = logging.getLogger("new_process")


############################################################################
#
# process produce
#
############################################################################
def new_one_process(G_process={}, m_class=None, m_name=None):
    """process produce.
    """
    assert G_process, "G_process is None."
    assert m_class,   "m_class is None."
    assert m_name,    "m_name is None."
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
    except Exception, e:
        log.error("new_one_process(m_class, %s) Exception, %s"%(m_name, str(e)))
        raise str(e)
    # return
    return True
