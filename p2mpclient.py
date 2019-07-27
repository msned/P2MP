"""
The client/sender file for p2mp
@author: Mark Snedecor
"""
import socket
import time
import sys
import struct
from threading import Thread, BoundedSemaphore
import ctypes

# The known port for receiving servers
receivePort = 7735

#List of servers to receive
servers = []

#List of servers that have acked
ackServers = []

#Name of file to transfer
filename = ""

#MSS size
MSS = 0

#Number of packets sent
sequenceNumber = -1

#Value for a data packet, equi to 0101010101010101
dataVal = 21845

#Value for an acknowledgement packet, equi to 1010101010101010
ackVal = 43690

#Ack packets per segment burst
acksRecieved = 0

# Semaphore for accessing ack number
ackSem = BoundedSemaphore(1)

# Semaphore for accessing ack server list
ackServerSem = BoundedSemaphore(1)

#Time before resending packets
timeoutTime = .5

#Message to send
segMessage = None

#Variable that lets threads know the program is done
running = True


#Creates bytes object for header
def createHeader(check, done):
    checksum = check
    typeD = dataVal
    if done == True:
        typeD = 0
    return struct.pack('IHH', sequenceNumber + 1, checksum, typeD)

#Handling method for threads
def threadSendMessage(serv, sock, port, index):
    global segVal
    global timeoutTime

    #Local tracking of sequence
    locSeq = -1

    while running == True:
        while(locSeq == sequenceNumber and running == True):
            pass
        if running is False:
            break
        sendMessage(segMessage, serv[1], sock, port)
        receiveAck(sock)

        #Remove server from current list of unacked servers
        ackServerSem.acquire()
        try:
            ackServers.remove(serv)
        except:
            pass 
        ackServerSem.release()

        locSeq += 1

    return

#Method for receiving acks
def receiveAck(sock):
    global acksRecieved
    global receiveTime
    while(True):
        data, server = sock.recvfrom(8)
        ackFields = struct.unpack('IHH', data)
        if(ackFields[2] == ackVal and ackFields[0] == sequenceNumber):
            ackSem.acquire()
            acksRecieved += 1
            ackSem.release()
            return

#Function sends a message
def sendMessage(message, serv, sock, port):
    sock.sendto(message, (serv, port))

#calculates checksum for data
def createCheckSum(data):
    dataseg = data.decode('latin-1')
    dataSeg = dataseg.encode('utf-16')
    total = 0
    for seg in dataSeg:
        total += seg
        carry= total >> 16
        total = total & 0xffff
        total += carry 
    return (0xffff -total)

#Method for sending packets to multiple servers
def rdt_send():
    global ackServers
    global acksRecieved
    global sequenceNumber
    global timeoutTime
    global segMessage
    global running

    beginTransfer = time.time()
    #Open file to be transfered
    transferFile = open(filename, 'rb')
    bufferData = transferFile.read(MSS)

    avgTime = 0
    sockets = []
    threads = []
    for i in range(0, len(servers)):
        #Create UDP socket
        sockets.append(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        threads.append(Thread(target=threadSendMessage, args=(servers[i], sockets[i], receivePort + i, i)))
        threads[i].start()
        

    #read in data while file has some
    while(bufferData):
        ackServers = servers.copy()
        checks = createCheckSum(bufferData)
        message = createHeader(checks, False) + bufferData
        
        #Set the new message
        segMessage = message

        #Start the new segment
        sequenceNumber += 1
        
        #Wait for the timeout time for acks
        start = time.time()
        while((time.time() - start) < timeoutTime and acksRecieved != len(servers)):
            pass
        while(acksRecieved != len(servers)):
            #Goes through unacknowledged servers and resends message
            ackServerSem.acquire()
            for serv in ackServers:
                index = servers.index(serv)
                print("Timeout, sequence number = " + str(sequenceNumber))
                sendMessage(message, serv[1], sockets[index], receivePort + index)
            ackServerSem.release()

            start = time.time()
            while((time.time() - start) < timeoutTime and acksRecieved != len(servers)):
                pass

        avgTime += (time.time() - start)
        #Update Timeout Time
        if sequenceNumber % 10 == 0 and sequenceNumber != 0:
            avgTime  = avgTime / 10
            timeoutTime = avgTime * 2.5
            avgTime = 0
            if timeoutTime > .5:
                timeoutTime = .5

        #Reset values
        acksRecieved = 0
        bufferData = transferFile.read(MSS)


    totalDelay = time.time() - beginTransfer
    running = False
    #print("\nTotal delay: " + str(totalDelay) + '\n')
    #Send message to get server to close
    for i in range(0, len(servers)):
        sockets[i].close()
        threads[i].join()

    time.sleep(1)
    for i in range(0, len(servers)):
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        endHeader = createHeader(0, True)
        sendMessage(endHeader, servers[i][1], sock, receivePort + i)
        sock.close()

"""
Main method of client
"""
if __name__ == "__main__":
    #Read in command line arguments
    for argu in range(1, len(sys.argv) - 3):
        hostname = ("server{}").format(argu)
        servers.append((hostname, sys.argv[argu]))
    receivePort = int(sys.argv[-3])
    filename = sys.argv[-2]
    MSS = int(sys.argv[-1]) - 8

    rdt_send()
    