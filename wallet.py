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
import PySimpleGUI as sg
import hashlib

class Wallet:
    unix_time = time()

    def __init__(self):

        if not os.path.isfile('data/wallet.json'):
            self.generate_wallet()

        self.nodes = []

        # GUI INIT
        layout = [[sg.Text('Please enter the address/ip and port of a known node')],
                  [sg.InputText()],
                  [sg.Submit(), sg.Cancel()]]

        window = sg.Window('Wallet waiting to connect...', layout)

        event, values = window.read()
        window.close()

        # variable inits
        self.node = values[0]
        self.nodes.append(self.node)

        sg.popup("Connecting to ", values[0])

        # get the chain from the blockchain node
        self.chain = self.get_chain()

        #load our wallet file
        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']

        # if wallet doesnt exist we'll generate one
        if not os.path.exists('data'):
            os.makedirs('data')

        if not os.path.isfile('data/wallet.json'):
            self.generate_wallet()


    # wallet file functions
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

    def write_json(self, data, mode, filename='data/wallet.json'):
        # opens the file in write mode
        with open(filename, mode) as file:
            block_dict = json.dumps(data, indent=6)
            file.write(block_dict)


    # hash functions
    @staticmethod
    def hash(block):
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

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




    # functions for transactions
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
        total_bytes = self.calculate_bytes(trans_data)
        fee = self.calculate_fee(total_bytes)
        total_amount = amount + fee

        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
            'time_submitted': unix_time,
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


        confirmation_window_layout = [
            [sg.Text("Are you sure you want to send this Transaction?")],
            [[sg.Text("Recipient", justification='left'), sg.Text(recipient, justification='right')]],
            [[sg.Text("Amount to send: ", justification='left')], [sg.Text(amount, justification='right')]],
            [[sg.Text("Transaction Fee: ", justification='left')], sg.Text(fee, justification='right')],
            [[sg.Text("Total Amount: ", justification='left')], sg.Text(total_amount, justification='right')],
            [[sg.Button('Confirm')], [sg.Button('Exit')]]
        ]

        window = sg.Window('Python-blockchain Wallet', confirmation_window_layout)

        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Exit'):
            window.close()
            return "cancelled"

        if event in 'Confirm':
            if self.broadcast_transaction(full_transaction):
                self.chain = self.get_chain()
                window.close()
                return "confirmed"
            else:
                self.chain = self.get_chain()
                window.close()
                return False

    def broadcast_transaction(self, transaction):

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        for node in self.nodes:
            response = requests.post(f'http://{node}/transactions/new', json=transaction, headers=headers)
            if response.status_code == 201:
                return True

            else:
                return False

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return signature

    def calculate_bytes(self, transaction):
        tx_string = json.dumps(transaction)
        tx_bytes = tx_string.encode('ascii')
        return len(tx_bytes)

    def calculate_fee(self, tx_bytes_length):
        per_kb_fee = 0.25
        sig_hash_bytes = 800
        total = tx_bytes_length + sig_hash_bytes
        return (total / 1000) * per_kb_fee

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")

        return signature_hex

    # functions for getting blockchain data

    def get_balance(self):
        chain_balance = Validation.enumerate_funds(self.public_key_hash, self.chain)
        if chain_balance > 0:
            return chain_balance

        if chain_balance == False:
            return 0

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

            return chain[length - 1]['current_hash']

    def get_chain(self):
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')

        if response.status_code == 200:
            chain = response.json()['chain']

            return chain


wallet = Wallet()

layout = [
    [sg.Text('Welcome to the Python-blockchain wallet')],
    [sg.Text('Your blockchain address'), sg.Text(wallet.public_key_hash)],
    [sg.Text("Available Funds: "), sg.Text(wallet.get_balance(), key='-BALANCE-')],
    [sg.Button('Update Blockchain'), sg.Button('Transaction History')],
    [sg.Text("Address: "), sg.InputText(key='-ADDRESS-', size=(20, 20)), sg.Text("Amount: "),
     sg.InputText(key='-AMOUNT-', size=(8, 20)), sg.Button('Send Transaction')],
    [sg.Button('Exit')]
]

window = sg.Window('Python-blockchain Wallet', layout)
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event in 'Update Blockchain':
        wallet.chain = wallet.get_chain()
        wallet.get_balance()
        window['-BALANCE-'].update(wallet.get_balance())

    if event in 'Transaction History':
        window.close()
        # code to find relevant transactions in the blockchain pertaining to our wallets address
        chain = wallet.get_chain()  # get the chain
        sent = []  # list for storing sent transactions
        received = []  # list for storing received transactions
        for block in chain:  # iterate through the blockchain
            for transaction in block['transactions']:
                # code to find received transactions
                if transaction['recipient'] == wallet.public_key_hash:
                    print("received: ", transaction)
                    received.append(transaction)
                # code to find sent transactions
                if transaction['sender'] == wallet.public_key_hash:
                    print("sent: ", transaction)
                    sent.append(transaction)
                else:
                    continue

        sent_json = json.dumps(sent, indent=2)
        received_json = json.dumps(received, indent=2)

        transaction_window_layout = [
            [sg.Text("Sent Transactions:")],
            [sg.Multiline(sent_json, size=(100, 25))],
            [sg.Text("Received Transactions:")],
            [sg.Multiline(received_json, size=(100, 25))],

            [sg.Button('Exit')]
        ]
        transaction_window = sg.Window('Transaction History', transaction_window_layout)
        events, values = transaction_window.read()
        if event in 'Exit':
            transaction_window.close()

    if event in 'Send Transaction':
        time = wallet.unix_time
        recipient = values['-ADDRESS-']
        amount = float(values['-AMOUNT-'])
        if wallet.new_transaction(recipient, amount, time) == "confirmed":
            sg.popup(
                'Transaction submitted and accepted by network...\nPlease wait for next block confirmation for transaction to confirm')
            continue
        if wallet.new_transaction(recipient, amount, time) == "cancelled":
            sg.popup("Transaction Cancelled")
        else:
            sg.popup(
                'Transaction denied by network\nyou either have unconfirmed transactions in the mempool or insufficient balance.\nPlease try again')

window.close()
