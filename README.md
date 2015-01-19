# TCPDLY
This software provides a mechanism for simulating large delays in the delivery of TCP/IP packets.  This is useful for developing and testing communication protocols which will be subject to such delays when deployed so their behaviour can be simulated within a laboratory environment.  For instance, this software has been used to observe and tune how the linux TCP/IP stack behaves on large geographically dispersed networks.

Three scripts are provided.  The first two `tcptx.py` and `tcprx.py` provide a simple command line bridge to transmit, receive and display text as it is typed.   The `comsdly.py` program, on the other hand, implements the network delay.   

#How does it work?
The communication delay is implemented by setting up a raw TAP interface and changing the routing tables in the host so that all traffic is directed to it.   The interfaces are bridged by the program, which reads, timestamps and buffer packets from the input interface (using a FIFO), and outputs them after the specified delay has elapsed.

#How do I use it?
Simply run the script and specify the desired delay:
`comsdly -d 3`
The script will try to clean after itself, however this may not work in systems with complex networks, VPNs or custom routing tables defined.

