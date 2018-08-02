#!/usr/bin/python
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
from ClusterShell.Task import task_self, NodeSet
from .nlog import vlog
import json
from pipes import quote

def run_task(cmd):
    """ run task on pbs server node """

    task = task_self()

    for node in NodeSet('@pbsadmin'): 
        """ run on pbs nodes until it works """
        #print (cmd, node)
        task.run(cmd, nodes=node, timeout=60)

        #print 'node: %s error: %s' % (node, task.node_error(node))
        vlog(4, '%s timeouts:%s Error=%s' % (node, task.num_timeout(), task.node_error(node)))

        for output, nodelist in task.iter_buffers():
            #print 'nodelist:%s' % NodeSet.fromlist(nodelist)
            if str(NodeSet.fromlist(nodelist)) == node:
                return str(output)
            #print '%s: %s' % (NodeSet.fromlist(nodelist), output)

    return None

def node_states():
    """ Query Node states from PBS """
    statesjson = run_task("/opt/pbs/default/bin/pbsnodes -av -Fjson")

    if statesjson is None:
        return None

    state = json.loads(statesjson)
    del statesjson

    return state['nodes']
           
def set_offline_nodes(nodes, comment = None):
    """ Set nodes offline in PBS 
    nodeset: nodes to offline
    string: comment
    """

    if comment:
        return run_task("/opt/pbs/default/bin/pbsnodes -o -C %s %s" % (quote(comment), ' '.join(nodes)) )
    else:
        return run_task("/opt/pbs/default/bin/pbsnodes -o %s" % (' '.join(nodes)) )

def set_online_nodes(nodes, comment = None):
    """ Set nodes online in PBS 
    nodeset: nodes to online
    string: comment
    """
    if comment:
        return run_task("/opt/pbs/default/bin/pbsnodes -r -C %s %s" % (quote(comment), ' '.join(nodes)) )
    else:
        return run_task("/opt/pbs/default/bin/pbsnodes -r %s" % (' '.join(nodes)) )
           
def is_pbs_down(states):
    """ Do the PBS Node states mean node is down """
    for state in states:
        if state in [ "offline" , "offline_by_mom" , "down" , "Stale" , "state-unknown" , "maintenance" , "initializing" , "unresolvable" ]:
            return True

    return False

def is_pbs_job_excl(states):
    """ Do the PBS Node states mean node has exclusive job """
    for state in states:
        if state in [ "job-exclusive" , "resv-exclusive" , "default_excl" , "default_exclhost" , "force_excl" , "force_exclhost" ]:
            return True

    return False

def is_pbs_node_busy(node):
    """ Check if node can be considered to have a job """
    return 'ncpus' in node['resources_assigned'] and node['resources_assigned']['ncpus'] > 0



