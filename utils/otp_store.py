# utils/otp_store.py
# Simple in-memory store for OTPs. For production use Redis or DB.
import time

# structure: { email: {"otp": "123456", "expires": 1670000000.0} }
store = {}
