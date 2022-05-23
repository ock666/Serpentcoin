import binascii
import hashlib
import json
from time import time
from urllib.parse import urlparse
import Validation
import os
import requests
from Crypto.Signature import pkcs1_15
from flask import Flask, jsonify, request
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import utils
import logging


class pool:
    def __init__(self):
        # silence flask console
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # init variables
        self.chain = []
        self.miners = []
        self.shares = []
        self.unpaid_rewards = {}
        self.transactions = []
        self.node_address = input("Please enter the address of a node\n")
        self.port = 6000
        self.unix_time = time()

        # what to do if the directory 'data' is not present, if not present; creates it.
        if not os.path.exists('data'):
            os.makedirs('data')

        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/wallet.json'):
            utils.generate_wallet()

        # attempting to open wallet file
        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.pool_identifier = wallet_file['public key hash']
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']

    # functions to get different chain data from the blockchain
    def get_chain(self):
        response = requests.get(f'http://{self.node_address}/chain')
        if response.status_code == 200:
            return response.json()['chain']

    def get_last_block_hash(self):
        response = requests.get(f'http://{self.node_address}/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            return chain[length - 1]['current_hash']

    def get_last_block(self):
        response = requests.get(f'http://{self.node_address}/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            return chain[length - 1]

    def get_last_proof(self):
        response = requests.get(f'http://{self.node_address}/proof')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't obtain proof")

    # functions for transactions

    def new_transaction(self, recipient, amount, unix_time):
        sender = self.pool_identifier
        previous_block_hash = self.get_last_block_hash()
        trans_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time_submitted': unix_time,
            'previous_block_hash': previous_block_hash,
            'public_key_hex': self.public_key_hex
        }

        hashed_trans = self.hash(trans_data)

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
        if self.broadcast_transaction(full_transaction):
            self.chain = self.get_chain()
            return True
        else:
            self.chain = self.get_chain()
            return False

    def broadcast_transaction(self, transaction):

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


        response = requests.post(f'http://{self.node_address}/transactions/new', json=transaction, headers=headers)
        if response.status_code == 201:
            return True

        else:
            return False

    # functions for cryptographic verification
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
        return guess_hash[:6] == "000000"

    def hash(self, block):
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return signature

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")

        return signature_hex

    def send_proof(self, proof, prev_proof):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        proof_transaction = {
            'proof': proof,
            'last_proof': prev_proof,
            'public_key_hash': self.pool_identifier,
            'public_key_hex': self.public_key_hex,
            'previous_block_hash': self.get_last_block_hash()
        }

        proof_signature = self.sign(proof_transaction)

        proof_transaction_with_sig = {
            'proof': proof,
            'last_proof': prev_proof,
            'public_key_hash': self.pool_identifier,
            'public_key_hex': self.public_key_hex,
            'previous_block_hash': self.get_last_block_hash(),
            'signature': proof_signature
        }

        response = requests.post(f'http://{self.node_address}/miners', json=proof_transaction_with_sig, headers=headers)

        if response.status_code == 200:
            print('New Block Forged! Proof Accepted ', proof)

        if response.status_code == 400:
            print("stale proof submitted, getting new proof")

    # Share calculations

    def count_shares(self, shares):
        addresses = {}

        for share in shares:
            address = share['address']
            if address not in addresses:
                addresses[address] = 1
            if address in addresses:
                addresses[address] += 1

        return addresses

    def calculate_split(self, shares):
        total_shares = len(self.shares)
        print(total_shares)
        for address in shares:
            block_reward = 10
            contributed = shares.get(address)
            print(address)
            print("total shares: ", contributed)
            share = contributed / total_shares
            print("share of reward: ", share)
            pool_fee = 0.5
            total_reward = (block_reward * share) - pool_fee
            print("total reward: ", total_reward)
            if address in self.unpaid_rewards:
                self.unpaid_rewards[address] += total_reward
            else:
                self.unpaid_rewards[address] = total_reward

    def dispense_reward(self, address, amount):
        unix_time = time()
        confirmed = self.new_transaction(recipient=address, amount=amount, unix_time=unix_time)
        if confirmed:
            self.unpaid_rewards[address] = 0








# Node instance
app = Flask(__name__)

pool = pool()


@app.route('/proof', methods=['GET'])
def last_proof():
    proof = pool.get_last_proof()
    return jsonify(proof), 200


@app.route('/submit', methods=['POST'])
def share_submit():
    values = request.get_json()
    last_proof = pool.get_last_proof()
    share_last_proof = values['last_proof']
    tried_proof = values['proof']
    hash = values['proof_hash']
    share_address = values['public_key_hash']

    proof_to_be_hashed = int(str(last_proof) + str(tried_proof))


    share = {
        'address': share_address,
        'last_proof': last_proof,
        'tried_proof': tried_proof,
        'hash': hash
    }

    if last_proof != share_last_proof:
        print("stale share")
        return "stale share", 400

    if pool.hash(proof_to_be_hashed) != hash:
        print('invalid share')
        return "invalid share", 400

    if pool.valid_proof(last_proof, tried_proof):
        print("Proof Found!")
        pool.shares.append(share)
        pool.send_proof(proof=tried_proof, prev_proof=share_last_proof)

        share_dict = pool.count_shares(pool.shares)
        pool.calculate_split(share_dict)
        #reset the share list
        pool.shares = []
        print(pool.unpaid_rewards)
        for address in pool.unpaid_rewards:
            amount = pool.unpaid_rewards.get(address)
            if amount > 100:
                pool.dispense_reward(address, amount)
                break

    if share in pool.shares:
        print('share already in list')
        return "stale share", 400

    else:
        pool.shares.append(share)
        return "share accepted", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=pool.port)
