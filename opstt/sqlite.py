#!/usr/bin/python
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
import sqlite3
from nlog import vlog,die_now

def init(database_path):
    """ Attempt to open a SQLite database and returns the connection and cursor """
    try:
	SQL_CONNECTION = sqlite3.connect(database_path, isolation_level=None, timeout=600)
	SQL_CONNECTION.row_factory = sqlite3.Row
	SQL = SQL_CONNECTION.cursor()
	return (SQL_CONNECTION, SQL)
    except Exception as err:
	vlog(1, 'Unable to Open DB: {0}'.format(err))

    return None
 
def close(SQL_CONNECTION, SQL):
    """ Safely close a sqlite db conneciton """
    SQL.close()
    SQL_CONNECTION.close()
 
def add_column(SQL, table, column, column_type):
    """ Add a column to sqlite table if it is missing 
    this is the easy way to update tables for new features
    """

    SQL.execute('PRAGMA table_info(%s);' % (table))

    for row in SQL.fetchall():
	if row['name'] == column:
	    return True #already exists

    #SQL.execute('ALTER TABLE ? ADD ? ?;', (table, column, column_type))
    SQL.execute('ALTER TABLE %s ADD %s %s;' % (table, column, column_type))

    return True
 

