Both client and server were written in Python 3.7

1) First start the p2mp servers on their respective machines with the follwoing command:

-python p2mpserver port# file-name p

2) Make sure they are running on the 7735 port

3) Find IP addresses of servers

4) Start the client with the server IPs, 7735, the file to transfer, and # bytes

 -python p2mpclient server-1 server-2 server-3 server-port# file-name MSS 

5) When done transmitting the client will exit and the servers will close when done writing