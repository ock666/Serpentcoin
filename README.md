# Python-Blockchain

A blockchain written in python which outputs and reads chain data from a json file. The code was adapted from the following tutorial and expanded upon.

> https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

The original code was not persistant between restarts of the program; and any values stored in the chain table would be lost.
I thought that wasn't very cash money and learning to work with JSON objects sounded like fun.

The blockchain can be interacted with using either Postman or simple cURL commands to send POST/GET requests to the API to either:

````
1. Request the blockchain history /chain 		\\ GET
````
![postman chain request](pictures/postman-chain-get.png)
``````
2. Register a new node /nodes/register 			// POST
``````
![syntax for node registration](pictures/postman-node-register.png)
``````````
3. Resolve/update node chain data /nodes/resolve 			\\ GET
``````````
![postman resolve node chain](pictures/postman-resolve-node.png)

Nodes will also resolve when registering a new node.


The blockchain can also be interacted with using the miner.py, pool.py, and wallet.py. Each serve their own function

### blockchain.py
This is the main blockchain node that everything will connect to, including other blockchain.py nodes, as well as pool.py, and wallet.py. The blockchain will verify funds, hashes, and signatures and forge blocks with new transactions waiting to be confirmed in the mem-pool when a miner or pool finds the correct proof for the next block.
### miner.py
This is the miner for the blockchain that will attempt to forge new blocks by solving proofs that output to a defined hash structure; which will solve for the next block. The miner has two modes, solo and pool. In solo mode the miner must be connected to blockchain.py directly, in pool mode it must connect to pool.py.
Note: currently pool mode is must slower at solving blocks than solo mode, this is a known issue/limitation of the code currently.
### pool.py
This is the pool node which miners configured to pool mode will connect to. pool.py verifies all submitted tested proofs from miners and tallys the total number submitted by each miner. After a block is solved, will calculate each miners share of the coinbase reward from the amount of valid shares they submitted in that given block time. Once a miner reachs 100 coins they will be eligible for a payout. Once per block the pool will submit 1 payout transaction to a miner with over 100 coins in unpaid reward balance, this transaction should confirm in the next block.
### wallet.py
This is the GUI wallet for ease of sending transactions to the blockchain. Simply input the address of the recipient, the amount to send, and hit OK. If you have enough funds, and dont have an existing transaction in the mem-pool; your transaction will be broadcasted to the network and confirmed in the next block.
### chain.json / wallet.json
Included with the repo is is a data directory containing a placeholder chain.json and wallet.json.
feel free to delete these files as the program (blockchain.py) will regenerate the directory and files if they are not present,
any changes to the hardcoded genesis block will require a new chain to be made regardless.



install the requirements with

````
pip3 install -r requirements.txt
````

Feel free to reimplement the code however you please.


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
### Hash Verification
The blockchain will check the hashes of any broadcasted transactions or blocks to ensure authenticity in transmission.
### Transaction Broadcast
Upon receiving and verifying a new transaction nodes will broadcast the transaction to other nodes,
receiving nodes will check if the transaction is already in their mem-pool, perform their own validation; and either accept or deny the transaction.
### Pool Mining
pool.py pools together hashes checked by miners, checks for total shares upon a solved block and calculates each miners earned reward. Pays out a maximum of 1 miner per block per pool. 
### GUI wallet (wallet.py)
a simple GUI wallet to send transactions to the blockchain node.

![wallet init](pictures/wallet-init.png)
### Miner (miner.py)
a miner which gets the last block and performs proof of work, submits the proof to a node upon completion for the block reward

![miner.py](pictures/miner-and-chain.png)
### Transaction History
view your transaction history within the wallet

![wallet-transaction-history](pictures/wallet-transaction-history.png)


```
TO DO

Node Persistence, nodes do not remember each other if shutdown.

implement signature validation within amount validation for extra security

continue work on the wallet.py, The GUI is much better than CLI, but it could use some touches || WIP

Fix up some of the response codes and json messages between the wallet.py and blockchain.py

Block and transaction broadcast on network || DONE [x]

Improve the performance of pool mining within miner.py, currently the mining loop for pool mining is quite inefficient.

an actual personal use case? apart from learning?  || WIP

code clean up, bug fixes, and optimisation || WIP

increase code robustness so entering an incorrect value doesnt crash the program etc. || WIP
```


