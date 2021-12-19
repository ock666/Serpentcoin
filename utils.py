import json
import requests


def response_translator(response, node):
    if response.status_code == 201:
        return 'transaction broadcast accepted by: ', node

    if response.status_code == 200:
        return 'transaction signature not valid as calculated by: ', node

    if response.status_code == 400:
        return 'transaction missing values according to: ', node

    if response.status_code == 420:
        return 'One Transaction per block, wait for next block confirmation says: ', node

    if response.status_code == 440:
        return 'Transaction already in this nodes mem-pool', node




def generate_wallet():

    private_key = RSA.generate(2048)
    private_key_plain = private_key.export_key("PEM")
    public_key_plain = private_key.publickey().export_key("PEM")
    public_key = private_key.publickey().export_key("DER")
    public_key_hex = binascii.hexlify(public_key).decode("utf-8")
    public_key_hash = self.calculate_hash(self.calculate_hash(public_key_hex, hash_function="sha256"),
                                              hash_function="ripemd160")