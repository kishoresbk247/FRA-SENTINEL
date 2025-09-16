#!/usr/bin/env python3
"""
Test script to verify upload route is working correctly
"""

import requests
import json

def test_upload_route():
    """Test the upload route directly"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Upload Route")
    print("=" * 50)
    
    # Test 1: Check if upload route exists
    try:
        # Try to access the upload route (should redirect to login)
        response = requests.post(f"{base_url}/upload_patta", allow_redirects=False)
        if response.status_code in [302, 401, 403]:
            print("✅ Upload route exists and redirects properly")
        else:
            print(f"❌ Upload route returned unexpected status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask app is running.")
        return
    
    # Test 2: Check if admin panel is accessible
    try:
        response = requests.get(f"{base_url}/admin_panel", allow_redirects=False)
        if response.status_code in [302, 401, 403]:
            print("✅ Admin panel route exists and redirects properly")
        else:
            print(f"❌ Admin panel returned unexpected status: {response.status_code}")
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
    print("6. You should see: '✅ File [filename] uploaded successfully! Added Test Village to map with coordinates (22.0000, 80.0000).'")
    print("7. Go back to dashboard and check if new marker appears on map")
    
    print("\n🔍 Expected Results:")
    print("- NO MORE 'Claim ID and document are required' error")
    print("- Success message should appear after upload")
    print("- New blue marker should appear on map at coordinates (22.0000, 80.0000)")
    print("- Marker popup should show 'Test Village' and 'Test Holder'")

if __name__ == "__main__":
    test_upload_route()
