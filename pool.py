import random
import binascii
import hashlib
import json
from time import time
from tqdm import tqdm
import os
import requests
from Crypto.Signature import pkcs1_15
from flask import Flask, jsonify, request
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from src.utils import Generate
import logging
import Validation
from multiprocessing import Process



class pool:
    def __init__(self):
        # silence flask console
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # init variables
        self.chain = []
        self.node_address = input("Please enter the address of a node\n")
        self.lower_proof_range = 0
        self.upper_proof_range = 1000000
        self.unchecked_range = range(self.lower_proof_range, self.upper_proof_range)
        self.current_index = self.get_index()
        self.share_dict = {}
        self.unpaid_rewards = {}
        self.transactions = []

        self.port = 6000
        self.unix_time = time()
        self.difficulty = self.get_difficulty()
        # what to do if the directory 'data' is not present, if not present; creates it.
        if not os.path.exists('data'):
            os.makedirs('data')

        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/wallet.json'):
            Generate.generate_wallet()



        print(f'current chain difficulty {self.difficulty}')

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

    def get_difficulty(self):
        response = requests.get(f'http://{self.node_address}/difficulty')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't get difficulty")


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

    def get_index(self):
        last_block = self.get_last_block()
        return last_block['index']

    def get_last_proof(self):
        response = requests.get(f'http://{self.node_address}/proof')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't obtain proof")

    def get_mempool(self):
        response = requests.get(f'http://{self.node_address}/mempool')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't obtain mem-pool")

    def get_fees(self):
        mempool = self.get_mempool()
        mempool_fees = 0
        for transaction in mempool:
            fee = transaction['fee']
            mempool_fees += fee
        print("Total block fees: ", mempool_fees)
        return mempool_fees

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

        total_bytes = self.calculate_bytes(trans_data)
        fee = self.calculate_fee(total_bytes)

        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
            'time_submitted': trans_data['time_submitted'],
            'previous_block_hash': previous_block_hash,
            'public_key_hex': self.public_key_hex
        }

        hashed_trans = self.hash(transaction)

        trans_with_hash = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
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
            'fee': fee,
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
        valid_guess = ""
        for i in range(pool.difficulty):
            valid_guess += "0"
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:pool.difficulty] == valid_guess

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
            return True

        if response.status_code == 400:
            print("stale proof submitted, getting new proof")
            return False

    # Fee calculations
    def calculate_bytes(self, transaction):
        tx_string = json.dumps(transaction)
        tx_bytes = tx_string.encode('ascii')
        return len(tx_bytes)

    def calculate_fee(self, tx_bytes_length):
        per_kb_fee = 0.25
        sig_hash_bytes = 800
        total = tx_bytes_length + sig_hash_bytes
        return (total / 1000) * per_kb_fee

    # Share calculations

    def count_shares(self, shares):
        valid_share = ""
        pool_diff = self.difficulty - 1
        last_proof = self.get_last_proof()

        for i in range(pool_diff):
            valid_share += "0"

        for share in tqdm(shares):
            share_hash = share['proof_hash']
            address = share['public_key_hash']
            if share['last_proof'] == last_proof:
                if share_hash[:pool_diff] == valid_share:
                    if address not in self.share_dict:
                        self.share_dict[address] = 1
                    if address in self.share_dict:
                        self.share_dict[address] += 1



    def calculate_split(self):
        total_shares = sum(self.share_dict.values())
        addresses = list(self.share_dict.keys())
        block_fees = pool.get_fees()
        print("Total shares contributed this round: ", total_shares)

        for address in addresses:
            block_reward = 10
            pool_fee = 0.2
            contributed = self.share_dict.get(address)
            print(address, "total shares: ", contributed)
            split = contributed / total_shares
            print("share of reward", split)
            total_reward = ((block_reward + block_fees) * split) - pool_fee
            print("total reward: ", total_reward)
            if address in self.unpaid_rewards:
                self.unpaid_rewards[address] += total_reward
            else:
                self.unpaid_rewards[address] = total_reward
        self.share_dict = {}
        print(self.unpaid_rewards)


    def dispense_reward(self, address, amount):
        unix_time = time()
        confirmed = self.new_transaction(recipient=address, amount=amount, unix_time=unix_time)
        if confirmed:
            print(amount, " paid out to ", address, " at ", unix_time)
            self.unpaid_rewards[address] = 0
        if not confirmed:
            print("Reward Share error")




# Node instance
app = Flask(__name__)

pool = pool()

@app.route('/chain', methods=['GET'])
def forward_chain_request():
    response = requests.get(f'http://{pool.node_address}/chain')
    forward = {
        'chain': response.json()['chain'],
        'length': response.json()['length']
    }
    return jsonify(forward), 200

@app.route('/getjob', methods=['GET'])
def get_job():
    current_index = pool.get_index()
    if current_index != pool.current_index:
        pool.current_index = current_index
        pool.lower_proof_range = 0
        pool.upper_proof_range = 1000000
    job = {
        'lower': pool.lower_proof_range,
        'upper': pool.upper_proof_range
    }
    pool.lower_proof_range = (pool.upper_proof_range + 1)
    pool.upper_proof_range = (pool.upper_proof_range + 1000000)
    print(f'Next unchecked range: {pool.lower_proof_range} to {pool.upper_proof_range}')


    return jsonify(job), 200


@app.route('/difficulty', methods=['GET'])
def difficulty():
    return jsonify(pool.difficulty), 200

@app.route('/proof', methods=['GET'])
def last_proof():
    proof = pool.get_last_proof()
    return jsonify(proof), 200


@app.route('/submit', methods=['POST'])
def hash_rate_submit():
    processes = []
    share_id = random.randint(10, 99)
    print(f"Received Shares! ID {share_id}")
    values = request.get_json()

    p = Process(target=pool.count_shares(values))
    processes.append(p)
    p.start()

    for p in processes:
        p.join()
        print(f"finished processing Share ID {share_id}")
        return "shares accepted", 200


@app.route('/submit/proof', methods=['POST'])
def receive_proof():
    #table for storing received json
    values = request.get_json()
    pool.difficulty = pool.get_difficulty()

    #variables for storing the proof data
    proof = values['proof']
    last_proof = pool.get_last_proof()

    # check to see if the proof is valid
    proof_valid = pool.valid_proof(last_proof, proof)

    if not proof_valid:
        return "invalid proof", 400

    if proof_valid:
        #reset search values
        pool.lower_proof_range = 0
        pool.upper_proof_range = 1000000
        print("Proof Found!")
        # if proof is valid we will continue to assign variables
        confirming_address = values['public_key_hash']
        public_key_hex = values['public_key_hex']
        previous_hash = values['previous_block_hash']
        signature = values['signature']

        trans_data = {
            'proof': proof,
            'last_proof': last_proof,
            'public_key_hash': confirming_address,
            'public_key_hex': public_key_hex,
            'previous_block_hash': previous_hash
        }
        if Validation.validate_signature(public_key_hex, signature, trans_data):
            print("signature valid")
            pool.calculate_split()
            if pool.send_proof(proof=proof, prev_proof=last_proof):
                for address in pool.unpaid_rewards:
                    amount = pool.unpaid_rewards.get(address)
                    print(amount)
                    if amount >= 20:
                        pool.dispense_reward(address=address, amount=amount)
                        return "ok", 200
                return "ok", 200




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=pool.port)
