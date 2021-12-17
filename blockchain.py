import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import os

import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):

        # list for storing the chain
        self.chain = []

        # pending transactions waiting to be added to a block
        self.current_transactions = []

        # what to do if the directory 'data' is not present, if not present; creates it.
        if not os.path.exists('data'):
            os.makedirs('data')

        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/chain.json'):
            self.genesis(previous_hash='Oskars Immutable Blockchain', proof=100)

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

        # appends the block to the chain list
        # no longer needed as we're reading the chain from json
        #self.chain.append(block)
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

        # Reset the current list of transactions
        self.current_transactions = []

        # append the block to the chain list
        self.chain.append(block)
        # we dont need this anymore as we're reading from the chain.json
        return block

    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

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

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

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


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    counter = 0

    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    counter += 1
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run()
