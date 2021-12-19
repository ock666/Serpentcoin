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
                amount = int(transaction['amount'])
                outputs.append(int(amount))


            if transaction['sender'] == address:
                amount = int(transaction['amount'])
                inputs.append(int(amount))

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
        print("signature: ", signature_decoded)
        public_key_decoded = binascii.unhexlify(public_key.encode("utf-8"))
        print(public_key_decoded)
        public_key_object = RSA.import_key(public_key_decoded)

        transaction_bytes = json.dumps(transaction_data, sort_keys=True).encode("utf-8")
        print(transaction_bytes)

        transaction_hash = SHA256.new(transaction_bytes)
        pkcs1_15.new(public_key_object).verify(transaction_hash, signature_decoded)
        return True

    except:
        return False




publickey = \
    """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv/UWVuwMHWl00AG8zeZb
mDeKLKmswTadbxWtRYH1s3GKp0fU/YVZ4MvmUWJz/VYMszUTIZ3pzAnM6Xbz2OI+
vo+JyIFfgH0j4RLK4jGQDby4jJwfIQZWznwGHo7WL9zJbVw1VolilPXPj+rnGXZQ
y65TGma/pC0lUjbI3RHP25V+JtWpbFBOEtGQuYJ/7GjKWmpxIwHSGCmPLf4yhacL
OlHl6UioYv7S2bkHc6L66RgPJDYfdX0WwqmwmgIXmJTpCezEsIn/zSOwm1woL3lN
gvBpa9rZiKmvvJQqXwwUUPydv0RA3WfF/gcqEMBHwj2KV6kwTey0bgb80GjOZBfv
7QIDAQAB
-----END PUBLIC KEY-----"""

