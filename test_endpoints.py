#!/usr/bin/env python3
"""
Test script to verify all Flask API endpoints are working correctly.
This script tests both the existing endpoints and the new ones from test_flask.py.
"""

import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, files=None, description=""):
    """Test a single endpoint and return the result."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            elif isinstance(data, dict):
                response = requests.post(url, json=data)
            else:
                response = requests.post(url, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            json_response = response.json()
            print("JSON Response:")
            print(json.dumps(json_response, indent=2))
        except:
            # If not JSON, show text response (truncated)
            text_response = response.text[:500]
            if len(response.text) > 500:
                text_response += "... (truncated)"
            print("Text Response:")
            print(text_response)
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask server!")
        print("Make sure the Flask app is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all endpoint tests."""
    print("🧪 Flask API Endpoint Testing Suite")
    print("=" * 60)
    
    results = []
    
    # Test main application routes
    tests = [
        ("GET", "/", None, None, "Home page"),
        ("GET", "/shopping", None, None, "Shopping assistant page"),
        ("GET", "/chatbot", None, None, "Chatbot page"),
        ("GET", "/local-tasks", None, None, "Local tasks page"),
        ("GET", "/terminal", None, None, "Terminal page (from test_flask.py)"),
    ]
    
    # Test API endpoints
    api_tests = [
        ("GET", "/api/status", None, None, "System status and information"),
        
        ("POST", "/api/search", {
            "query": "Find the best laptop under 50000"
        }, None, "Product search with AI analysis"),
        
        ("POST", "/api/chat", {
            "message": "Hello, how are you?",
            "file_content": None
        }, None, "Basic chatbot conversation"),
        
        ("POST", "/api/chat", {
            "message": "Explain this code",
            "file_content": "print('Hello World')\nfor i in range(5):\n    print(i)"
        }, None, "Chatbot with file content analysis"),
        
        # Local tasks tests
        ("POST", "/api/local-task/open_vscode", {}, None, "Open VS Code"),
        ("POST", "/api/local-task/show_system_info", {}, None, "Get system information"),
        
        # Terminal functionality tests (from test_flask.py)
        ("POST", "/run", {
            "cmd": "echo Hello from Flask API test"
        }, None, "Execute terminal command"),
        
        ("POST", "/write", {
            "filename": "test_file.txt",
            "content": "This is a test file created by the Flask API test script.\nCurrent time: " + str(time.time())
        }, None, "Create and write file"),
    ]
    
    # Run all tests
    all_tests = tests + api_tests
    
    for method, endpoint, data, files, description in all_tests:
        success = test_endpoint(method, endpoint, data, files, description)
        results.append((endpoint, success))
        time.sleep(1)  # Small delay between requests
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {endpoint}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Flask backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the Flask server logs for details.")
    
    return passed == total

def test_file_upload():
    """Test file upload functionality separately."""
    print(f"\n{'='*60}")
    print("Testing File Upload Endpoint")
    print(f"{'='*60}")
    
    # Create a test file
    test_content = "This is a test file for upload.\nLine 2\nLine 3"
    with open("temp_test_file.txt", "w") as f:
        f.write(test_content)
    
    try:
        with open("temp_test_file.txt", "rb") as f:
            files = {"file": ("test_upload.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/api/file-upload", files=files)
        
        print(f"Status Code: {response.status_code}")
        try:
            json_response = response.json()
            print("JSON Response:")
            print(json.dumps(json_response, indent=2))
        except:
            print("Text Response:", response.text[:500])
        
        return response.status_code == 200
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists("temp_test_file.txt"):
            os.remove("temp_test_file.txt")

if __name__ == "__main__":
    print("Starting Flask API tests...")
    print("Make sure the Flask server is running: python app.py")
    print("Press Ctrl+C to cancel...")
    
    try:
        time.sleep(2)  # Give user time to read
        success = main()
        
        # Test file upload separately
        upload_success = test_file_upload()
        
        if success and upload_success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
        sys.exit(0) 