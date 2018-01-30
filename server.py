import socket
import sys
from socket import error as SocketError
import errno

stored_data_file = open("serverDB/data_from_client.txt","w")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost',4000)
print >>sys.stderr,'starting up on %s port %s' %server_address
sock.bind(server_address)

sock.listen(1)
while True:
    print >>sys.stderr,'waiting for connection'
    connection,client_address = sock.accept()

    try:
        print >>sys.stderr,'connection from', client_address
        while True:
            data = connection.recv(1000)
            print >>sys.stderr,'received "%s"' % data
            if data:
                print >>sys.stderr, 'sending data back to the client'
                connection.sendall("all data received")
                stored_data_file.write(data)
            else:
                print >>sys.stderr, 'sending data back to the client'
                connection.sendall("all data received")
                print >>sys.stderr, 'no more data from', client_address
                break
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise
        pass
    finally:

        connection.close()
