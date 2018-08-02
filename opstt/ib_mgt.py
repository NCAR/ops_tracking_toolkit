#!/usr/bin/env python
# vim: set tabstop=8 softtabstop=4 noexpandtab
#Copyright (c) 2017, University Corporation for Atmospheric Research
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, 
#this list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice,
#this list of conditions and the following disclaimer in the documentation
#and/or other materials provided with the distribution.
#
#3. Neither the name of the copyright holder nor the names of its contributors
#may be used to endorse or promote products derived from this software without
#specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
#ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
#CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
#SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
#INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
#WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
from sys import path, argv
from .nlog import vlog,die_now
from . import nfile
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import task_self
from . import cluster_info
import re
import os

def pull_opensm_files ( local_path, remote_path ):
    """ Pulls files in remote_path from openSM host to local_path on localhost"""
    SM = NodeSet.fromlist(cluster_info.get_sm()[0:1])

    vlog(3, 'Pulling %s from OpenSM %s to local path %s' % (remote_path, SM, local_path))

    task = task_self()

    if type(remote_path) is list:
        for rp in remote_path:
            vlog(3, 'Pulling %s from OpenSM %s to local path %s' % (rp, SM, local_path))
            task.rcopy(rp, local_path, SM, timeout=120, stderr=True,  preserve=True )
    else:
        vlog(3, 'Pulling %s from OpenSM %s to local path %s' % (remote_path, SM, local_path))
        task.rcopy(remote_path, local_path, SM, timeout=120, stderr=True,  preserve=True )

    task.resume()

    for buffer, nodelist in task.iter_errors():
        n = str(NodeSet.fromlist(nodelist))
        vlog(2, 'Error: Node=%s %s' % (n, str(buffer)))

    vlog(5, 'Pull complete ret=%s ' % (task.max_retcode()))

    #TODO: make clush not mangle the names
    if not type(remote_path) is list:
        remote_path = [remote_path]

    for rp in remote_path:
        np=os.path.join(local_path, os.path.basename(rp))
        mp=os.path.join(local_path, '%s.%s' % (os.path.basename(rp), SM))
        vlog(6, 'Unmangling %s -> %s' % (mp, np))
        os.rename(mp, np)
    
def exec_opensm_to_string ( cmd, primary_only = False, timeout = 300  ):
    """ Runs cmd on openSM host and places Return Value, STDOUT, STDERR into returned list  """
    vlog(5, 'start exec_opensm_to_string cmd=%s primary_only=%s' % (
        [cmd],
        primary_only
    ))

    SM = None

    if primary_only:
        SM = NodeSet.fromlist(cluster_info.get_sm()[0:1])
    else:
        SM = NodeSet.fromlist(cluster_info.get_sm())

    output = {}

    task = task_self()

    task.run(
        cmd,
        nodes=SM, 
        timeout=int(timeout),
        #stderr=True
    )

    for buffer, nodelist in task.iter_buffers():
        n = str(NodeSet.fromlist(nodelist))

        if not n in output:
            output[n] = list()

        output[n].append(str(buffer))

    vlog(5, 'finish exec_opensm_to_string cmd=%s ret=%s' % (
        [cmd],
        task.max_retcode()
    ))

    if task.max_retcode() > 0:
        vlog(1, 'Opensm command may have failed with ret code %s: %s' % (task.max_retcode(), cmd))

    return {'output': output, 'max_retcode': task.max_retcode()}

def exec_opensm_to_file ( cmd, output_file, timeout = 300 ):
    """ Runs cmd on openSM host and pipes STDOUT to output_file """

    ret = exec_opensm_to_string( cmd, True, timeout )

    if not ret or not 'output' in ret:
        return None

    output = ret['output']

    for node, out in list(output.items()):
        return nfile.write_file(output_file, "\n".join(out))

    return None

def disable_port( guid, port ):
    """ Disable port in fabric 
    Warning: Never disable a port on a HCA. you will have to restart openib on node to re-enable
    GUID must be integer and not hex string
    """

    if not isinstance(guid, int) or not isinstance(port, (int)):
        vlog(1, 'guid/port must be ints. given %s/P%s %s/%s' % (guid, port, type(guid), type(port)))
        return None

    if query_port_disabled( guid, port ):
        vlog(2, 'Port %s/P%s already disabled' % (hex(guid), port))
        return None

    vlog(2, 'Disabling %s/P%s in fabric' % (hex(guid), port))
    ret = exec_opensm_to_string('ibportstate -G %s %s disable' % (guid, port), True)
    if ret and 'output' in ret:
        return ret['output'];

def enable_port( guid, port, retry = 10 ):
    """ Enable port in fabric 
    GUID must be integer and not hex string
    """

    if not isinstance(guid, int) or not isinstance(port, (int)):
        vlog(1, 'guid/port must be ints. given %s/P%s %s/%s' % (guid, port, type(guid), type(port)))
        return None

    if not query_port_disabled( guid, port ):
        vlog(2, 'Port %s/P%s already enabled' % (hex(guid), port))
        return None

    vlog(2, 'Enabling %s/P%s in fabric' % (hex(guid), port))
    ret = exec_opensm_to_string('ibportstate -G %s %s enable' % (guid, port), True)
    if ret and 'max_retcode' in ret and 'output' in ret:
        if ret['max_retcode'] > 0 and retry > 0:
            vlog(2, 'Enabled %s/P%s failed. Retrying more %s times' % (hex(guid), port, retry))
            return enable_port( guid, port, retry - 1 )
        else:
            return ret['output'];

def query_port( guid, port ):
    """ Query port in fabric 
    GUID must be integer and not hex string
    """

    if not isinstance(guid, int) or not isinstance(port, (int)):
        vlog(1, 'guid/port must be ints. given %s/P%s %s/%s' % (guid, port, type(guid), type(port)))
        return None

    vlog(4, 'Querying %s/P%s in fabric' % (hex(guid), port))
    ret = exec_opensm_to_string('ibportstate -G %s %s' % (guid, port), True)
    if ret and 'output' in ret:
        return ret['output'];

def ibportstate_parse_dict( output ):
    """ Parses the output from ibportstate into a dictionary of states 
    """
    d = {}

    #Mkey:............................<not displayed>
    ibregex = re.compile( r"""
        (?P<key>\w+):\.+
        (?P<value>.+)$
        """,
        re.VERBOSE
        ) 

    for sm,out in list(output.items()):
        for smout in out:
            for line in smout.split(os.linesep):
                match = ibregex.match(line)
                if match:
                    d[match.group('key')] = match.group('value')

    return d
 
def query_port_disabled( guid, port ):
    """ Query port in fabric and return True if it is physically disabled
    GUID must be integer and not hex string
    """

    status = query_port( guid, port )
    if not status:
        return None

    d = ibportstate_parse_dict( status )
    if 'PhysLinkState' in d:
        return d['PhysLinkState'] == 'Disabled'

    return None

 
