#!/usr/bin/env python3
"""
Test script to verify upload functionality works correctly
"""

import requests
import json
import os

def test_upload_functionality():
    """Test the upload functionality"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Upload Functionality")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask app is running.")
        return
    
    # Test 2: Check FRA data API
    try:
        response = requests.get(f"{base_url}/api/fra_data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ FRA data API working - {len(data.get('features', []))} features")
            print(f"   Current villages: {[f['properties']['village'] for f in data.get('features', [])]}")
        else:
            print("❌ FRA data API not working")
    except Exception as e:
        print(f"❌ FRA data API error: {e}")
    
    # Test 3: Check admin panel access
    try:
        response = requests.get(f"{base_url}/admin_panel")
        if response.status_code == 200:
            print("✅ Admin panel accessible")
        else:
            print("❌ Admin panel not accessible")
    except Exception as e:
        print(f"❌ Admin panel error: {e}")
    
    print("\n📋 Manual Test Instructions:")
    print("1. Open browser and go to: http://localhost:5000")
    print("2. Login with: ccf.admin@fra.gov.in / fra2025ccf")
    print("3. Click 'Admin' → 'Upload Document'")
    print("4. Fill the form with:")
    print("   - Village Name: Test Village")
    print("   - Patta Holder: Test Holder")
    print("   - Latitude: 22.0000")
    print("   - Longitude: 80.0000")
    print("   - Area: 3.5")
    print("   - Upload any PDF file")
    print("5. Click 'Upload Patta Document'")
    print("6. Check if success message appears")
    print("7. Go back to dashboard and check if new marker appears on map")
    
    print("\n🔍 Expected Results:")
    print("- Success message should appear after upload")
    print("- New blue marker should appear on map at coordinates (22.0000, 80.0000)")
    print("- Marker popup should show 'Test Village' and 'Test Holder'")

if __name__ == "__main__":
    test_upload_functionality()
