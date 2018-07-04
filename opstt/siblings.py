#!/usr/bin/env python
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
import re

nodes_per_blade = 2
slots_per_iru = 9

if re.search("^la", socket.gethostname()) is None:
    nodes_per_blade = 4
 
def node_to_tuple(n):
    m = re.match("([rR])([0-9]+)([iI])([0-9]+)([nN])([0-9]+)", n)
    if m is not None:
	#(rack, iru, node)
	return (int(m.group(2)), int(m.group(4)), int(m.group(6)))
    else:
	return None

def resolve_siblings(nodes):
    """ resolve out list of sibling nodes to given set of nodes """
    result = []
    for n in nodes:
	nt = node_to_tuple(n)
	for i in range(0,nodes_per_blade):
	    nid = (nt[2] % slots_per_iru) + (i*slots_per_iru)
	    nodename = "r%di%dn%d" % (nt[0], nt[1], nid)

	    if not nodename in result:
		result.append(nodename)

    return result

