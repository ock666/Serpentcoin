import os
import requests
import json
from Crypto.PublicKey import RSA
from flask import Flask, request, jsonify
from urllib.parse import urlparse
from src.validation import Transaction, ValidChain, ValidBlock, Hash_Validation, Funds
from src.utilities import Write, Generate
from src.broadcast import Broadcast
from src.epoch import Epoch
import logging


class Blockchain:
    def __init__(self):
        # list for storing the chain
        self.chain = []

        config = json.load(open('data/config.json', 'r'))

        # local ip
        self.local_ip = config['local_ip']

        # hard-coded coinbase reward
        self.coinbase_reward = 20

        # port to run blockchain on
        self.port = config['port']

        # development option, silences the flask console while the mining algorithm sucks
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # create data dir if it does not exist
        if not os.path.exists('data'):
            print('creating data directory')
            os.makedirs('data')

        s = open('data/chain.json', 'r')
        for line in s.readlines():
            try:
                j = line.split('|')[-1]
                self.chain.append(json.loads(j))

            except ValueError:
                print("the json is rekt slut")
                continue
        # checks to see if there is a chain.json file, if not present; creates it.
        if not os.path.isfile('data/wallet.json'):
            print('generating wallet...')
            Generate.generate_wallet()
            print('done')

        # attempting to open wallet file
        wallet_file = json.load(open('data/wallet.json', 'r'))
        self.private_key = RSA.import_key(wallet_file['private key'])
        self.public_key = RSA.import_key(wallet_file['public key'])
        self.public_key_hex = wallet_file['public key hex']
        self.public_key_hash = wallet_file['public key hash']

        print("Now validating local chain, please wait.")
        if ValidChain.valid_chain(self.chain):
            print("Chain is valid")
        else:
            print("Local chain is invalid, please sync the node with another upstream node.")

    @property
    def last_proof(self):
        """
        Returns the last nonce
        """
        return self.last_block['nonce']

    @property
    def last_block(self):
        """
        Returns the last block in the chain
        """
        return self.chain[-1]

    @property
    def block_time(self, block):
        """
        Returns the timestamp from a given block in unix millis
        """
        return block['timestamp']

    @property
    def last_hash(self):
        """
        Returns the hash of the last block in the chain
        """
        last_block = self.last_block()
        return last_block['block_hash']


class Mempool:
    def __init__(self):
        # pending transactions waiting to be added to a block
        self.current_transactions = []

        # total pending fees
        self.pending_fees = 0

    def clear_mempool(self):
        self.current_transactions = []

    def transaction_in_pool(self, transaction):
        if transaction in self.current_transactions:
            return True
        return False

    def clear_fees(self):
        self.pending_fees = 0

    def assess_fees(self):
        for transaction in self.current_transactions:
            self.pending_fees += transaction['fee']

class Node:
    # set for storing nodes
    nodes = set()
    config = json.load(open('data/config.json', 'r'))
    prefix = config['protocol']
    local_ip = config['local_ip']

    def __init__(self):

        for neighbour in Node.config['nodes']:
            # here we register our first node upon start up
            self.register_node(str(self.prefix + neighbour))
        choice = input("Would you like to grab the chain from an upstream node? (y/n)\n")
        if choice == "y":
            # get the blockchain from a registered neighbour
            self.resolve_conflicts()
        else:
            pass

    #method not yet implmented
    @staticmethod
    def introduce_self_to_neighbours():

        data = {'nodes': [f'{Node.prefix}{Node.local_ip}:{blockchain.port}']}

        for node in Node.nodes:
            link = f'{Node.prefix}{node}/nodes/register'

            response = requests.post(link, json=data)
            if response.status_code == 201:
                print("Node introduction successful")

            else:
                print("failed to introduce to node")
                print("status code: ", response.status_code)
                return False
            return True


    @staticmethod
    def register_node(address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        Node.nodes.add(parsed_url.netloc)

    @staticmethod
    def remove_node(address):
        """
        Remove a node from the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        Node.nodes.remove(parsed_url.netloc)

    @staticmethod
    def resolve_conflicts():
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = Node.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(blockchain.chain)

        # Grab and verify the chains from all the nodes in our network
        for neighbour in neighbours:
            response = requests.get(f'{Node.prefix}{neighbour}/chain')
            mempool_resp = requests.get(f'{Node.prefix}{neighbour}/mempool')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and ValidChain.valid_chain(chain):
                    for transaction in mempool_resp.json():
                        # if the mempool is invalid we discard this nodes chain and proceed
                        if not Transaction.verify_transaction(transaction, chain, blockchain.coinbase_reward,
                                                              mp.pending_fees):
                            print('invalid mempool')
                            return False
                        max_length = length

        # if the mempool and chain are valid we add those values to our node
        new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:

            print("chain and mempool verified")
            current_mempool = mempool_resp.json()
            mp.current_transactions = current_mempool
            diff.level = Epoch.get_difficulty(f'{Node.prefix}{neighbour}')

            mp.clear_fees()

            for transaction in mp.current_transactions:
                mp.pending_fees += transaction['fee']

            Blockchain.chain = new_chain

            print("chain has been updated...")

            if os.path.exists('data/chain.json'):
                os.remove('data/chain.json')
                print("old chain removed, now writing new chainfile")
            else:
                print("no chainfile found... Creating it now.")

            with open('data/chain.json', 'w') as f:
                for i in Blockchain.chain:
                    string = json.dumps(i)
                    f.write(string)
                    f.write('\n')

            return True

        return False


class Difficulty:
    def __init__(self):
        self.last_block = blockchain.chain[-1]
        self.difficulty_1_target = 0xe0000000000000000000000000000000000000000000000000000000000000
        self.target_nonce = int(self.last_block['target_nonce_hex'], 16)
        self.level = self.difficulty_1_target / self.target_nonce

    def check_epoch_time(self):
        if Epoch.evaluate_epoch_difficulty(blockchain.chain) == "Increase":
            self.target_nonce = int(self.target_nonce * .9)
            print("increasing difficulty")
            self.level = self.difficulty_1_target / self.target_nonce
            print("Difficulty Level: ", self.level)
            print(hex(self.target_nonce))
            return True

        if Epoch.evaluate_epoch_difficulty(blockchain.chain) == "Decrease":
            print("decreasing difficulty")
            self.target_nonce = int(self.target_nonce * 1.1)
            self.level = self.difficulty_1_target / self.target_nonce
            print("Difficulty Level: ", self.level)
            print(hex(self.target_nonce))
            return True

        else:
            print('difficulty stable')


# Instantiate the Node
app = Flask(__name__)

# stop sorting keys
app.config['JSON_SORT_KEYS'] = False

# Instantiate the Blockchain, Difficulty, Node and Mempool classes
mp = Mempool()
blockchain = Blockchain()
diff = Difficulty()
node = Node()


@app.route('/fees', methods=['GET'])
def mempool_fees():
    return jsonify(mp.pending_fees), 200


@app.route('/coinbase', methods=['GET'])
def coinbase():
    return jsonify(blockchain.coinbase_reward), 200


@app.route('/mempool', methods=['GET'])
def mempool():
    return jsonify(mp.current_transactions), 200


@app.route('/lastblock', methods=['GET'])
def last_block():
    return blockchain.last_block, 200


@app.route('/nonce', methods=['GET'])
def target_nonce():
    proof = diff.target_nonce
    return jsonify(proof), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def all_nodes():
    response = {
        'message': 'all nodes',
        'total_nodes': list(node.nodes),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    for neighbour in nodes:
        if neighbour in node.nodes:
            return "Error: Node already registered", 600

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 500

    for neighbour in nodes:
        node.register_node(neighbour)
        mempool_resp = requests.get(f'{neighbour}/mempool')
        for transaction in mempool_resp.json():
            if not Transaction.verify_transaction(transaction, blockchain.chain, blockchain.coinbase_reward,
                                                  mp.pending_fees):
                return "Invalid transaction in mempool", 850

        current_mempool = mempool_resp.json()
        mp.current_transactions = current_mempool
        diff.level = Epoch.get_difficulty(neighbour)

    mp.pending_fees = 0

    for transaction in mp.current_transactions:
        mp.pending_fees += transaction['fee']

    print(f'got mempool:\n{mp.current_transactions}')
    print(f'pending fees: {mp.pending_fees}')

    node.resolve_conflicts()

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(node.nodes),
    }
    return jsonify(response), 201


@app.route('/block', methods=['POST'])
def receive_block():
    values = request.get_json()
    required = ['index', 'difficulty', 'previous_hash', 'block_hash', 'nonce', 'target_nonce_hex', 'timestamp',
                'transactions', 'public_key', 'signature']
    if not all(k in values for k in required):
        # if not we return an error so the sending node can do something
        return "block broadcast denied", 400

    print("Received new block! Now validating...")

    # code to validate block
    index = values['index']
    target_nonce = diff.target_nonce
    last_block_index = blockchain.last_block['index']

    forged_block = {
        'index': values['index'],
        'difficulty': values['difficulty'],
        'previous_hash': values['previous_hash'],
        'block_hash': values['block_hash'],
        'nonce': values['nonce'],
        'target_nonce_hex': values['target_nonce_hex'],
        'timestamp': values['timestamp'],
        'transactions': values['transactions'],
        'public_key': values['public_key'],
        'signature': values['signature']
    }
    if forged_block == blockchain.chain[-1]:
        print("block already received")
        return "block already received", 201

    if not index - last_block_index == 1:
        print('stale block')
        return "out of order", 500

    if not ValidBlock.validate_block(target_nonce=target_nonce, block_data=values):
        return "invalid block", 600

    else:

        print("target_nonce ", hex(diff.target_nonce))

        for transaction in values['transactions']:
            if not Transaction.verify_transaction(transaction, blockchain.chain,
                                                  coinbase_reward=blockchain.coinbase_reward,
                                                  fee_reward=mp.pending_fees):
                print("received block contains invalid transaction... Discarding.")
                return "invalid transaction in block", 650

        Write.write_chain(forged_block)
        blockchain.chain.append(forged_block)

        for transaction in values['transactions']:
            if transaction in mp.current_transactions:
                mp.current_transactions.remove(transaction)

        mp.clear_fees()
        mp.assess_fees()

        print("Block", forged_block['index'], "valid! Successfully added to chain")

    if index % 10 == 0:
        diff.check_epoch_time()

    # list for storing the failed nodes
    failed_nodes = []
    prefix = Node.prefix

    if len(node.nodes) > 0:

        # iterate through nodes to broadcast the new block
        for neighbour in node.nodes:
            # Broadcast the block to the registered nodes
            broadcast_status = Broadcast.broadcast_block(block=values, node=neighbour)

            # if a node times out or doesnt return a response we will add it to the failed nodes list
            if broadcast_status == "TimeoutError":
                failed_nodes.append(neighbour)

            if broadcast_status == "Block Received":
                print(neighbour, " has already received block ", forged_block['index'])

            # if the broadcast is rejected we will resolve our chain.
            if broadcast_status:
                print("Broadcast Accepted!")

            if broadcast_status == "Block Invalid":
                Node.resolve_conflicts()

            else:
                Node.resolve_conflicts()
                # if the function returns False the block is denied.
                print("broadcast denied")
                return "block broadcast denied", 700

        # if the length of the failed node list is greater than zero
        # we iterate through the list and remove those nodes.
        if len(failed_nodes) > 0:
            for neighbour in failed_nodes:
                address = prefix + neighbour
                Node.remove_node(address)

        return "ok", 200
    else:
        return "ok", 200


@app.route('/difficulty', methods=['GET'])
def difficulty():
    return jsonify(diff.level)


@app.route('/balance', methods=['GET'])
def balance():
    address = request.args.get('address')

    if address is None:
        return 'Missing address', 400

    if len(address) < 40 or len(address) > 40:
        return 'Invalid address', 400

    bal = Funds.enumerate_funds(address, blockchain.chain)

    if bal >= 0:
        response = {
            'address': address,
            'balance': bal,
        }
        return jsonify(response), 200

    # If balance is false, the address no found on blockchain
    if not bal:
        response = {
            'message': 'address not found',
        }
        return jsonify(response), 400

@app.route('/transactions/new', methods=['POST'])
def receive_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'fee', 'time_submitted', 'previous_hash', 'public_key_hex',
                'transaction_hash', 'signature']

    print("transaction received\n", values)

    # Check that the required fields are in the POST'ed data
    if not all(k in values for k in required):
        print('Error 400: Transaction Malformed')
        return 'Missing values', 400

        # Check if this address already has a transaction in the chain
    for transaction in mp.current_transactions:
        if transaction['sender'] == values['sender']:
            print('Error 420: One Transaction per Block')
            return 'One Transaction per block, wait for next block confirmation', 420

        # Validates the public_key_hash also known as the address.
    if not Hash_Validation.validate_pubkey_hash(pubkey=values['public_key_hex'], provided_pubkey_hash=values['sender']):
        print('Error 480: provided address does not match locally hashed result of provided public key')
        return "Error 490", 490

        # Check if the sender is trying to send themselves coins to the same address, this is not allowed
    if values['sender'] == values['recipient']:
        return "You cant send a transaction to yourself", 430

    if not mp.transaction_in_pool(values):
        if Transaction.verify_transaction(values=values, chain=blockchain.chain, coinbase_reward=None, fee_reward=None):
            # Create a new Transaction in the mempool to await confirmation

            transaction = {
                'sender': values['sender'],
                'recipient': values['recipient'],
                'amount': values['amount'],
                'fee': values['fee'],
                'time_submitted': values['time_submitted'],
                'previous_hash': values['previous_hash'],
                'public_key_hex': values['public_key_hex'],
                'transaction_hash': values['transaction_hash'],
                'signature': values['signature']
            }
            mp.pending_fees += float(transaction['fee'])
            mp.current_transactions.append(transaction)
            for node in Node.nodes:
                Broadcast.broadcast_transaction(transaction, node)
            return "ok", 201




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=blockchain.port)
