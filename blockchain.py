import hashlib
import json
import time
from datetime import datetime

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 1

    def create_genesis_block(self):
        return Block(0, [], time.time(), "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        block = Block(
            len(self.chain),
            self.pending_transactions,
            time.time(),
            self.get_latest_block().hash
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []

    def create_vote_transaction(self, voter_name, voter_id, candidate, timestamp):
        return {
            "type": "VOTE",
            "voter_name": voter_name,
            "voter_id": voter_id,
            "candidate": candidate,
            "timestamp": timestamp,
            "hash": hashlib.sha256(f"{voter_id}{candidate}{timestamp}".encode()).hexdigest()
        }

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

    def get_vote_count(self, candidate):
        count = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("type") == "VOTE" and transaction.get("candidate") == candidate:
                    count += 1
        return count

    def get_all_votes(self):
        votes = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("type") == "VOTE":
                    votes.append(transaction)
        return votes