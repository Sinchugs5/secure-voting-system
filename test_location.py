#!/usr/bin/env python3
"""
Test script to verify location functionality
"""
import requests

def test_reverse_geocoding():
    """Test reverse geocoding with the provided coordinates"""
    latitude = 12.3307739
    longitude = 76.6037222
    
    print(f"Testing reverse geocoding for coordinates: {latitude}, {longitude}")
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'VotingSystem/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            print("Raw response:")
            print(f"  Display name: {data.get('display_name', 'N/A')}")
            print(f"  Address components: {address}")
            
            # Build location string from components
            location_parts = []
            if address.get('house_number'):
                location_parts.append(address['house_number'])
            if address.get('road'):
                location_parts.append(address['road'])
            if address.get('suburb') or address.get('neighbourhood'):
                location_parts.append(address.get('suburb') or address['neighbourhood'])
            if address.get('city') or address.get('town') or address.get('village'):
                location_parts.append(address.get('city') or address.get('town') or address['village'])
            if address.get('state'):
                location_parts.append(address['state'])
            
            formatted_location = ', '.join(location_parts) if location_parts else f"Lat: {latitude}, Lng: {longitude}"
            
            print(f"\nFormatted location: {formatted_location}")
            print(f"Google Maps URL: https://www.google.com/maps?q={latitude},{longitude}&z=15")
            
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_reverse_geocoding()