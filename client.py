import socket, sys, random, hmac, hashlib, binascii, os,json
import textwrap
import pyaes.aes as pyaes


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

data = open("data/"+d, "r").read()

size_piece = len(data)//nB
splited_data = textwrap.wrap(data,size_piece,break_long_words=True)
#print splited_data


def randomBinaryKey(k):
    key = ""
    for i in range(k):
        if random.random() < 0.5:
            key = key+"0"
        else:
            key = key+"1"

    key = "%32X" % int(key,2)

    return key


class keys:
    w = randomBinaryKey(k)
    z = randomBinaryKey(k)
    k = randomBinaryKey(k)

class dataToSend:
    saved_data = False
    token_array = []
    def __init__(self, load_object=False):
        if load_object:
            saved_data = load_object["data"]
            token_array = load_object["tokens"]
    def toJson(self):
        return {
            "data": self.saved_data,
            "tokens": self.token_array
        }


class element:
    i = 0
    vi = 0
    def toJson(self):
        return{
            "i": self.i,
            "vi": self.vi
        }


def permutation_iter(r, kx):

    aux = []
    for it in xrange(r):
        aux.append(it)

    #print aux
    aes = pyaes.AES(kx)
    permuted_array = aes.encrypt(aux)

    return permuted_array


def prepare_data_to_send(dataBlock,x,new_vx):
    new_element = element()
    new_element.i = x
    new_element.vi = new_vx
    dataBlock.token_array.append(new_element.toJson())


def sendDataToServer(obj):
    print obj.toJson()
    #codificar de otra forma... error en dumps utf-8
    data_string = json.dumps(obj.toJson())

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 4000)
    print >>sys.stderr, 'connection to %s port %s' % server_address
    sock.connect(server_address)
    try:
        message = data_string
        sock.sendall(message)

        amount_received = 0
        amount_expected = len(message)

        while amount_received < 1:
            data = sock.recv(1000)
            amount_received += 1
            print >> sys.stderr, 'received "%s"' % data
    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()


dataBlock = dataToSend()
dataBlock.saved_data = data
for x in xrange(1,t+1):
    #generate kx = fw(x)
    kx = hmac.new(keys.w)
    kx.update(str(x))
    kx = kx.hexdigest()

    #generate cx = fz(x)
    cx = hmac.new(keys.z)
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

    #calculate vi -> cx + D[gk(1)] + D[gk(2)] + ...
    vx = hashlib.sha256()
    vx.update(inputKey)
    vx = vx.hexdigest()

    #calculate v'i -> AEk(i,vi) : aes de x+vx concatenat amb el hash del resultat (aes de x+vx).
    aes = pyaes.AESModeOfOperationCTR(keys.z)
    encrypted_vx = aes.encrypt(str(x)+vx)
    new_vx = hmac.new(keys.z)
    new_vx.update(encrypted_vx)
    new_vx = encrypted_vx + new_vx.hexdigest()

    prepare_data_to_send(dataBlock,x,new_vx)


sendDataToServer(dataBlock)

print "wKey: " + keys.w
print "zKey: " + keys.z
print "kKey: " + keys.k
