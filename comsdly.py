#!/usr/bin/python

# TCP Communication delay                       
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

import sys, os, fcntl, struct, socket, time, Queue, thread, getopt

TUNSETIFF   = 0x400454ca
IFF_TUN     = 0x0001
IFF_TAP 	= 0x0002
IFF_NOPI	= 0x1000
ETH_P_ALL	= 3
IFF_TOUSE	= IFF_NOPI | IFF_TAP


FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(src, length=8):
    N=0; result=''
    while src:
       s,src = src[:length],src[length:]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
       N+=length
    return result

class interface:  ##defines basic interface functions
	def __init__(self, interfaceName):
		self.interfaceName=interfaceName
		self.mac=None
		self.IP=None
		self.Mask=None
		self.routes=None
		
	def setMAC(self, MAC):
		os.popen("/sbin/ifconfig "+ self.interfaceName+ " hw ether "+ MAC)
		
	def getMAC(self):
		if(self.mac!=None):
			return self.mac
		for line in os.popen("/sbin/ifconfig"):
			if line.find(self.interfaceName) > -1:
				self.mac = line.split()[4]
			break 
		if self.mac==None:
			print "Could not get MAC address!"
			os.exit(1)
		return self.mac
		
	def getIP(self):
		if(self.IP==None):
			for line in os.popen("/sbin/ifconfig " + self.interfaceName):
				if line.find("inet addr") > -1:
					self.IP = line.split()[1].split(':')[1]
					self.Mask=line.split()[3].split(':')[1]
					break 
		return ((self.IP, self.Mask))
			
	def setIP(self, IP, MASK=None):
		self.getIP() #get our current IP before modifying (so we can restore)
		self.getROUTES()
		if MASK==None:
			os.popen("/sbin/ifconfig "+ self.interfaceName+" "+IP)
		else:
			os.popen("/sbin/ifconfig "+ self.interfaceName+" "+IP+ " netmask "+ MASK)
	
	def restoreIP(self):
		if (self.IP != None):
			self.setIP(self.IP, self.Mask)
		
	def getROUTES(self):
		if(self.routes!=None):
			return self.routes
		self.routes=[]
		for line in os.popen("/sbin/route -n"):
			if line.find(self.interfaceName) > -1:
				dest = line.split()[0]
				gw=line.split()[1]
				mask=line.split()[2]
				self.routes.append((dest, gw, mask))
		return self.routes
				
	def setROUTES(self, routes):
		for t_dgm in routes:
			(dest, gw, mask)=t_dgm
			if gw!='0.0.0.0':
				#print "/sbin/route add -net "+dest+" netmask "+mask+" gw "+gw+" dev "+self.interfaceName
				os.popen("/sbin/route add -net "+dest+" netmask "+mask+" gw "+gw+" dev "+self.interfaceName)
			else:
				#print "/sbin/route add -net "+dest+" netmask "+mask+" dev "+self.interfaceName
				os.popen("/sbin/route add -net "+dest+" netmask "+mask+" dev "+self.interfaceName)
			
	def restoreROUTES(self):
		if(self.routes!=None):
			self.setROUTES(self.routes)

class raw_tap(interface):
	def __init__(self,interfaceName):
		interface.__init__(self, interfaceName)
		self.netDeviceFD = os.open("/dev/net/tun", os.O_RDWR)
		ifs = fcntl.ioctl(self.netDeviceFD, TUNSETIFF, struct.pack("16sH", interfaceName, IFF_TOUSE))
		print "Using interface %s" % ifs[:16].strip("\x00")
		#self.socket=socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
		#self.socket.bind((str(ifs[:16].strip("\x00") ), ETH_P_ALL))
		
	def Read(self):
		packet = os.read(self.netDeviceFD,1600)
		return packet
		
	def Write(self, packet):
		os.write(self.netDeviceFD, packet)
		
		
		
class raw_eth(interface):
	def __init__(self, interfaceName):
		interface.__init__(self, interfaceName)
		try:
			self.socket=socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
			self.socket.bind((interfaceName, ETH_P_ALL))
			
		except socket.error,msg:
			print msg
			os.exit(1)
	def Read(self):
		return self.socket.recv(1600)
	
	def Write(self,packet):
		self.socket.sendall(packet)
		

		
class Delayed_Bridge:
	def __init__(self, tunif, ethif, delay, bw):
		self.bw=bw ##BW is limited by delaying readings by this ammount of time
		self.delay=delay
		#Create buffers to hold (time, packet) tuples:
		self.eth2tun=Queue.Queue()
		self.tun2eth=Queue.Queue()
		
		self.tun=raw_tap(tunif)
		self.eth=raw_eth(ethif)
		##Create threads
	
				
		thread.start_new_thread(self.T_tunrx, ((1,)))
		thread.start_new_thread(self.T_ethrx, ((2,)))
		thread.start_new_thread(self.T_tuntx, ((3,)))
		thread.start_new_thread(self.T_ethtx, ((4,)))
		
	def set_delay(self, delay):
		self.delay=delay
		
	def set_bandwidth(self, bw):
		self.bw=bw
						
	def T_tunrx(self, id):
		timesent=0
		while True:
			to=timesent+self.bw-time.time() ##Calculate time to wait for BW control
			if (to>0):
				time.sleep(to)
			p=self.tun.Read()
			self.tun2eth.put((time.time(), p))
			timesent=time.time()
			#self.eth.Write(p)
			#print "QUEUED TUN -> ETH" , len(p), " bytes."
			
	def T_ethrx(self,id):
		timesent=0
		while True:
			to=timesent+self.bw-time.time() ##Calculate time to wait for BW control
			if (to>0):
				time.sleep(to)
			p=self.eth.Read()
			self.eth2tun.put((time.time(), p))
			timesent=time.time()
			#sel	f.tun.Write(p)
			#print "QUEUED ETH -> TUN ", len(p)," bytes."
			#print dump(p)
			
	def T_tuntx(self,id):
		#print "TUN TX THREAD is alive"
		while True:
					(t,p)=self.eth2tun.get()
					to=t+self.delay-time.time()
					
					#print "Tun tx thread has data for d=",to
					
					if (to>0):
						time.sleep(to)
					self.tun.Write(p)
					#print "SENT ETH -> TUN ", len(p)," bytes."
					#print dump(p)
					
	def T_ethtx(self,id):
		#print "ETH TX THREAD is alive"
		while True:
					(t,p)=self.tun2eth.get()
					#print "ETH tx thread has data"
					to=t+self.delay-time.time()
					if (to>0):
						time.sleep(to)
					self.eth.Write(p)
					#print "SENT TUN -> ETH ", len(p)," bytes."
					#print dump(p)

def usage():
	print 
	print "comsdly  -i internal_interface -x external_interface -d delay(each way) -b bandwidth"
	print
	print "Notes:"
	print "* internal interface is tapx (i.e. tap0, or tap1 or tap2 ...)"
	print "* bandwidth control is achieved by pacing the reading of packets"
	print "  so -b specifies the minimum delay between readings."
				
def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:x:d:b:", ["help", "internal=","external=","delay=", "bandwidth="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)
	internal = "tap0"
	external = "eth0"
	delay=0
	bandwidth=0
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-i", "--internal"):
			internal = a
		elif o in ("-x", "--external"):
			external = a
		elif o in ("-d", "--delay"):
			delay=float(a)
		elif o in ("-b", "--bandwidth"):
			bandwidth=float(a)
			print "WARNING:  BANDWIDTH CONTROL IS EXPERIMENTAL."
		else:
			assert False, "unhandled option"


	print "COMSDLY - (c) Dr. Fernando Rodriguez, 2009, University of Glasgow."
	print "Starting comsdly with the following parameters:"
	print "Internal interface is:  ", internal
	print "External interface is:  ", external
	print "Packets will be delayed (each way) by:  ", delay, " seconds."
	print "Bandwidth will be limited by pacing reads at no more than ", bandwidth, " seconds (between reads)."
	print
	mybridge=Delayed_Bridge(internal, external, delay, bandwidth)
	mybridge.tun.setMAC(mybridge.eth.getMAC())  ##Copy MAC address
	ip,mask=mybridge.eth.getIP()
	mybridge.tun.setIP(ip,mask)

	ethroutes=mybridge.eth.getROUTES()
	mybridge.eth.setIP('0.0.0.0')  ##Turns off eth0 IP stack

	mybridge.tun.setROUTES(ethroutes)


	raw_input ("NET DELAYS CONTROL ACTIVE. Press any key to stop")
	mybridge.eth.restoreIP()
	mybridge.eth.restoreROUTES()



if __name__ == "__main__":
	main()
