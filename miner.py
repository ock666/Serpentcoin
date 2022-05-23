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


class Miner:

    def __init__(self):
        self.mining_mode = input("Please enter mining mode: pool or solo:\n")
        self.node = input('Please enter the address of a node to begin mining:\n')

        if not os.path.isfile('data/wallet.json'):
            utils.generate_wallet()

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
            proof = random.randint(1, 9999999999)

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
        return guess_hash[:5] == "00000"

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

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine(self):

        if self.mining_mode == "pool":

            shares = []

            while True:

                last_proof = self.get_last_proof()
                proof = random.randint(1, 9999999999)
                proof_to_be_hashed = int(str(last_proof) + str(proof))

                share = {
                    'proof': proof,
                    'last_proof': last_proof,
                    'public_key_hash': self.public_key_hash,
                    'proof_hash': self.hash(proof_to_be_hashed)
                }

                shares.append(share)
                print(len(shares))
                if len(shares) >= 5000:
                    print("collected 5000 shares, now sharing with pool")

                    response = requests.post(f'http://{self.node}/submit', json=shares)

                    if response.status_code == 200:
                        print("share accepted!")

                    if response.status_code == 400:
                        print("stale share submitted, getting new proof")
                        self.get_last_proof()
                        break
                    # clear the list storing our generated shares after sharing them
                    # with the pool or receiving a stale 400 code
                    print("Share Broadcast Complete")
                    shares = []

        if self.mining_mode == 'solo':

            while True:
                last_proof = self.get_last_proof()
                proof = self.proof_of_work(last_proof)
                print("Last Proof: ", last_proof)
                print("Proof: ", proof)
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

                    response = requests.post(f'http://{self.node}/miners', json=proof_transaction_with_sig,
                                             headers=headers)

                    if response.status_code == 200:
                        print('New Block Forged! Proof Accepted ', proof)
                        time.sleep(5)

                    if response.status_code == 400:
                        print("stale proof submitted, getting new proof")


Miner = Miner()

Miner.mine()
