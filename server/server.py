import socket
import sys, time,json, hashlib
from socket import error as SocketError
import errno

def permutation_iter(r, kx,nB):
    aux = []
    random.seed(kx)
    for it in xrange(r):
        aux.append(random.randint(0,nB-1))

    print aux
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
        data = ''

        while True:
            part = connection.recv(10000)
            data += part
            if len(part) < 10000:
                break

        print >>sys.stderr,'received "%s"' % data

        json_data = json.loads(data)
        mode = json_data["mode"]
        if mode == "store":
        	stored_data_file = open("serverDB/data_from_client"+time.strftime('%d_%m_%y-%H%M')+".txt","w")
        	print >>sys.stderr, 'sending data back to the client'
        	del json_data['mode']
        	data = json.dumps(json_data)
        	try:
        		stored_data_file.write(data)
        		connection.sendall(json_response)
        	except ValueError:
        		connection.sendall("error saving data! Try it later!")

        elif mode == "challenge":

        	#Get all elements from client request
        	ki = json_data["ki"]
        	ci = json_data["ci"]
        	r = int(json_data["r"])
        	i = json_data["i"]
        	nB = int(json_data["nB"])
        	fdate =  json_data["file"]

        	stored_data_file = open("serverDB/data_from_client"+ fdate +".txt","r")
        	data = stored_data_file.read()
        	stored_data = json.loads(data)

        	#get token with index i
        	for token in mock_data["tokens"]:
        		if token["i"] == int(i):
        			vi = token["vi"]
        			break

        	size_piece = len(stored_data["data"])//nB

        	splited_data = textwrap.wrap(stored_data["data"],size_piece,break_long_words=True)

        	permuted_array = permutation_iter(r,ki, nB)

        	for j in permuted_array:
        		inputKey += format(splited_data[j])

        	z = hashlib.sha256()
        	z.update(inputKey)
        	z = z.hexdigest()

        	json_response = {"z": z,"vi": vi}
        	json_response = json.dumps(json_response)

        	connection.sendall(json_response)


	except SocketError as e:
		if e.errno != errno.ECONNRESET:
			raise
		pass

	finally:
		connection.close()
