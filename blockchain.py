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


class Blockchain:
    def __init__(self):

        # silence flask console
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # list for storing the chain
        self.chain = []

        # pending transactions waiting to be added to a block
        self.current_transactions = []

        # set for storing nodes
        self.nodes = set()

        # port to run blockchain on
        self.port = input("Please input port number for chain to run on\n")

        # total pending fees
        self.pending_fees = 0



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
        unix_time = time()

        block = {
            'index': len(self.chain) + 1,
            'timestamp': unix_time,
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }

        block_hash = self.hash(block)

        block_with_hash = {
            'index': len(self.chain) + 1,
            'timestamp': unix_time,
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
            'current_hash': block_hash
        }

        # opens the chain.json file and writes the genesis block to it
        with open('data/chain.json', 'w') as f:
            block_dict = json.dumps(block_with_hash)
            f.write(block_dict)
            f.write('\n')

        return block_with_hash





    def write_json(self, data, filename='data/chain.json'):
        # opens the file in append mode
        with open(filename, 'a') as file:
            block_dict = json.dumps(data)
            file.write(block_dict)
            file.write('\n')

    def new_block(self, proof, time, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time,
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }


        block_hash = self.hash(block)

        block_with_hash = {
            'index': len(self.chain) + 1,
            'timestamp': time,
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
            'current_hash': block_hash
        }

        # function to write the new block to chain.json
        self.write_json(block_with_hash)

        # broadcast the block to the network
        self.broadcast_block(block_with_hash)

        # Reset the current list of transactions
        self.current_transactions = []

        # append the block to the chain list
        self.chain.append(block_with_hash)



        return block_with_hash

    def new_transaction(self, sender, recipient, amount, fee, unix_time, previous_block_hash, pub_key_hex, trans_hash,
                        signature):
        trans_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
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

    def last_hash(self):
        last_block = self.last_block()
        return last_block['current_hash']

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
        return guess_hash[:6] == "000000"


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

            # dictionary to store values to confirm appended hash
            last_block_no_hash = {
                'index': last_block['index'],
                'timestamp': last_block['timestamp'],
                'transactions': last_block['transactions'],
                'proof': last_block['proof'],
                'previous_hash': last_block['previous_hash']
            }

            block = chain[current_index]

            # Check that the hash of the blocks is consistent
            if last_block['current_hash'] != block['previous_hash']:
                print("hashes on chain dont match when syncing... ignored this chain")

                return False
            # Hash the block ourselves to check for tampering
            if last_block['current_hash'] != self.hash(last_block_no_hash):
                print(last_block['current_hash'], " not equal to ", self.hash(last_block_no_hash))
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                print('invalid proof on block when syncing')
                return False

            last_block = block
            current_index += 1


        return True


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

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain


            print("chain updated")

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




@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'fee', 'time_submitted', 'previous_block_hash', 'public_key_hex',
                'transaction_hash', 'signature']
    if not all(k in values for k in required):
        print('Error 400: Transaction Malformed')
        return 'Missing values', 400

    # Check that the broadcasted transaction is in the nodes mem-pool already if so return an error and break
    if Validation.transaction_in_pool(blockchain.current_transactions, values):
        print('Error 440: Transaction already in this nodes mem-pool')
        return 'Transaction already in this nodes mem-pool', 440

    # Check if this address already has a transaction in the chain
    for transaction in blockchain.current_transactions:
        if transaction['sender'] == values['sender']:
            print('Error 420: One Transaction per Block')
            return 'One Transaction per block, wait for next block confirmation', 420

    # Check if the sender is trying to send themselves coins to the same address, this is not allowed
    if values['sender'] == values['recipient']:
        return "You cant send a transaction to yourself", 430


    # If all checks clear continue validation
    print("New transaction: ", values, "\n...Validating...")

    # Format for transaction data for hash verification
    trans_to_be_hashed = {
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
        'fee': values['fee'],
        'time_submitted': values['time_submitted'],
        'previous_block_hash': values['previous_block_hash'],
        'public_key_hex': values['public_key_hex']
    }

    # Check the local hash matches what has been provided
    # If this fails the transaction has been tampered with or a transmission error has occured
    local_trans_hash = blockchain.hash(trans_to_be_hashed)

    # If the transaction fails hash verification we throw it out and return an error
    if local_trans_hash != values['transaction_hash']:
        print("Transaction hash mismatch")
        response = {'message': f'Transaction hash failed CRC'}
        return response, 450

    # If the Hash is correct we proceed
    else:
        print("Transaction Hash verified!")

    # Format of transaction data for signature verification
    trans_to_be_validated = {
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
        'fee': values['fee'],
        'time_submitted': values['time_submitted'],
        'previous_block_hash': values['previous_block_hash'],
        'public_key_hex': values['public_key_hex'],
        'transaction_hash': values['transaction_hash']
    }

    # This line checks the signature against the broadcasted data If true we proceed
    # If not we throw out the transaction as it has been tampered with
    if Validation.validate_signature(values['public_key_hex'], values['signature'], trans_to_be_validated):

        #Check if funds are available for the given address, or if the transaction is a Coinbase Reward
        if values['sender'] == 'Coinbase Reward' or Validation.enumerate_funds(
                values['sender'], blockchain.chain) >= values['amount']:
            print('funds are available')

            # Create a new Transaction in the mempool to await confirmation
            index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], values['fee'],
                                               values['time_submitted'], values['previous_block_hash'],
                                               values['public_key_hex'], values['transaction_hash'],
                                               values['signature'])

            # add the fee to pending fees
            blockchain.pending_fees += values['fee']

            print(f'Transaction will be added to Block {index}')
            response = {'message': f'Transaction will be added to Block {index}'}
            return jsonify(response), 201

        # If theres not enough funds we throw an error and discard the transaction
        else:
            response = {'message': f'Not enough funds for transaction'}
            return jsonify(response), 220
    # If the signature fails verification we throw out the transaction and throw an error
    else:
        response = {'message': f'Transaction signature not valid'}
        return jsonify(response), 460




@app.route('/miners', methods=['POST'])
def receive_proof():
    #table for storing received json
    values = request.get_json()

    #variables for storing the transaction data
    proof = values['proof']
    last_proof = blockchain.last_block['proof']

    # check to see if the proof is valid
    proof_valid = blockchain.valid_proof(last_proof, proof)

    if not proof_valid:
        return "invalid proof", 400

    # If the proof is valid we will proceed
    if proof_valid:
        print("Valid Proof Submitted...\n")
        # if proof is valid we will continue to assign variables
        confirming_address = values['public_key_hash']
        public_key_hex = values['public_key_hex']
        previous_hash = values['previous_block_hash']
        signature = values['signature']
        unix_time = time()

        # Format of proof data to be verified
        trans_data = {
            'proof': proof,
            'last_proof': last_proof,
            'public_key_hash': confirming_address,
            'public_key_hex': public_key_hex,
            'previous_block_hash': previous_hash
        }
        # If the signature is verified we will proceed with creating a block
        if Validation.validate_signature(public_key_hex, signature, trans_data):
            print('Signature valid! proceeding...\n')
            block_reward_transaction = {
                'sender': 'Coinbase Reward',
                'recipient': confirming_address,
                'amount': 10,
                'fee': 0,
                'time_submitted': unix_time,
                'previous_block_hash': previous_hash,
                'public_key_hex': public_key_hex,
                'signature': signature
            }

            hashed_reward = blockchain.hash(json.dumps(block_reward_transaction, sort_keys=True))

            full_block_reward_transaction = {
                'sender': 'Coinbase Reward',
                'recipient': confirming_address,
                'amount': 10,
                'fee': 0,
                'time_submitted': block_reward_transaction['time_submitted'],
                'previous_block_hash': previous_hash,
                'public_key_hex': blockchain.public_key_hex,
                'signature': signature,
                'transaction_hash': hashed_reward
            }


                # We must receive a reward for finding the proof.
                # The sender is "Coinbase" to signify a new block reward has been mined.
            blockchain.new_transaction(full_block_reward_transaction['sender'],
                                       full_block_reward_transaction['recipient'],
                                       full_block_reward_transaction['amount'],
                                       full_block_reward_transaction['fee'],
                                       full_block_reward_transaction['time_submitted'],
                                       full_block_reward_transaction['previous_block_hash'],
                                       full_block_reward_transaction['public_key_hex'],
                                       full_block_reward_transaction['transaction_hash'],
                                       full_block_reward_transaction['signature'])

            # If there are pending fees create a transaction to award fees to miner
            if blockchain.pending_fees > 0:
                fee_reward_trans = {
                    'sender': 'Transaction Fee Reward',
                    'recipient': confirming_address,
                    'amount': blockchain.pending_fees,
                    'fee': 0,
                    'time_submitted': block_reward_transaction['time_submitted'],
                    'previous_block_hash': previous_hash,
                    'public_key_hex': blockchain.public_key_hex,
                }
                signed_fees = blockchain.sign(fee_reward_trans)

                fee_reward_trans_with_sig = {
                    'sender': 'Transaction Fee Reward',
                    'recipient': confirming_address,
                    'amount': blockchain.pending_fees,
                    'fee': 0,
                    'time_submitted': block_reward_transaction['time_submitted'],
                    'previous_block_hash': previous_hash,
                    'public_key_hex': blockchain.public_key_hex,
                    'signature': signed_fees,
                }

                hashed_fees = blockchain.hash(fee_reward_trans_with_sig)

                fee_reward_trans_with_hash = {
                    'sender': 'Transaction Fee Reward',
                    'recipient': confirming_address,
                    'amount': blockchain.pending_fees,
                    'fee': 0,
                    'time_submitted': block_reward_transaction['time_submitted'],
                    'previous_block_hash': previous_hash,
                    'public_key_hex': blockchain.public_key_hex,
                    'signature': signed_fees,
                    'transaction_hash': hashed_fees
                }

                blockchain.new_transaction(fee_reward_trans_with_hash['sender'],
                                           fee_reward_trans_with_hash['recipient'],
                                           fee_reward_trans_with_hash['amount'],
                                           fee_reward_trans_with_hash['fee'],
                                           fee_reward_trans_with_hash['time_submitted'],
                                           fee_reward_trans_with_hash['previous_block_hash'],
                                           fee_reward_trans_with_hash['public_key_hex'],
                                           fee_reward_trans_with_hash['transaction_hash'],
                                           fee_reward_trans_with_hash['signature'])

                blockchain.pending_fees = 0


                # Forge the new Block by adding it to the chain
            block = blockchain.new_block(proof, unix_time, previous_hash)
            print("New block forged at: ", unix_time, " by ", confirming_address)
            return block, 200
        # If signature fails validation we discard the proof/block
        if not Validation.validate_signature(public_key_hex, signature, trans_data):
            print('signature failed verification')
            return "signature malformed", 400

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



    if block_confirmed:
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

    if not block_confirmed:
        print("block proof not valid")
        response = {
            'message': 'block has invalid proof, skipping...',
            'block': values,
        }
        return jsonify(response), 400

@app.route('/mempool', methods=['GET'])
def mempool():
    return jsonify(blockchain.current_transactions), 200


@app.route('/proof', methods=['GET'])
def last_proof():
    last_block = blockchain.last_block
    proof = last_block['proof']
    return jsonify(proof), 200


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

    blockchain.resolve_conflicts()

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
    app.run(host='0.0.0.0', port=blockchain.port)
