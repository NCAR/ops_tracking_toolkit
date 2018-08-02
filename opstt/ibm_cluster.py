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

def get_cluster_name():
    if re.search("^ys", socket.gethostname()):
        return 'yellowstone'
    elif re.search("^js", socket.gethostname()):
        return 'jellystone'
    elif re.search("^er", socket.gethostname()):
        return 'erebus'
    return None

def get_cluster_name_formal():
    if re.search("^ys", socket.gethostname()):
        return 'Yellowstone'
    elif re.search("^js", socket.gethostname()):
        return 'Jellystone'
    elif re.search("^er", socket.gethostname()):
        return 'Erebus'
    return None        
 
def is_xcat_mgr():
    host = socket.gethostname()

    if host == 'ysmgt1' or host == 'ermgt1' or host == 'jsmgt1':
        return True
    else:
        return False
  
def get_sm():
    """ get smc nodes """

    host = socket.gethostname()

    if host == 'jsmgt1':
        return ['jsufm1', 'jsufm2']
    elif host == 'ysmgt1':
        return ['ysmgt1', 'ysmgt2']
    elif host == 'ermgt1':
        return ['erufm1', 'erufm2']
    return None                    

def get_bmc(node):
    """ get node bmc name """

    return "{0}-imm".format(node)

def get_ib_speed():
    """ get Infiniband network speed """

    host = socket.gethostname()

    if host == 'ysmgt1':
        return {'speed': 'FDR', 'link': 14, 'width': '4x'};
    elif host == 'ermgt1':
        return {'speed': 'FDR10', 'link': 10, 'width': '4x'};
    elif host == 'jsmgt1':
        return {'speed': 'FDR', 'link': 14, 'width': '4x'};
    return None
     
