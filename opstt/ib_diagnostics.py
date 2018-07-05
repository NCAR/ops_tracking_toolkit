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
from sys import path, argv
from .nlog import vlog,die_now,to_hex,is_ascii
import re
import os
import csv
from . import cluster_info
from . import sgi_cluster
import math

def parse_port ( label ):
    """ Parse the name of a IB port 
    returns dictionary with parsed values

    Known Formats:
	'ys4618 HCA-1'(4594/1)
	'ys4618 HCA-1'(4594/1)
	MF0;ys75ib1:SXX536/L05/U1/P2
	ys75ib1/L05/U1/P2
	ys46ib1:SX60XX/U1/P26
	MF0;ca00ib1a:SXX512/S01/U1
	'MF0;ys72ib1:SXX536/L22/U1'(395/1)
	geyser1/H3/P1
	ys70ib1 L05 P12
	ys22ib1 P13 
    	ys2324 HCA-1
    	geyser01 HCA-1 P3

    """
    name  = None
    hca   = None
    leaf  = None
    spine = None #only used for internal orca connections
    port  = None   
    guid  = None   
    unit  = None #chip unit or hca count

    #regex matches following:
    #'ys4618 HCA-1'(4594/1)
    #'ys4618 HCA-1'(4594/1)
    #MF0;ys75ib1:SXX536/L05/U1/P2
    #ys75ib1/L05/U1/P2
    #ys46ib1:SX60XX/U1/P26
    #MF0;ca00ib1a:SXX512/S01/U1
    #'MF0;ys72ib1:SXX536/L22/U1'(395/1)
    #geyser1/H3/P1
    ib_portname_type1_regex = re.compile(
		r"""
		^\s*
		(?:\'|)
		(?:
		    (?P<hca_host_name>\w+)\s+			#Host name
		    [hcaHCA]+-(?P<hca_id>\d+)			#HCA number
		    |                          	
		    (?:MF0;|)					#MF0 - useless id	
		    (?P<tca_host_name>\w+)			#TCA Name
		    (?::SX\w+|)					#Switch Type
		    (?:\/[hcaHCA]{1,3}(?P<hca_id2>\d+)|)	#HCA number
		    (?:\/[lLiIdD]+(?P<leaf>\d+)|)		#Leaf (sometimes called /LID in error)
		    (?:\/S(?P<spine>\d+)|)			#Spine
		    (?:\/U(?P<unit>\d+)|)			#U number
		    (?:\/P(?P<port1>\d+)|)			#Port
		)
		(?:
		    (?:\'|)
		    \(
			\d+					#LID: just assume it is wrong
			\/
			(?P<port2>\d+)				#Port
		    \)
		    |
		)
		\s*$
		""",
		re.VERBOSE
		) 

    match = ib_portname_type1_regex.match(label)
    if match:
	vlog(6,'matched: %s' % match.group())
	if match.group('hca_host_name'):
	    name = match.group('hca_host_name')
	    hca = match.group('hca_id')
	if match.group('tca_host_name'):
	    name = match.group('tca_host_name')
	    spine = match.group('spine')
	    hca = match.group('hca_id2')
	    leaf = match.group('leaf') 
	if match.group('unit'):
	    hca = match.group('unit') 
	if match.group('port1'):
	    port = match.group('port1')
	if match.group('port2'):
	    port = match.group('port2')
    else:
	#regex matches following: (mlnx default format if unlabeled)
	#Sguid/Nguid/Pport
	#S7cfe900300bdf570/N7cfe900300bdf570/P28
	#S248a0703003f1932/U/P1
	ib_portname_type3_regex = re.compile(
		    r"""
		    ^\s*
		    S(?P<guid>[a-f0-9]*)  
		    (
			\/
			N[a-f0-9]*
			|
			\/U
		    )
		    (|
			/P(?P<port>[0-9]*?)
		    )$
		    """,
		    re.VERBOSE
		    ) 
	match = ib_portname_type3_regex.match(label) 
	if match:
	    guid = '0x{0}'.format(match.group('guid'))
	    name = guid
	    if match.group('port'):
	        port = int(match.group('port'))

	    vlog(5, 'matched: %s GUID=%s Port=%s' % (match.group(), guid, port))
	else:
	    #regex matches following: (these are usually from human entry)
	    #ys70ib1 L05 P12
	    #ys22ib1 P13 
	    #ys2324 HCA-1
	    #geyser01 HCA-1 P3
	    ib_portname_type2_regex = re.compile(
			r"""
			^\s*
			(?P<name>\w+)			#name
			(?:
			    (?:\s+
			    [hcaHCA]+(?:-|)(?P<hca>\d+)	#hca id
			    )
			    |
			)
			(?:\s+
			    [lLiIdD]+			
			    (?P<leaf>\d+)			#leaf (called lid in error)
			    |
			)	
			(?:\s+U\d+|)			#/U useless
			(?:
			    (?:\s+[pP](?P<port>\d+))	#port number
			    |
			    )
			\s*$
			""",
			re.VERBOSE
			) 
	    match = ib_portname_type2_regex.match(label)
	    if match:
		vlog(5, 'matched: %s' % match.group())
		name = match.group('name')
		hca = match.group('hca')
		leaf = match.group('leaf')
		port = match.group('port')
	    else:
		vlog(6, 'unable to parse: %s' % (label))
		name = label

    return {
		'name'	: name,
		'hca'	: hca,
		'leaf'	: leaf,
		'spine'	: spine,
		'port'	: port,
		'connection' : None,
		'dumped' : False,
		'serial' : None,
		'length' : None,
		'partnumber' : None,
		'guid' : guid,
		'type' : None,
		'speed' : None,
		'width' : None,
		'lid' : None
	    }

def register_cable ( ports, port1, port2 ):
    """ add cable ports to ports list (for now). port2 can be None for unconnected ports. """

    #check for and ignore dups
    for port in ports:
	if  (
		port['lid']    == port1['lid'] and
		port['port']    == port1['port']
	    ) or ( port2 and (
		port['lid']    == port2['lid'] and
		port['port']    == port2['port']
	    )):
		return

    ports.append(port1)
    if port2:
	ports.append(port2)

def parse_ibnetdiscover_cables ( ports, contents ):

    vlog(4, 'parse_ibnetdiscover_cables()')

    """ Parse the output of 'ibnetdiscover -p' 

    Two types of line formats:
    CA    44  1 0x0002c9030045f121 4x FDR - SW     2 17 0x0002c903006e1430 ( 'localhost HCA-1' - 'MF0;js01ib2:SX60XX/U1' )
    SW     2 19 0x0002c903006e1430 4x SDR                                    'MF0;js01ib2:SX60XX/U1'
    SW    82 19 0x7cfe900300bdf4f0 4x ???                                    'r1i0s0 SW1'

    """
    ibcable_regex = re.compile(
	    r"""
	    ^(?P<HCA1_type>CA|SW)\s+		#HCA1 type
	    (?P<HCA1_lid>\d+)\s+		#HCA1 LID
	    (?P<HCA1_port>\d+)\s+		#HCA1 Port
	    (?P<HCA1_guid>0x\w+)\s+		#HCA1 GUID
	    (?P<width>\w+)\s+			#Cable Width
	    (?P<speed>\w+|\?\?\?)\s+	        #Cable Speed
	    (
		\'(?P<HCA_name>.+)\'		#Port Name
		|				#cable is connected
		-\s+		
		(?P<HCA2_type>CA|SW)\s+		#HCA2 Type
		(?P<HCA2_lid>\d+)\s+		#HCA2 LID
		(?P<HCA2_port>\d+)\s+		#HCA2 Port
		(?P<HCA2_guid>0x\w+)\s+		#HCA2 GUID
		\(\s+
		    \'(?P<HCA1_name>.+)\'	#HCA1 Name
		    \s+-\s
		    +\'(?P<HCA2_name>.+)\'	#HCA2 Name
		\s+\)
	    )$
	    """,
	    re.VERBOSE
	    ) 
    for line in contents.split(os.linesep):
	match = ibcable_regex.match(line)
	if match:
	    if match.group('HCA_name'):
		port = parse_port(match.group('HCA_name'))
		port['port'] = match.group('HCA1_port')
		port['lid'] = match.group('HCA1_lid')
		port['guid'] = match.group('HCA1_guid')
		port['type'] = match.group('HCA1_type')
		port['speed'] = match.group('speed')
		port['width'] = match.group('width')
		port['connection'] = None
		register_cable(ports, port, None)
		#vlog(5, port)
	    else:
		port1 = parse_port(match.group('HCA1_name'))
		port1['port'] = match.group('HCA1_port')
		port1['lid'] = match.group('HCA1_lid')
		port1['type'] = match.group('HCA1_type')
		port1['guid'] = match.group('HCA1_guid')
		port1['speed'] = match.group('speed')
		port1['width'] = match.group('width')

		port2 = parse_port(match.group('HCA2_name'))
		port2['port'] = match.group('HCA2_port')
		port2['lid'] = match.group('HCA2_lid')
		port2['guid'] = match.group('HCA2_guid')
		port2['type'] = match.group('HCA2_type')
		port2['speed'] = match.group('speed')
		port2['width'] = match.group('width')

		#vlog(5, port1)
		#vlog(5, port2)

		#cross reference connecting port
		port1['connection'] = port2
		port2['connection'] = port1
		register_cable(ports, port1, port2)
	else:
	    if line != "":
		vlog(3, 'Parse fail: %s' % line )

def msg_port_pretty_long ( port, why ): 
    """ msg port label with helpful info"""
    vlog(1,'%s: %s SPEED=%s LID=%s GUID=%s SN=%s PN=%s' % (
	    why,
	    port_pretty(port),
	    port['speed'],
	    port['lid'],
	    port['guid'],
	    port['SN'] if 'SN' in port else '',
	    port['PN'] if 'PN' in port else '',
	)
    )

def port_name_pretty ( port ):
    """ return pretty port name """
    if not port:
	return 'None'
    if not isinstance(port, dict):
	name = port
    else:
	name = port['name']

    name = re.sub(r'\s*SwitchX\s*-\s*Mellanox\ Technologies', '', name)
    return name

def port_pretty ( port ):
    """ return pretty port label """
    if not port:
	return 'None'

    name = port_name_pretty(port['name'])

    if port['spine']: #spine
	return '%s/S%s/P%s' % (name, port['spine'], port['port'])
    if port['leaf']: #port on orca
	return '%s/L%s/P%s' % (name, port['leaf'], port['port']) 
    if port['hca']: #hca on node
	return '%s/U%s/P%s' % (name, port['hca'], port['port'])

    return '%s/P%s' % (name, port['port']) #tor port

def find_underperforming_cables ( ports, issues, speed, width = "4x"):
    """ Checks all of the ports for any that are not at full width or speed or disabled """

    vlog(4, 'find_underperforming_cables()')

    #PhysLinkState:...................LinkUp
    #PhysLinkState:...................Disabled
    #PhysLinkState:...................Polling
    portstate_regex = re.compile(
	    r"""
	    ^(?P<property>\w+):\.+		#property
	    (?P<value>\w+)$			#value
	    """,
	    re.VERBOSE
	    );

    for port in ports:
	if port['name'] == "localhost": #complain about localhost named ports but no need to complain
	   vlog(5,'Localhost labeled port: %s <-> %s' % (port_pretty(port), 'N/A' if not port['connection'] else port_pretty(port['connection'])))
	   issues.append({ 
	       'type': 'label',
	       'ports': [port],
	       'issue': port['name'],
	       'raw': None,
	       'source': 'ibnetdiscover -p'
	   })         

	if port['connection']: #ignore unconnected ports
	    if port['speed'] != speed:
	       issues.append({ 
		   'type': 'speed',
		   'ports': [port, port['connection']],
		   'issue': 'Port Speed: %s' % port['speed'],
		   'raw': None,
		   'source': 'ibnetdiscover -p'
	       })        
	    if port['width'] != width:
 	       issues.append({ 
 		   'type': 'width',
		   'ports': [port, port['connection']],
		   'issue': 'Port Width: %s' % port['width'],
		   'raw': None,
		   'source': 'ibnetdiscover -p'
	       })        
	else: #check if unconnected ports are disabled
	    if 'PortPhyState' in port:
		vlog(5, 'down port guid=%s port=%s physstate:%s state:%s' % (port['guid'], port['port'], port['PortPhyState'],port['PortState']))
		#PortPhyState
		#2=polling
		#3=disabled
		#PortState           
		if int(port['PortPhyState']) == 3: #physical state is disabled
		    vlog(4, 'disabled port found guid=%s port=%s physstate:%s state:%s' % (port['guid'], port['port'], port['PortPhyState'],port['PortState']))
		    issues.append({ 
			'type': 'disabled',
			'ports': [port],
			'issue': 'Port Physical State Disabled',
			'raw': None,
			'source': 'ibdiagnet2'
		    })     
	    else:
		vlog(4, 'down port missing physstate %s' % (port))

def parse_sgi_ibcv2 ( ports, issues, contents ):
    """ Parse the useful output of SGI's ibcv2 tool """

    def parse(label):
	""" Parse the ibcv2 specific label names """
	vlog(5, 'parse_sgi_ibcv2::parse(%s)' % (label))


	#r1i0s0c0.16
	#r9i2s0c1.20
	#r10i2s0c1.20
	p = sgi_cluster.parse_label(label)
        sgi_cluster.physical_to_logical_dict(p)
	vlog(4, 'parse %s -> %s' % (label, sgi_cluster.print_label(p, 'simple')))
 	
        if p and 'port' in p and not p['port'] is None:        
	    return resolve_port(ports, {
		'name': sgi_cluster.print_label(p, 'firmware_name'),
                'port': int(p['port']),
		'hca': None,
		'spine': None,
		'leaf': None
	    })
	else:
	    vlog(2, 'unable to parse ibcv2 port %s' % label)
	    return None

    vlog(4, 'parse_sgi_ibcv2()')

    #Errors to parse out:
    #print "NOT FOUND: $comment\n";
    #print "MISCABLE:\n";
    #printf "\tFOUND:    %s <---> %s\n", $phy_sact, $phy_dact;
    #printf "\tEXPECTED: $phy_sexp <---> $phy_dexp\n";
    #NOT FOUND: r2i2s2 INTERNAL port 12 to 12
    for match in re.finditer(r"""
	\s*
	(
	    ERROR:\s*(?P<error>.+)
	    |
	    NOT\ FOUND:\s*(?P<missingi>\S+)\s*INTERNAL\ port\ (?P<missingip1>\d+)\ to\ (?P<missingip2>\d+)
            |
	    NOT\ FOUND:\s*(?P<missing1>\S+)\s*(?P<missing2>\S+|)
	    |
	    FOUND:\s*(?P<found1>\S+)\s*<-*>\s*(?P<found2>\S+)
	)
	\s*
	""", contents, re.VERBOSE):

	if match.group('error'):
	    vlog(5, 'unknown error: %s' % match.group('error'))
            issues.append({ 
		'type': 'unknown',
		'ports': [],
		'issue': 'Unknown Error detected',
		'raw': match.group(1),
		'source': 'sgi ibcv2'
	    })        
	elif match.group('missingi'): 
            p1 = '%sc0.%s' % (match.group('missingi'), match.group('missingip1'))
            p2 = '%sc1.%s' % (match.group('missingi'), match.group('missingip2'))
	    vlog(5, 'missing internal cable: %s <--> %s' % (p1, p2))
            issues.append({ 
		'type': 'missing',
		'ports': [parse(p1), parse(p2)],
		'issue': 'Missing cable',
		'raw': match.group(1),
		'source': 'sgi ibcv2'
	    })   
	elif match.group('missing1'): 
	    vlog(5, 'missing cable: %s <--> %s' % (match.group('missing1'), match.group('missing2')))
            issues.append({ 
		'type': 'missing',
		'ports': [parse(match.group('missing1')), parse(match.group('missing2'))],
		'issue': 'Missing cable',
		'raw': match.group(1),
		'source': 'sgi ibcv2'
	    })   
	elif match.group('found1'): 
	    vlog(5, 'unexpected cable: %s <--> %s' % (match.group('found1'), match.group('found2')))
            issues.append({ 
		'type': 'unexpected',
		'ports': [parse(match.group('found1')),parse(match.group('found2'))],
		'issue': 'Unexpected cable',
		'raw': match.group(1),
		'source': 'sgi ibcv2'
	    })

def parse_ibdiagnet ( ports, issues, contents ):
    """ Parse the output of ibdiagnet """

    vlog(4, 'parse_ibdiagnet()')

    ibdiag_line_regex = re.compile(r"""
	    \s*-[^IW]-\s+	    #find all none Info and Warns
	    (?:
		(?!lid=0x[0-9a-z]+\ dev=\d+)		#ignore the lid dumps for counters since its dup
		(?P<msg>.*)				#extract message after type
	    )
	""", re.VERBOSE) 

    #Se41d2d03004bcfb0/Ne41d2d03004bcfb0/P20 - "port_rcv_remote_physical_errors" increased during the run (difference value=1,difference allowed threshold=1)
    #r9i1n24/U1/P1 - "port_rcv_remote_physical_errors" increased during the run (difference value=117,difference allowed threshold=1)
    ibdiag_line_regex_port = re.compile(r"""
	    ^\s*
	    (?P<port>\S*)
	    \s*-\s*" 
            (?P<counter>\S*)"\s*
            increased\ during\ the\ run\ \(difference\ value=
            (?P<value>[0-9]*),
	""", re.VERBOSE)  
    #Link: S7cfe900300a51030/N7cfe900300a51030/P28<-->ime2/U1/P1 - Unexpected actual link speed 14
    ibdiag_line_regex_link = re.compile(r"""
	    ^\s*Link:\s*
	    (?P<port>\S*?)
	    (|<-->
		(?P<port2>\S*)
	    )
	    \s*-\s*(?P<what>.*)
	""", re.VERBOSE)  

    #Unassigned LFT for lid:4 Dead end at:S7cfe900300bdf4f0/N7cfe900300bdf4f0 PLFT:0
    #Error in mark route from:gs1/U1 SLID:108 to DLID:103
    #Fail to find a path from:r1i3n6/U1/1 to:r1i3n12/U1/1
    #Error in mark route from:r1i1n17/U1 SLID:46 to DLID:64
    ibdiag_line_regex_lft = re.compile(r"""
	    ^\s*
	    (?::\s*|)
	    (?:
		Unassigned\ LFT\ for
		|
		Error\ in\ mark\ route
		|
		Fail\ to\ find\ a\ path
		|
		Error\ in\ mark\ route
	    ).*
	""", re.VERBOSE)   
    for match in re.finditer(r"""
	(?![#-]+[\n\r])[\r\n]*		#all of the stanzas start with --- or ###
	(?P<label>(?![#-]+).*)[\r\n]+   #first real line is the label
	(?P<content>			#content follows label
	    (?:
		(?![#-]+[\n\r])		#make sure not to run into next stanza
		.*[\r\n]*		#suck in the ws
	    )+
	)
	""", contents, re.VERBOSE):

       #Look for summary to extract to ignore it
       if match.group('label') == "Summary":
	   for line in match.group('content').split("\n"):
	       if line == "": #stop at end of the summary count stanza
		   break
       else: #stanza containing detail information
	   for line in match.group('content').split("\n"):
	       lmatch = ibdiag_line_regex.match(line)
	       if lmatch:
		   vlog(4,'IBDiagnet2: %s: %s' % (match.group('label'), lmatch.group('msg')))

		   cmatch = ibdiag_line_regex_port.match(lmatch.group('msg'))
		   lnmatch = ibdiag_line_regex_link.match(lmatch.group('msg'))
		   lftmatch = ibdiag_line_regex_lft.match(lmatch.group('msg'))
		   if cmatch:
		       port = parse_resolve_port(ports, cmatch.group('port'))

		       if (
			       str(cmatch.group('counter')) in [ 
				   #ignored congestion counters  in general
				   'port_rcv_switch_relay_errors', 
				   'port_xmit_discard',
				   'port_rcv_remote_physical_errors' #mlnx will not honor these as symbol errors should catch issue
			       ] or
			       ( #ignore reconnects for HCAs since they happen often for node crashes
				   cmatch.group('counter') == 'link_down_counter' and int(cmatch.group('value')) < 3
			       )  or
			       ( #ignore small numbers of corruption errors
				   str(cmatch.group('counter')) in [ 'port_rcv_errors', 'symbol_error_counter' ] and
				   int(cmatch.group('value')) < 100
			       )   or
			       ( #ignore small numbers of control errors
				   str(cmatch.group('counter')) in [ 'vl15_dropped' ] and
				   int(cmatch.group('value')) < 100
			       )   or
			       ( #ignore small numbers of errors
				   str(cmatch.group('counter')) in [ 
				       'error_detection_counter_lane0',
				       'error_detection_counter_lane1',
				       'error_detection_counter_lane2',
				       'error_detection_counter_lane3',
				       'unknown_block_cnt',
				       'sync_header_err_cnt',
				       'link_error_recovery_counter'
				   ] and
				   int(cmatch.group('value')) < 7
			       ) 
			  ):
			       vlog(4, 'ignoring counter %s with %s' % (cmatch.group('counter'), cmatch.group('value')))
		       else:
			   issues.append({ 
			       'type': 'counters',
			       'ports': [port],
			       'issue': 'Counter %s increased to %s' % (cmatch.group('counter'), cmatch.group('value')),
			       'raw': cmatch.string,
			       'source': 'ibdiagnet2.log'
			   })    
		   elif lnmatch:
 		       dport2 = None
		       if lnmatch.group('port2'):
			   dport2 = parse_resolve_port(ports, lnmatch.group('port2'))
		       issues.append({ 
		           'type': 'link',
		           'ports': [parse_resolve_port(ports, lnmatch.group('port')), dport2],
		           'issue': lnmatch.group('what'),
		           'raw': lnmatch.string,
		           'source': 'ibdiagnet2.log'
		       })
		   elif lftmatch:
		       issues.append({ 
		           'type': 'lft',
		           'ports': [],
		           'issue': 'LFT Error',
		           'raw': lmatch.group('msg'),
		           'source': 'ibdiagnet2.log'
		       }) 
		   else:
		       if not str(lmatch.group('msg')) in [
			        'Ports counters value Check finished with errors',
				'Ports counters Difference Check (during run) finished with errors',
				'Links Speed Check finished with errors',
				'Links Check finished with errors',
				'Links Width Check finished with errors',
				'Fabric Discover finished with errors',
				'Alias GUIDs finished with errors',
				'Partition Keys finished with errors'
			    ]:

			    port1 = None
			    port2 = None

			    #attempt to brute force resolve a port from each word
			    for w in lmatch.group('msg').split():
				port = parse_resolve_port(ports, w)
				if port:
				    if not port1:
					port1 = port
				    elif not port2:
					port2 = port

			    vlog(4,'IBDiagnet2 unknown: %s: %s' % (match.group('label'), lmatch.group('msg')))

			    issues.append({ 
				'type': 'unknown',
				'ports': [port1, port2],
				'issue': '%s: %s' % (match.group('label'), lmatch.group('msg')),  
				'raw': lmatch.string,
				'source': 'ibdiagnet2.log'
			    }) 

def sanity_check_string(issues, source, what, string, check_type = "string"):
    """ sanity check string is ascii or make issue. 
	returns true if string is good 

	check_type: string, hex integer, integer
	
    """
    if not string:
	return True

    if check_type in [ 'hex integer', 'integer' ] and len(string) == 0:
 	issues.append({ 
	    'type': 'unknown',
	    'ports': [],
	    'issue': '%s is empty instead of numbers' % (what),
	    'raw': string,
	    'source': source
	})  
	return False

    if not is_ascii(string):
 	issues.append({ 
	    'type': 'unknown',
	    'ports': [],
	    'issue': '%s is non-ascii string' % (what),
	    'raw': '%s: hexdump: %s' % (what, to_hex(string)),
	    'source': source
	})  
	return False

    if len(string) > 4096:
	issues.append({ 
	    'type': 'unknown',
	    'ports': [],
	    'issue': '%s is too long of a string' % (what),
	    'raw': string,
	    'source': source
	})  
	return False

    if check_type == "integer":
	try:
	    buf = int(string)
	except ValueError:
	    issues.append({ 
		'type': 'unknown',
		'ports': [],
		'issue': '%s is invalid integer' % (what),
		'raw': string,
		'source': source
	    })  
	    return False
    elif check_type == "hex integer":
 	try:
	    buf = int(string, 16)
	except ValueError:
	    issues.append({ 
		'type': 'unknown',
		'ports': [],
		'issue': '%s is invalid base 16 integer' % (what),
		'raw': string,
		'source': source
	    })  
	    return False
    elif not check_type == "string":
       vlog(1, 'Invalid check_type: %s' % (check_type))

    return True


def parse_ibdiagnet_csv ( ports, issues, fcsv ):
    """ Parse the output of ibdiagnet ibdiagnet2.db_csv
	Limited to pulling the cable serials and state out currently
    """

    def sc(field, var, ctype = "string"):
	""" quick sanity check of dict field """
	if field in var:
	    return sanity_check_string(issues, 'ibdiagnet2.log', field, var[field], ctype)
	else:
	    return True

    vlog(4, 'parse_ibdiagnet_csv()')
    csv_mode=None
    csv_headers=None

    #START_CABLE_INFO
    #END_CABLE_INFO

    csv_reader = csv.reader(fcsv)
    for row in csv_reader:
	if len(row) == 1 and row[0] != "" :
	    if row[0].startswith('START_'):
		csv_mode = row[0];
		csv_headers = None
	    if row[0].startswith('END_'):
		csv_mode = None
		csv_headers = None
	else:
	    if csv_mode: #in a data block
		if csv_headers == None:
		    csv_headers = row;
		else: #data
		    rowdict = dict(list(zip(csv_headers, row)))

		    if csv_mode == 'START_CABLE_INFO':
                        if (
			    sc('PortGuid', rowdict, "hex integer") and
			    sc('PortNum', rowdict, "integer") and
			    sc('SN', rowdict) and
			    sc('PN', rowdict) and
			    sc('LengthDesc', rowdict)
			):
			
			   rowdict['guid'] = rowdict['PortGuid']
			   rowdict['port'] = rowdict['PortNum']
			   resolve_update_port(ports,rowdict) 

		    elif csv_mode == 'START_PORTS':
                        if (
			    sc('NodeGuid', rowdict, "hex integer") and
			    sc('PortNum', rowdict, "integer") and
			    sc('SN', rowdict) and
			    sc('PN', rowdict) and
			    sc('LengthDesc', rowdict)
			):
			    rowdict['guid'] = rowdict['NodeGuid']
			    rowdict['port'] = rowdict['PortNum']
			    resolve_update_port(ports,rowdict)

		    #elif csv_mode == 'START_LINKS':
		    #   rowdict['guid'] = rowdict['NodeGuid1']
		    #   rowdict['port'] = rowdict['PortNum1']
		    #   resolve_update_port(ports,rowdict)

		    #   rowdict['guid'] = rowdict['NodeGuid2']
		    #   rowdict['port'] = rowdict['PortNum2']
		    #   resolve_update_port(ports,rowdict) 
                          
def parse_ibdiagnet_cables ( ports, issues, contents ):
    """ Parse the output of ibdiagnet ibdiagnet2.cables """
    vlog(4, 'parse_ibdiagnet_cables()')

    def sc(field, var, ctype = "string"):
	""" quick sanity check of dict field """
	if field in var:
	    return sanity_check_string(issues, 'ibdiagnet2.db_csv', field, var[field], ctype)
	else:
	    return True

    def add_port(port):
	if not 'SN' in port or not port['SN']:
	    #ignore any port that doesnt have SN
	    return

	resolve_update_port(ports, port)

    #-------------------------------------------------------
    #Port=2 Lid=0x02d7 GUID=0x0002c9030068eaf0 Port Name=gladei00ib1a/L02/U1/P2
    #-------------------------------------------------------
    #Vendor: Mellanox
    #OUI: 0x2c9
    #PN: 00W0085
    #SN: 4008537306W
    #Rev: A1
    #Length: 20 m
    #Type: 850 nm VCSEL
    #SupportedSpeed: SDR/DDR/QDR/FDR

    port = None
    for match in re.finditer(r"""
	(?!
	    [#-]+
	    [\n\r]
	)
	[\r\n]*				#all of the stanzas start with --- or ###
	(?:
	    (?![#-]+)
	    (?:
		Port=(?P<port>\d+)\s+
 		Lid=(?P<lid>\w+)\s+
		GUID=(?P<guid>\w+)\s+
		Port\ Name=(?P<port_name>.*)\s* 
		|
		(?P<field>\w*)
		\s*:\s+
		(?P<value>\w*)
	    )
	)[\r\n]+   #first real line is the label
	
	""", contents, re.VERBOSE):

	if match.group('port'):
	    if port:
		add_port(port)

	    port = {
		    'port': match.group('port'),
		    'lid': match.group('lid'),
		    'guid': match.group('guid')
		}
	else:
	    port[match.group('field')] = match.group('value')

    if (
	port and 
	sc('port', port, 'integer') and
	sc('lid', port, 'hex integer') and
	sc('guid', port, 'hex integer') and
	sc('SN', port) and
	sc('PN', port) and
	sc('LengthDesc', port)
    ):
	add_port(port)

def find_cable_by_switch_leaf_port ( ports, name, leaf, port ):
    """ Checks all of the ports for any that are not at full width or speed """

    for port in ports:
	if port['name'] == name and port['leaf'] == leaf and port['port'] == port:
	    return port

    return None

def resolve_port(ports, port):
    """ Resolves out port from ports list """
    if not port:
	vlog(4, 'unable to resolve none port')
	return None

    #match by guid (preferred match)
    if 'guid' in port and port['guid'] and port['port']:
	for pport in ports:
	    #if port['guid'] == pport['guid'] and port['port'] == pport['port']:
	    if int(port['guid'], 16) == int(pport['guid'], 16) and int(port['port']) == int(pport['port']):
		return pport
	vlog(5, 'unable to resolve port: GUID={0} PortNum={1}'.format(port['guid'], port['port']))

    #match by port label (flawed match if port names are not unique)
    if 'name' in port and port['name'] and port['port'] and port['name'] != "localhost":
 	for pport in ports:
	    if port['name'] == pport['name'] and int(port['port']) == int(pport['port']):
		match = True;

		for key in ['hca', 'leaf', 'spine']:
		    if key in port and key in pport:
			if port[key] != pport[key]:
			    match = False
		    elif (key in port) != (key in pport):
			#defined in one and not the other?
			match = False

		if match:
		    return pport

	vlog(5, 'unable to resolve port: Name={0} PortNum={1} HCA={2} Leaf={3} Spine={4}'.format(
	    port['name'], 
	    port['port'],
	    port['hca'] if 'hca' in port else None,
	    port['leaf'] if 'leaf' in port else None,
	    port['spine'] if 'spine' in port else None
	))

    vlog(4, 'unable to resolve port: {0}'.format(port))
    return None
 
def resolve_update_port(ports, port):
    """ Resolves out port from ports list and update port dictionary with searched port values """
    if not port:
	vlog(4, 'unable to resolve and update none port')
	return None

    if int(port['port']) == 0:
	vlog(4, 'ignoring loopback port {0}/P{1}'.format(port['guid'],port['port']))
	return None

    pport = resolve_port(ports, port)

    if pport:
	pport.update(port);
    else:
	vlog(4, 'unable to resolve port and update %s' % port)

    return pport
 
def parse_resolve_port(ports, label):
    """ Parses port label string and then resolves out port from ports list """
    pport = parse_port(label)
    if not pport: 
	return None

    return resolve_port(ports, pport)
