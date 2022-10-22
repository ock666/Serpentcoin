import binascii
import json
import hashlib
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from src.utilities import Hash


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
            transactions = block['transactions']
            for transaction in transactions:
                recipient = transaction['recipient']
                sender = transaction['sender']

                if recipient == address:
                    amount = transaction['amount']
                    outputs.append(amount)

                if sender == address:
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
        signature_decoded = binascii.unhexlify(signature.encode("utf-8"))
        public_key_decoded = binascii.unhexlify(public_key.encode("utf-8"))
        public_key_object = RSA.import_key(public_key_decoded)

        transaction_bytes = json.dumps(transaction_data, sort_keys=True).encode("utf-8")
        transaction_hash = SHA256.new(transaction_bytes)
        pkcs1_15.new(public_key_object).verify(transaction_hash, signature_decoded)
        return True


class ValidChain:

    @staticmethod
    def validate_nonce(target_nonce, block):
        """
        function to validate numbers only used once
        """
        encoded_block = f'{block}'.encode()
        value = int.from_bytes(hashlib.sha256(encoded_block).digest(), 'little')
        if value <= target_nonce:
            return True
        if value >= target_nonce:
            return False

    @staticmethod
    def valid_chain(chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        for block in chain:

            target = int(block['target_nonce_hex'], 16)

            # Check that the Proof of Work is correct
            if not ValidBlock.validate_block(block_data=block, target_nonce=target):
                return False

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
    def verify_transaction(values, chain, coinbase_reward, fee_reward):
        """
        function to verify a transaction, transaction is hashed
        and checked against the hash provided in the 'transaction_hash' field of the transaction
        if valid, proceeds. Next the attached signature is validated against the public key, if valid, proceeds.
        Finally if all checks have passed, the function will check if the address has enough balance for the transaction.
        If all checks pass the function will return True and the transaction will be considered valid.
        """

        # Format for transaction data for hash verification
        trans_to_be_hashed = {
            'sender': values['sender'],
            'recipient': values['recipient'],
            'amount': values['amount'],
            'fee': values['fee'],
            'time_submitted': values['time_submitted'],
            'previous_hash': values['previous_hash'],
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
            'previous_hash': values['previous_hash'],
            'public_key_hex': values['public_key_hex'],
            'transaction_hash': values['transaction_hash']
        }

        # This line checks the signature against the broadcasted data If true we proceed
        # If not we throw out the transaction as it has been tampered with
        if not Signature.validate_signature(values['public_key_hex'], values['signature'], trans_to_be_validated):
            return False, "signature invalid"


        # Check if a transaction is a coinbase or fee reward transaction as a result of forging a block
        if values['sender'] == "Coinbase Reward":
            # Check to make sure the correct amount of coins has been forged
            if values['amount'] != coinbase_reward:
                print("Incorrect coinbase reward, discarding...")
                return False
            return True

        if values['sender'] == "Fee Reward":
            # Check if a fee reward transaction contains the appropriate fees
            if values['amount'] != fee_reward:
                print("Incorrect fee reward, discarding...")
                return False
            return True

        else:
            # Check if funds are available for the given address,
            if Funds.enumerate_funds(address=values['sender'], chain=chain) >= values['amount']:
                print('funds are available')
                return True

            else:
                print("not enough funds")
                return False


class ValidBlock:
    @staticmethod
    def validate_block(block_data, target_nonce):
        """
        function to evaluate a forged block received from another node.
        function will check if the proof is valid, taking into account
        the last proof, new proof and difficulty.
        If the proof is confirmed the function will check the provided
        hash against a locally hashed result, if the hashes match the block is considered valid.
        """

        block = {
            'index': block_data['index'],
            'difficulty': block_data['difficulty'],
            'previous_hash': block_data['previous_hash'],
            'nonce': block_data['nonce'],
            'target_nonce_hex': block_data['target_nonce_hex'],
            'timestamp': block_data['timestamp'],
            'transactions': block_data['transactions']

        }


        nonce_confirmed = ValidChain.validate_nonce(target_nonce=target_nonce, block=block)
        if nonce_confirmed:
            block_hash = Hash.hash(block)

            if block_hash != block_data['block_hash']:
                print("Provided block hash differs from locally hashed result")
                print("Local Hash: ", block_hash)
                print("Supplied Hash: ", block_data['block_hash'])
                return False



            index = block_data['index']
            difficulty = block_data['difficulty']
            previous_hash = block_data['previous_hash']
            block_hash = block_data['block_hash']
            nonce = block_data['nonce']
            target_nonce_hex = block_data['target_nonce_hex']
            timestamp = block_data['timestamp']
            transactions = block_data['transactions']
            public_key = block_data['public_key']

            block = {
                'index': index,
                'difficulty': difficulty,
                'previous_hash': previous_hash,
                'block_hash': block_hash,
                'nonce': nonce,
                'target_nonce_hex': target_nonce_hex,
                'timestamp': timestamp,
                'transactions': transactions,
                'public_key': public_key,
            }

            if Signature.validate_signature(public_key=block_data['public_key'], signature=block_data['signature'],
                                            transaction_data=block):
                return True
            else:
                print("signature validation failed")
                return False
        else:
            print("block nonce failed")


Hash_Validation = Hash_Validation()
Signature = Signature()
