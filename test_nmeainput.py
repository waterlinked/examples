import socket
import sys
import time

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(sock, data):
    address = ('localhost', 10110)
    sent = sock.sendto(data, address)
    time.sleep(0.1)


# Send position
send(sock, "$GPGGA,172814.0,3723.46587704,N,12202.26957864,W,2,6,1.2,18.893,M,-25.669,M,2.0,0031*4F\n")

# Send heading HDT
send(sock, "$IIHDT,91.8,T*12\n")

# Send heading HDG
send(sock, "$HCHDG,205.2,,,2.7,W\n")

# Send heading HDM
send(sock, "$HCHDM,205.2,M\n")
