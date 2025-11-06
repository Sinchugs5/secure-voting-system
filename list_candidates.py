#!/usr/bin/env python3
import sqlite3
import os

DATABASE = 'Election.db'

def list_candidate_table():
    """List the Candidate table structure and contents"""
    
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found!")
        return
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get table schema
        print("=" * 60)
        print("CANDIDATE TABLE SCHEMA")
        print("=" * 60)
        
        cursor.execute("PRAGMA table_info(Candidate)")
        columns = cursor.fetchall()
        
        if not columns:
            print("Candidate table does not exist!")
            conn.close()
            return
        
        print("Column Name       | Type    | Not Null | Default | Primary Key")
        print("-" * 60)
        for col in columns:
            cid, name, type_, notnull, default, pk = col
            print(f"{name:<17} | {type_:<7} | {notnull:<8} | {default or 'NULL':<7} | {pk}")
        
        # Get table contents
        print("\n" + "=" * 60)
        print("CANDIDATE TABLE CONTENTS")
        print("=" * 60)
        
        cursor.execute("SELECT * FROM Candidate")
        candidates = cursor.fetchall()
        
        if not candidates:
            print("No candidates found in the table.")
        else:
            print(f"Total candidates: {len(candidates)}")
            print("\nName        | Party      | Age | Gender | Email           | Phone      | Symbol")
            print("-" * 80)
            for candidate in candidates:
                print(f"Candidate data length: {len(candidate)}")
                print(f"Data: {candidate}")
                
                # Handle different schema lengths
                name = candidate[0] if len(candidate) > 0 else 'N/A'
                
                if len(candidate) >= 10:  # New full schema
                    _, party_name, photo, description, party_name_new, symbol, age, gender, email, phone = candidate
                    party_name = party_name_new if party_name_new else party_name
                    age_str = str(age) if age else 'N/A'
                    gender_str = gender if gender else 'N/A'
                    email_str = (email[:15] + '...') if email and len(email) > 15 else (email or 'N/A')
                    phone_str = phone if phone else 'N/A'
                    symbol_str = 'Yes' if symbol else 'No'
                    print(f"{name:<11} | {party_name:<10} | {age_str:<3} | {gender_str:<6} | {email_str:<15} | {phone_str:<10} | {symbol_str}")
                elif len(candidate) == 4:  # Old schema
                    _, class_name, photo, description = candidate
                    print(f"{name:<11} | {class_name:<10} | N/A | N/A    | N/A             | N/A        | N/A")
                else:
                    print(f"{name:<11} | Mixed schema - {len(candidate)} fields")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_candidate_table()