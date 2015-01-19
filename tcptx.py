#!/usr/bin/env python

# TCP transmitter
# Copyright Dr. Fernando Rodriguez, 2010


''' This program is free software: you can redistribute it and/or modify
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


import socket, sys, select

TCP_IP = '130.209.178.196'
TCP_PORT = 9999
BUFFER_SIZE = 1024
packetCount=0

def isKey():
	return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

#Initialize the TCP Connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print "TCP connection established"
print "Hit Enter to start transmission..."
while not isKey():
	pass
sys.stdin.read(1) #Need to read the character!

print "Hit Enter to stop transmission..."
##Now send a large stream of data
while not isKey():  ##Loop forever; will send packets as fast as possible
	packetCount=packetCount+1
	MESSAGE="No:"+str(packetCount)
	MESSAGE=MESSAGE+"Mary had a little lamb"*50  ##Produces 1100 bytes of text
	MESSAGE=MESSAGE[0:1024]  ##We only take 1024 bytes of it.

	s.send(MESSAGE)
	

#data = s.recv(BUFFER_SIZE)
s.close()
print "TCP connection finished."

#print "received data:", data
