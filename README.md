# Python-Blockchain

A blockchain written in python which outputs and reads chain data from a json file. The code was adapted from the following tutorial and expanded upon.

> https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

The original code was not persistent between restarts of the program; and any values stored in the chain table would be lost.
I thought that wasn't very cash money and learning to work with JSON objects sounded like fun.

# How to use
```
1. Start blockchain.py node, (and provide it a port number to run on) to generate wallet.json, and chain.json.
2. If a node already exists call the /nodes/register API on the new node the receive the chain (explained further below in the readme).
3. Call the /nodes/register API on the existing node to tell it about the new blockchain.py node so that any blocks confirmed by each node can be shared.
4. Start pool.py and connect it to the IP and port number of a blockchain.py node, pool.py will always run on port 6000.
5. To begin mining, start miner.py and select the mode.
6. If you are solo mining you should connect miner.py directly to the blockchain node to receive proofs, for example 192.168.0.25:5000.
7. if you are pool mining you should connect miner.py to the pool.py node, and specify port 6000, for example 192.168.0.20:6000.
8. Miners will now be attempting to solve proofs either through a pool or solo.
9. Congrats! the blockchain network is now set up!
10. Upon miners receiving rewards, wallet.py can be used to send coins to other addresses on the network.
11. any transactions sent from the wallet.py or pool.py will confirm in the next block.
```


# Features

## blockchain.py
This is the main blockchain node that everything will connect to, including other blockchain.py nodes, as well as pool.py, and wallet.py. The blockchain will verify funds, hashes, and signatures and forge blocks with new transactions waiting to be confirmed in the mem-pool when a miner or pool finds the correct proof for the next block.
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

## miner.py
This is the miner for the blockchain that will attempt to forge new blocks by solving proofs that output to a defined hash structure; which will solve for the next block. The miner has two modes, solo and pool.
### Solo Mining
In this mode the miner will connect directly to the blockchain node to obtain the last blocks proof, and attempt to compute what the next proof is.
Note: currently when solo mining, a miner will not see an update in the last proof until it has finished finding a correct proof.
### Pool Mining
miner.py will pool together hashes with other miners, upon a miner finding a valid proof it will submit the proof to the pool, and each miner will receive a share of the coinbase reward.
Note: currently pool mode is must slower at solving blocks than solo mode, this is a known issue/limitation of the code currently.


## pool.py
This is the pool node which miners configured to pool mode will connect to. pool.py verifies all submitted tested proofs from miners and tallys the total number submitted by each miner. After a block is solved, will calculate each miners share of the coinbase reward from the amount of valid shares they submitted in that given block time. Once a miner reachs 100 coins they will be eligible for a payout. Once per block the pool will submit 1 payout transaction to a miner with over 100 coins in unpaid reward balance, this transaction should confirm in the next block.
### Share verification
pool.py will verify submitted shares to check if the proofs in a share (last_proof, proof) produce the hash value provided to the pool by a miner. When a share is verified to be correct it is tallied in a dictionary with the miners address as the key.
### Reward distribution
upon pool.py receiving a valid proof and forging a block, the pool will begin to calculate the share of the coinbase reward for each miner and add the value to a dictionary with the miners address as the key. When a miners balance exceeds the payout threshold the pool will submit a transaction to the blockchain to pay the miner their accumulated unpaid reward.


## wallet.py
This is the GUI wallet for ease of sending transactions to the blockchain. Simply input the address of the recipient, the amount to send, and hit OK. If you have enough funds, and dont have an existing transaction in the mem-pool; your transaction will be broadcasted to the network and confirmed in the next block.
### GUI (wallet.py)
a simple GUI to send transactions to the blockchain node without having to interact with a terminal.
![wallet init](pictures/wallet-init.png)
### Transaction History
view your transaction history within the wallet
![wallet-transaction-history](pictures/wallet-transaction-history.png)

##API Calls


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

Nodes will also resolve their chain when registering a new node.



##Requirements

install the requirements with

````
pip3 install -r requirements.txt
````



##To Do/Future feature wishlist

```
Node Persistence, nodes do not remember each other if shutdown.

implement signature validation within amount validation for extra security

continue work on the wallet.py, The GUI is much better than CLI, but it could use some touches || WIP

Fix up some of the response codes and json messages between the wallet.py and blockchain.py

Blockchain explorer to view the chain in more detail/more easily.

Improve the performance of pool mining within miner.py, currently the mining loop for pool mining is quite inefficient. || WIP

an actual personal use case? apart from learning?  || WIP

code clean up, bug fixes, and optimisation || WIP

increase code robustness so entering an incorrect value doesnt crash the program etc. || WIP

Unit test more of the code
```


