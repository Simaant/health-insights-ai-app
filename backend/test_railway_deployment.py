#!/usr/bin/env python3
"""
Test script to verify Railway deployment is working
"""
import requests
import json

def test_railway_deployment():
    base_url = "https://health-insights-ai-app-production.up.railway.app"
    
    print("🧪 Testing Railway Deployment...")
    print(f"Base URL: {base_url}")
    
    # Test 1: Health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
        else:
            print("   ❌ Health endpoint failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 200:
            print("   ✅ Root endpoint working")
        else:
            print("   ❌ Root endpoint failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Debug routes endpoint
    print("\n3. Testing debug routes endpoint...")
    try:
        response = requests.get(f"{base_url}/debug/routes", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            routes = response.json()
            print(f"   ✅ Found {len(routes.get('routes', []))} routes")
            
            # Check for key endpoints
            route_paths = [r.get('path', '') for r in routes.get('routes', [])]
            key_endpoints = ['/reports/upload', '/auth/login', '/chat/sessions']
            
            for endpoint in key_endpoints:
                if endpoint in route_paths:
                    print(f"   ✅ {endpoint} registered")
                else:
                    print(f"   ❌ {endpoint} missing")
        else:
            print("   ❌ Debug routes endpoint failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Simple test endpoint
    print("\n4. Testing simple test endpoint...")
    try:
        response = requests.get(f"{base_url}/simple", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 200:
            print("   ✅ Simple test endpoint working")
        else:
            print("   ❌ Simple test endpoint failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Railway deployment test completed!")

if __name__ == "__main__":
    test_railway_deployment()
