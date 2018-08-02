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
#
# Filler module to get information about cluster
# TODO: clean this up and make it load from somewhere intelligently
#
import socket
import re
from .nlog import vlog,die_now
from . import nfile

def get_cluster_name():
    if re.search("^la", socket.gethostname()):
        return 'laramie'
    if re.search("^ch", socket.gethostname()):
        return 'cheyenne'
    return None

def get_cluster_name_formal():
    if re.search("^la", socket.gethostname()):
        return 'Laramie'
    if re.search("^ch", socket.gethostname()):
        return 'Cheyenne'
    return None

def get_smc_version():
    smcvtxt = nfile.read_file_first_line('/etc/sgi-admin-node-release')
    if not smcvtxt:
        return None

    #Known patterns:
    #SGI Management Center Admin Node 3.5.0, Build 716r177.sles12sp2-1705051348
    #SGI Tempo Admin Node 3.3.0, Build 714r18.sles12sp1-1604041900

    #split by comma first
    vi = smcvtxt.split(',')
    #grab last word after comma
    vt = vi[0].split()
    return vt[len(vt) - 1]

def is_smc_version_atleast(version):
    """ Compare smc version by each revision to insure running is atleast version """
    vp = version.split('.')
    sp = get_smc_version().split('.')

    if sp[0] < vp[0]:
        return False
    if sp[1] < vp[1]:
        return False
    if sp[2] < vp[2]:
        return False

    return True
 
def is_sac():
    host = socket.gethostname()

    if host == 'lamgt' or host == 'chmgt':
        return True
    else:
        return False

def get_sac_hostname():
    if not is_sac():
        return None
    else:
        return socket.gethostname()

def get_ice_info(node):
    m = re.search('^r([0-9]+)i([0-9]+)n([0-9]+)$', node) 

    if not m:
        return False

    return {
	'rack':	m.group(1),
	'lead':	'r{0}lead'.format(m.group(1)),
	'cmc':	'r{0}i{1}c'.format(m.group(1), m.group(2)),
	'iru':	m.group(2),
	'node':	m.group(3),
	'bmc':	'r{0}i{1}n{2}-bmc'.format(m.group(1), m.group(2), m.group(3))
    }

def get_ice_node_image(node):
    #SGI renamed to query
    if is_smc_version_atleast("3.5.0"): 
        (ret, out, err) = nfile.exec_to_string(['/opt/sgi/sbin/cimage', '--show-nodes', node])
    else:
        (ret, out, err) = nfile.exec_to_string(['/opt/sgi/sbin/cimage', '--list-nodes', node])

    if ret != 0:
        return None

    #/opt/sgi/sbin/cimage --show-nodes r1i2n1
    #r1i2n1: ice-sles12sp2 4.4.21-69-default tmpfs
    sp = out.split()
    vlog(5, "%s Images: %s" % (node, sp))
    if len(sp) > 1:
        return sp[1]
    else:
        vlog(1, 'invalid response from cimage: %s' % (out))
        return None
 
def get_ice_switch_info(node):
    m = re.search('^r([0-9]+)i([0-9]+)s([0-9]+)(-bmc|)$', node) 

    if not m:
        return False

    return {
	'rack':	m.group(1),
	'lead':	'r{0}lead'.format(m.group(1)),
	'scmc':	'r{0}i{1}s{2}-bmc'.format(m.group(1), m.group(2), m.group(3)),
	'iru':	m.group(2),
	'switch': m.group(3),
	'bmc':	'r{0}i{1}s{2}-bmc'.format(m.group(1), m.group(2), m.group(3))
    }
 

def get_lead(node):
    """ get lead but only from sac """
    if not is_sac():
        return False

    info = get_ice_info(node)
    if info:
        return info['lead']
    info = get_ice_switch_info(node)
    if info:
        return info['lead']
     
    return socket.gethostname() 

def get_bmc(node):
    """ get node bmc name """
    
    info = get_ice_info(node)
    if info:
        return info['bmc']
    info = get_ice_switch_info(node)
    if info:
        return info['bmc']
 
    return '%s-bmc' % (node)
 
def get_sm():
    """ get smc nodes """
    
    host = socket.gethostname()

    if host == 'lamgt':
        return ['r1lead']
    elif host == 'chmgt':
        return ['r1lead', 'r2lead']
    return None

def get_ib_speed():
    """ get Infiniband network speed """
    
    host = socket.gethostname()

    if host == 'lamgt':
        return {'speed': 'EDR', 'link': 25, 'width': '4x'};
    elif host == 'chmgt':
        return {'speed': 'EDR', 'link': 25, 'width': '4x'};
    return None

def logical_to_physical_dict(v):
    """ convert dict of entity to physical """
    a = logical_to_physical(v['rack'], v['iru'])
    v['rack'] = a['rack']
    v['iru'] = a['iru']

def physical_to_logical_dict(v):
    """ convert dict of entity to physical """
    a = physical_to_logical(v['rack'], v['iru'])
    v['rack'] = a['rack']
    v['iru'] = a['iru']

def logical_to_physical(rack, iru):
    """ Convert SGI logical labels to physical labels """
    if iru > 3:
        rack *= 2
        iru -= 4
    else: #IRU in rack
        rack = rack * 2 - 1
    
    return {
	'rack': rack,
	'iru': iru
    }

def physical_to_logical(rack, iru):
    """ Convert SGI physical labels to logical labels """
    if rack & 1:
        #odd rack
        rack = (rack + 1) / 2
    else: #even rack
        rack /= 2
        iru += 4

    return {
	'rack': rack,
	'iru': iru
    }


def print_label(v, pformat = None):
    """ prints an sgi label from dict

    formats:
	raw: values as dict
	ibcv2: SGI ibcv2 format (r10i2s0c1.20)
	firmware: firmare label (r1i0s0 SW1 SwitchX -  Mellanox Technologies)
	physical: physical label (001IRU2-0-1-14)
	simple: simple label (r1i0s0 SW1/P1 or r1i3n17)
	simple_name: simple label without port (r1i0s0 SW1 or r1i3n17)
    
    """

    if pformat == 'raw':
        return str(v)
    elif pformat == 'ibcv2':
        return 'r%si%ss%sc%s.%s' % (
	    v['rack'],
	    v['iru'],
	    v['switch'],
	    v['switch_chip'],
	    v['port']
	)
    elif pformat == 'firmware' or pformat == 'firmware_name':
        if not v['switch'] is None:
            if pformat == 'firmware_name' or v['port'] is None:
                return 'r%si%ss%s SW%s SwitchX -  Mellanox Technologies' % (
		    v['rack'],
		    v['iru'],
		    v['switch'],
		    v['switch_chip']
		)
            else:
                return 'r%si%ss%s SW%s SwitchX -  Mellanox Technologies/P%s' % (
		    v['rack'],
		    v['iru'],
		    v['switch'],
		    v['switch_chip'],
		    v['port']
		)
        elif not v['node'] is None:
            if pformat == 'firmware_name':
                return 'r%si%ss%s/U%s' % (
		    v['rack'],
		    v['iru'],
		    v['node'],
		    v['hca'] if v['hca'] else 1 #default to first hca
		) 
            else:
                return 'r%si%ss%s/U%s/P%s' % (
		    v['rack'],
		    v['iru'],
		    v['node'],
		    v['hca'] if v['hca'] else 1, #default to first hca
		    v['port'] if v['port'] else 1, #default to first port
		) 
    elif pformat == 'physical':
        if not v['port'] is None:
            return '{0:0>3}IRU{1}-{2}-{3}-{4}'.format(
		v['rack'],
		v['iru'],
		v['switch'],
		v['switch_chip'],
		v['port']
	    )
        else:
            return '{0:0>3}IRU{1}-{2}-{3}'.format(
		v['rack'],
		v['iru'],
		v['switch'],
		v['switch_chip']
	    ) 
    elif pformat == 'simple' or pformat == 'simple_name':
        if not v['node'] is None:
            return 'r%si%sn%s' % (
		v['rack'],
		v['iru'],
		v['node']
	    ) 
        if not v['switch'] is None:
            if not v['port'] is None and pformat == 'simple':
                return 'r%si%ss%s SW%s/P%s' % (
		    v['rack'],
		    v['iru'],
		    v['switch'],
		    v['switch_chip'],
		    v['port']
		)  
            else:
                return 'r%si%ss%s SW%s' % (
		    v['rack'],
		    v['iru'],
		    v['switch'],
		    v['switch_chip']
		) 
    vlog(1, 'unknown format: %s' % (pformat))	    
    return ''

def parse_label(label):
    """ Parse the sgi label names """

    def tint(v):
        if v:
            return int(v)
        else:
            return None

    vlog(5, 'parse_label(%s)' % (label))

    v = {
	'rack': None,
	'iru': None,
	'switch': None,
	'switch_chip': None,
	'node': None,
	'port': None,
	'hca': None,
    }

    #SGI ibcv2 format
    #r1i0s0c0.16
    #r9i2s0c1.20
    #r10i2s0c1.20
    r1 = re.compile(
	r"""
	r(?P<rack>[0-9]+)  #E-cell Rack - not E-Cell number
	i(?P<iru>[0-9]+)
	s(?P<switch>[0-9]+)
	c(?P<swchip>[0-9]+)
	\.
	(?P<port>[0-9]+)
	\s*
	""",
	re.VERBOSE
	)
    #r1i3n17/U1/P1
    r2 = re.compile(
	r"""
	r(?P<rack>[0-9]+)  #E-cell Rack - not E-Cell number
	i(?P<iru>[0-9]+)
	n(?P<node>[0-9]+)
	(?:
	    (?:/U(?P<hca>\d+)|)
	    (?:/P(?P<port>\d+)|)
	)
	\s*
	""",
	re.VERBOSE
	)
    #r1i0s0 SW1 SwitchX -  Mellanox Technologies
    #r1i0s0 SW0/P27
    r3 = re.compile(
	r"""
	r(?P<rack>[0-9]+)  #E-cell Rack - not E-Cell number
	i(?P<iru>[0-9]+)
	s(?P<switch>[0-9]+)
 	(?: 
	    \s+SW(?P<swchip>\d+)|
	) 
 	(?:
	    \s+SwitchX\s+\-+\s+Mellanox\ Technologies\s*|
	) 
 	(?:
	    /P(?P<port>\d+)|
	) 
	\s*
	""",
	re.VERBOSE
	)     
    #001IRU2-0-1-14 
    r4 = re.compile(
	r"""
	(?P<rack>[0-9]+)  #E-cell Rack - not E-Cell number
	IRU(?P<iru>[0-9]+)
	(?P<switch>[0-9]+)
	-
	(?P<swchip>\d+)
	-
	(?P<port>\d+)
	\s*
	""",
	re.VERBOSE
	)     
 
    match = r1.match(label) 
    if match:        
        v['rack'] = tint(match.group('rack'))
        v['iru'] = tint(match.group('iru'))
        v['switch'] = tint(match.group('switch'))
        v['switch_chip'] = tint(match.group('swchip'))
        v['port'] = tint(match.group('port'))
        return v
    match = r2.match(label) 
    if match:        
        v['rack'] = tint(match.group('rack'))
        v['iru'] = tint(match.group('iru'))
        v['node'] = tint(match.group('node'))
        v['port'] = tint(match.group('port'))
        v['hca'] = tint(match.group('hca'))
        return v
    match = r3.match(label) 
    if match:        
        v['rack'] = tint(match.group('rack'))
        v['iru'] = tint(match.group('iru'))
        v['switch'] = tint(match.group('switch'))
        v['switch_chip'] = tint(match.group('swchip'))
        v['port'] = tint(match.group('port'))
        return v    
    match = r4.match(label) 
    if match:        
        v['rack'] = tint(match.group('rack'))
        v['iru'] = tint(match.group('iru'))
        v['switch'] = tint(match.group('switch'))
        v['switch_chip'] = tint(match.group('swchip'))
        v['port'] = tint(match.group('port'))
        return v    
    return None

