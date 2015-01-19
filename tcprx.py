#!/usr/bin/env python

# TCP receiver  
# Copyright Dr. Fernando Rodriguez, 2010


'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import socket, time

TCP_IP = '130.209.178.196'
TCP_PORT = 9999
BUFFER_SIZE = 1024 # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print 'Connection address:', addr
ot=time.time() #Initialize timer
tbytes=0
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    nt=time.time() #This is current time
    bytes=len(data)
    tbytes+=bytes
    print "received ", bytes," bytes [",tbytes/(1000*(nt-ot)), "kB/s ","]  --->", data[0:20], "..."  #We print only first few chars
    #conn.send(data)  # echo
conn.close()
