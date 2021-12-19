# Python-Blockchain

A simple blockchain which outputs and reads chain data from a json file. The code was adapted from the following tutorial
> https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

The original code was not persistant between restarts of the program; and any values stored in the chain table would be lost.
I thought that wasn't very cash money and learning to work with JSON objects sounded like fun.

The blockchain can be interacted with using either Postman or simple cURL commands to send POST/GET requests to the API to either:

```
1. Mine a block /mine 					\\ GET
2. Submit a new transaction /transactions/new 		// POST
3. Request the blockchain history /chain 		\\ GET
4. Register a new node /nodes/register 			// POST
5. Resolve chain data /nodes/resolve 			\\ GET
6. Receive mined blocks from other nodes /broadcast 	//POST 
```

install the requirements with

```
pip3 install -r requirements.txt
```

Feel free to reimplement the code however you please.

### chain.json / wallet.json
Included with the repo is is a data directory containing a placeholder chain.json and wallet.json.
feel free to delete these files as the program will regenerate the directory and files if they are not present,
any changes to the hardcoded genesis block will require a new chain to be made regardless.
## Features
### Block Solution Broadcast
The blockchain now has the capability to share newly mined block with other nodes, receiving nodes will perform 
validation on the new block to confirm the proof
### Signature Validation
Nodes will verify the public key hex and the signature to verify a transaction. if the signature verification fails, 
the transaction is denied.
### Balance Verification
Nodes will check the balance of an address from the blockchain, if a sender has insufficient balance.
The transaction will be denied.
### Transaction Broadcast
Upon receiving and verifying a new transaction nodes will broadcast the transaction to other nodes,
receiving nodes will check if the transaction is already in their mem-pool, perform their own validation; and either accept or deny the transaction.
### Simple wallet (wallet.py)
a simple CLI wallet to send transactions to the blockchain node. 

```
TO DO

implement signature validation within amount validation for extra security

continue work on the wallet.py, it is currently quite rudimentary and has a type error with the time() function occuring after sending a transaction and attempting to send another

Fix up some of the response codes and json messages between the wallet.py and blockchain.py

Integrate code to allow for nodes, whats a blockchain without decentralisation? DONE [x]

Block and transaction broadcast on network || DONE [x]

balance checking with public/private keys, UTXO's? DONE [x]

a fully hectic PoW algorithm (PoS actually stands for piece of shit)

an actual personal use case? apart from learning?  || WIP

code clean up, it works but its kind of a mess right now haha || WIP
```


