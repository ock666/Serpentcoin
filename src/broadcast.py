import requests
from requests.exceptions import Timeout
from time import time


class Broadcast:
    def __init__(self):
        print("broadcast module starting....")

    @staticmethod
    def broadcast_difficulty(difficulty, node):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(f'http://{node}/diffupdate', json=difficulty, headers=headers)
        try:
            if response.status_code == 200:
                print(f'difficulty update accepted by {node}')

        except:
            return "TimeoutError"

    @staticmethod
    def broadcast_transaction(transaction, node):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(f'http://{node}/transactions/new', json=transaction, headers=headers)
        try:
            if response.status_code == 201:
                print('transaction broadcast accepted by: ', node)

            else:
                print('transaction broadcast denied by: ', node)

        except:
            return "TimeoutError"


    @staticmethod
    def broadcast_block(block, node):

        current_time = str(time())
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        try:
            response = requests.post(f'http://{node}/block', json=block, headers=headers)

            if response.status_code == 200:
                print("Block broadcast accepted by ", node, "at ", current_time)
                return True

            if response.status_code == 201:
                print("Block broadcast already received by ", node)
                return "Block Received"

            if response.status_code == 400:
                print("block malformed")
                return "Block Malformed"

            if response.status_code == 500:
                print("block out of order")
                return "Block Out Of Order"

            if response.status_code == 600:
                print("block invalid")
                return "Block Invalid"

        except:
            return "TimeoutError"


