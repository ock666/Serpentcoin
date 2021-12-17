# python-blockchain

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
6. Recieve mined blocks from other nodes /broadcast 	//POST 
```

install the requirements with

```
pip3 install -r requirements.txt
```

Feel free to reimplement the code however you please.

### chain.json
Included with the repo is is a data directory containing a placeholder chain.json with 2 blocks.
feel free to delete this file as the program will regenerate the directory and file if they are not present,
any changes to the hardcoded genesis block will require a new chain to be made regardless.


```
TO DO

Integrate code to allow for nodes, whats a blockchain without decentralisation? DONE [x]

a fully hectic PoW algorithm (PoS actually stands for piece of shit)

balance checking with public/private keys, UTXO's? I honestly am probably getting in over my head.

an actual personal use case? apart from learning?  || WIP

Block and transaction broadcast on network || WIP

```


