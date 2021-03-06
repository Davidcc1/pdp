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

class AESCipher(object):

    def __init__(self, key):
        self.bs = 16
        self.key = key

    def encrypt(self, raw):
        raw = self._pad(raw)
        #iv = Random.new().read(AES.block_size)
        #actually is random string with 16 bytes length
        iv = "LSFUw7ndObHjY2bA"
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
    """
    Generates a random string of 0 ans 1 with k length
    """
    key = ""
    for i in range(k):
        if random.random() < 0.5:
            key = key+"0"
        else:
            key = key+"1"

    key = "%32X" % int(key,2)
    print key
    return str(key)


class keys(object):
    def __init__(self,k):
        self.w = randomBinaryKey(k)
        self.z = randomBinaryKey(k)
        self.k = randomBinaryKey(k)


class dataToSend:
    """
    Class to structure all data pending to send to server
    """
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
    """
    Store each element generated by an index
    """
    i = 0
    vi = 0

    def toJson(self):
        return{
            "i": self.i,
            "vi": self.vi
        }


def permutation_iter(r, kx,nB):
    """
    Pseudo Random Permutation generates an array with length r with random data
    index, numbers between 0 and nB, all random numbers are generated with seed
    kx
    """
    aux = []
    random.seed(kx)
    for it in xrange(r):
        aux.append(random.randint(0,nB-1))

    for elem in xrange(r):
        rand = random.randint(0,r-1)
        tmp = aux[elem]
        aux[elem] = aux[rand]
        aux[rand] = tmp

    return aux


def prepare_data_to_send(dataBlock,x,new_vx):
    """
    Add to array of tokens a data tuple to send from client to server
    """
    new_element = element()
    new_element.i = x
    new_element.vi = new_vx
    dataBlock.token_array.append(new_element.toJson())


def storeKeys(jsonKeys):
    """
    Store data into a file
    """
    keys_file = open("metadata/keys"+time.strftime('%d_%m_%y-%H%M')+".txt","w")
    keys_file.write(json.dumps(jsonKeys))


def pseudoRandomFunction(key, index):
    mac =  hmac.new(key)
    mac.update(index)
    mac = mac.hexdigest()

    return mac

def AEk(k,vx,x):
    """
    Authenticated encryption scheme, encript x index concatenated with vx under key k
    then append a hash of the result of encryption.
    return the result.
    """

    aes = AESCipher(str(k))
    encrypted_vx = aes.encrypt(str(x)+vx)
    new_vx = hmac.new(k)
    new_vx.update(encrypted_vx)
    new_vx = encrypted_vx + new_vx.hexdigest()
    return new_vx


def sendDataToServer(obj):
    """
    Communication with server, obtain an object as argument and parse it to
    json, then obtain all data to send it to server
    """
    obj_json = obj.toJson()
    obj_json["mode"] = "store"
    data_string = json.dumps(obj_json)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 4000)
    print >>sys.stderr, 'connection to %s port %s' % server_address
    sock.connect(server_address)
    try:
        message = data_string
        sock.sendall(message)

        response = ''

        while True:
            data = sock.recv(1000000)
            response += data
            if len(data) < 1000000:
                break

        print >> sys.stderr, 'received "%s"' % response

    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()


def challengeServer(data_string):
    """
    Send a request to server in order to obtain keys to validate the data possession
    as string then return that string
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 4000)
    print >>sys.stderr, 'connection to %s port %s' % server_address
    sock.connect(server_address)
    try:
        message = data_string
        sock.sendall(message)

        response = ''
        while True:
            data = sock.recv(10000)
            response += data
            if len(data) < 10000:
                break

        print >> sys.stderr, 'received "%s"' % data
        return response

    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()

"""
initial execution
"""
start_time = time.time()

mode = sys.argv[1].split('=')[1]

if mode == 'store':
    input_array = sys.argv[2].split(',')
    k = int(input_array[0].split('=')[1])
    t = int(input_array[1].split('=')[1])
    r = int(input_array[2].split('=')[1])
    nB = int(input_array[3].split('=')[1])

    d = sys.argv[3]

    data = open("data/"+d, "r").read()

    size_piece = len(data)//nB
    #print data
    splited_data = textwrap.wrap(data,size_piece,break_long_words=True)
    #print splited_data
    keys = keys(k)
    dataBlock = dataToSend()
    dataBlock.saved_data = data
    for x in xrange(1,t+1):

        #generate kx = fw(x)
        kx = pseudoRandomFunction(keys.w, str(x))
        #generate cx = fz(x)
        cx = pseudoRandomFunction(keys.z, str(x))

        inputKey = str(cx)

        permuted_array = permutation_iter(r,kx, nB)

        for j in permuted_array:
            inputKey += format(splited_data[j])

        #calculate vi -> cx + D[gk(1)] + D[gk(2)] + ...
        vx = hashlib.sha256()
        vx.update(inputKey)
        vx = vx.hexdigest()

        #calculate v'i -> AEk(i,vi) : aes de x+vx concatenat amb el hash del resultat (aes de x+vx).
        new_vx = AEk(keys.k,vx,x)

        prepare_data_to_send(dataBlock,x,new_vx)


    jsonKeys = {'w':keys.w,'z':keys.z,'k':keys.k,'tokens':str(r),'nB':str(nB),'r':str(r)}
    storeKeys(jsonKeys)
    sendDataToServer(dataBlock)

elif mode == 'challenge':
    input_array = sys.argv[2].split(',')
    i = int(input_array[0].split('=')[1])
    f_data = input_array[1].split('=')[1]

    keys_file = open("metadata/keys"+f_data+".txt","r")

    data = keys_file.read()
    json_data = json.loads(data)
    r = json_data["r"]
    nB = json_data["nB"]

    #generate kx = fw(x)
    ki = pseudoRandomFunction(str(json_data["w"]), str(i))
    #generate cx = fz(x)
    ci = pseudoRandomFunction(str(json_data["z"]), str(i))

    json_to_server = {'mode': "challenge", 'ki': ki, 'ci': ci,'r':r,'nB':nB,'file':f_data,'i':i}
    str_to_server = json.dumps(json_to_server)

    check_data = challengeServer(str_to_server)

    json_checker = json.loads(check_data)
    z = json_checker["z"]
    vi = json_checker["vi"]
    k = str(json_data["k"])

    checker = AEk(k,z,i)

    if str(checker) == str(vi):
        print "DATA VERIFIED!"
    else:
        print
        print "DATA SERVER HAS DELETED OR MODIFIED"


print "time ->  " + str(time.time()-start_time) + " s"
