import socket
import sys, time,json
from socket import error as SocketError
import errno

def permutation_iter(r, kx):
    aux = []
    for it in xrange(r):
        aux.append(it)

    random.seed(kx)
    for elem in xrange(r):
        rand = random.randint(0,r-1)
        tmp = aux[elem]
        aux[elem] = aux[rand]
        aux[rand] = tmp

    return aux

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
            data = connection.recv(100000)
            print >>sys.stderr,'received "%s"' % data
            if data:
                json_data = json.loads(data)
                mode = json_data["mode"]
                if mode == "store":
                    stored_data_file = open("serverDB/data_from_client"+time.strftime('%d_%m_%y-%H%M')+".txt","w")
                    print >>sys.stderr, 'sending data back to the client'
                    connection.sendall("mode is -> " + mode)
                    del json_data['mode']
                    data = json.dumps(json_data)
                    stored_data_file.write(data)

                elif mode == "challenge":
                    ki = json_data["ki"]
                    ci = json_data["ci"]

                    connection.sendall("response")

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
