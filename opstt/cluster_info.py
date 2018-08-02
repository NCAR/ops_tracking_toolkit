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
from sys import path, argv
from . import sgi_cluster
from . import ibm_cluster
import socket
import re

def get_cluster_info():
    if re.search("^(la|ch)", socket.gethostname()):
        return { 
            'vendor':	'sgi', 
            'type':	'icexa' 
        };
    if re.search("^(ys|er|js)", socket.gethostname()):
        return {
        'vendor':	'ibm',
        'type':	'1410' #idataplex
        };                   
    return None

def get_cluster_type():
    i = get_cluster_info()
    if not i:
        return None

    return i['type']

def get_cluster_vendor():
    i = get_cluster_info()
    if not i:
        return None

    return i['vendor']

def get_cluster_name():
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.get_cluster_name()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.get_cluster_name()
    return None 

def get_cluster_name_formal():
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.get_cluster_name_formal()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.get_cluster_name_formal()
    return None

def get_bmc(node):
    """ get node bmc name """
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.get_bmc()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.get_bmc()
    return None
 
def get_sm():
    """ get smc nodes """
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.get_sm()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.get_sm()
    return None

def get_ib_speed():
    """ get Infiniband network speed """
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.get_ib_speed()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.get_ib_speed()
    return None
    
def is_mgr():
    """ Is this node the cluster manager """
    if get_cluster_vendor() == "sgi":
        return sgi_cluster.is_sac()
    elif get_cluster_vendor() == "ibm": 
        return ibm_cluster.is_xcat_mgr()

    return False

