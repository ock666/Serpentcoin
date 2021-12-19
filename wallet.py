import binascii
import json
import os
import requests
from time import time
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Hash import RIPEMD160
from Crypto.Signature import pkcs1_15
import Validation



class Wallet:

    def __init__(self):

        if not os.path.isfile('data/wallet.json'):
            self.generate_wallet()
        self.unix_time = time()
        self.nodes = []

        self.node = input("Please enter the IP or domain of a node:\n")
        self.nodes.append(self.node)

        self.chain = self.get_chain()

        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']

        if not os.path.exists('data'):
            os.makedirs('data')

        if not os.path.isfile('data/wallet.json'):
            self.generate_wallet()






    def get_balance(self):
        chain_balance = Validation.enumerate_funds(self.public_key_hash, self.chain)
        if chain_balance > 0:
            return chain_balance

        if chain_balance == False:
            return 0



    def generate_wallet(self):

        private_key = RSA.generate(2048)
        private_key_plain = private_key.export_key("PEM")
        public_key_plain = private_key.publickey().export_key("PEM")
        public_key = private_key.publickey().export_key("DER")
        public_key_hex = binascii.hexlify(public_key).decode("utf-8")
        public_key_hash = self.calculate_hash(self.calculate_hash(public_key_hex, hash_function="sha256"),
                                              hash_function="ripemd160")

        wallet_data = {
            'private key': private_key_plain.decode(),
            'public key': public_key_plain.decode(),
            'public key hex': public_key_hex,
            'public key hash': public_key_hash
        }
        self.write_json(wallet_data, 'w')

    def calculate_hash(self, data, hash_function):
        data = bytearray(data, "utf-8")
        if hash_function == "sha256":
            h = SHA256.new()
            h.update(data)
            return h.hexdigest()
        if hash_function == "ripemd160":
            h = RIPEMD160.new()
            h.update(data)
            return h.hexdigest()

    def write_json(self, data, mode, filename='data/wallet.json'):
        # opens the file in write mode
        with open(filename, mode) as file:
            block_dict = json.dumps(data, indent=6)
            file.write(block_dict)

    def new_transaction(self, recipient, amount, unix_time):

        sender = self.public_key_hash
        previous_block_hash = self.get_last_block_hash()

        trans_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time_submitted': unix_time,
            'previous_block_hash': previous_block_hash,
            'public_key_hex': self.public_key_hex
        }

        hashed_trans = self.calculate_hash(json.dumps(trans_data, sort_keys=True), "sha256")

        trans_with_hash = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time_submitted': trans_data['time_submitted'],
            'previous_block_hash': previous_block_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': hashed_trans
        }

        signed_trans = self.sign(trans_with_hash)

        full_transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time_submitted': trans_data['time_submitted'],
            'previous_block_hash': previous_block_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': hashed_trans,
            'signature': signed_trans
        }
        print(json.dumps(full_transaction, indent=2))
        self.broadcast_transaction(full_transaction)
        self.chain = self.get_chain()

    def broadcast_transaction(self, transaction):

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        for node in self.nodes:
            response = requests.post(f'http://{node}/transactions/new', json=transaction, headers=headers)
            if response.status_code == 201:
                print("Transaction broadcast accepted\n", json.dumps(transaction, indent=2), "\nby ", node)

            else:
                print("Transaction broadcast denied")
                print(response)

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return signature

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")

        return signature_hex

    def get_block_height(self):
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                return chain[length - 1]['index']

    def get_last_block_hash(self):
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            return chain[length - 1]['previous_hash']

    def get_chain(self):
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')

        if response.status_code == 200:
            chain = response.json()['chain']

            return chain





wallet = Wallet()



while True:
    ##CLI API FOR WALLET
    print('Availables Funds: ', wallet.get_balance(), "\n\n\n")

    print('Welcome to the Wallet\nWhat would you like to do?: \n')
    print('1. Update the blockchain')
    print('2. Send Funds')
    print('3. Receive Funds')
    choice = int(input('Select a number: '))

    if choice == 1:
        wallet.chain = wallet.get_chain()
        print("Blockchain Updated")


    if choice == 2:
        time = Wallet.unix_time
        recipient = input('Please enter recipient address: ')
        amount = float(input('Please enter an amount: '))
        wallet.new_transaction(recipient, amount, time)


    if choice == 3:
        print('Your Address: ', wallet.public_key_hash)
