import json
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Hash import RIPEMD160
import binascii
import hashlib

class Hash:

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def calculate_hash(data, hash_function):
        """
        function for creating hashes of keys for wallet generation
        returns a SHA256 or RIPEMD160 hash depending
        on the hash function selected in the function call.
        """
        data = bytearray(data, "utf-8")
        if hash_function == "sha256":
            h = SHA256.new()
            h.update(data)
            return h.hexdigest()
        if hash_function == "ripemd160":
            h = RIPEMD160.new()
            h.update(data)
            return h.hexdigest()

class Write:

    @staticmethod
    def write_json_wallet(data, mode, filename='data/wallet.json'):
        """
        write a generated wallet to wallet.json
        """
        # opens the file in write mode
        with open(filename, mode) as file:
            block_dict = json.dumps(data, indent=6)
            file.write(block_dict)

    @staticmethod
    def write_chain(data, filename='data/chain.json'):
        """
        appends block to chain.json
        """
        # opens the file in append mode
        with open(filename, 'a') as file:
            block_dict = json.dumps(data)
            file.write(block_dict)
            file.write('\n')

class Generate:
    @staticmethod
    def generate_wallet():
        """
        function for the generation of wallets
        """
        private_key = RSA.generate(4096)
        private_key_plain = private_key.export_key("PEM")
        public_key_plain = private_key.publickey().export_key("PEM")
        public_key = private_key.publickey().export_key("DER")
        public_key_hex = binascii.hexlify(public_key).decode("utf-8")
        public_key_hash = Hash.calculate_hash(Hash.calculate_hash(public_key_hex, hash_function="sha256"),
                                              hash_function="ripemd160")

        wallet_data = {
            'private key': private_key_plain.decode(),
            'public key': public_key_plain.decode(),
            'public key hex': public_key_hex,
            'public key hash': public_key_hash
        }
        Write.write_json_wallet(data=wallet_data, mode='w')


Hash()
