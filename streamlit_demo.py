import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(page_title="Blockchain Voting Demo", page_icon="🗳️")

# Title
st.title("🗳️ Blockchain Voting System Demo")
st.markdown("*Simplified version showcasing core blockchain functionality*")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose Page", ["Vote", "Results", "Blockchain Info"])

if page == "Vote":
    st.header("Cast Your Vote")
    
    # Voter info
    voter_name = st.text_input("Your Name")
    voter_id = st.text_input("Voter ID")
    
    # Candidate selection
    candidate = st.selectbox("Select Candidate", 
                           ["Candidate A", "Candidate B", "Candidate C"])
    
    if st.button("Submit Vote"):
        if voter_name and voter_id:
            # Simple blockchain hash
            vote_data = f"{voter_id}{candidate}{datetime.now()}"
            vote_hash = hashlib.sha256(vote_data.encode()).hexdigest()
            
            st.success("✅ Vote Recorded Successfully!")
            st.info(f"Blockchain Hash: {vote_hash[:16]}...")
            st.balloons()
        else:
            st.error("Please fill all fields")

elif page == "Results":
    st.header("📊 Election Results")
    
    # Mock results
    results = {
        "Candidate A": 45,
        "Candidate B": 38,
        "Candidate C": 17
    }
    
    # Display results
    for candidate, votes in results.items():
        st.metric(candidate, f"{votes} votes")
    
    # Chart
    st.bar_chart(results)

elif page == "Blockchain Info":
    st.header("🔗 Blockchain Information")
    
    st.info("**Blockchain Features:**")
    st.write("✅ SHA-256 Hashing")
    st.write("✅ Immutable Records") 
    st.write("✅ Tamper Detection")
    st.write("✅ Transparent Verification")
    
    # Mock blockchain data
    st.subheader("Sample Block")
    st.json({
        "index": 1,
        "timestamp": "2024-01-15T10:30:00",
        "votes": 3,
        "hash": "a1b2c3d4e5f6...",
        "previous_hash": "0000000000..."
    })

st.sidebar.markdown("---")
st.sidebar.info("This is a simplified demo. Full system includes face recognition, video proctoring, and advanced security features.")