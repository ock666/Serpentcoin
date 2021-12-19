import binascii
import json

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


def enumerate_funds(address, chain):
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
                inputs.append(amount)

    total_outputs = sum(outputs)
    total_inputs = sum(inputs)

    balance = total_outputs - total_inputs

    if balance > 0:
        return balance

    elif balance <= 0:
        return False


def transaction_in_pool(transaction_list, transaction):
    for entry in transaction_list:
        if transaction == entry:
            return True
    return False



def validate_signature(public_key, signature, transaction_data):
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





