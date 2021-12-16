# python-blockchain

A simple blockchain which outputs and reads chain data from a json file. The code was adapted from the following tutorial
> https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

The original code was not persistant between restarts of the program; and any values stored in the chain table would be lost.
I thought that wasn't very cash money and learning to work with JSON objects sounded like fun.

The blockchain can be interacted with using either Postman or simple cURL commands to send POST/GET requests to the API to either:

```
1. Mine a block /mine
2. Submit a new transaction /transactions/new
3. Request the blockchain history /chain
```

install the requirements with

```
pip3 install -r requirements.txt
```

Feel free to reimplement the code however you please.

TO DO
```
Integrate code to allow for nodes, whats a blockchain without decentralisation?

a fully hectic PoW algorithm (PoS actually stands for piece of shit)

balance checking

an actual personal use case? apart from learning?

```


