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


class Blockchain:
    def __init__(self):



        # list for storing the chain
        self.chain = []

        # pending transactions waiting to be added to a block
        self.current_transactions = []

        # set for storing nodes
        self.nodes = set()

        # what to do if the directory 'data' is not present, if not present; creates it.
        if not os.path.exists('data'):
            os.makedirs('data')

        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/wallet.json'):
            utils.generate_wallet()

        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/chain.json'):
            self.genesis(previous_hash='Times, Chancellor on brink of second bailout for banks', proof=30109)


        # attempting to open wallet file
        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']





        # attempting to read our json to the self.chain table.
        # dont ask me how this works, as far as I'm concerned its witchcraft
        # such a damn simple task seemingly, but this is the only syntax I could find to get the job done lmfao.
        s = open('data/chain.json', 'r')
        for line in s.readlines():
            try:
                j = line.split('|')[-1]
                self.chain.append(json.loads(j))

            except ValueError:
                print("the json is rekt slut")
                continue

    def genesis(self, proof, previous_hash=None):
        # the structure of our block to be filled in
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # opens the chain.json file and writes the genesis block to it
        with open('data/chain.json', 'w') as f:
            block_dict = json.dumps(block)
            f.write(block_dict)
            f.write('\n')

        return block

    def write_json(self, data, filename='data/chain.json'):
        # opens the file in append mode
        with open(filename, 'a') as file:
            block_dict = json.dumps(data)
            file.write(block_dict)
            file.write('\n')

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # function to write the new block to chain.json
        self.write_json(block)

        # broadcast the block to the network
        self.broadcast_block(block)

        # Reset the current list of transactions
        self.current_transactions = []

        # append the block to the chain list
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount, unix_time, previous_block_hash, pub_key_hex, trans_hash,
                        signature):
        trans_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time_submitted': unix_time,
            'previous_block_hash': previous_block_hash,
            'public_key_hex': pub_key_hex,
            'transaction_hash': trans_hash,
            'signature': signature
        }

        if sender == "Coinbase Reward":
            self.current_transactions.append(trans_data)

        else:
            self.current_transactions.append(trans_data)
            for node in self.nodes:
                self.broadcast_transaction(trans_data, node)


        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

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
    def valid_proof(last_proof, proof):
        """
        Validates the Proof
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :return: True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:8] == "00000000"

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def calculate_hash(self, data):
        data = bytearray(data, "utf-8")
        h = SHA256.new()
        h.update(data)
        return h.hexdigest()

    def broadcast_transaction(self, transaction, node):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(f'http://{node}/transactions/new', json=transaction, headers=headers)
        if response.status_code == 201:
            print('transaction broadcast accepted by: ', node)

        else:
            print('transaction broadcast denied by: ', node)




    def broadcast_block(self, block):
        nodes = self.nodes
        current_time = str(time())
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        for node in nodes:
            response = requests.post(f'http://{node}/broadcast', json=block, headers=headers)

            if response.status_code == 200:
                print("Block broadcast accepted ", block, "\nby ", node, "at ", current_time)

            else:
                print("Block broadcast denied")
                self.resolve_conflicts()

    def sign_transaction_data(self, data):
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        print(transaction_bytes)
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.private_key).sign(hash_object)
        return signature

    def sign(self, data):
        signature_hex = binascii.hexlify(self.sign_transaction_data(data)).decode("utf-8")

        return signature_hex

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')


            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                print(length)
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            print("chain updated with", new_chain)

            if os.path.exists('data/chain.json'):
                os.remove('data/chain.json')
                print("old chain removed, now writing new chain")
            else:
                print("no chain data found... Creating it now.")

            with open('data/chain.json', 'w') as f:
                for i in self.chain:
                    string = json.dumps(i)
                    f.write(string)
                    f.write('\n')

            return True

        return False


# Instantiate the Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()

# Unique address on the chain is a 2 part hash of our public key
node_identifier = blockchain.public_key_hash


#@app.route('/mine', methods=['GET'])
#def mine():
    # We run the proof of work algorithm to get the next proof...
#    last_block = blockchain.last_block
#    last_proof = last_block['proof']
#    proof = blockchain.proof_of_work(last_proof)

#    unix_time = time()

#    block_reward_transaction = {
#        'sender': 'Coinbase Reward',
#        'recipient': node_identifier,
#        'amount': 10,
#        'time_submitted': unix_time,
#        'previous_block_hash': blockchain.hash(last_block),
#        'public_key_hex': blockchain.public_key_hex
#    }

#    hashed_reward = blockchain.calculate_hash(json.dumps(block_reward_transaction, sort_keys=True))

#    block_reward_transaction_with_hash = {
#        'sender': "Coinbase Reward",
#        'recipient': node_identifier,
#        'amount': 10,
#        'time_submitted': block_reward_transaction['time_submitted'],
#        'previous_block_hash': blockchain.hash(last_block),
#        'public_key_hex': blockchain.public_key_hex,
#        'transaction_hash': hashed_reward
#    }

#    signature = blockchain.sign(block_reward_transaction_with_hash)

#    full_block_reward_transaction = {
#        'sender': "Coinbase Reward",
#        'recipient': node_identifier,
#        'amount': 10,
#        'time_submitted': block_reward_transaction['time_submitted'],
#        'previous_block_hash': blockchain.hash(last_block),
#        'public_key_hex': blockchain.public_key_hex,
#        'transaction_hash': hashed_reward,
#        'signature': signature
#    }
#    if Validation.validate_signature(full_block_reward_transaction['public_key_hex'],
#                                     full_block_reward_transaction['signature'], block_reward_transaction_with_hash):
        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
#        blockchain.new_transaction(full_block_reward_transaction['sender'], full_block_reward_transaction['recipient'],
#                                   full_block_reward_transaction['amount'],
#                                   full_block_reward_transaction['time_submitted'],
#                                   full_block_reward_transaction['previous_block_hash'],
#                                   full_block_reward_transaction['public_key_hex'],
#                                   full_block_reward_transaction['transaction_hash'],
#                                   full_block_reward_transaction['signature'])

        # Forge the new Block by adding it to the chain
#        previous_hash = blockchain.hash(last_block)
#        block = blockchain.new_block(proof, previous_hash)
#
#        response = {
#            'message': "New Block Forged",
#            'index': block['index'],
#            'transactions': block['transactions'],
#            'proof': block['proof'],
#            'previous_hash': block['previous_hash'],
#        }

#    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'time_submitted', 'previous_block_hash', 'public_key_hex',
                'transaction_hash', 'signature']
    if not all(k in values for k in required):
        print('Error 400: Transaction Malformed')
        return 'Missing values', 400

    if Validation.transaction_in_pool(blockchain.current_transactions, values):
        print('Error 440: Transaction already in this nodes mem-pool')
        return 'Transaction already in this nodes mem-pool', 440

    for transaction in blockchain.current_transactions:
        if transaction['sender'] == values['sender']:
            print('Error 420: One Transaction per Block')
            return 'One Transaction per block, wait for next block confirmation', 420



    print("New transaction: ", values, "\n...Validating...")

    trans_to_be_validated = {
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
        'time_submitted': values['time_submitted'],
        'previous_block_hash': values['previous_block_hash'],
        'public_key_hex': values['public_key_hex'],
        'transaction_hash': values['transaction_hash']
    }

    if Validation.validate_signature(values['public_key_hex'], values['signature'], trans_to_be_validated):

        if values['sender'] == 'Coinbase Reward' or Validation.enumerate_funds(
                values['sender'], blockchain.chain) >= values['amount']:
            print('funds are available')

            # Create a new Transaction
            index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'],
                                               values['time_submitted'], values['previous_block_hash'],
                                               values['public_key_hex'], values['transaction_hash'],
                                               values['signature'])

            response = {'message': f'Transaction will be added to Block {index}'}
            return jsonify(response), 201

        else:
            response = {'message': f'Not enough funds for transaction'}
            return jsonify(response), 220

    else:
        response = {'message': f'Transaction signature not valid'}
        return jsonify(response), 460


@app.route('/miners', methods=['POST'])
def receive_proof():
    values = request.get_json()
    last_proof = blockchain.last_block['proof']
    proof = values['proof']
    confirming_address = values['public_key_hash']
    previous_hash = values['previous_block_hash']
    proof_valid = blockchain.valid_proof(last_proof, proof)
    unix_time = time()

    if not proof_valid:
        print("stale proof")
        return "invalid proof", 400

    if proof_valid:
        block_reward_transaction = {
            'sender': 'Coinbase Reward',
            'recipient': confirming_address,
            'amount': 10,
            'time_submitted': unix_time,
            'previous_block_hash': previous_hash,
            'public_key_hex': blockchain.public_key_hex
        }

        hashed_reward = blockchain.calculate_hash(json.dumps(block_reward_transaction, sort_keys=True))

        block_reward_transaction_with_hash = {
            'sender': 'Coinbase Reward',
            'recipient': confirming_address,
            'amount': 10,
            'time_submitted': block_reward_transaction['time_submitted'],
            'previous_block_hash': previous_hash,
            'public_key_hex': blockchain.public_key_hex,
            'transaction_hash': hashed_reward
        }

        signature = blockchain.sign(block_reward_transaction_with_hash)

        full_block_reward_transaction = {
            'sender': "Coinbase Reward",
            'recipient': confirming_address,
            'amount': 10,
            'time_submitted': block_reward_transaction['time_submitted'],
            'previous_block_hash': previous_hash,
            'public_key_hex': blockchain.public_key_hex,
            'transaction_hash': hashed_reward,
            'signature': signature
        }

        if Validation.validate_signature(full_block_reward_transaction['public_key_hex'],
                                         full_block_reward_transaction['signature'],
                                         block_reward_transaction_with_hash):
            # We must receive a reward for finding the proof.
            # The sender is "0" to signify that this node has mined a new coin.
            blockchain.new_transaction(full_block_reward_transaction['sender'],
                                       full_block_reward_transaction['recipient'],
                                       full_block_reward_transaction['amount'],
                                       full_block_reward_transaction['time_submitted'],
                                       full_block_reward_transaction['previous_block_hash'],
                                       full_block_reward_transaction['public_key_hex'],
                                       full_block_reward_transaction['transaction_hash'],
                                       full_block_reward_transaction['signature'])
            # Forge the new Block by adding it to the chain
            previous_hash = blockchain.hash(blockchain.last_block)
            block = blockchain.new_block(proof, previous_hash)
            return block, 200

@app.route('/nodes', methods=['GET'])
def all_nodes():
    response = {
        'message': 'all nodes',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200

@app.route('/broadcast', methods=['POST'])
def receive_block():
    values = request.get_json()
    last_proof = blockchain.last_block['proof']
    new_proof = values['proof']
    block_confirmed = blockchain.valid_proof(last_proof, new_proof)


    if block_confirmed == True:
        print('new block added to chain: ', values)
        blockchain.write_json(values)
        blockchain.chain.append(values)
        response = {
            'message': 'new block added to chain',
            'block': values,
        }
        # clears the current transaction table, i'll just call it the mem-pool even though is isnt a proper one
        blockchain.current_transactions = []
        print('transactions in mem-pool cleared')
        print(blockchain.current_transactions)
        return jsonify(response), 200

    if block_confirmed == False:
        print("block proof not valid")
        response = {
            'message': 'block has invalid proof, skipping...',
            'block': values,
        }
        return jsonify(response), 400


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
