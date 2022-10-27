import hashlib
import time
import binascii
import requests
import os
import json
import time
import random
from src.utilities import Generate
from Crypto.PublicKey import RSA
import random
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from multiprocessing import Process
#from tqdm import tqdm
from src.utilities import Hash, Write

class Miner:

    def __init__(self):
        self.thread_number = 1
        self.node = '127.0.0.1:5000'


        if not os.path.isfile('data/wallet.json'):
            Generate.generate_wallet()

        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']

    def get_mempool(self):
        response = requests.get(f'http://{self.node}/mempool')
        if response.status_code == 200:
            return response.json()

    @staticmethod
    def valid_proof(target_nonce, block):
        encoded_block = f'{block}'.encode()
        value = int.from_bytes(hashlib.sha256(encoded_block).digest(), 'little')
        if value <= target_nonce:
            return True
        if value >= target_nonce:
            return False

    def get_fees(self):
        value = requests.get(f'http://{self.node}/fees')
        if value.status_code == 200:
            return value.json()

    def get_difficulty(self):
        value = requests.get(f'http://{self.node}/difficulty')
        if value.status_code == 200:
            return value.json()

    def get_last_block(self):
        response = requests.get(f'http://{self.node}/lastblock')
        if response.status_code == 200:
            return response.json()

    def get_coinbase(self):
        value = requests.get(f'http://{self.node}/coinbase')
        if value.status_code == 200:
            return value.json()

    def get_last_nonce(self):
        response = requests.get(f'http://{self.node}/nonce')
        if response.status_code == 200:
            return response.json()
        else:
            print("couldn't obtain proof")

    def get_last_hash(self):
        last_block = self.get_last_block()
        last_block_hash = last_block['block_hash']
        return last_block_hash

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return binascii.hexlify(signature).decode("utf-8")

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")
        return signature_hex

    def coinbase_transaction(self, coinbase_amount, unix_millis, previous_hash):
        transaction = {
            'sender': "Coinbase Reward",
            'recipient': self.public_key_hash,
            'amount': coinbase_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex
        }

        transaction_hash = Hash.hash(transaction)

        transaction_with_hash = {
            'sender': "Coinbase Reward",
            'recipient': self.public_key_hash,
            'amount': coinbase_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': transaction_hash
        }

        trans_sig = self.sign_transaction_data(data=transaction_with_hash)

        transaction_with_sig = {
            'sender': "Coinbase Reward",
            'recipient': self.public_key_hash,
            'amount': coinbase_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': transaction_hash,
            'signature': trans_sig
        }

        return transaction_with_sig

    def fee_reward_transaction(self, fee_amount, unix_millis, previous_hash):
        transaction = {
            'sender': "Fee Reward",
            'recipient': self.public_key_hash,
            'amount': fee_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex
        }

        transaction_hash = Hash.hash(transaction)

        transaction_with_hash = {
            'sender': "Fee Reward",
            'recipient': self.public_key_hash,
            'amount': fee_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': transaction_hash
        }

        trans_sig = self.sign_transaction_data(data=transaction_with_hash)

        transaction_with_sig = {
            'sender': "Fee Reward",
            'recipient': self.public_key_hash,
            'amount': fee_amount,
            'fee': 0,
            'time_submitted': unix_millis,
            'previous_hash': previous_hash,
            'public_key_hex': self.public_key_hex,
            'transaction_hash': transaction_hash,
            'signature': trans_sig
        }
        return transaction_with_sig

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
        while True:
            difficulty = self.get_difficulty()
            last_block = self.get_last_block()
            target = self.get_last_nonce()
            target_hex = hex(target)
            transactions = []
            unix_time = time.time()
            pending_fees = self.get_fees()
            coinbase = self.get_coinbase()
            coinbase_reward_transaction = self.coinbase_transaction(coinbase_amount=coinbase, unix_millis=unix_time, previous_hash=last_block['block_hash'])
            mempool = self.get_mempool()
            transactions.append(coinbase_reward_transaction)
            round_end = time.time() + 30
            if pending_fees > 0:
                fee_reward_transaction = self.fee_reward_transaction(fee_amount=pending_fees, unix_millis=unix_time,
                                                                     previous_hash=last_block['block_hash'])
                transactions.append(fee_reward_transaction)
            if len(mempool) > 0:
                for transaction in mempool:
                    transactions.append(transaction)
            print("Round Start!")
            while time.time() < round_end:
                unix_time = time.time()
                nonce = random.randint(1, 100000000000000000000000000000000000000000000)

                unforged_block = {
                    'index': last_block['index'] + 1,
                    'difficulty': difficulty,
                    'previous_hash': last_block['block_hash'],
                    'nonce': nonce,
                    'target_nonce_hex': target_hex,
                    'timestamp': unix_time,
                    'transactions': transactions
                }

                if self.valid_proof(target, unforged_block):
                    block_hash = Hash.hash(unforged_block)
                    block_with_hash = {
                        'index': unforged_block['index'],
                        'difficulty': unforged_block['difficulty'],
                        'previous_hash': unforged_block['previous_hash'],
                        'block_hash': block_hash,
                        'nonce': unforged_block['nonce'],
                        'target_nonce_hex': unforged_block['target_nonce_hex'],
                        'timestamp': unforged_block['timestamp'],
                        'transactions': unforged_block['transactions'],
                        'public_key': self.public_key_hex
                    }



                    block_sig = self.sign_transaction_data(data=block_with_hash)

                    forged_block = {
                        'index': unforged_block['index'],
                        'difficulty': unforged_block['difficulty'],
                        'previous_hash': unforged_block['previous_hash'],
                        'block_hash': block_hash,
                        'nonce': unforged_block['nonce'],
                        'target_nonce_hex': unforged_block['target_nonce_hex'],
                        'timestamp': unforged_block['timestamp'],
                        'transactions': unforged_block['transactions'],
                        'public_key': self.public_key_hex,
                        'signature': block_sig
                    }

                    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                    response = requests.post(f'http://{self.node}/block', json=forged_block,
                                             headers=headers)

                    if response.status_code == 200:
                        print("new block forged!")
                        break

                    else:
                        print("error")
                        break





Miner = Miner()

Miner.mine()
