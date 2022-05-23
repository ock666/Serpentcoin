import hashlib
import time
import binascii
import requests
import os
import json
import utils
from Crypto.PublicKey import RSA
import random
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import threading

class Miner:

    def __init__(self):

        self.node = input('Please enter the address of a node to begin mining:\n')

        if not os.path.isfile('data/wallet.json'):
            utils.generate_wallet()

        threading.Timer.daemon = True


        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']


    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        """

        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            proof += 1                     #random.randint(1, 999999999999)


        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :return: True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:7] == "0000000"


    def get_last_block(self):

        response = requests.get(f'http://{self.node}/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            return chain[length - 1]

    def get_last_proof(self):
        response = requests.get(f'http://{self.node}/proof')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't obtain proof")



    def get_last_hash(self):
        last_block = self.get_last_block()
        last_block_hash = last_block['current_hash']
        return last_block_hash

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return signature

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")
        return signature_hex





    def mine(self):
        while True:
            last_proof = self.get_last_proof()
            print("Last Proof: ", last_proof)

            proof = self.proof_of_work(last_proof)


            if self.valid_proof(last_proof, proof):
                print('Proof Found: ', proof)
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

                proof_transaction = {
                    'proof': proof,
                    'last_proof': last_proof,
                    'public_key_hash': self.public_key_hash,
                    'public_key_hex': self.public_key_hex,
                    'previous_block_hash': self.get_last_hash()
                }

                proof_signature = self.sign(proof_transaction)

                proof_transaction_with_sig = {
                    'proof': proof,
                    'last_proof': last_proof,
                    'public_key_hash': self.public_key_hash,
                    'public_key_hex': self.public_key_hex,
                    'previous_block_hash': self.get_last_hash(),
                    'signature': proof_signature
                }

                response = requests.post(f'http://{self.node}/miners', json=proof_transaction_with_sig, headers=headers)

                if response.status_code == 200:
                    print('New Block Forged! Proof Accepted ', proof)
                    time.sleep(5)

                if response.status_code == 400:
                    print("stale proof submitted, getting new proof")



Miner = Miner()

Miner.mine()

