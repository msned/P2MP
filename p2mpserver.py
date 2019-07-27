"""
The server file for recieving files
@Author: Mark Snedecor
"""

import sys
import struct
import socket
import random

#Port number
port = 7735

#Filename to store
filename = ""

#Probability of losing a packet
lossProb = 0

#Expected Seq
expSeq = 0

#Value for an acknowledgement packet, equi to 1010101010101010
ackVal = 43690

#calculates checksum for data
def checkCheckSum(data, check):
    dataseg = data.decode('latin-1')
    dataSeg = dataseg.encode('utf-16')
    total = 0
    for seg in dataSeg:
        total += seg
        carry= total >> 16
        total = total & 0xffff
        total += carry 
    complementCheck = (total + check)
    if complementCheck == 0xffff:
        return False
    return True

#Receive data from client
def rdt_recv():
    global expSeq
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    print('\nWaiting for data')
    with open(filename, 'wb') as fileWrite:
        while(True):
            data, client = sock.recvfrom(4096)
            dropPacket = random.random()
            if dropPacket > lossProb:
                header = struct.unpack('IHH', data[:8])
                fileContent = data[8:]
                if not data:
                    break

                corrupt = checkCheckSum(fileContent, header[1])
                if header[0] == expSeq and corrupt == False:
                    sendAck(expSeq, sock, client)
                    fileWrite.write(fileContent)
                    expSeq += 1
                elif(header[2] == 0):
                    break
                else:
                    sendAck(expSeq - 1, sock, client)
            else:
                print("Packet loss, sequence number = " + str(expSeq))
    fileWrite.close()
    sock.close()

#Send ack packet back
def sendAck(seq, sock, client):
    message = struct.pack('IHH', seq, 0, ackVal)
    sock.sendto(message, client)

"""
Main method of server
"""
if __name__ == "__main__":
    port = int(sys.argv[1])
    filename = sys.argv[2]
    lossProb = float(sys.argv[3])

    rdt_recv()

