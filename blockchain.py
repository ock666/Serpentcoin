import os
import json
from time import time
from src.utils import Generate, Write, Hash
from src.validation import Transaction, ValidChain, ValidBlock, Hash_Validation
from src.epoch import Epoch
from flask import Flask, request, jsonify
from Crypto.PublicKey import RSA
import requests
from urllib.parse import urlparse
from src.broadcast import Broadcast


class Blockchain:
    def __init__(self):
        # list for storing the chain
        self.chain = []

        # port to run blockchain on
        self.port = input("input a port number: ")

        if not os.path.exists('data'):
            print('creating data directory')
            os.makedirs('data')

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

        # if no chain exists, forges a genesis block
        if not os.path.isfile('data/chain.json'):
            print("now generating genesis block")
            Block.genesis(previous_hash='Times, Chancellor on brink of second bailout for banks', proof=30109)

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

        print("Now validating local chain, please wait.")
        if ValidChain.valid_chain(self.chain):
            print("Chain is valid")
        else:
            print("Local chain is invalid, please sync the node with another upstream node.")

        # current difficulty
        self.difficulty = self.last_block['difficulty'] or 5

    @property
    def last_proof(self):
        """
        Returns the last proof
        """
        return self.last_block['proof']

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
        return last_block['current_hash']

    def check_epoch_time(self):
        if not Epoch.evaluate_epoch_difficulty(self.chain):
            blockchain.difficulty += 1
            return True

        if Epoch.evaluate_epoch_difficulty(self.chain):
            blockchain.difficulty -= 1
            return True

        else:
            return False


class Block:
    @staticmethod
    def genesis(proof, previous_hash=None):
        unix_time = time()
        block = {
            'index': 1,
            'timestamp': unix_time,
            'transactions': [],
            'difficulty': 4,
            'proof': proof,
            'previous_hash': previous_hash
        }

        block_hash = Hash.hash(block)

        block_with_hash = {
            'index': 1,
            'timestamp': unix_time,
            'transactions': [],
            'difficulty': 4,
            'proof': proof,
            'previous_hash': previous_hash,
            'current_hash': block_hash
        }

        # opens the chain.json file and writes the genesis block to it
        with open('data/chain.json', 'w') as f:
            block_dict = json.dumps(block_with_hash)
            f.write(block_dict)
            f.write('\n')

    @staticmethod
    def new_block(proof, time, mempool, previous_hash=None):
        block = {
            'index': len(blockchain.chain) + 1,
            'timestamp': time,
            'transactions': mempool,
            'difficulty': blockchain.difficulty,
            'proof': proof,
            'previous_hash': previous_hash
        }

        block_hash = Hash.hash(block)

        block_with_hash = {
            'index': len(blockchain.chain) + 1,
            'timestamp': time,
            'transactions': mempool,
            'difficulty': blockchain.difficulty,
            'proof': proof,
            'previous_hash': previous_hash,
            'current_hash': block_hash
        }

        Write.write_chain(block_with_hash)
        blockchain.chain.append(block_with_hash)
        if block['index'] % Epoch.block_epoch == 0:
            if blockchain.check_epoch_time():
                print(f"Difficulty adjusted to {blockchain.difficulty}")

        # list for storing the failed nodes
        failed_nodes = []
        prefix = "http://"

        # iterate through nodes to broadcast the new block
        for neighbour in node.nodes:
            # Broadcast the block to the registered nodes
            broadcast_status = Broadcast.broadcast_block(block=block_with_hash, node=neighbour)

            # if a node times out or doesnt return a response we will add it to the failed nodes list
            if broadcast_status == "TimeoutError":
                failed_nodes.append(neighbour)

            # if the broadcast is successful we clear the mempool
            if broadcast_status:
                mp.clear_mempool()
                mp.clear_fees()

            # if the broadcast is rejected we will resolve our chain.
            if not broadcast_status:
                Node.resolve_conflicts()

        # if the length of the failed node list is greater than zero
        # we iterate through the list and remove those nodes.
        if len(failed_nodes) > 0:
            for neighbour in failed_nodes:
                address = prefix + neighbour
                Node.remove_node(address)

        return block_with_hash


class Mempool:
    def __init__(self):
        # pending transactions waiting to be added to a block
        self.current_transactions = []

        # total pending fees
        self.pending_fees = 0

    def clear_mempool(self):
        self.current_transactions = []

    def clear_fees(self):
        self.pending_fees = 0

    def transaction_in_pool(self, transaction):
        if transaction in self.current_transactions:
            return True
        return False

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

        if sender == "Coinbase Reward" or sender == "Transaction Fee Reward":
            self.current_transactions.append(trans_data)

        else:
            self.current_transactions.append(trans_data)
            nodes = node.nodes
            for neighbour in nodes:
                if Broadcast.broadcast_transaction(trans_data, neighbour):
                    print("Transaction Broadcast accepted")

                else:
                    pass
        return True

    def new_coinbase_transaction(self, values):
        confirming_address = values['public_key_hash']
        public_key_hex = values['public_key_hex']
        previous_hash = values['previous_block_hash']
        signature = values['signature']
        unix_time = time()

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

        hashed_reward = Hash.hash(json.dumps(block_reward_transaction, sort_keys=True))

        full_block_reward_transaction = {
            'sender': 'Coinbase Reward',
            'recipient': confirming_address,
            'amount': 10,
            'fee': 0,
            'time_submitted': block_reward_transaction['time_submitted'],
            'previous_block_hash': previous_hash,
            'public_key_hex': public_key_hex,
            'signature': signature,
            'transaction_hash': hashed_reward
        }

        # We must receive a reward for finding the proof.
        # The sender is "Coinbase" to signify a new block reward has been mined.
        self.new_transaction(full_block_reward_transaction['sender'],
                             full_block_reward_transaction['recipient'],
                             full_block_reward_transaction['amount'],
                             full_block_reward_transaction['fee'],
                             full_block_reward_transaction['time_submitted'],
                             full_block_reward_transaction['previous_block_hash'],
                             full_block_reward_transaction['public_key_hex'],
                             full_block_reward_transaction['transaction_hash'],
                             full_block_reward_transaction['signature'])

    @staticmethod
    def new_fee_reward_transaction(values):
        confirming_address = values['public_key_hash']
        public_key_hex = values['public_key_hex']
        previous_hash = values['previous_block_hash']
        signature = values['signature']
        unix_time = time()
        fees = mp.pending_fees
        if fees > 0:
            fee_reward_trans = {
                'sender': 'Transaction Fee Reward',
                'recipient': confirming_address,
                'amount': fees,
                'fee': 0,
                'time_submitted': unix_time,
                'previous_block_hash': previous_hash,
                'public_key_hex': public_key_hex,
                'signature': signature
            }

            hashed_fees = Hash.hash(fee_reward_trans)

            fee_reward_trans_with_hash = {
                'sender': 'Transaction Fee Reward',
                'recipient': confirming_address,
                'amount': fees,
                'fee': 0,
                'time_submitted': unix_time,
                'previous_block_hash': previous_hash,
                'public_key_hex': public_key_hex,
                'signature': signature,
                'transaction_hash': hashed_fees
            }

            mp.new_transaction(fee_reward_trans_with_hash['sender'],
                               fee_reward_trans_with_hash['recipient'],
                               fee_reward_trans_with_hash['amount'],
                               fee_reward_trans_with_hash['fee'],
                               fee_reward_trans_with_hash['time_submitted'],
                               fee_reward_trans_with_hash['previous_block_hash'],
                               fee_reward_trans_with_hash['public_key_hex'],
                               fee_reward_trans_with_hash['transaction_hash'],
                               fee_reward_trans_with_hash['signature'])
            mp.pending_fees = 0


class Node:
    # set for storing nodes
    nodes = set()

    def __init__(self):


        choice = input("would you like to connect to a node? y/n\n")
        if choice == "y":
            prefix = "http://"
            node_input = input("Please input the address of a node i.e 192.168.0.xxx:xxxx:\n")

            # here we register our first node upon start up
            self.register_node(str(prefix + node_input))

            # get the blockchain from the registered neighbour
            self.resolve_conflicts()
        else:
            pass

    def register_node(self, address):
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
            response = requests.get(f'http://{neighbour}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and ValidChain.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            blockchain.chain = new_chain

            print("chain updated")

            if os.path.exists('data/chain.json'):
                os.remove('data/chain.json')
                print("old chain removed, now writing new chain")
            else:
                print("no chain data found... Creating it now.")

            with open('data/chain.json', 'w') as f:
                for i in blockchain.chain:
                    string = json.dumps(i)
                    f.write(string)
                    f.write('\n')

            return True

        return False


# Instantiate the Node
app = Flask(__name__)

# Instantiate the Blockchain, Node and Mempool classes
mp = Mempool()
blockchain = Blockchain()
node = Node()


# Unique address on the chain is a 2 part hash of our public key
node_identifier = blockchain.public_key_hash


@app.route('/difficulty', methods=['GET'])
def difficulty():
    return jsonify(blockchain.difficulty)


@app.route('/mempool', methods=['GET'])
def mempool():
    return jsonify(mp.current_transactions), 200


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


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount', 'fee', 'time_submitted', 'previous_block_hash', 'public_key_hex',
                'transaction_hash', 'signature']

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

        # check if the minimum fee has been paid
    if values['fee'] < .0005:
        return "Please send transaction with minimum fee of .0005", 410

    if not mp.transaction_in_pool(values):
        if Transaction.verify_transaction(values=values, chain=blockchain.chain):
            # Create a new Transaction in the mempool to await confirmation
            if mp.new_transaction(values['sender'], values['recipient'], values['amount'],
                                  values['fee'],
                                  values['time_submitted'], values['previous_block_hash'],
                                  values['public_key_hex'], values['transaction_hash'],
                                  values['signature']):
                mp.pending_fees += values['fee']
                return "ok", 201


@app.route('/broadcast', methods=['POST'])
def receive_block():
    values = request.get_json()
    # check all the block info has been submitted
    required = ['index', 'timestamp', 'transactions', 'difficulty', 'proof', 'previous_hash', 'current_hash']
    if not all(k in values for k in required):
        # if not we return an error so the sending node can do something
        return "block broadcast denied", 400

    # if all goes as planned we continue
    index = values['index']
    last_proof = blockchain.last_proof
    last_block_index = blockchain.last_block['index']

    if not index - last_block_index == 1:
        print('blocks out of order... resolving')
        Node.resolve_conflicts()
        return "out of order", 400



    # call function to validate block
    if ValidBlock.validate_received_block(values, last_proof, blockchain.difficulty):
        # if valid we append it to the local chain
        Write.write_chain(values)
        blockchain.chain.append(values)
        # and clear the mempool
        mp.clear_mempool()
        mp.clear_fees()
        # check to see if the block index is the beginning of a new epoch to do difficulty calculations
        if index % 100 == 0:
            blockchain.check_epoch_time()

        # list for storing the failed nodes
        failed_nodes = []
        prefix = "http://"

        # iterate through nodes to broadcast the new block
        for neighbour in node.nodes:
            # Broadcast the block to the registered nodes
            broadcast_status = Broadcast.broadcast_block(block=values, node=neighbour)

            # if a node times out or doesnt return a response we will add it to the failed nodes list
            if broadcast_status == "TimeoutError":
                failed_nodes.append(neighbour)


            # if the broadcast is rejected we will resolve our chain.
            if not broadcast_status:
                Node.resolve_conflicts()

            # if the length of the failed node list is greater than zero
            # we iterate through the list and remove those nodes.
            if len(failed_nodes) > 0:
                for neighbour in failed_nodes:
                    address = prefix + neighbour
                    Node.remove_node(address)

        return "ok", 200
    else:
        Node.resolve_conflicts()
    # if the function returns False the block is denied.
        return "block broadcast denied", 400


@app.route('/miners', methods=['POST'])
def receive_proof():
    # table for storing received json
    values = request.get_json()
    unix_time = time()

    submitted_last_proof = values['last_proof']
    last_proof = blockchain.last_block['proof']

    if submitted_last_proof == last_proof:
        if Transaction.verify_proof_transaction(values=values, last_proof=last_proof, difficulty=blockchain.difficulty):
            proof = values['proof']
            previous_block_hash = values['previous_block_hash']
            mp.new_coinbase_transaction(values=values)
            if mp.pending_fees > 0:
                mp.new_fee_reward_transaction(values=values)
            Block.new_block(proof=proof, time=unix_time, mempool=mp.current_transactions,
                            previous_hash=previous_block_hash)
            mp.clear_mempool()
            return "proof accepted", 200
    return "stale proof", 400


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    for neighbour in nodes:
        if neighbour in node.nodes:
            return "Error: Node already registered", 400

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for neighbour in nodes:
        node.register_node(neighbour)
        mempool_resp = requests.get(f'{neighbour}/mempool')
        current_mempool = mempool_resp.json()
        mp.current_transactions = current_mempool
        blockchain.difficulty = Epoch.get_difficulty(neighbour)

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


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = node.resolve_conflicts()

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


@app.route('/nodes', methods=['GET'])
def all_nodes():
    response = {
        'message': 'all nodes',
        'total_nodes': list(node.nodes),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=blockchain.port)
