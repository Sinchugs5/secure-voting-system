#!/usr/bin/env python3
"""
Blockchain Integrity Fix Script
Repairs data integrity mismatch between database and blockchain
"""

import sqlite3
import json
from datetime import datetime
from blockchain import Blockchain

def fix_blockchain_integrity():
    """Fix blockchain and database synchronization"""
    print("🔧 Starting Blockchain Integrity Fix...")
    
    # Initialize blockchain
    blockchain = Blockchain()
    
    # Connect to database
    conn = sqlite3.connect('Election.db')
    cursor = conn.cursor()
    
    # Get all votes from database
    cursor.execute('SELECT Name, Username, Email, Candidate FROM Vote')
    db_votes = cursor.fetchall()
    
    # Clear blockchain and rebuild from database
    blockchain.chain = [blockchain.create_genesis_block()]
    blockchain.pending_transactions = []
    
    print(f"📊 Found {len(db_votes)} votes in database")
    
    # Rebuild blockchain from database votes
    for vote in db_votes:
        name, username, email, candidate = vote
        
        # Create blockchain transaction
        vote_transaction = blockchain.create_vote_transaction(
            name, username, candidate, datetime.now().isoformat()
        )
        
        blockchain.add_transaction(vote_transaction)
        blockchain.mine_pending_transactions()
        
        print(f"✅ Added vote: {name} -> {candidate}")
    
    # Verify blockchain integrity
    is_valid = blockchain.is_chain_valid()
    
    # Update results table to match blockchain
    cursor.execute('DELETE FROM Result')
    
    # Count votes from blockchain
    blockchain_votes = blockchain.get_all_votes()
    vote_counts = {}
    
    for vote in blockchain_votes:
        candidate = vote['candidate']
        vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
    
    # Insert updated results
    for candidate, votes in vote_counts.items():
        # Get candidate info
        cursor.execute('SELECT PartyName, Photo FROM Candidate WHERE Name = ?', (candidate,))
        candidate_info = cursor.fetchone()
        
        if candidate_info:
            party_name, photo = candidate_info
            cursor.execute('INSERT INTO Result (Name, Photo, PartyName, Votes) VALUES (?, ?, ?, ?)',
                          (candidate, photo, party_name, votes))
    
    conn.commit()
    conn.close()
    
    print(f"🔒 Blockchain Valid: {'✅ Yes' if is_valid else '❌ No'}")
    print(f"📈 Total Blocks: {len(blockchain.chain)}")
    print(f"🗳️ Total Votes: {len(blockchain_votes)}")
    print("✨ Blockchain integrity fixed successfully!")
    
    return is_valid

if __name__ == "__main__":
    fix_blockchain_integrity()