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
import socket
from sys import path, argv
from .nlog import vlog,die_now
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import task_self
import ClusterShell
from . import sgi_cluster
import syslog

class __OutputHandler(ClusterShell.Event.EventHandler):
    output = False

    def __init__(self, label, output):
        self._label = label
        self.output = output
    def ev_read(self, worker):
        buf = worker.current_msg
        ns = worker.current_msg
        if self._label:
            if not self._label in self.output:
                self.output[self._label] = []

            self.output[self._label].append(buf)

    def ev_hup(self, worker):
        if worker.current_rc > 0:
            vlog(2, "clush: %s: exited with exit code %d" % (worker.current_node, worker.current_rc))

    def ev_timeout(self, worker):
        if worker.current_node:
            vlog(2, "clush: %s: command timeout" % worker.current_node)
        else:
            vlog(2, "clush: command timeout")

def command(nodeset, command):
    output = {}

    task = task_self()

    vlog(4,'clush_ipmi: nodeset:%s command:%s' % (nodeset, command))

    if not sgi_cluster.is_sac():
        vlog(1, "only run this from SAC node")
        return False

    for node in nodeset:
        lead = sgi_cluster.get_lead(node)
        if lead:
            if lead == socket.gethostname():
                cmd = '/usr/diags/bin/bcmd -H {0} {1}'.format(sgi_cluster.get_bmc(node), command)
                vlog(4, 'calling bcmd on localhost: %s' % cmd)
                task.shell(
                    cmd, 
                    timeout=120,  
                    handler=__OutputHandler(node, output)
                ) 
            else:
                cmd = '/usr/diags/bin/bcmd -H {0} {1}'.format(sgi_cluster.get_bmc(node), command)
                vlog(4, 'calling bcmd on %s: %s' % (lead, cmd))
                task.shell(
                    cmd,
                    nodes=lead, 
                    timeout=120,  
                    handler=__OutputHandler(node, output)
                )

    task.run()

    return output
 
