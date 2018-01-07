import socket, sys, random, hmac, hashlib, binascii, os
import textwrap
import pyaes.aes as pyaes

def comunication():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 4000)
    print >>sys.stderr, 'connection to %s port %s' % server_address
    sock.connect(server_address)
    try:
        message = 'Message 1.'
        print >>sys.stderr, 'connecting to %s port %s' %server_address
        sock.sendall(message)

        amount_received = 0
        amount_expected = len(message)

        while amount_received < amount_expected:
            data = sock.recv(16)
            amount_received += len(data)
            print >> sys.stderr, 'received "%s"' % data
    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()


def randomBinaryKey(k):
    key = ""
    for i in range(k):
        if random.random() < 0.5:
            key = key+"0"
        else:
            key = key+"1"
        key_256 = os.urandom(k/8)
        return key_256

#Pseudo-random Function
def prf(x,key):

    return 0

def permutation_iter(r, kx):

    aux = []
    for it in xrange(r):
        aux.append(it)

    print aux
    aes = pyaes.AES(kx)
    permuted_array = aes.encrypt(aux)

    return permuted_array


def getToken(cx,kx):
    return

# k-> n bits of keis
#c ?
#l output of g (PRP)
#L -> n bits of output Function f (PRF) best case is 128

# FUNCTION F -> HMAC SHA-256
# PERMUTATION G -> AES

# t -> number of tokens (possible challenges) example = 50
# r -> indices per verification example = 16

k = int(sys.argv[1])
t = int(sys.argv[2])
r = int(sys.argv[3])
nB = int(sys.argv[4])
d = sys.argv[5]

wKey = randomBinaryKey(k)
zKey = randomBinaryKey(k)
kKey = randomBinaryKey(k)

data = open("data/"+d, "r").read()


size_piece = len(data)//nB
splited_data = textwrap.wrap(data,size_piece,break_long_words=True)
print splited_data

for x in xrange(1,t):
    #generate kx = fw(x)
    kx = hmac.new(wKey)
    kx.update(str(x))
    kx = kx.hexdigest()

    #generate cx = fz(x)
    cx = hmac.new(zKey)
    cx.update(str(x))
    cx = cx.hexdigest()

    #print "hex -> "+ cx

    inputKey = str(cx)

    #Crec que es una mala permutation, ja que amb un array de [0-15] retorna valors molt superiors...
    permuted_array = permutation_iter(r,kx)
    modulo_arr = []

    for j in permuted_array:
        inputKey += format(splited_data[j%nB].encode("hex"))
        modulo_arr.append(j%nB)

    print modulo_arr
    #print inputKey
    vx = hashlib.sha256()
    vx.update(inputKey)
    vx = vx.hexdigest()

    print vx

    print len(kx)
    print len(kKey)

    aes = pyaes.AESModeOfOperationCTR(kKey)
    encrypted_vx = aes.encrypt(str(x)+vx)
    print "at start vx -> " + str(x)+vx
    print "encripted -> " + encrypted_vx
    #aes = pyaes.AESModeOfOperationCTR(kKey)
    #print "decripted -> " + aes.decrypt(encrypted_vx)
    new_vx = hmac.new(kKey)
    new_vx.update(encrypted_vx)
    new_vx = encrypted_vx + new_vx.hexdigest()

    print new_vx

#class keys:
#    w = wKey
#    z = zKey
#    k = kKey
#print lib.w


print "wKey: " + wKey
print "zKey: " + zKey
print "kKey: " + kKey

#comunication()
