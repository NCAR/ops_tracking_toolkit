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
import os
import time
import fcntl
from .nlog import vlog,die_now

def _try_lock_once(fd):
    """ Try to get lock once """
    try:
	ret = fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
	vlog(5, 'flock ret: {0}'.format(ret))
	if ret == None:
	    return True
    except Exception as exp:
	vlog(5, 'flock exception: {0}'.format(exp))
	return False
    except:
	return False

    return False

def try_lock(file_path, tries = 5):
    """ Open file and try to get lock tries times 
	The file_descriptor must remain in scope for lock to hold
    """
    try:
	file_descriptor = open(file_path, 'a')
    except Exception as exp:
	vlog(5, 'unable to open {0} with exception: {1}'.format(file_path, exp))
	return False

    for x in range(0, tries):
	if _try_lock_once(file_descriptor):
	    vlog(5, 'lock obtained')
	    return file_descriptor 
	elif x != tries: 
	    vlog(4, 'attemping {0} of {1} to get lock failed. retrying in {2} seconds.'.format(x, tries, x))
	    time.sleep(x)     

    return False

