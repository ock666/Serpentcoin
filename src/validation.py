import binascii
import json
import hashlib
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from src.utils import Hash



class Funds:
    @staticmethod
    def enumerate_funds(address, chain):
        """
        function to enumerate funds from a given address.
        returns a balance if greater than 0
        returns False otherwise.
        """
        inputs = []
        outputs = []
        iteration_count = 0

        for block in chain:
            iteration_count += 1
            for transaction in block['transactions']:

                if transaction['recipient'] == address:
                    amount = transaction['amount']
                    outputs.append(amount)

                if transaction['sender'] == address:
                    amount = transaction['amount']
                    fee = transaction['fee']
                    inputs.append(amount)
                    inputs.append(fee)

        total_outputs = sum(outputs)
        total_inputs = sum(inputs)

        balance = total_outputs - total_inputs

        if balance > 0:
            return balance

        elif balance <= 0:
            return False


class Signature:

    def sign_data(self, data, key):
        """
        Signs data to be verified later.
        Sorts the keys in the data, encodes in 'utf-8'
        creates a SHA256 hash and signs the hash
        decodes from 'utf-8'
        returns readable signature
        Function can be used to sign transaction data
        """
        transaction_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        print(transaction_bytes)
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(key).sign(hash_object)
        return binascii.hexlify(signature).decode("utf-8")
    @staticmethod
    def validate_signature(public_key, signature, transaction_data):
        """
        Function for validation of signatures in submitted transactions
        will return True upon a valid signature,
        or False upon failing to verify a signature
        """
        try:
            signature_decoded = binascii.unhexlify(signature.encode("utf-8"))
            public_key_decoded = binascii.unhexlify(public_key.encode("utf-8"))
            public_key_object = RSA.import_key(public_key_decoded)

            transaction_bytes = json.dumps(transaction_data, sort_keys=True).encode("utf-8")

            transaction_hash = SHA256.new(transaction_bytes)
            pkcs1_15.new(public_key_object).verify(transaction_hash, signature_decoded)
            return True

        except:
            return False


class ValidChain:

    @staticmethod
    def validate_proof(last_proof, proof, difficulty):
        """
        function to validate proofs
        """
        valid_guess = ""
        for i in range(difficulty):
            valid_guess += "0"
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == valid_guess

    @staticmethod
    def valid_chain(chain):
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
                'difficulty': last_block['difficulty'],
                'proof': last_block['proof'],
                'previous_hash': last_block['previous_hash']
            }

            block = chain[current_index]

            # Check that the hash of the blocks is consistent
            if last_block['current_hash'] != block['previous_hash']:
                print("hashes on chain dont match when syncing... ignored this chain")

                return False
            # Hash the block ourselves to check for tampering
            if last_block['current_hash'] != Hash.hash(last_block_no_hash):
                print(last_block['current_hash'], " not equal to ", Hash.hash(last_block_no_hash))
                return False

            # Check that the Proof of Work is correct
            if not ValidChain.validate_proof(last_block['proof'], block['proof'], block['difficulty']):
                print('invalid proof on block when syncing')
                return False

            last_block = block
            current_index += 1

        return True


class Hash_Validation:
    def validate_pubkey_hash(self, pubkey, provided_pubkey_hash):
        """
        Validate whether a pubkey included in a transaction actually matches the pub_key hash
        included in the transaction, returns True if yes, False if no.
        """
        local_key_hash = Hash.calculate_hash(Hash.calculate_hash(pubkey, hash_function="sha256"),
                                              hash_function="ripemd160")
        if provided_pubkey_hash != local_key_hash:
            return False
        return True

class Transaction:

    @staticmethod
    def verify_proof_transaction(values, last_proof, difficulty):
        """
        function to verify a submitted proof transaction from a miner
        returns True in the case of a valid proof
        """
        required = ['public_key_hash', 'public_key_hex', 'previous_block_hash', 'proof', 'signature']
        if not all(k in values for k in required):
            print('Error 400: Transaction Malformed')
            return 'Missing values', 400

        # variables for storing the transaction data
        proof = values['proof']


        # check to see if the proof is valid
        proof_valid = ValidChain.validate_proof(last_proof, proof, difficulty)

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

            # Format of proof data to be verified
            trans_data = {
                'proof': proof,
                'last_proof': last_proof,
                'public_key_hash': confirming_address,
                'public_key_hex': public_key_hex,
                'previous_block_hash': previous_hash
            }

        if Signature.validate_signature(public_key=public_key_hex, signature=signature, transaction_data=trans_data):
            return True

        if not Signature.validate_signature(public_key=public_key_hex, signature=signature, transaction_data=trans_data):
            print('signature failed verification')
            return "signature malformed", 400


    @staticmethod
    def verify_transaction(values, chain):
        """
        function to verify a transaction, transaction is hashed
        and checked against the hash provided in the 'transaction_hash' field of the transaction
        if valid, proceeds. Next the attached signature is validated against the public key, if valid, proceeds.
        Finally if all checks have passed, the function will check if the address has enough balance for the transaction.
        If all checks pass the function will return True and the transaction will be considered valid.
        """
        # If all API checks clear continue validation
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
        local_trans_hash = Hash.hash(trans_to_be_hashed)

        # If the transaction fails hash verification we throw it out and return an error
        if local_trans_hash != values['transaction_hash']:
            print("Transaction hash mismatch")
            response = {'message': f'Transaction hash failed CRC'}
            return False

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
        if Signature.validate_signature(values['public_key_hex'], values['signature'], trans_to_be_validated):

            # Check if funds are available for the given address,
            if Funds.enumerate_funds(address=
                    values['sender'], chain=chain) >= values['amount']:
                print('funds are available')

                return True

            # If theres not enough funds we throw an error and discard the transaction
            else:
                return False, "not enough funds"
        # If the signature fails verification we throw out the transaction and throw an error
        else:
            return False, "signature invalid"

class ValidBlock:
    @staticmethod
    def validate_received_block(block_data, last_proof, difficulty):
        """
        function to evaluate a forged block received from another node.
        function will check if the proof is valid, taking into account
        the last proof, new proof and difficulty.
        If the proof is confirmed the function will check the provided
        hash against a locally hashed result, if the hashes match the block is considered valid.
        """
        proof = block_data['proof']
        proof_confirmed = ValidChain.validate_proof(last_proof, proof, difficulty)
        if proof_confirmed:
            block = {
                'index': block_data['index'],
                'timestamp': block_data['timestamp'],
                'transactions': block_data['transactions'],
                'difficulty': block_data['difficulty'],
                'proof': block_data['proof'],
                'previous_hash': block_data['previous_hash']
            }

            block_hash = Hash.hash(block)

            if block_hash != block_data['current_hash']:
                print("Provided block hash differs from locally hashed result")
                return False
        print("block valid!")
        return True


Hash_Validation = Hash_Validation()
Signature = Signature()