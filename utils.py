import json
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Hash import RIPEMD160
import binascii


def response_translator(response, node):
    if response.status_code == 201:
        return 'transaction broadcast accepted by: ', node

    if response.status_code == 200:
        return 'transaction signature not valid as calculated by: ', node

    if response.status_code == 400:
        return 'transaction missing values according to: ', node

    if response.status_code == 420:
        return 'One Transaction per block, wait for next block confirmation says: ', node

    if response.status_code == 440:
        return 'Transaction already in this nodes mem-pool', node


def write_json_wallet(data, mode, filename='data/wallet.json'):
    # opens the file in write mode
    with open(filename, mode) as file:
        block_dict = json.dumps(data, indent=6)
        file.write(block_dict)


def calculate_hash(data, hash_function):
    data = bytearray(data, "utf-8")
    if hash_function == "sha256":
        h = SHA256.new()
        h.update(data)
        return h.hexdigest()
    if hash_function == "ripemd160":
        h = RIPEMD160.new()
        h.update(data)
        return h.hexdigest()

def import_wallet():
    wallet_file = json.load(open('data/wallet.json', 'r'))
    private_key = RSA.import_key(wallet_file['private key'])
    public_key = RSA.import_key(wallet_file['public key'])
    self.public_key_hex = wallet_file['public key hex']
    self.public_key_hash = wallet_file['public key hash']


def generate_wallet():

    private_key = RSA.generate(2048)
    private_key_plain = private_key.export_key("PEM")
    public_key_plain = private_key.publickey().export_key("PEM")
    public_key = private_key.publickey().export_key("DER")
    public_key_hex = binascii.hexlify(public_key).decode("utf-8")
    public_key_hash = calculate_hash(calculate_hash(public_key_hex, hash_function="sha256"),
                                              hash_function="ripemd160")

    wallet_data = {
        'private key': private_key_plain.decode(),
        'public key': public_key_plain.decode(),
        'public key hex': public_key_hex,
        'public key hash': public_key_hash
    }
    write_json_wallet(wallet_data, 'w')