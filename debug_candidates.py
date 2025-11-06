#!/usr/bin/env python3
import sqlite3
import json

DATABASE = 'Election.db'

def debug_candidates():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # This is the exact query from get_stats route
    cursor.execute('''
        SELECT c.Name, c.Photo, c.PartyName, c.Symbol, COALESCE(r.Votes, 0) as Votes 
        FROM Candidate c 
        LEFT JOIN Result r ON c.Name = r.Name 
        ORDER BY COALESCE(r.Votes, 0) DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    print("Query Results:")
    for i, result in enumerate(results):
        print(f"Candidate {i+1}:")
        print(f"  Name: {result[0]}")
        print(f"  Photo: {result[1]}")
        print(f"  PartyName: {result[2]}")
        print(f"  Symbol: {result[3]}")
        print(f"  Votes: {result[4]}")
        print()
        
        # Create the JSON structure that would be sent to frontend
        candidate_json = {
            'name': result[0],
            'photo': result[1],
            'party_name': result[2],
            'symbol': result[3],
            'votes': result[4]
        }
        print(f"JSON: {json.dumps(candidate_json, indent=2)}")
        print("-" * 50)

if __name__ == "__main__":
    debug_candidates()