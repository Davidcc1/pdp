import socket, sys, random, hmac, hashlib, binascii, os, json, base64,time
import textwrap
from Crypto import Random
from Crypto.Cipher import AES

# k-> n bits of keis
#c ?
#l output of g (PRP)
#L -> n bits of output Function f (PRF) best case is 128

# FUNCTION F -> HMAC SHA-256
# PERMUTATION G -> AES

# t -> number of tokens (possible challenges) example = 50
# r -> indices per verification example = 16
#nB -> number of blocks = 128

mode = sys.argv[1].split('=')[1]

class AESCipher(object):

    def __init__(self, key):
        self.bs = 16
        self.key = key

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


def randomBinaryKey(k):
    key = ""
    for i in range(k):
        if random.random() < 0.5:
            key = key+"0"
        else:
            key = key+"1"

    key = "%32X" % int(key,2)
    print key
    return key


class keys(object):
    def __init__(self,k):
        self.w = randomBinaryKey(k)
        self.z = randomBinaryKey(k)
        self.k = randomBinaryKey(k)


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

    random.seed(kx)
    for elem in xrange(r):
        rand = random.randint(0,r-1)
        tmp = aux[elem]
        aux[elem] = aux[rand]
        aux[rand] = tmp

    return aux


def prepare_data_to_send(dataBlock,x,new_vx):
    new_element = element()
    new_element.i = x
    new_element.vi = new_vx
    dataBlock.token_array.append(new_element.toJson())

def storeKeys(jsonKeys):
    keys_file = open("client/keys"+time.strftime('%d_%m_%y-%H%M')+".txt","w")
    keys_file.write(json.dumps(jsonKeys))


def sendDataToServer(obj):
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
            data = sock.recv(100000)
            amount_received += 1
            print >> sys.stderr, 'received "%s"' % data
    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()


if mode == 'store':
    input_array = sys.argv[2].split(',')
    k = int(input_array[0].split('=')[1])
    t = int(input_array[1].split('=')[1])
    r = int(input_array[2].split('=')[1])
    nB = int(input_array[3].split('=')[1])

    d = sys.argv[3]

    data = open("data/"+d, "r").read()

    size_piece = len(data)//nB

    splited_data = textwrap.wrap(data,size_piece,break_long_words=True)
    keys = keys(k)
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


        inputKey = str(cx)

        #Crec que es una mala permutation, ja que amb un array de [0-15] retorna valors molt superiors...
        permuted_array = permutation_iter(r,kx)

        for j in permuted_array:
            inputKey += format(splited_data[j])
        print inputKey
        #calculate vi -> cx + D[gk(1)] + D[gk(2)] + ...
        vx = hashlib.sha256()
        vx.update(inputKey)
        vx = vx.hexdigest()
        print vx

        #calculate v'i -> AEk(i,vi) : aes de x+vx concatenat amb el hash del resultat (aes de x+vx).
        aes = AESCipher(keys.z)
        encrypted_vx = aes.encrypt(str(x)+vx)
        new_vx = hmac.new(keys.z)
        new_vx.update(encrypted_vx)
        new_vx = encrypted_vx + new_vx.hexdigest()

        prepare_data_to_send(dataBlock,x,new_vx)


    jsonKeys = {'w':keys.w,'z':keys.z,'k':keys.k,'tokens':str(r)}
    storeKeys(jsonKeys)
    sendDataToServer(dataBlock)

    print "wKey: " + keys.w
    print "zKey: " + keys.z
    print "kKey: " + keys.k
elif mode == 'challenge':
    print 'not implemented yet'
